/**
 * Cartola FC backend service
 * - Proxy for Cartola FC API (mercado, atletas, partidas)
 * - Queries to Neon PostgreSQL (jogadores_historico, competicoes_paralelas, escalacoes)
 */
import axios from "axios";
import { neonQuery, neonQueryOne } from "./neonDb";
import type {
  MercadoStatus,
  AtletaMercado,
  JogadorHistorico,
  CompetParalela,
  RodadaProcessada,
  DbStats,
  Partida,
} from "../shared/cartola";
import { POSICOES, STATUS_JOGADOR } from "../shared/cartola";

const CARTOLA_BASE = "https://api.cartola.globo.com";
const HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
};

// ============================================
// CARTOLA FC API PROXY
// ============================================

export async function getMercadoStatus(): Promise<MercadoStatus | null> {
  try {
    const { data } = await axios.get(`${CARTOLA_BASE}/mercado/status`, { headers: HEADERS, timeout: 15000 });
    return data as MercadoStatus;
  } catch {
    return null;
  }
}

export async function getClubes(): Promise<Record<string, { id: number; nome: string; abreviacao: string; escudos: Record<string, string> }>> {
  try {
    const { data } = await axios.get(`${CARTOLA_BASE}/clubes`, { headers: HEADERS, timeout: 15000 });
    return data;
  } catch {
    return {};
  }
}

export async function getAtletasMercado(): Promise<AtletaMercado[]> {
  try {
    const { data } = await axios.get(`${CARTOLA_BASE}/atletas/mercado`, { headers: HEADERS, timeout: 30000 });
    if (!data?.atletas) return [];
    const clubes = await getClubes();
    return data.atletas.map((a: Record<string, unknown>) => ({
      atleta_id: a.atleta_id,
      apelido: a.apelido,
      nome: a.nome,
      posicao_id: a.posicao_id,
      posicao_nome: POSICOES[a.posicao_id as number] || "?",
      clube_id: a.clube_id,
      clube_nome: clubes[String(a.clube_id)]?.nome || "Desconhecido",
      clube_abreviacao: clubes[String(a.clube_id)]?.abreviacao || "???",
      preco: a.preco_num || 0,
      media: a.media_num || 0,
      variacao: a.variacao_num || 0,
      pontos_ultima_rodada: a.pontos_num || 0,
      jogos: a.jogos_num || 0,
      status_id: a.status_id,
      status_nome: STATUS_JOGADOR[a.status_id as number] || "Desconhecido",
      entrou_em_campo: a.entrou_em_campo,
      scout: a.scout,
      foto: a.foto ? `https://s.sde.globo.com/media/person_role/2025/${a.foto}` : undefined,
    }));
  } catch {
    return [];
  }
}

// Raw mercado data for the engine (not processed)
export async function getRawMercado(): Promise<{ atletas: any[]; clubes: Record<string, any> } | null> {
  try {
    const { data } = await axios.get(`${CARTOLA_BASE}/atletas/mercado`, { headers: HEADERS, timeout: 30000 });
    if (!data?.atletas) return null;
    const clubes = await getClubes();
    return { atletas: data.atletas, clubes };
  } catch {
    return null;
  }
}

export async function getAtletasPontuados(rodada?: number): Promise<Record<string, unknown>[]> {
  try {
    const url = rodada ? `${CARTOLA_BASE}/atletas/pontuados/${rodada}` : `${CARTOLA_BASE}/atletas/pontuados`;
    const { data } = await axios.get(url, { headers: HEADERS, timeout: 15000 });
    if (!data?.atletas) return [];
    return Object.entries(data.atletas).map(([id, info]) => ({
      atleta_id: Number(id),
      ...(info as Record<string, unknown>),
    }));
  } catch {
    return [];
  }
}

export async function getPartidas(rodada?: number): Promise<Partida[]> {
  try {
    const url = rodada ? `${CARTOLA_BASE}/partidas/${rodada}` : `${CARTOLA_BASE}/partidas`;
    const { data } = await axios.get(url, { headers: HEADERS, timeout: 15000 });
    if (!data?.partidas) return [];
    const clubes = await getClubes();
    return data.partidas.map((p: Record<string, unknown>) => ({
      partida_id: p.partida_id,
      clube_casa_id: p.clube_casa_id,
      clube_visitante_id: p.clube_visitante_id,
      mandante: clubes[String(p.clube_casa_id)]?.nome || "?",
      visitante: clubes[String(p.clube_visitante_id)]?.nome || "?",
      placar_oficial_mandante: p.placar_oficial_mandante,
      placar_oficial_visitante: p.placar_oficial_visitante,
      valida: p.valida as boolean | undefined,
      partida_data: p.partida_data as string | undefined,
    }));
  } catch {
    return [];
  }
}

// ============================================
// NEON DB QUERIES
// ============================================

export async function getDbStats(): Promise<DbStats> {
  const row = await neonQueryOne<{
    total_historico: string;
    rodadas_proc: string;
    escalacoes: string;
    jogadores_stats: string;
  }>(`
    SELECT 
      (SELECT COUNT(*) FROM jogadores_historico) as total_historico,
      (SELECT COUNT(*) FROM rodadas_processadas) as rodadas_proc,
      (SELECT COUNT(*) FROM escalacoes_salvas) as escalacoes,
      (SELECT COUNT(*) FROM modelo_stats) as jogadores_stats
  `);

  const ultima = await neonQueryOne<{ ano: number; rodada: number; processado_em: string }>(`
    SELECT ano, rodada, processado_em FROM rodadas_processadas ORDER BY ano DESC, rodada DESC LIMIT 1
  `);

  return {
    total_registros_historico: Number(row?.total_historico || 0),
    rodadas_processadas: Number(row?.rodadas_proc || 0),
    escalacoes_salvas: Number(row?.escalacoes || 0),
    jogadores_com_stats: Number(row?.jogadores_stats || 0),
    ultima_rodada: ultima ? `${ultima.ano}-R${ultima.rodada}` : undefined,
    ultimo_processamento: ultima?.processado_em ? String(ultima.processado_em) : undefined,
  };
}

export async function getJogadorHistorico(atletaId: string, limite = 50): Promise<JogadorHistorico[]> {
  return neonQuery<JogadorHistorico>(`
    SELECT * FROM (
      SELECT atleta_id, apelido, posicao_id, clube_id, clube_nome,
             rodada, ano, pontos, media, preco, variacao, jogos,
             entrou_em_campo, status_id, data_jogo, competicao
      FROM jogadores_historico 
      WHERE atleta_id = $1 AND competicao = 'Brasileirão'
      ORDER BY ano DESC, rodada DESC 
      LIMIT $2
    ) sub
    ORDER BY ano DESC, rodada DESC
  `, [atletaId, limite]);
}

/** Combined history: Brasileirão + competições paralelas in chronological order.
 *  Matches Python db_historico.carregar_historico_jogador() - queries jogadores_historico
 *  which already has all competitions unified (Brasileirão + paralelas).
 */
export async function getJogadorHistoricoCompleto(atletaId: string, limite = 200) {
  // Query the MOST RECENT N entries from jogadores_historico
  // Use a subquery to get the last N rows, then order them chronologically
  const rows = await neonQuery<any>(`
    SELECT * FROM (
      SELECT atleta_id, apelido, posicao_id, clube_id, clube_nome,
             rodada, ano, pontos, media, preco, variacao, jogos,
             entrou_em_campo, status_id, data_jogo, competicao,
             peso
      FROM jogadores_historico 
      WHERE atleta_id = $1
      ORDER BY data_jogo DESC, ano DESC, rodada DESC
      LIMIT $2
    ) sub
    ORDER BY data_jogo ASC, ano ASC, rodada ASC
  `, [atletaId, limite]);

  // Apply peso (weight) for parallel competitions like Python does
  const PESOS_COMPETICAO: Record<string, number> = {
    'Copa do Brasil': 0.85,
    'Libertadores': 0.80,
    'Sulamericana': 0.75,
    'Paulista A1': 0.60,
    'Carioca': 0.55,
    'Mineiro': 0.55,
    'Gaúcho': 0.55,
    'Baiano': 0.50,
    'Paranaense': 0.50,
    'Cearense': 0.50,
    'Goiano': 0.50,
    'Pernambucano': 0.50,
  };

  return rows.filter((r: any) => {
    const comp = r.competicao || 'Brasileirão';
    const isBrasileiro = comp === 'Brasileirão';
    const pontos = Number(r.pontos) || 0;
    const entrou = isBrasileiro ? (r.entrou_em_campo || pontos !== 0) : true;
    return entrou || pontos !== 0;
  }).map((r: any) => {
    const comp = r.competicao || 'Brasileirão';
    const isBrasileiro = comp === 'Brasileirão';
    const pontosRaw = Number(r.pontos) || 0;
    let pontosFinal = pontosRaw;
    if (!isBrasileiro) {
      const peso = Number(r.peso) || PESOS_COMPETICAO[comp] || 0.5;
      pontosFinal = pontosRaw * peso;
    }
    return { ...r, pontos: pontosFinal, competicao: comp };
  });
}

export async function getJogadoresRodada(rodada: number, ano: number): Promise<JogadorHistorico[]> {
  return neonQuery<JogadorHistorico>(`
    SELECT atleta_id, apelido, posicao_id, clube_id, clube_nome,
           rodada, ano, pontos, media, preco, variacao, jogos,
           entrou_em_campo, status_id
    FROM jogadores_historico 
    WHERE rodada = $1 AND ano = $2 AND competicao = 'Brasileirão'
  `, [rodada, ano]);
}

export async function getRodadasProcessadas(): Promise<RodadaProcessada[]> {
  return neonQuery<RodadaProcessada>(`
    SELECT rodada, ano, total_jogadores, jogadores_provaveis, processado_em
    FROM rodadas_processadas 
    ORDER BY ano DESC, rodada DESC
  `);
}

export async function getCompetParalelas(atletaId: string): Promise<CompetParalela[]> {
  return neonQuery<CompetParalela>(`
    SELECT atleta_id, apelido, posicao, clube_nome, competicao, temporada,
           data_jogo, fixture_id, adversario, pontuacao_simulada,
           gols, assistencias, desarmes, cartao_amarelo, cartao_vermelho,
           defesas, gols_sofridos, minutos_jogados
    FROM competicoes_paralelas 
    WHERE atleta_id = $1 
    ORDER BY data_jogo DESC
    LIMIT 50
  `, [atletaId]);
}

export async function getStatusColeta() {
  const totais = await neonQueryOne<{
    total_cp: string;
    total_jh: string;
    total_fixtures: string;
  }>(`
    SELECT 
      (SELECT COUNT(*) FROM competicoes_paralelas) as total_cp,
      (SELECT COUNT(*) FROM jogadores_historico) as total_jh,
      (SELECT COUNT(DISTINCT fixture_id) FROM competicoes_paralelas) as total_fixtures
  `);

  const competicoes = await neonQuery<{
    competicao: string;
    total: string;
    ultima_data: string;
  }>(`
    SELECT competicao, COUNT(*) as total, MAX(data_jogo)::text as ultima_data
    FROM competicoes_paralelas
    GROUP BY competicao
    ORDER BY total DESC
  `);

  const ultimos = await neonQuery<{
    fixture_id: number;
    competicao: string;
    data_jogo: string;
    total_jogadores: string;
  }>(`
    SELECT fixture_id, competicao, data_jogo::text, COUNT(*) as total_jogadores
    FROM competicoes_paralelas
    GROUP BY fixture_id, competicao, data_jogo
    ORDER BY data_jogo DESC
    LIMIT 20
  `);

  return {
    total_competicoes_paralelas: Number(totais?.total_cp || 0),
    total_jogadores_historico: Number(totais?.total_jh || 0),
    total_fixtures: Number(totais?.total_fixtures || 0),
    competicoes: competicoes.map(c => ({
      competicao: c.competicao,
      total: Number(c.total),
      ultima_data: c.ultima_data,
    })),
    ultimos_jogos: ultimos.map(u => ({
      fixture_id: u.fixture_id,
      competicao: u.competicao,
      data_jogo: u.data_jogo,
      total_jogadores: Number(u.total_jogadores),
    })),
  };
}

export async function getEscalacaoSessao() {
  const row = await neonQueryOne<{ dados: unknown }>(`
    SELECT dados FROM sessao_escalacao ORDER BY atualizado_em DESC LIMIT 1
  `);
  return row?.dados || null;
}

export async function getHistoricoRodadas(ano: number) {
  return neonQuery(`
    SELECT id, rodada, ano, formacao, pontos_reais, valorizacao_real, atualizado,
           data_criacao, escalacao_json
    FROM escalacoes_salvas 
    WHERE ano = $1 
    ORDER BY rodada DESC
  `, [ano]);
}

export async function getMediaPosicao(posicaoId: number, rodada: number, ano: number) {
  const row = await neonQueryOne<{ media_pontos: string; total: string }>(`
    SELECT AVG(pontos) as media_pontos, COUNT(*) as total
    FROM jogadores_historico
    WHERE posicao_id = $1 AND rodada = $2 AND ano = $3 AND entrou_em_campo = true AND competicao = 'Brasileirão'
  `, [posicaoId, rodada, ano]);
  return {
    media: Number(row?.media_pontos || 0),
    total: Number(row?.total || 0),
  };
}

export async function getTopJogadoresRodada(rodada: number, ano: number, limite = 10) {
  return neonQuery(`
    SELECT atleta_id, apelido, posicao_id, clube_nome, pontos, media, preco
    FROM jogadores_historico
    WHERE rodada = $1 AND ano = $2 AND entrou_em_campo = true AND competicao = 'Brasileirão'
    ORDER BY pontos DESC
    LIMIT $3
  `, [rodada, ano, limite]);
}

// ============================================
// TIME IDEAL CALCULATION
// ============================================

const FORMACAO_MAP: Record<string, Record<string, number>> = {
  '3-4-3': { '1': 1, '3': 3, '2': 0, '4': 4, '5': 3, '6': 1 },
  '3-5-2': { '1': 1, '3': 3, '2': 0, '4': 5, '5': 2, '6': 1 },
  '4-3-3': { '1': 1, '3': 2, '2': 2, '4': 3, '5': 3, '6': 1 },
  '4-4-2': { '1': 1, '3': 2, '2': 2, '4': 4, '5': 2, '6': 1 },
  '4-5-1': { '1': 1, '3': 2, '2': 2, '4': 5, '5': 1, '6': 1 },
  '5-3-2': { '1': 1, '3': 3, '2': 2, '4': 3, '5': 2, '6': 1 },
  '5-4-1': { '1': 1, '3': 3, '2': 2, '4': 4, '5': 1, '6': 1 },
};

/**
 * Calculate the ideal team for a given round - top scorers per position within budget.
 * Similar to Python's calcular_time_ideal function.
 */
export async function calcularTimeIdeal(
  ano: number,
  rodada: number,
  orcamento: number,
  formacao: string = '4-3-3'
): Promise<{
  titulares: any[];
  capitao: any | null;
  pontuacao_real: number;
  custo_total: number;
  formacao: string;
} | null> {
  // Get all players who played in this round
  const jogadores = await neonQuery<any>(`
    SELECT atleta_id, apelido, posicao_id, clube_id, clube_nome, pontos, media, preco
    FROM jogadores_historico
    WHERE rodada = $1 AND ano = $2 AND entrou_em_campo = true AND competicao = 'Brasileirão'
    ORDER BY pontos DESC
  `, [rodada, ano]);

  if (!jogadores || jogadores.length === 0) return null;

  const qtdPorPosicao = FORMACAO_MAP[formacao] || FORMACAO_MAP['4-3-3'];
  const titulares: any[] = [];
  const usados = new Set<string>();

  // For each position, pick the top scorers
  for (const [posId, qtd] of Object.entries(qtdPorPosicao)) {
    if (qtd === 0) continue;
    const posJogadores = jogadores
      .filter((j: any) => String(j.posicao_id) === posId && !usados.has(String(j.atleta_id)))
      .sort((a: any, b: any) => Number(b.pontos) - Number(a.pontos))
      .slice(0, qtd);

    for (const j of posJogadores) {
      usados.add(String(j.atleta_id));
      titulares.push({
        atleta_id: j.atleta_id,
        apelido: j.apelido,
        pos_id: Number(j.posicao_id),
        posicao: POSICOES[Number(j.posicao_id)] || 'N/A',
        clube_id: j.clube_id,
        clube: j.clube_nome,
        pontos: Number(j.pontos),
        preco: Number(j.preco || 0),
        media: Number(j.media || 0),
      });
    }
  }

  // Find the best captain (highest scorer)
  const capitao = titulares.length > 0
    ? titulares.reduce((best, j) => (j.pontos > best.pontos ? j : best), titulares[0])
    : null;

  const pontuacao_real = titulares.reduce((sum, j) => {
    const pts = j.pontos;
    const bonus = capitao && String(j.atleta_id) === String(capitao.atleta_id) ? pts * 0.5 : 0;
    return sum + pts + bonus;
  }, 0);

  const custo_total = titulares.reduce((sum, j) => sum + j.preco, 0);

  return {
    titulares,
    capitao,
    pontuacao_real,
    custo_total,
    formacao,
  };
}
