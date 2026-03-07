import { COOKIE_NAME } from "@shared/const";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { protectedProcedure, publicProcedure, router } from "./_core/trpc";
import { z } from "zod";
import {
  getMercadoStatus,
  getAtletasMercado,
  getRawMercado,
  getAtletasPontuados,
  getPartidas,
  getClubes,
  getDbStats,
  getJogadorHistorico,
  getJogadoresRodada,
  getRodadasProcessadas,
  getCompetParalelas,
  getStatusColeta,
  getHistoricoRodadas,
  getMediaPosicao,
  getTopJogadoresRodada,
  getJogadorHistoricoCompleto,
  calcularTimeIdeal,
} from "./cartola";
import { EstrategiaV7, FORMACOES, POSICAO_MAP, type Escalacao, type Jogador } from "./estrategia";
import { neonQuery } from "./neonDb";
import { simularViaPython, escalarViaPython, checkPythonServiceHealth, getMercadoRanqueado } from "./pythonService";

// Calculate valorização considering substitutions (same logic as Python)
function calcularValorizacaoComSubstituicoes(esc: any): number {
  const jogadores = esc.jogadores || [];
  const reservas = esc.reservas || {};
  const reservaLuxo = esc.reserva_luxo;

  // Track each titular
  const jogInfo: Record<string, { pontos: number | null; pos_id: number; variacao: number; entrou: boolean; substituido: boolean; subLuxo: boolean }> = {};
  for (const j of jogadores) {
    const aid = String(j.atleta_id || '');
    const pontos = j.pontos_real ?? null;
    jogInfo[aid] = {
      pontos,
      pos_id: j.pos_id,
      variacao: parseFloat(j.variacao || '0') || 0,
      entrou: j.entrou_em_campo ?? (pontos !== null),
      substituido: false,
      subLuxo: false,
    };
  }

  // Normal reserves substitution
  const reservasQueEntraram: any[] = [];
  for (const posIdStr of Object.keys(reservas)) {
    const reserva = reservas[posIdStr];
    if (!reserva) continue;
    const resId = String(reserva.atleta_id || '');
    if (reservaLuxo && resId === String(reservaLuxo.atleta_id || '')) continue;
    const pontosRes = reserva.pontos_real ?? null;
    const resEntrou = reserva.entrou_em_campo ?? (pontosRes !== null);
    const posId = parseInt(posIdStr);
    const tits = Object.entries(jogInfo).filter(([, info]) => info.pos_id === posId && !info.substituido);
    for (const [aid, info] of tits) {
      const titNaoJogou = !info.entrou || info.pontos === null;
      if (titNaoJogou && (resEntrou || pontosRes !== null)) {
        jogInfo[aid].substituido = true;
        reservasQueEntraram.push(reserva);
        break;
      }
    }
  }

  // Luxury reserve substitution
  let luxoEntrou = false;
  if (reservaLuxo) {
    const luxoPosId = reservaLuxo.pos_id;
    const pontosLuxo = reservaLuxo.pontos_real ?? null;
    if (pontosLuxo !== null) {
      const tits = Object.entries(jogInfo).filter(([, info]) =>
        info.pos_id === luxoPosId && info.entrou && info.pontos !== null && !info.substituido
      );
      if (tits.length > 0) {
        const pior = tits.reduce((best, cur) => (cur[1].pontos! < best[1].pontos! ? cur : best));
        if (pontosLuxo > pior[1].pontos!) {
          jogInfo[pior[0]].subLuxo = true;
          luxoEntrou = true;
        }
      }
    }
  }

  // Sum valorização of players who effectively played
  let val = 0;
  for (const [, info] of Object.entries(jogInfo)) {
    if (!info.substituido && !info.subLuxo) val += info.variacao;
  }
  for (const res of reservasQueEntraram) {
    val += parseFloat(res.variacao || '0') || 0;
  }
  if (luxoEntrou && reservaLuxo) {
    val += parseFloat(reservaLuxo.variacao || '0') || 0;
  }
  return Math.round(val * 100) / 100;
}

// Singleton engine instance
let engineInstance: EstrategiaV7 | null = null;
function getEngine(orcamento: number = 100, modoSimulacao: boolean = false): EstrategiaV7 {
  if (!engineInstance || modoSimulacao) {
    engineInstance = new EstrategiaV7(orcamento, modoSimulacao);
  }
  return engineInstance;
}

// In-memory escalação storage (per session)
let escalacaoAtual: Escalacao | null = null;
let escalacoesSalvas: Array<{
  id: string;
  rodada: number;
  ano: number;
  formacao: string;
  data: string;
  escalacao: Escalacao;
  pontosReais?: number;
  valorizacaoReal?: number;
  atualizado?: boolean;
}> = [];

// Load saved escalações from Neon on startup
async function carregarEscalacoesSalvas() {
  try {
    const rows = await neonQuery(`
      SELECT * FROM escalacoes_salvas 
      ORDER BY data_criacao DESC
      LIMIT 100
    `);
    if (rows && rows.length > 0) {
      escalacoesSalvas = rows.map((r: any) => ({
        id: String(r.id),
        rodada: Number(r.rodada),
        ano: Number(r.ano),
        formacao: String(r.formacao || '4-3-3'),
        data: String(r.data_criacao),
        escalacao: typeof r.escalacao_json === 'string' ? JSON.parse(r.escalacao_json) : r.escalacao_json,
        pontosReais: r.pontos_reais ? Number(r.pontos_reais) : undefined,
        valorizacaoReal: r.valorizacao_real ? Number(r.valorizacao_real) : undefined,
        atualizado: Boolean(r.atualizado),
      }));
    }
  } catch (e) {
    // Table may not exist yet - create it
    try {
      await neonQuery(`
        CREATE TABLE IF NOT EXISTS escalacoes_salvas (
          id SERIAL PRIMARY KEY,
          rodada INTEGER NOT NULL,
          ano INTEGER NOT NULL,
          formacao VARCHAR(10) DEFAULT '4-3-3',
          escalacao_json JSONB NOT NULL,
          pontos_reais DECIMAL(10,2),
          valorizacao_real DECIMAL(10,2),
          atualizado BOOLEAN DEFAULT FALSE,
          data_criacao TIMESTAMP DEFAULT NOW()
        )
      `);
    } catch (e2) {
      console.error('[DB] Error creating escalacoes_salvas table:', e2);
    }
  }
}

// Initialize on module load
carregarEscalacoesSalvas().catch(console.error);

export const appRouter = router({
  system: systemRouter,
  auth: router({
    me: publicProcedure.query(opts => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return { success: true } as const;
    }),
  }),

  // Cartola FC API proxy
  cartola: router({
    mercadoStatus: protectedProcedure.query(() => getMercadoStatus()),
    atletasMercado: protectedProcedure.query(() => getAtletasMercado()),

    mercadoRanqueado: protectedProcedure.query(async () => {
      const data = await getMercadoRanqueado();
      return data;
    }),
    atletasPontuados: protectedProcedure
      .input(z.object({ rodada: z.number().optional() }).optional())
      .query(({ input }) => getAtletasPontuados(input?.rodada)),
    partidas: protectedProcedure
      .input(z.object({ rodada: z.number().optional() }).optional())
      .query(({ input }) => getPartidas(input?.rodada)),
    clubes: protectedProcedure.query(() => getClubes()),
  }),

  // Neon DB queries
  db: router({
    stats: protectedProcedure.query(() => getDbStats()),
    jogadorHistorico: protectedProcedure
      .input(z.object({ atletaId: z.string(), limite: z.number().default(20) }))
      .query(({ input }) => getJogadorHistorico(input.atletaId, input.limite)),
    jogadorHistoricoCompleto: protectedProcedure
      .input(z.object({ atletaId: z.string(), limite: z.number().default(50) }))
      .query(({ input }) => getJogadorHistoricoCompleto(input.atletaId, input.limite)),
    jogadoresRodada: protectedProcedure
      .input(z.object({ rodada: z.number(), ano: z.number() }))
      .query(({ input }) => getJogadoresRodada(input.rodada, input.ano)),
    rodadasProcessadas: protectedProcedure.query(() => getRodadasProcessadas()),
    competParalelas: protectedProcedure
      .input(z.object({ atletaId: z.string() }))
      .query(({ input }) => getCompetParalelas(input.atletaId)),
    statusColeta: protectedProcedure.query(() => getStatusColeta()),
    historicoRodadas: protectedProcedure
      .input(z.object({ ano: z.number() }))
      .query(({ input }) => getHistoricoRodadas(input.ano)),
    mediaPosicao: protectedProcedure
      .input(z.object({ posicaoId: z.number(), rodada: z.number(), ano: z.number() }))
      .query(({ input }) => getMediaPosicao(input.posicaoId, input.rodada, input.ano)),
    topJogadoresRodada: protectedProcedure
      .input(z.object({ rodada: z.number(), ano: z.number(), limite: z.number().default(10) }))
      .query(({ input }) => getTopJogadoresRodada(input.rodada, input.ano, input.limite)),
    timeIdeal: protectedProcedure
      .input(z.object({ ano: z.number(), rodada: z.number(), orcamento: z.number().default(100), formacao: z.string().default('4-3-3') }))
      .query(({ input }) => calcularTimeIdeal(input.ano, input.rodada, input.orcamento, input.formacao)),
    pontosIdeaisBatch: protectedProcedure
      .input(z.object({ ano: z.number(), rodadas: z.array(z.number()) }))
      .query(async ({ input }) => {
        const results: Record<number, number> = {};
        for (const rodada of input.rodadas) {
          const ideal = await calcularTimeIdeal(input.ano, rodada, 999, '4-3-3');
          results[rodada] = ideal?.pontuacao_real || 0;
        }
        return results;
      }),
  }),

  // EstrategiaV7 - Motor de Escalação
  estrategia: router({
    // Escalar time com formação e orçamento
    escalarTime: protectedProcedure
      .input(z.object({
        formacao: z.string().default('4-3-3'),
        orcamento: z.number().default(100),
        rodada: z.number().optional(),
        ano: z.number().optional(),
        excluirIds: z.array(z.string()).optional(),
      }))
      .mutation(async ({ input }) => {
        // Try Python service first (identical results to Streamlit)
        const pyHealthy = await checkPythonServiceHealth();
        if (pyHealthy) {
          try {
            const pyResult = await escalarViaPython({
              formacao: input.formacao,
              orcamento: input.orcamento,
              ano: input.ano,
              rodada: input.rodada,
              excluir_ids: input.excluirIds,
            });
            
            const esc = pyResult.escalacao || {};
            const POS_MAP_INV: Record<number, string> = { 1: 'GOL', 2: 'LAT', 3: 'ZAG', 4: 'MEI', 5: 'ATA', 6: 'TEC' };
            
            // Map Python result to the expected frontend format
            const titulares = (esc.titulares || []).map((t: any) => ({
              atleta_id: String(t.atleta_id || ''),
              apelido: t.apelido || '',
              posicao_id: t.pos_id || 0,
              pos_id: t.pos_id || 0,
              posicao: t.posicao || POS_MAP_INV[t.pos_id] || 'N/A',
              preco: t.preco || 0,
              media: t.media || 0,
              score: t.score || 0,
              pontuacao_esperada: t.pontuacao_esperada || t.score || 0,
              clube_nome: t.clube || '',
              clube_id: t.clube_id || 0,
              valorizacao_prevista: t.valorizacao_prevista || 0,
              pontos_reais: t.pontos_reais || 0,
              explicacao: t.explicacao || {},
              explicacao_resumo: t.explicacao?.resumo || '',
            }));
            
            const capitao = esc.capitao ? {
              atleta_id: String(esc.capitao.atleta_id || ''),
              apelido: esc.capitao.apelido || '',
              posicao_id: esc.capitao.pos_id || 0,
              pos_id: esc.capitao.pos_id || 0,
              posicao: esc.capitao.posicao || POS_MAP_INV[esc.capitao.pos_id] || 'N/A',
              preco: esc.capitao.preco || 0,
              media: esc.capitao.media || 0,
              score: esc.capitao.score || 0,
              pontuacao_esperada: esc.capitao.pontuacao_esperada || esc.capitao.score || 0,
              clube_nome: esc.capitao.clube || '',
              clube: esc.capitao.clube || '',
              clube_id: esc.capitao.clube_id || 0,
              valorizacao_prevista: esc.capitao.valorizacao_prevista || 0,
              explicacao: esc.capitao.explicacao || {},
            } : null;
            
            const reservas: Record<string, any> = {};
            if (esc.reservas && typeof esc.reservas === 'object') {
              for (const [posId, r] of Object.entries(esc.reservas as Record<string, any>)) {
                if (r) {
                  reservas[posId] = {
                    atleta_id: String(r.atleta_id || ''),
                    apelido: r.apelido || '',
                    posicao_id: r.pos_id || Number(posId),
                    pos_id: r.pos_id || Number(posId),
                    posicao: r.posicao || POS_MAP_INV[Number(posId)] || 'N/A',
                    preco: r.preco || 0,
                    media: r.media || 0,
                    score: r.score || 0,
                    clube_nome: r.clube || '',
                  };
                }
              }
            }
            
            const reservaLuxo = esc.reserva_luxo ? {
              atleta_id: String(esc.reserva_luxo.atleta_id || ''),
              apelido: esc.reserva_luxo.apelido || '',
              posicao_id: esc.reserva_luxo.pos_id || 0,
              pos_id: esc.reserva_luxo.pos_id || 0,
              posicao: esc.reserva_luxo.posicao || POS_MAP_INV[esc.reserva_luxo.pos_id] || 'N/A',
              preco: esc.reserva_luxo.preco || 0,
              media: esc.reserva_luxo.media || 0,
              score: esc.reserva_luxo.score || 0,
              clube_nome: esc.reserva_luxo.clube || '',
            } : null;
            
            // Build top 10 per position from df_ranqueado
            const top10PorPosicao: Record<number, any[]> = {};
            const dfRanqueado = esc.df_ranqueado;
            if (dfRanqueado && typeof dfRanqueado === 'object' && dfRanqueado.apelido) {
              const idsEscalados = new Set(titulares.map((t: any) => String(t.atleta_id)));
              const indices = Object.keys(dfRanqueado.apelido || {});
              const jogadoresArr: any[] = indices.map(idx => ({
                atleta_id: String(dfRanqueado.atleta_id?.[idx] || dfRanqueado.id?.[idx] || ''),
                apelido: dfRanqueado.apelido?.[idx] || '',
                posicao_id: Number(dfRanqueado.posicao_id?.[idx] || 0),
                score: Number(dfRanqueado.score?.[idx] || dfRanqueado.pred?.[idx] || 0),
                preco: Number(dfRanqueado.preco?.[idx] || 0),
                media: Number(dfRanqueado.media?.[idx] || 0),
                clube_id: Number(dfRanqueado.clube_id?.[idx] || 0),
                clube_nome: dfRanqueado.clube_nome?.[idx] || dfRanqueado.clube_abreviacao?.[idx] || '',
                status_id: Number(dfRanqueado.status_id?.[idx] || 0),
                escalado: idsEscalados.has(String(dfRanqueado.atleta_id?.[idx] || dfRanqueado.id?.[idx] || '')),
              }));
              for (const posId of [1, 2, 3, 4, 5, 6]) {
                top10PorPosicao[posId] = jogadoresArr
                  .filter(j => j.posicao_id === posId && j.preco > 0)
                  .sort((a, b) => b.score - a.score)
                  .slice(0, 10);
              }
            }

            const escalacao = {
              titulares,
              capitao,
              reservas,
              reserva_luxo: reservaLuxo,
              pontuacao_esperada: esc.pontuacao_esperada || 0,
              custo_total: esc.custo_total || 0,
              orcamento_restante: esc.orcamento_restante || 0,
              formacao: esc.formacao || pyResult.formacao || input.formacao,
              valorizacao_total: esc.valorizacao_total || 0,
              estrategia_especial: esc.estrategia_especial || 'PADRÃO',
              fonte: 'python' as const,
              top10PorPosicao,
            };
            
            escalacaoAtual = escalacao as any;
            return escalacao;
          } catch (pyError: any) {
            console.error('[Escalação] Python service error, falling back to TypeScript:', pyError.message);
          }
        }
        
        // TypeScript fallback
        const engine = getEngine(input.orcamento, false);
        const mercadoData = await getRawMercado();
        if (!mercadoData || !mercadoData.atletas) {
          throw new Error('Não foi possível obter dados do mercado');
        }
        const jogadores: Jogador[] = mercadoData.atletas.map((a: any) => ({
          atleta_id: String(a.atleta_id),
          apelido: a.apelido || a.apelido_abreviado || '',
          posicao_id: a.posicao_id,
          clube_id: a.clube_id,
          clube_nome: mercadoData.clubes?.[a.clube_id]?.abreviacao || '',
          preco: a.preco_num || 0,
          media: a.media_num || 0,
          pontos_num: a.pontos_num || 0,
          variacao_num: a.variacao_num || 0,
          status_id: a.status_id,
          entrou_em_campo: a.entrou_em_campo,
          foto: a.foto ? a.foto.replace('FORMATO', '140x140') : undefined,
          scout: a.scout || {},
        }));
        const escalacao = await engine.escalarTime(
          jogadores, input.formacao, input.orcamento, true, false, input.rodada, input.ano
        );
        escalacaoAtual = escalacao;
        return escalacao;
      }),

    // Analisar todas as formações
    analisarFormacoes: protectedProcedure
      .input(z.object({
        orcamento: z.number().default(100),
        rodada: z.number().optional(),
      }))
      .mutation(async ({ input }) => {
        const engine = getEngine(input.orcamento, false);
        
        const mercadoData = await getRawMercado();
        if (!mercadoData || !mercadoData.atletas) {
          throw new Error('Não foi possível obter dados do mercado');
        }
        
        const jogadores: Jogador[] = mercadoData.atletas.map((a: any) => ({
          atleta_id: String(a.atleta_id),
          apelido: a.apelido || a.apelido_abreviado || '',
          posicao_id: a.posicao_id,
          clube_id: a.clube_id,
          clube_nome: mercadoData.clubes?.[a.clube_id]?.abreviacao || '',
          preco: a.preco_num || 0,
          media: a.media_num || 0,
          pontos_num: a.pontos_num || 0,
          variacao_num: a.variacao_num || 0,
          status_id: a.status_id,
          entrou_em_campo: a.entrou_em_campo,
          scout: a.scout || {},
        }));
        
        const resultados = await engine.analisarTodasFormacoes(jogadores, input.orcamento, false, input.rodada);
        return resultados;
      }),

    // Simulação histórica
    simularRodada: protectedProcedure
      .input(z.object({
        rodada: z.number(),
        ano: z.number(),
        formacao: z.string().default('4-3-3'),
        orcamento: z.number().default(150),
        formacaoAutomatica: z.boolean().default(false),
      }))
      .mutation(async ({ input }) => {
        // Get historical data for this round
        const jogadoresRodada = await getJogadoresRodada(input.rodada, input.ano);
        if (!jogadoresRodada || jogadoresRodada.length === 0) {
          throw new Error(`Sem dados para rodada ${input.rodada}/${input.ano}`);
        }
        
        const jogadores: Jogador[] = jogadoresRodada.map((j: any) => ({
          atleta_id: String(j.atleta_id),
          apelido: j.apelido || '',
          posicao_id: Number(j.posicao_id),
          clube_id: Number(j.clube_id),
          clube_nome: j.clube_nome || '',
          preco: parseFloat(j.preco) || 5,
          media: parseFloat(j.media) || 0,
          pontos_num: parseFloat(j.pontos) || 0,
          variacao_num: parseFloat(j.variacao) || 0,
          status_id: 7,
          entrou_em_campo: j.entrou_em_campo !== false,
        }));
        
        let escalacao: Escalacao;
        
        if (input.formacaoAutomatica) {
          // Try all formations, pick the best
          let melhorEsc: Escalacao | null = null;
          let melhorPts = -Infinity;
          for (const form of Object.keys(FORMACOES)) {
            try {
              const eng = new EstrategiaV7(input.orcamento, true);
              const esc = await eng.escalarTime(
                jogadores, form, input.orcamento, true, true, input.rodada, input.ano
              );
              if (esc && esc.titulares.length === 12 && esc.pontuacao_esperada > melhorPts) {
                melhorPts = esc.pontuacao_esperada;
                melhorEsc = esc;
              }
            } catch { /* skip */ }
          }
          if (!melhorEsc) throw new Error('Nenhuma formação produziu resultado válido');
          escalacao = melhorEsc;
        } else {
          const engine = new EstrategiaV7(input.orcamento, true);
          escalacao = await engine.escalarTime(
            jogadores, input.formacao, input.orcamento, true, true, input.rodada, input.ano
          );
        }
        
        // Calculate real points with captain 1.5x multiplier (matching Python logic)
        let pontosReais = 0;
        const capIdSingle = escalacao.capitao?.atleta_id;
        for (const t of escalacao.titulares) {
          const jog = jogadoresRodada.find((j: any) => String(j.atleta_id) === t.atleta_id);
          if (jog) {
            t.pontos_reais = parseFloat(String(jog.pontos)) || 0;
            let pts = t.pontos_reais;
            if (capIdSingle && t.atleta_id === capIdSingle) {
              pts *= 1.5;
            }
            pontosReais += pts;
          }
        }
        
        return {
          ...escalacao,
          pontos_reais_total: Math.round(pontosReais * 100) / 100,
          diferenca: Math.round((pontosReais - escalacao.pontuacao_esperada) * 100) / 100,
        };
      }),

    // Simular todas as rodadas de um ano
    simularTodasRodadas: protectedProcedure
      .input(z.object({
        ano: z.number(),
        formacao: z.string().default('4-3-3'),
        orcamento: z.number().default(150),
        formacaoAutomatica: z.boolean().default(false),
        orcamentoDinamico: z.boolean().default(false),
        usePython: z.boolean().default(true),
      }))
      .mutation(async ({ input }) => {
        // Try Python service first (identical results to Streamlit)
        if (input.usePython) {
          const pyHealthy = await checkPythonServiceHealth();
          if (pyHealthy) {
            try {
              const formacao = input.formacaoAutomatica ? 'auto' : input.formacao;
              const pyResult = await simularViaPython({
                ano: input.ano,
                orcamento: input.orcamento,
                formacao,
                orcamento_dinamico: input.orcamentoDinamico,
              });
              
              // Transform Python result to match the expected frontend format
              const POS_MAP_INV: Record<number, string> = { 1: 'GOL', 2: 'LAT', 3: 'ZAG', 4: 'MEI', 5: 'ATA', 6: 'TEC' };
              let acumEscalado = 0;
              let acumIdeal = 0;
              const resultados = pyResult.rodadas.map((r: any) => {
                const ptsEscalado = Number(r['Pts Escalado']) || 0;
                const ptsIdeal = Number(r['Pts Ideal']) || 0;
                const ptsPrevisto = Number(r['Pts Previsto']) || 0;
                acumEscalado += ptsEscalado;
                acumIdeal += ptsIdeal;
                const aprovAcumulado = acumIdeal > 0 ? (acumEscalado / acumIdeal * 100) : 0;
                const acertosStr = String(r['Acertos'] || '0/12');
                const acertosNum = parseInt(acertosStr.split('/')[0]) || 0;
                const custoStr = String(r['Custo'] || 'C$ 0');
                const custoNum = parseFloat(custoStr.replace('C$', '').trim()) || 0;
                const orcStr = r['Orçamento'] ? String(r['Orçamento']).replace('C$', '').trim() : String(input.orcamento);
                const orcNum = parseFloat(orcStr) || input.orcamento;
                const aprovStr = String(r['Aproveitamento'] || '0%');
                const aprovNum = parseFloat(aprovStr.replace('%', '')) || 0;
                
                // Get detail data if available
                // Python returns: { escalacao: { titulares, reservas, capitao, ... }, melhores, substituicoes, ... }
                const detail = pyResult.detalhes?.[String(r['Rodada'])];
                const esc = detail?.escalacao || {};
                const titulares = (esc?.titulares || []).map((t: any) => ({
                  atleta_id: String(t.atleta_id || ''),
                  apelido: t.apelido || '',
                  pos_id: t.pos_id || 0,
                  posicao: POS_MAP_INV[t.pos_id] || 'N/A',
                  preco: t.preco || 0,
                  score: t.score || 0,
                  pontos_reais: t.pontos_reais || 0,
                  explicacao_resumo: t.explicacao?.resumo || '',
                  explicacao: t.explicacao || {},
                  media: t.media || 0,
                  clube_id: t.clube_id || 0,
                  clube_nome: t.clube || '',
                  valorizacao_prevista: t.valorizacao_prevista || 0,
                })) || [];
                
                // melhores is a dict: { formacao, titulares: [...] } from obter_melhores_reais
                const melhoresList = Array.isArray(detail?.melhores) ? detail.melhores : (detail?.melhores?.titulares || []);
                const melhores = melhoresList.map((m: any) => ({
                  atleta_id: String(m.atleta_id || ''),
                  apelido: m.apelido || '',
                  pos_id: m.pos_id || 0,
                  posicao: POS_MAP_INV[m.pos_id] || m.posicao || 'N/A',
                  preco: m.preco || 0,
                  pontos: m.pontos_reais || m.pontos || 0,
                  clube_id: m.clube_id || 0,
                  clube_nome: m.clube || '',
                  score_previsto: m.score || 0,
                })) || [];
                
                const substituicoes = (esc?.substituicoes || []).map((s: any) => ({
                  tipo: s.tipo || 'reserva',
                  saiu: (typeof s.saiu === 'object' ? s.saiu?.apelido : s.saiu) || '',
                  entrou: (typeof s.entrou === 'object' ? s.entrou?.apelido : s.entrou) || '',
                  pontos_saiu: (typeof s.saiu === 'object' ? s.saiu?.pontos_reais : 0) || 0,
                  pontos_entrou: (typeof s.entrou === 'object' ? s.entrou?.pontos_reais : 0) || 0,
                }));
                
                return {
                  rodada: Number(r['Rodada']),
                  pontuacao_esperada: ptsPrevisto,
                  pontos_reais: ptsEscalado,
                  pts_ideal: ptsIdeal,
                  pts_previsto: ptsPrevisto,
                  aproveitamento: aprovNum,
                  aproveitamento_acumulado: Math.round(aprovAcumulado * 100) / 100,
                  acertos: acertosNum,
                  formacao: String(r['Formação'] || input.formacao),
                  diferenca: Math.round((ptsEscalado - ptsPrevisto) * 100) / 100,
                  orcamento_usado: orcNum,
                  custo_total: custoNum,
                  capitao: String(r['Capitão Escalado'] || '—'),
                  capitao_ideal: String(r['Capitão Ideal'] || '—'),
                  cap_ok: String(r['Cap OK']) === '✓',
                  titulares,
                  melhores,
                  substituicoes,
                  reserva_luxo: esc?.reserva_luxo ? {
                    apelido: esc.reserva_luxo.apelido || '',
                    posicao: esc.reserva_luxo.posicao || POS_MAP_INV[esc.reserva_luxo.pos_id] || '',
                    pontos_reais: esc.reserva_luxo.pontos_reais || 0,
                  } : null,
                };
              });
              
              const totalPtsReais = resultados.reduce((s: number, r: any) => s + r.pontos_reais, 0);
              const totalPtsEsperada = resultados.reduce((s: number, r: any) => s + r.pontuacao_esperada, 0);
              const totalPtsIdeal = resultados.reduce((s: number, r: any) => s + r.pts_ideal, 0);
              const capsOk = resultados.filter((r: any) => r.cap_ok).length;
              const aprovTotal = totalPtsIdeal > 0 ? (totalPtsReais / totalPtsIdeal * 100) : 0;
              
              // Position stats
              const posStats: Record<string, { escalado: number; ideal: number }> = {};
              for (const pos of ['GOL', 'LAT', 'ZAG', 'MEI', 'ATA', 'TEC']) posStats[pos] = { escalado: 0, ideal: 0 };
              for (const r of resultados) {
                for (const t of r.titulares) {
                  if (posStats[t.posicao]) posStats[t.posicao].escalado += t.pontos_reais;
                }
                for (const m of r.melhores) {
                  if (posStats[m.posicao]) posStats[m.posicao].ideal += m.pontos;
                }
              }
              const aprovPosicao: Record<string, number> = {};
              for (const [pos, s] of Object.entries(posStats)) {
                aprovPosicao[pos] = s.ideal > 0 ? Math.round(s.escalado / s.ideal * 10000) / 100 : 0;
              }
              
              // Justificativa distribution
              const justificativas: Record<string, number> = {};
              for (const r of resultados) {
                for (const t of r.titulares) {
                  const resumo = (t.explicacao_resumo || '').toLowerCase();
                  let just = 'Consistente';
                  if (resumo.includes('recuperação')) just = 'Recuperação';
                  else if (resumo.includes('boa fase')) just = 'Boa Fase';
                  else if (resumo.includes('queda')) just = 'Em Queda';
                  else if (resumo.includes('premium')) just = 'Premium';
                  else if (resumo.includes('custo')) just = 'Custo-Benefício';
                  else if (resumo.includes('aposta')) just = 'Aposta';
                  justificativas[just] = (justificativas[just] || 0) + 1;
                }
              }
              
              // Gauge data
              const justGauges: Record<string, { acertos: number; total: number }> = {};
              for (const r of resultados) {
                for (const t of r.titulares) {
                  const resumo = (t.explicacao_resumo || '').toLowerCase();
                  let just = 'Consistente';
                  if (resumo.includes('recuperação')) just = 'Recuperação';
                  else if (resumo.includes('boa fase')) just = 'Boa Fase';
                  else if (resumo.includes('queda')) just = 'Em Queda';
                  else if (resumo.includes('premium')) just = 'Premium';
                  else if (resumo.includes('custo')) just = 'Custo-Benefício';
                  else if (resumo.includes('aposta')) just = 'Aposta';
                  if (!justGauges[just]) justGauges[just] = { acertos: 0, total: 0 };
                  justGauges[just].total++;
                  if (t.pontos_reais >= t.media) justGauges[just].acertos++;
                }
              }
              
              // Formation distribution
              const formacoes: Record<string, number> = {};
              for (const r of resultados) {
                formacoes[r.formacao] = (formacoes[r.formacao] || 0) + 1;
              }
              
              // Top 5 most picked players
              const jogStats: Record<string, { pontos: number; escalacoes: number }> = {};
              for (const r of resultados) {
                for (const t of r.titulares) {
                  if (!jogStats[t.apelido]) jogStats[t.apelido] = { pontos: 0, escalacoes: 0 };
                  jogStats[t.apelido].pontos += t.pontos_reais;
                  jogStats[t.apelido].escalacoes++;
                }
              }
              const top5 = Object.entries(jogStats)
                .sort((a, b) => b[1].pontos - a[1].pontos)
                .slice(0, 5)
                .map(([nome, stats]) => ({ nome, pontos: Math.round(stats.pontos * 100) / 100, escalacoes: stats.escalacoes }));
              
              return {
                ano: input.ano,
                resultados: resultados.map((r: any) => ({
                  rodada: r.rodada,
                  pontos_reais: r.pontos_reais,
                  pts_previsto: r.pts_previsto,
                  pts_ideal: r.pts_ideal,
                  aproveitamento: r.aproveitamento,
                  aproveitamento_acumulado: r.aproveitamento_acumulado,
                  acertos: r.acertos,
                  formacao: r.formacao,
                  capitao: r.capitao,
                  capitao_ideal: r.capitao_ideal,
                  cap_ok: r.cap_ok,
                  custo_total: r.custo_total,
                  orcamento_usado: r.orcamento_usado,
                  pontuacao_esperada: r.pontuacao_esperada,
                  diferenca: r.diferenca,
                  titulares: r.titulares,
                  melhores: r.melhores,
                  substituicoes: r.substituicoes,
                  reserva_luxo: r.reserva_luxo,
                })),
                media_pontos_reais: pyResult.resumo.media_rodada,
                media_esperada: resultados.length > 0 ? Math.round(totalPtsEsperada / resultados.length * 100) / 100 : 0,
                total_rodadas: pyResult.resumo.num_rodadas,
                total_pontos_reais: pyResult.resumo.total_pontos,
                total_pontos_esperada: Math.round(totalPtsEsperada * 100) / 100,
                total_pontos_ideal: pyResult.resumo.total_ideal,
                capitaes_ok: capsOk,
                aproveitamento_total: pyResult.resumo.aproveitamento,
                orcamento_final: input.orcamentoDinamico ? undefined : undefined,
                aprovPosicao,
                justificativas,
                justGauges,
                formacoes,
                top5,
                fonte: 'python' as const,
              };
            } catch (pyError: any) {
              console.error('[Simulação] Python service error, falling back to TypeScript:', pyError.message);
              // Fall through to TypeScript implementation
            }
          }
        }
        // TypeScript fallback implementation
        const rodadasProcessadas = await getRodadasProcessadas();
        const rodadasAno = rodadasProcessadas
          .filter((r: any) => Number(r.ano) === input.ano)
          .map((r: any) => Number(r.rodada))
          .sort((a: number, b: number) => a - b);
        
        const resultados: Array<{
          rodada: number;
          pontuacao_esperada: number;
          pontos_reais: number;
          pts_ideal: number;
          pts_previsto: number;
          aproveitamento: number;
          aproveitamento_acumulado: number;
          acertos: number;
          formacao: string;
          diferenca: number;
          orcamento_usado: number;
          custo_total: number;
          capitao: string;
          capitao_ideal: string;
          cap_ok: boolean;
          titulares: Array<{ atleta_id: string; apelido: string; pos_id: number; posicao: string; preco: number; score: number; pontos_reais: number; explicacao_resumo: string; explicacao: any; media: number; clube_id: number; clube_nome: string; valorizacao_prevista: number; }>;
          melhores: Array<{ atleta_id: string; apelido: string; pos_id: number; posicao: string; preco: number; pontos: number; clube_id: number; clube_nome: string; score_previsto: number; }>;
          substituicoes: Array<{ tipo: string; saiu: string; entrou: string; }>;
          reserva_luxo: { apelido: string; posicao: string; pontos_reais: number; } | null;
        }> = [];
        
        let orcamentoAtual = input.orcamento;
        const formacoesDisponiveis = Object.keys(FORMACOES);
        const POS_MAP_INV: Record<number, string> = { 1: 'GOL', 2: 'LAT', 3: 'ZAG', 4: 'MEI', 5: 'ATA', 6: 'TEC' };
        
        // Create a shared engine that will reload history per-round with progressive data
        // Like Python: for each round N, load previous year + current year up to round N-1
        const sharedEngine = new EstrategiaV7(input.orcamento, true);
        
        // Pre-fetch all rodada data in parallel
        const allJogadoresData = await Promise.all(
          rodadasAno.map(async (rodada) => {
            try {
              const data = await getJogadoresRodada(rodada, input.ano);
              return { rodada, data };
            } catch {
              return { rodada, data: null };
            }
          })
        );
        
        // Accumulators for running totals
        let acumEscalado = 0;
        let acumIdeal = 0;
        
        for (const { rodada, data: jogadoresRodada } of allJogadoresData) {
          try {
            if (!jogadoresRodada || jogadoresRodada.length === 0) continue;
            
            const jogadores: Jogador[] = jogadoresRodada.map((j: any) => ({
              atleta_id: String(j.atleta_id),
              apelido: j.apelido || '',
              posicao_id: Number(j.posicao_id),
              clube_id: Number(j.clube_id),
              clube_nome: j.clube_nome || '',
              preco: parseFloat(j.preco) || 5,
              media: parseFloat(j.media) || 0,
              pontos_num: parseFloat(j.pontos) || 0,
              variacao_num: parseFloat(j.variacao) || 0,
              status_id: 7,
              entrou_em_campo: j.entrou_em_campo !== false,
            }));
            
            const orcamentoRodada = input.orcamentoDinamico ? orcamentoAtual : input.orcamento;
            const formacaoUsada = input.formacaoAutomatica ? 'auto' : input.formacao;
            
            let melhorEscalacao: Escalacao | null = null;
            let melhorFormacao = input.formacao;
            
            if (input.formacaoAutomatica) {
              let melhorPontuacao = -Infinity;
              for (const form of formacoesDisponiveis) {
                try {
                  sharedEngine.orcamento = orcamentoRodada;
                  const esc = await sharedEngine.escalarTime(
                    jogadores, form, orcamentoRodada, true, true, rodada, input.ano
                  );
                  if (esc && esc.titulares.length === 12 && esc.pontuacao_esperada > melhorPontuacao) {
                    melhorPontuacao = esc.pontuacao_esperada;
                    melhorEscalacao = esc;
                    melhorFormacao = form;
                  }
                } catch { /* skip */ }
              }
            } else {
              sharedEngine.orcamento = orcamentoRodada;
              melhorEscalacao = await sharedEngine.escalarTime(
                jogadores, input.formacao, orcamentoRodada, false, true, rodada, input.ano
              );
              melhorFormacao = input.formacao;
            }
            
            if (!melhorEscalacao) continue;
            
            // Calculate real points for each titular
            let pontosReais = 0;
            const titularesDetalhes: typeof resultados[0]['titulares'] = [];
            const substituicoesRodada: Array<{tipo: string; saiu: string; entrou: string; pontos_saiu: number; pontos_entrou: number}> = [];
            
            // Build reservas map: pos_id -> reserva player data
            const reservasMap: Record<number, {atleta_id: string; apelido: string; pos_id: number; pontos_reais: number; preco: number; media: number; clube: string}> = {};
            if (melhorEscalacao.reservas) {
              for (const [posIdStr, reserva] of Object.entries(melhorEscalacao.reservas)) {
                if (reserva) {
                  const rJog = jogadoresRodada.find((j: any) => String(j.atleta_id) === (reserva as any).atleta_id);
                  reservasMap[Number(posIdStr)] = {
                    atleta_id: (reserva as any).atleta_id,
                    apelido: (reserva as any).apelido || '',
                    pos_id: Number(posIdStr),
                    pontos_reais: rJog ? (parseFloat(String(rJog.pontos)) || 0) : 0,
                    preco: (reserva as any).preco || 0,
                    media: (reserva as any).media || 0,
                    clube: (reserva as any).clube || '',
                  };
                }
              }
            }
            
            // Reserva de luxo data
            let reservaLuxoData: {atleta_id: string; apelido: string; pos_id: number; pontos_reais: number; preco: number; media: number; clube: string; posicao: string} | null = null;
            if (melhorEscalacao.reserva_luxo) {
              const rl = melhorEscalacao.reserva_luxo;
              const rlJog = jogadoresRodada.find((j: any) => String(j.atleta_id) === rl.atleta_id);
              reservaLuxoData = {
                atleta_id: rl.atleta_id,
                apelido: rl.apelido || '',
                pos_id: rl.pos_id,
                pontos_reais: rlJog ? (parseFloat(String(rlJog.pontos)) || 0) : 0,
                preco: rl.preco || 0,
                media: rl.media || 0,
                clube: rl.clube || '',
                posicao: POS_MAP_INV[rl.pos_id] || 'N/A',
              };
            }
            
            for (const t of melhorEscalacao.titulares) {
              const jog = jogadoresRodada.find((j: any) => String(j.atleta_id) === t.atleta_id);
              const ptsReal = jog ? (parseFloat(String(jog.pontos)) || 0) : 0;
              titularesDetalhes.push({
                atleta_id: t.atleta_id,
                apelido: t.apelido,
                pos_id: t.pos_id,
                posicao: POS_MAP_INV[t.pos_id] || 'N/A',
                preco: t.preco,
                score: t.score || t.pontuacao_esperada || 0,
                pontos_reais: ptsReal,
                explicacao_resumo: t.explicacao?.resumo || '',
                explicacao: t.explicacao || {},
                media: t.media || 0,
                clube_id: t.clube_id || 0,
                clube_nome: t.clube || '',
                valorizacao_prevista: t.valorizacao_prevista || 0,
              });
            }
            
            // SUBSTITUIÇÃO 1: Reservas substituem titulares que NÃO JOGARAM (pontos = 0)
            const usedReservas = new Set<number>();
            for (let i = 0; i < titularesDetalhes.length; i++) {
              const td = titularesDetalhes[i];
              if (td.pontos_reais === 0) {
                const posId = td.pos_id;
                const reserva = reservasMap[posId];
                if (reserva && !usedReservas.has(posId) && reserva.pontos_reais > 0) {
                  substituicoesRodada.push({
                    tipo: 'reserva',
                    saiu: td.apelido,
                    entrou: reserva.apelido,
                    pontos_saiu: 0,
                    pontos_entrou: reserva.pontos_reais,
                  });
                  // Update the titular's points to the reserva's points
                  titularesDetalhes[i] = { ...td, pontos_reais: reserva.pontos_reais, apelido: `${reserva.apelido} (sub)` };
                  usedReservas.add(posId);
                }
              }
            }
            
            // SUBSTITUIÇÃO 2: Reserva de luxo substitui o PIOR PONTUADOR da sua posição
            if (reservaLuxoData && reservaLuxoData.pontos_reais > 0) {
              const posId = reservaLuxoData.pos_id;
              const titularesPos = titularesDetalhes.filter(t => t.pos_id === posId);
              if (titularesPos.length > 0) {
                const piorIdx = titularesDetalhes.findIndex(t => 
                  t.pos_id === posId && t.pontos_reais === Math.min(...titularesPos.map(tp => tp.pontos_reais))
                );
                if (piorIdx >= 0 && reservaLuxoData.pontos_reais > titularesDetalhes[piorIdx].pontos_reais) {
                  substituicoesRodada.push({
                    tipo: 'luxo',
                    saiu: titularesDetalhes[piorIdx].apelido,
                    entrou: reservaLuxoData.apelido,
                    pontos_saiu: titularesDetalhes[piorIdx].pontos_reais,
                    pontos_entrou: reservaLuxoData.pontos_reais,
                  });
                  titularesDetalhes[piorIdx] = { ...titularesDetalhes[piorIdx], pontos_reais: reservaLuxoData.pontos_reais, apelido: `${reservaLuxoData.apelido} (luxo)` };
                }
              }
            }
            
            // Sum real points AFTER substitutions, with captain 1.5x multiplier
            // Match Python logic: for each titular, if captain, multiply effective points by 1.5
            const capId = melhorEscalacao.capitao?.atleta_id;
            pontosReais = 0;
            for (const t of titularesDetalhes) {
              let pts = t.pontos_reais;
              if (capId && t.atleta_id === capId) {
                pts *= 1.5;
              }
              pontosReais += pts;
            }
            
            // === Calculate IDEAL team (best possible) for this rodada ===
            const formConfig = FORMACOES[melhorFormacao];
            // Group players by position and sort by real points
            const byPos: Record<number, Array<{ atleta_id: string; apelido: string; posicao_id: number; pontos: number; preco: number }>> = {};
            for (const j of jogadoresRodada) {
              const posId = Number(j.posicao_id);
              const pts = parseFloat(String(j.pontos)) || 0;
              if (!byPos[posId]) byPos[posId] = [];
              byPos[posId].push({ atleta_id: String(j.atleta_id), apelido: j.apelido || '', posicao_id: posId, pontos: pts, preco: parseFloat(String(j.preco)) || 0 });
            }
            // Sort each position by points desc
            for (const posId of Object.keys(byPos)) {
              byPos[Number(posId)].sort((a, b) => b.pontos - a.pontos);
            }
            // Pick best per position according to formation
            let ptsIdeal = 0;
            const melhoresDetalhes: typeof resultados[0]['melhores'] = [];
            let melhorCapIdeal = { apelido: '', pontos: 0 };
            const idsEscaladosSet = new Set(melhorEscalacao.titulares.map(t => t.atleta_id));
            for (const [posIdStr, count] of Object.entries(formConfig)) {
              const posId = Number(posIdStr);
              const candidates = byPos[posId] || [];
              for (let i = 0; i < count && i < candidates.length; i++) {
                const c = candidates[i];
                ptsIdeal += c.pontos;
                // Find the full jogador data for clube info and score
                const jogFull = jogadoresRodada.find((j: any) => String(j.atleta_id) === c.atleta_id);
                // Check if this player was in our escalação
                const wasEscalado = idsEscaladosSet?.has(c.atleta_id) ?? false;
                melhoresDetalhes.push({
                  atleta_id: c.atleta_id,
                  apelido: c.apelido,
                  pos_id: posId,
                  posicao: POS_MAP_INV[posId] || 'N/A',
                  preco: c.preco,
                  pontos: c.pontos,
                  clube_id: jogFull ? Number(jogFull.clube_id) || 0 : 0,
                  clube_nome: jogFull?.clube_nome || '',
                  score_previsto: jogFull ? (parseFloat(String(jogFull.media)) || 0) : 0,
                });
                if (c.pontos > melhorCapIdeal.pontos) {
                  melhorCapIdeal = { apelido: c.apelido, pontos: c.pontos };
                }
              }
            }
            // Captain ideal bonus
            ptsIdeal += melhorCapIdeal.pontos * 0.5;
            
            // Acertos: how many escalados are in the ideal team
            const idsEscalados = idsEscaladosSet;
            const idsMelhores = new Set(melhoresDetalhes.map(m => m.atleta_id));
            const acertos = Array.from(idsEscalados).filter(id => idsMelhores.has(id)).length;
            
            // Captain comparison
            const capEscalado = melhorEscalacao.capitao?.apelido || '—';
            const capIdeal = melhorCapIdeal.apelido || '—';
            const capOk = capEscalado === capIdeal;
            
            // Aproveitamento
            const aproveitamento = ptsIdeal > 0 ? (pontosReais / ptsIdeal * 100) : 0;
            
            // Acumulados
            acumEscalado += pontosReais;
            acumIdeal += ptsIdeal;
            const aprovAcumulado = acumIdeal > 0 ? (acumEscalado / acumIdeal * 100) : 0;
            
            // Dynamic budget
            if (input.orcamentoDinamico) {
              let valorizacaoTotal = 0;
              for (const t of melhorEscalacao.titulares) {
                const jog = jogadoresRodada.find((j: any) => String(j.atleta_id) === t.atleta_id);
                if (jog) valorizacaoTotal += parseFloat(String(jog.variacao)) || 0;
              }
              orcamentoAtual = orcamentoAtual + valorizacaoTotal;
            }
            
            resultados.push({
              rodada,
              pontuacao_esperada: Math.round(melhorEscalacao.pontuacao_esperada * 100) / 100,
              pontos_reais: Math.round(pontosReais * 100) / 100,
              pts_ideal: Math.round(ptsIdeal * 100) / 100,
              pts_previsto: Math.round(melhorEscalacao.pontuacao_esperada * 100) / 100,
              aproveitamento: Math.round(aproveitamento * 100) / 100,
              aproveitamento_acumulado: Math.round(aprovAcumulado * 100) / 100,
              acertos,
              formacao: melhorFormacao,
              diferenca: Math.round((pontosReais - melhorEscalacao.pontuacao_esperada) * 100) / 100,
              orcamento_usado: Math.round(orcamentoRodada * 100) / 100,
              custo_total: Math.round(melhorEscalacao.custo_total * 100) / 100,
              capitao: capEscalado,
              capitao_ideal: capIdeal,
              cap_ok: capOk,
              titulares: titularesDetalhes,
              melhores: melhoresDetalhes,
              substituicoes: substituicoesRodada,
              reserva_luxo: (melhorEscalacao as any).reserva_luxo ? {
                apelido: (melhorEscalacao as any).reserva_luxo.apelido || '',
                posicao: POS_MAP_INV[(melhorEscalacao as any).reserva_luxo.pos_id] || '',
                pontos_reais: (() => {
                  const rlJog = jogadoresRodada.find((j: any) => String(j.atleta_id) === (melhorEscalacao as any).reserva_luxo?.atleta_id);
                  return rlJog ? (parseFloat(String(rlJog.pontos)) || 0) : 0;
                })(),
              } : null,
            });
          } catch (e) {
            console.error(`[Simulação] Erro na rodada ${rodada}:`, e);
          }
        }
        
        const totalPtsReais = resultados.reduce((s, r) => s + r.pontos_reais, 0);
        const totalPtsEsperada = resultados.reduce((s, r) => s + r.pontuacao_esperada, 0);
        const totalPtsIdeal = resultados.reduce((s, r) => s + r.pts_ideal, 0);
        const capsOk = resultados.filter(r => r.cap_ok).length;
        const aprovTotal = totalPtsIdeal > 0 ? (totalPtsReais / totalPtsIdeal * 100) : 0;
        
        // Position stats
        const posStats: Record<string, { escalado: number; ideal: number }> = {};
        for (const pos of ['GOL', 'LAT', 'ZAG', 'MEI', 'ATA', 'TEC']) posStats[pos] = { escalado: 0, ideal: 0 };
        for (const r of resultados) {
          for (const t of r.titulares) {
            if (posStats[t.posicao]) posStats[t.posicao].escalado += t.pontos_reais;
          }
          for (const m of r.melhores) {
            if (posStats[m.posicao]) posStats[m.posicao].ideal += m.pontos;
          }
        }
        const aprovPosicao: Record<string, number> = {};
        for (const [pos, s] of Object.entries(posStats)) {
          aprovPosicao[pos] = s.ideal > 0 ? Math.round(s.escalado / s.ideal * 10000) / 100 : 0;
        }
        
        // Justificativa distribution
        const justificativas: Record<string, number> = {};
        for (const r of resultados) {
          for (const t of r.titulares) {
            const resumo = (t.explicacao_resumo || '').toLowerCase();
            let just = 'Consistente';
            if (resumo.includes('recuperação')) just = 'Recuperação';
            else if (resumo.includes('boa fase')) just = 'Boa Fase';
            else if (resumo.includes('queda')) just = 'Em Queda';
            else if (resumo.includes('premium')) just = 'Premium';
            else if (resumo.includes('custo')) just = 'Custo-Benefício';
            else if (resumo.includes('aposta')) just = 'Aposta';
            justificativas[just] = (justificativas[just] || 0) + 1;
          }
        }
        
        // Gauge data: aproveitamento by justificativa
        const justGauges: Record<string, { acertos: number; total: number }> = {};
        for (const r of resultados) {
          for (const t of r.titulares) {
            const resumo = (t.explicacao_resumo || '').toLowerCase();
            let just = 'Consistente';
            if (resumo.includes('recuperação')) just = 'Recuperação';
            else if (resumo.includes('boa fase')) just = 'Boa Fase';
            else if (resumo.includes('queda')) just = 'Em Queda';
            else if (resumo.includes('premium')) just = 'Premium';
            else if (resumo.includes('custo')) just = 'Custo-Benefício';
            else if (resumo.includes('aposta')) just = 'Aposta';
            if (!justGauges[just]) justGauges[just] = { acertos: 0, total: 0 };
            justGauges[just].total++;
            if (t.pontos_reais >= t.media) justGauges[just].acertos++;
          }
        }
        
        // Formation distribution
        const formacoes: Record<string, number> = {};
        for (const r of resultados) {
          formacoes[r.formacao] = (formacoes[r.formacao] || 0) + 1;
        }
        
        // Top 5 most picked players
        const jogStats: Record<string, { pontos: number; escalacoes: number }> = {};
        for (const r of resultados) {
          for (const t of r.titulares) {
            if (!jogStats[t.apelido]) jogStats[t.apelido] = { pontos: 0, escalacoes: 0 };
            jogStats[t.apelido].pontos += t.pontos_reais;
            jogStats[t.apelido].escalacoes++;
          }
        }
        const top5 = Object.entries(jogStats)
          .sort((a, b) => b[1].pontos - a[1].pontos)
          .slice(0, 5)
          .map(([nome, stats]) => ({ nome, pontos: Math.round(stats.pontos * 100) / 100, escalacoes: stats.escalacoes }));
        
        return {
          ano: input.ano,
          resultados: resultados.map(r => ({
            rodada: r.rodada,
            pontos_reais: r.pontos_reais,
            pts_previsto: r.pts_previsto,
            pts_ideal: r.pts_ideal,
            aproveitamento: r.aproveitamento,
            aproveitamento_acumulado: r.aproveitamento_acumulado,
            acertos: r.acertos,
            formacao: r.formacao,
            capitao: r.capitao,
            capitao_ideal: r.capitao_ideal,
            cap_ok: r.cap_ok,
            custo_total: r.custo_total,
            orcamento_usado: r.orcamento_usado,
            pontuacao_esperada: r.pontuacao_esperada,
            diferenca: r.diferenca,
            titulares: r.titulares,
            melhores: r.melhores,
            substituicoes: r.substituicoes,
            reserva_luxo: r.reserva_luxo,
          })),
          media_pontos_reais: resultados.length > 0 ? Math.round(totalPtsReais / resultados.length * 100) / 100 : 0,
          media_esperada: resultados.length > 0 ? Math.round(totalPtsEsperada / resultados.length * 100) / 100 : 0,
          total_rodadas: resultados.length,
          total_pontos_reais: Math.round(totalPtsReais * 100) / 100,
          total_pontos_esperada: Math.round(totalPtsEsperada * 100) / 100,
          total_pontos_ideal: Math.round(totalPtsIdeal * 100) / 100,
          capitaes_ok: capsOk,
          aproveitamento_total: Math.round(aprovTotal * 100) / 100,
          orcamento_final: input.orcamentoDinamico ? Math.round(orcamentoAtual * 100) / 100 : undefined,
          aprovPosicao,
          justificativas,
          justGauges,
          formacoes,
          top5,
        };
      }),

    // Salvar escalação
    salvarEscalacao: protectedProcedure
      .input(z.object({
        rodada: z.number(),
        ano: z.number(),
        formacao: z.string(),
        escalacao: z.any(),
      }))
      .mutation(async ({ input }) => {
        try {
          // Save to Neon
          await neonQuery(
            `INSERT INTO escalacoes_salvas (rodada, ano, formacao, escalacao_json)
             VALUES ($1, $2, $3, $4)`,
            [input.rodada, input.ano, input.formacao, JSON.stringify(input.escalacao)]
          );
          
          // Reload
          await carregarEscalacoesSalvas();
          
          return { sucesso: true, mensagem: `Escalação R${input.rodada} salva com sucesso!` };
        } catch (e: any) {
          return { sucesso: false, erro: e.message || String(e) };
        }
      }),

    // Listar escalações salvas
    listarEscalacoes: protectedProcedure
      .input(z.object({ ano: z.number().optional() }).optional())
      .query(async ({ input }) => {
        try {
          const whereClause = input?.ano ? `WHERE ano = ${input.ano}` : '';
          const rows = await neonQuery(`
            SELECT id, rodada, ano, formacao, pontos_reais, valorizacao_real, atualizado, data_criacao,
                   escalacao_json->'pontuacao_prevista' as pontuacao_prevista,
                   escalacao_json->'pontuacao_esperada' as pontuacao_esperada,
                   escalacao_json->'custo_total' as custo_total,
                   escalacao_json->'formacao' as formacao_esc,
                   escalacao_json->'orcamento_disponivel' as orcamento_disponivel,
                   escalacao_json->'pontuacao_real' as pontuacao_real_json,
                   escalacao_json as escalacao_json_full
            FROM escalacoes_salvas
            ${whereClause}
            ORDER BY data_criacao DESC
          `);
          // Calculate valorizacao_com_substituicoes and pts_ideal for each row
          const POS_MAP_INV_LOCAL: Record<number, string> = { 1: 'GOL', 2: 'LAT', 3: 'ZAG', 4: 'MEI', 5: 'ATA', 6: 'TEC' };
          const results: any[] = [];
          for (const r of (rows || [])) {
            let valComSub = 0;
            let ptsIdeal = 0;
            let melhoresIdeal: Array<{atleta_id: string; apelido: string; posicao: string; pontos: number; preco: number}> = [];
            let capIdeal = '';
            try {
              const esc = typeof r.escalacao_json_full === 'string' ? JSON.parse(r.escalacao_json_full) : r.escalacao_json_full;
              if (esc && esc.processado) {
                valComSub = calcularValorizacaoComSubstituicoes(esc);
              }
              // Calculate ideal team for this round
              const rodada = Number(r.rodada);
              const ano = Number(r.ano);
              const formacao = String(r.formacao || esc?.formacao || '4-4-2');
              const formConfig = FORMACOES[formacao] || FORMACOES['4-4-2'];
              const jogadoresRodada = await neonQuery(
                `SELECT atleta_id, apelido, posicao_id, pontos, preco, clube_nome FROM jogadores_historico WHERE rodada = $1 AND ano = $2 AND competicao = 'Brasileirão'`,
                [rodada, ano]
              );
              if (jogadoresRodada && jogadoresRodada.length > 0) {
                const byPos: Record<number, Array<{atleta_id: string; apelido: string; posicao_id: number; pontos: number; preco: number}>> = {};
                for (const j of jogadoresRodada) {
                  const posId = Number(j.posicao_id);
                  const pts = parseFloat(String(j.pontos)) || 0;
                  if (!byPos[posId]) byPos[posId] = [];
                  byPos[posId].push({ atleta_id: String(j.atleta_id), apelido: String(j.apelido || ''), posicao_id: posId, pontos: pts, preco: parseFloat(String(j.preco)) || 0 });
                }
                for (const posId of Object.keys(byPos)) {
                  byPos[Number(posId)].sort((a, b) => b.pontos - a.pontos);
                }
                let melhorCapPts = 0;
                for (const [posIdStr, count] of Object.entries(formConfig)) {
                  const posId = Number(posIdStr);
                  const candidates = byPos[posId] || [];
                  for (let i = 0; i < count && i < candidates.length; i++) {
                    const c = candidates[i];
                    ptsIdeal += c.pontos;
                    melhoresIdeal.push({
                      atleta_id: c.atleta_id,
                      apelido: c.apelido,
                      posicao: POS_MAP_INV_LOCAL[posId] || 'N/A',
                      pontos: c.pontos,
                      preco: c.preco,
                    });
                    if (c.pontos > melhorCapPts) {
                      melhorCapPts = c.pontos;
                      capIdeal = c.apelido;
                    }
                  }
                }
                ptsIdeal += melhorCapPts * 0.5; // Captain bonus
              }
            } catch {}
            results.push({ ...r, valorizacao_com_sub: valComSub, pts_ideal: Math.round(ptsIdeal * 100) / 100, melhores_ideal: melhoresIdeal, capitao_ideal: capIdeal, escalacao_json_full: undefined });
          }
          return results;
        } catch {
          return [];
        }
      }),

    // Obter escalação salva por ID
    obterEscalacao: protectedProcedure
      .input(z.object({ id: z.number() }))
      .query(async ({ input }) => {
        try {
          const rows = await neonQuery(
            `SELECT * FROM escalacoes_salvas WHERE id = $1`,
            [input.id]
          );
          if (rows && rows.length > 0) {
            const r = rows[0];
            return {
              id: r.id,
              rodada: r.rodada,
              ano: r.ano,
              formacao: r.formacao,
              escalacao: typeof r.escalacao_json === 'string' ? JSON.parse(r.escalacao_json) : r.escalacao_json,
              pontosReais: r.pontos_reais,
              valorizacaoReal: r.valorizacao_real,
              atualizado: r.atualizado,
              data: r.data_criacao,
            };
          }
          return null;
        } catch {
          return null;
        }
      }),

    // Escalação atual (em memória)
    escalacaoAtual: protectedProcedure.query(() => escalacaoAtual),

    // Orçamento dinâmico calculado como no Streamlit
    orcamentoDinamico: protectedProcedure.query(async () => {
      try {
        const anoAtual = new Date().getFullYear();
        const rows = await neonQuery(`
          SELECT rodada, escalacao_json 
          FROM escalacoes_salvas 
          WHERE ano = $1 
          ORDER BY rodada ASC
        `, [anoAtual]);
        
        let orcCalculado = 100.0;
        for (const row of rows) {
          const esc = typeof row.escalacao_json === 'string' ? JSON.parse(row.escalacao_json) : row.escalacao_json;
          const processado = esc.processado === true || (esc.pontuacao_real != null && esc.pontuacao_real > 0);
          if (!processado) continue;
          
          const orcDisp = esc.orcamento_disponivel ?? orcCalculado;
          // Calculate valorização from jogadores
          const jogadores = esc.jogadores || [];
          let valorizacao = 0;
          for (const j of jogadores) {
            valorizacao += (j.variacao || 0);
          }
          orcCalculado = Math.round((orcDisp + valorizacao) * 100) / 100;
        }
        
        return { orcamento: orcCalculado };
      } catch {
        return { orcamento: 100 };
      }
    }),

    // Atualizar resultados de uma rodada
    atualizarResultados: protectedProcedure
      .input(z.object({ escalacaoId: z.number() }))
      .mutation(async ({ input }) => {
        try {
          // Get saved escalação
          const rows = await neonQuery(
            `SELECT * FROM escalacoes_salvas WHERE id = $1`,
            [input.escalacaoId]
          );
          if (!rows || rows.length === 0) {
            return { sucesso: false, erro: 'Escalação não encontrada' };
          }
          
          const saved = rows[0];
          const escalacao = typeof saved.escalacao_json === 'string' 
            ? JSON.parse(saved.escalacao_json) : saved.escalacao_json;
          
          const engine = getEngine(100, false);
          const resultado = await engine.atualizarAutomatico(escalacao);
          
          if (resultado.sucesso) {
            // Update in DB
            await neonQuery(
              `UPDATE escalacoes_salvas 
               SET pontos_reais = $1, valorizacao_real = $2, atualizado = TRUE
               WHERE id = $3`,
              [resultado.pontos, resultado.valorizacao, input.escalacaoId]
            );
            
            await carregarEscalacoesSalvas();
          }
          
          return resultado;
        } catch (e: any) {
          return { sucesso: false, erro: e.message || String(e) };
        }
      }),

    // Atualizar rodada finalizada - busca pontuações reais da API
    atualizarRodada: protectedProcedure
      .mutation(async () => {
        try {
          // Get pontuados from API
          const pontuados = await getAtletasPontuados();
          if (!pontuados || Object.keys(pontuados).length === 0) {
            throw new Error('Nenhum atleta pontuado encontrado. A rodada pode não ter sido finalizada ainda.');
          }

          const mercado = await getMercadoStatus();
          const rodada = (mercado?.rodada_atual || 1) - 1;
          const ano = mercado?.temporada || 2026;

          // Get saved escalações for this round
          const escalacoesSalvas = await neonQuery(
            `SELECT * FROM escalacoes_salvas WHERE rodada = $1 AND ano = $2 AND atualizado = FALSE`,
            [rodada, ano]
          );

          let jogadoresAtualizados = 0;
          let substituicoes = 0;
          let valorizacaoTotal = 0;

          if (escalacoesSalvas && escalacoesSalvas.length > 0) {
            for (const saved of escalacoesSalvas) {
              const escalacao = typeof saved.escalacao_json === 'string'
                ? JSON.parse(saved.escalacao_json) : saved.escalacao_json;

              let pontosReais = 0;
              const titulares = escalacao.titulares || [];
              const reservas = escalacao.reservas || [];

              for (const t of titulares) {
                const pontuado = pontuados[t.atleta_id];
                if (pontuado) {
                  pontosReais += Number(pontuado.pontuacao) || 0;
                  jogadoresAtualizados++;
                }
              }

              // Captain bonus
              if (escalacao.capitao) {
                const capPontuado = pontuados[escalacao.capitao.atleta_id];
                if (capPontuado) {
                  pontosReais += (Number(capPontuado.pontuacao) || 0) * 0.5;
                }
              }

              await neonQuery(
                `UPDATE escalacoes_salvas SET pontos_reais = $1, atualizado = TRUE WHERE id = $2`,
                [pontosReais, saved.id]
              );
            }
          }

          return {
            rodada,
            ano,
            jogadores_atualizados: jogadoresAtualizados,
            substituicoes,
            valorizacao_total: valorizacaoTotal,
          };
        } catch (e: any) {
          throw new Error(e.message || 'Erro ao atualizar rodada');
        }
      }),

    // Obter formações disponíveis
    formacoes: protectedProcedure.query(() => {
      return Object.entries(FORMACOES).map(([nome, config]) => ({
        nome,
        config,
        total: Object.values(config).reduce((a, b) => a + b, 0),
      }));
    }),

    // Obter posições
    posicoes: protectedProcedure.query(() => POSICAO_MAP),

    // Calcular scores do mercado (para página de Mercado)
    mercadoComScores: protectedProcedure
      .input(z.object({ orcamento: z.number().default(100) }).optional())
      .query(async ({ input }) => {
        const engine = getEngine(input?.orcamento || 100, false);
        
        const mercadoData = await getRawMercado();
        if (!mercadoData || !mercadoData.atletas) return { atletas: [], clubes: {} };
        
        const jogadores: Jogador[] = mercadoData.atletas.map((a: any) => ({
          atleta_id: String(a.atleta_id),
          apelido: a.apelido || a.apelido_abreviado || '',
          posicao_id: a.posicao_id,
          clube_id: a.clube_id,
          clube_nome: mercadoData.clubes?.[a.clube_id]?.abreviacao || '',
          preco: a.preco_num || 0,
          media: a.media_num || 0,
          pontos_num: a.pontos_num || 0,
          variacao_num: a.variacao_num || 0,
          status_id: a.status_id,
          entrou_em_campo: a.entrou_em_campo,
          foto: a.foto ? a.foto.replace('FORMATO', '140x140') : undefined,
          scout: a.scout || {},
        }));
        
        const comFeatures = await engine.prepararFeaturesV9(jogadores, false);
        
        // Sort by score
        comFeatures.sort((a, b) => (b.score_geral_v9 || 0) - (a.score_geral_v9 || 0));
        
        return {
          atletas: comFeatures.map(j => ({
            atleta_id: j.atleta_id,
            apelido: j.apelido,
            posicao_id: j.posicao_id,
            clube_id: j.clube_id,
            clube_nome: j.clube_nome,
            preco: j.preco,
            media: j.media,
            pontos_num: j.pontos_num,
            variacao_num: j.variacao_num,
            status_id: j.status_id,
            foto: j.foto,
            score: Math.round((j.score_geral_v9 || 0) * 100) / 100,
            media_ultimas_3: Math.round((j.media_ultimas_3 || 0) * 100) / 100,
            media_ultimas_5: Math.round((j.media_ultimas_5 || 0) * 100) / 100,
            tendencia: j.tendencia,
            oportunidade_regressao: j.oportunidade_regressao,
            custo_beneficio: Math.round((j.custo_beneficio || 0) * 100) / 100,
          })),
          clubes: mercadoData.clubes || {},
        };
      }),
  }),
});

export type AppRouter = typeof appRouter;
