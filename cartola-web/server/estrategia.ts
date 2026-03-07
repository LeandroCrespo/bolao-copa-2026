/**
 * EstrategiaV7 - Motor de Escalação do Cartola FC
 * Portado fielmente do Python para TypeScript
 * 
 * Suporta:
 * - Cálculo de features preditivas (preparar_features_v9)
 * - Score geral v9 com regressão à média
 * - Otimização ILP (heurística) e Greedy
 * - Seleção de capitão, reservas e reserva de luxo
 * - Reotimização de orçamento
 * - Análise multi-formação
 * - Mando de campo
 * - Power Ranking dos times
 * - Multiplicadores por justificativa
 */

import { neonQuery } from './neonDb';
import { otimizarEscalacaoILP } from './otimizador';

// ========== TYPES ==========
export interface Jogador {
  atleta_id: string;
  apelido: string;
  posicao_id: number;
  clube_id: number;
  clube_nome?: string;
  preco: number;
  media: number;
  pontos_num?: number;
  variacao_num?: number;
  status_id?: number;
  entrou_em_campo?: boolean;
  foto?: string;
  scout?: Record<string, number>;
  // Computed features
  score?: number;
  pred?: number;
  score_geral_v9?: number;
  media_base?: number;
  media_ultimas_3?: number;
  media_ultimas_5?: number;
  media_ultimas_10?: number;
  std_ultimas_5?: number;
  max_ultimas_5?: number;
  pontos_ultima?: number;
  media_historica?: number;
  sequencia_jogos?: number;
  custo_beneficio?: number;
  tendencia?: number;
  momentum?: number;
  variacao_acum_3?: number;
  seq_valorizacao?: number;
  padrao_evolucao?: number;
  distancia_media?: number;
  abaixo_media?: number;
  oportunidade_regressao?: number;
  score_oportunidade?: number;
  score_recuperacao?: number;
  risco_regressao?: number;
  bonus_scouts?: number;
  power_ranking_time?: number;
  bonus_power_ranking?: number;
  prioridade_padrao?: number;
  prioridade_tendencia?: number;
  prioridade_regressao?: number;
  status_ok?: number;
  mult_justificativa?: number;
  ranking_posicao?: number;
  total_posicao?: number;
  [key: string]: any;
}

export interface JogadorFormatado {
  atleta_id: string;
  apelido: string;
  pos_id: number;
  posicao: string;
  preco: number;
  media: number;
  score: number;
  pontuacao_esperada: number;
  clube: string;
  clube_id: number;
  valorizacao_prevista: number;
  pontos_reais: number;
  foto?: string;
  explicacao?: {
    fatores: string[];
    resumo: string;
    significado: string;
    motivo: string;
    tendencia: string;
    analise_medias: string;
    medias: {
      ultimas_3: number;
      ultimas_5: number;
      ultimas_10: number;
      geral: number;
    };
  };
}

export interface Escalacao {
  titulares: JogadorFormatado[];
  reservas: Record<number, JogadorFormatado>;
  reserva_luxo: JogadorFormatado | null;
  capitao: JogadorFormatado | null;
  vice_capitao: JogadorFormatado | null;
  custo_total: number;
  orcamento_restante: number;
  pontuacao_esperada: number;
  valorizacao_total: number;
  formacao: string;
  estrategia_especial?: string;
  top5_por_posicao?: Record<number, JogadorFormatado[]>;
  df_ranqueado?: Jogador[];
}

export interface HistoricoJogador {
  pts: number[];
  entrou: boolean[];
  variacao: number[];
  total_jogos: number;
  gols: number[];
  assistencias: number[];
  participacao_gols: number[];
  desarmes: number[];
  saldo_gols: number[];
  apelido?: string;
  posicao_id?: number;
  clube_id?: number;
  clube_nome?: string;
}

// ========== CONSTANTS ==========
export const POSICAO_MAP: Record<number, string> = {
  1: 'GOL', 2: 'LAT', 3: 'ZAG', 4: 'MEI', 5: 'ATA', 6: 'TEC'
};

export const POSICAO_NOME: Record<number, string> = {
  1: 'Goleiro', 2: 'Lateral', 3: 'Zagueiro', 4: 'Meia', 5: 'Atacante', 6: 'Técnico'
};

export const FORMACOES: Record<string, Record<number, number>> = {
  '3-4-3': { 1: 1, 2: 0, 3: 3, 4: 4, 5: 3, 6: 1 },
  '3-5-2': { 1: 1, 2: 0, 3: 3, 4: 5, 5: 2, 6: 1 },
  '4-3-3': { 1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 1 },
  '4-4-2': { 1: 1, 2: 2, 3: 2, 4: 4, 5: 2, 6: 1 },
  '4-5-1': { 1: 1, 2: 2, 3: 2, 4: 5, 5: 1, 6: 1 },
  '5-3-2': { 1: 1, 2: 2, 3: 3, 4: 3, 5: 2, 6: 1 },
  '5-4-1': { 1: 1, 2: 2, 3: 3, 4: 4, 5: 1, 6: 1 },
};

// Multiplicadores de mando de campo por posição
const MULT_MANDO_POR_POSICAO: Record<number, Record<string, number>> = {
  1: { M: 1.00, V: 1.00 },   // GOL: sem efeito
  2: { M: 1.05, V: 0.95 },   // LAT: +5%/-5%
  3: { M: 1.07, V: 0.93 },   // ZAG: +7%/-7%
  4: { M: 1.04, V: 0.96 },   // MEI: +4%/-4%
  5: { M: 1.05, V: 0.95 },   // ATA: +5%/-5%
  6: { M: 1.05, V: 0.95 },   // TEC: +5%/-5%
};

// Multiplicadores por justificativa (aproveitamento 2025)
const MULT_JUSTIFICATIVA: Record<string, number> = {
  consistente: 1.12,
  aposta: 1.08,
  custo_beneficio: 1.05,
  boa_fase: 1.05,
  em_queda: 0.92,
  recuperacao: 0.95,
  premium: 0.88,
};

// Bonus de capitão por posição
const BONUS_CAPITAO: Record<number, number> = {
  5: 1.7,   // Atacante
  4: 1.45,  // Meia
  2: 1.1,   // Lateral
  1: 1.0,   // Goleiro
  3: 1.0,   // Zagueiro
  6: 0.8,   // Técnico
};

// Pesos de competições paralelas
const PESOS_COMPETICAO: Record<string, number> = {
  'Brasileirão': 1.0,
  'Paulistão': 0.5,
  'Carioca': 0.5,
  'Gaúcho': 0.45,
  'Mineiro': 0.45,
  'Copa do Brasil': 0.7,
  'Libertadores': 0.8,
  'Sul-Americana': 0.6,
};

// Parâmetros aprendidos (default)
const DEFAULT_PESOS_POSICAO: Record<string, number> = {
  GOL: 1.0, LAT: 1.0, ZAG: 1.0, MEI: 1.0, ATA: 1.0, TEC: 1.0
};
const DEFAULT_BONUS_PREMIUM = 0.5;

// ========== HELPER FUNCTIONS ==========
function mean(arr: number[]): number {
  if (arr.length === 0) return 0;
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}

function std(arr: number[]): number {
  if (arr.length === 0) return 0;
  const m = mean(arr);
  return Math.sqrt(arr.reduce((sum, v) => sum + (v - m) ** 2, 0) / arr.length);
}

function clip(val: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, val));
}

// ========== HISTORICO FROM NEON DB ==========
async function carregarHistoricoCompleto(anos?: number[], maxAno?: number, maxRodada?: number): Promise<Record<string, HistoricoJogador>> {
  let whereClause = '';
  if (anos && anos.length > 0) {
    whereClause = `WHERE ano IN (${anos.join(',')})`;
    // If maxAno and maxRodada are specified, exclude rounds >= maxRodada in maxAno
    // This enables progressive history: load all previous years + current year up to round N-1
    if (maxAno && maxRodada) {
      whereClause += ` AND NOT (ano = ${maxAno} AND rodada >= ${maxRodada})`;
    }
  }

  const query = `
    SELECT atleta_id, apelido, posicao_id, clube_id, clube_nome,
           rodada, ano, pontos, variacao, entrou_em_campo,
           competicao, peso, data_jogo
    FROM jogadores_historico
    ${whereClause}
    ORDER BY atleta_id, data_jogo NULLS FIRST, ano, rodada
  `;

  const rows = await neonQuery(query);
  const historico: Record<string, HistoricoJogador> = {};

  for (const row of rows) {
    const atletaId = String(row.atleta_id);
    const competicao = row.competicao || 'Brasileirão';
    const isBrasileiro = competicao === 'Brasileirão';

    if (!historico[atletaId]) {
      historico[atletaId] = {
        pts: [], entrou: [], variacao: [], total_jogos: 0,
        gols: [], assistencias: [], participacao_gols: [],
        desarmes: [], saldo_gols: [],
        apelido: String(row.apelido || ''),
        posicao_id: Number(row.posicao_id || 0),
        clube_id: Number(row.clube_id || 0),
        clube_nome: String(row.clube_nome || ''),
      };
    }

    const pontosRaw = parseFloat(String(row.pontos)) || 0;
    let pontosFinal: number;
    let entrou: boolean;

    if (isBrasileiro) {
      pontosFinal = pontosRaw;
      entrou = Boolean(row.entrou_em_campo) || pontosRaw !== 0;
    } else {
      const peso = parseFloat(String(row.peso)) || PESOS_COMPETICAO[competicao as string] || 0.5;
      pontosFinal = pontosRaw * peso;
      entrou = true;
    }

    if (entrou || pontosRaw !== 0) {
      historico[atletaId].pts.push(pontosFinal);
      historico[atletaId].entrou.push(true);
      historico[atletaId].variacao.push(parseFloat(String(row.variacao)) || 0);
      if (entrou) {
        historico[atletaId].total_jogos++;
      }
    }

    // Update latest info
    if (row.apelido) historico[atletaId].apelido = String(row.apelido);
    if (row.posicao_id) historico[atletaId].posicao_id = Number(row.posicao_id);
    if (row.clube_id) historico[atletaId].clube_id = Number(row.clube_id);
    if (row.clube_nome) historico[atletaId].clube_nome = String(row.clube_nome);
  }

  // Limit history to 15 entries
  for (const aid of Object.keys(historico)) {
    const h = historico[aid];
    for (const k of ['pts', 'entrou', 'variacao', 'gols', 'assistencias', 'participacao_gols', 'desarmes', 'saldo_gols'] as const) {
      if (h[k] && (h[k] as any[]).length > 15) {
        (h[k] as any[]) = (h[k] as any[]).slice(-15);
      }
    }
  }

  return historico;
}

// ========== POWER RANKING ==========
// Simplified power ranking based on team standings
async function getPowerRankings(): Promise<Record<number, number>> {
  try {
    const resp = await fetch('https://api.cartola.globo.com/mercado/status', { signal: AbortSignal.timeout(10000) });
    if (!resp.ok) return {};
    // For now, return neutral values - can be enhanced with real standings data
    return {};
  } catch {
    return {};
  }
}

// ========== MANDO DE CAMPO ==========
async function obterMandoApi(rodada: number): Promise<Record<number, string>> {
  try {
    const resp = await fetch(`https://api.cartola.globo.com/partidas/${rodada}`, { signal: AbortSignal.timeout(10000) });
    if (!resp.ok) return {};
    const data = await resp.json();
    const partidas = data.partidas || [];
    const mando: Record<number, string> = {};
    for (const p of partidas) {
      if (p.clube_casa_id && p.clube_visitante_id) {
        mando[p.clube_casa_id] = 'M';
        mando[p.clube_visitante_id] = 'V';
      }
    }
    return mando;
  } catch {
    return {};
  }
}

// ========== MAIN ENGINE CLASS ==========
export class EstrategiaV7 {
  public orcamento: number;
  private historico: Record<string, HistoricoJogador> = {};
  private historicoPorNome: Record<string, string> = {};
  private rodadaAtual: number = 1;
  private resultados: Array<{ rodada: number; pontos: number; valorizacao: number }> = [];
  private modoSimulacao: boolean;
  private historicoCarregado: boolean = false;
  private pesosAprendidos: Record<string, number> = DEFAULT_PESOS_POSICAO;
  private bonusPremium: number = DEFAULT_BONUS_PREMIUM;
  private lastMaxAno?: number;
  private lastMaxRodada?: number;

  constructor(orcamento: number = 100.0, modoSimulacao: boolean = false) {
    this.orcamento = orcamento;
    this.modoSimulacao = modoSimulacao;
  }

  // ========== CARREGAR HISTORICO DO BANCO ==========
  async carregarHistorico(maxAno?: number, maxRodada?: number): Promise<void> {
    if (this.historicoCarregado && !maxAno) return;
    // Skip reload if same maxAno/maxRodada (e.g., testing multiple formations for same round)
    if (maxAno && this.lastMaxAno === maxAno && this.lastMaxRodada === maxRodada) return;
    
    // For simulation: include the simulation year in history, filtered by maxRodada
    let anos: number[];
    if (this.modoSimulacao) {
      if (maxAno) {
        // Like Python: only load previous year + current year (filtered by maxRodada)
        anos = [maxAno - 1, maxAno];
      } else {
        anos = [2022, 2023, 2024];
      }
    } else {
      anos = [2022, 2023, 2024, 2025, 2026];
    }
    const hist = await carregarHistoricoCompleto(anos, maxAno, maxRodada);
    
    // Reset historico when reloading for a new round
    if (maxAno) {
      this.historico = {};
      this.historicoPorNome = {};
    }
    
    // Build historico and name mapping
    for (const [atletaId, data] of Object.entries(hist)) {
      this.historico[atletaId] = data;
      
      if (data.apelido) {
        const posId = data.posicao_id || 0;
        const clubeId = data.clube_id || 0;
        
        // Key: apelido_posicao_clube (most specific)
        this.historicoPorNome[`${data.apelido}_${posId}_${clubeId}`] = atletaId;
        // Key: apelido_posicao
        const keyPos = `${data.apelido}_${posId}`;
        if (!this.historicoPorNome[keyPos]) {
          this.historicoPorNome[keyPos] = atletaId;
        }
        // Key: apelido (fallback)
        if (!this.historicoPorNome[data.apelido]) {
          this.historicoPorNome[data.apelido] = atletaId;
        }
      }
    }
    
    if (!maxAno) this.historicoCarregado = true;
    if (maxAno) {
      this.lastMaxAno = maxAno;
      this.lastMaxRodada = maxRodada;
    }
    console.log(`[EstrategiaV7] Histórico carregado: ${Object.keys(this.historico).length} jogadores (maxAno=${maxAno}, maxRodada=${maxRodada})`);
  }

  // ========== IDENTIFICAR ARMADILHAS ==========
  identificarArmadilhas(jogadores: Jogador[]): Set<string> {
    const armadilhas = new Set<string>();
    for (const j of jogadores) {
      const aid = String(j.atleta_id);
      const hist = this.historico[aid];
      if (!hist || !hist.pts.length) continue;
      
      const mediaHist = mean(hist.pts);
      if (mediaHist <= 5) continue;
      
      const entrouCount = hist.entrou.filter(Boolean).length;
      const totalJogos = hist.pts.length;
      const ratioEntrou = totalJogos > 0 ? entrouCount / totalJogos : 0;
      
      const ptsRecentes = hist.pts.slice(-3);
      const mediaRecente = mean(ptsRecentes);
      const ratioPts = mediaHist > 0 ? mediaRecente / mediaHist : 0;
      
      if (ratioEntrou < 0.3 || ratioPts < 0.2) {
        armadilhas.add(aid);
      }
    }
    return armadilhas;
  }

  // ========== PREPARAR FEATURES V9 ==========
  async prepararFeaturesV9(jogadores: Jogador[], modoSimulacao: boolean = false, maxAno?: number, maxRodada?: number): Promise<Jogador[]> {
    await this.carregarHistorico(maxAno, maxRodada);
    
    const result: Jogador[] = jogadores.map(j => {
      const jog = { ...j };
      
      // Normalize fields
      jog.preco = parseFloat(String(jog.preco || jog.preco_num || 5));
      jog.posicao_id = parseInt(String(jog.posicao_id || 0));
      jog.atleta_id = String(jog.atleta_id || jog.id || '');
      jog.apelido = jog.apelido || jog.apelido_abreviado || jog.nome || 'Jogador';
      jog.status_ok = jog.status_id === 7 ? 1 : 0;
      
      // Media handling
      if (modoSimulacao) {
        jog.media = 0; // Will be calculated from history
      } else {
        jog.media = parseFloat(String(jog.media_num || jog.media || 0));
      }
      
      // Calculate features from history
      const aid = String(jog.atleta_id);
      const apelido = String(jog.apelido || '');
      
      // Find history by ID or name
      let hist = this.historico[aid];
      if ((!hist || !hist.pts.length) && apelido) {
        const posId = jog.posicao_id || 0;
        const clubeId = jog.clube_id || 0;
        
        const keyFull = `${apelido}_${posId}_${clubeId}`;
        let aidAntigo = this.historicoPorNome[keyFull];
        if (!aidAntigo) {
          aidAntigo = this.historicoPorNome[`${apelido}_${posId}`];
        }
        if (!aidAntigo) {
          aidAntigo = this.historicoPorNome[apelido];
        }
        if (aidAntigo && aidAntigo !== aid) {
          hist = this.historico[aidAntigo];
        }
      }
      
      if (!hist) {
        hist = { pts: [], entrou: [], variacao: [], total_jogos: 0, gols: [], assistencias: [], participacao_gols: [], desarmes: [], saldo_gols: [] };
      }
      
      const pts = hist.pts || [];
      const variacao = hist.variacao || [];
      const totalJogos = hist.total_jogos || 0;
      
      // Scout histories
      const golsHist = hist.gols || [];
      const assistHist = hist.assistencias || [];
      const partGolsHist = hist.participacao_gols || [];
      const desarmesHist = hist.desarmes || [];
      const sgHist = hist.saldo_gols || [];
      
      // Media base
      let mediaBase: number;
      if (modoSimulacao) {
        mediaBase = pts.length > 0 ? mean(pts) : 0;
      } else {
        if (pts.length >= 3) {
          mediaBase = mean(pts);
        } else if (jog.media > 0) {
          mediaBase = jog.media;
        } else {
          mediaBase = pts.length > 0 ? mean(pts) : 0;
        }
      }
      
      // Moving averages
      const mediaUltimas3 = pts.length >= 3 ? mean(pts.slice(-3)) : mediaBase;
      const mediaUltimas5 = pts.length >= 5 ? mean(pts.slice(-5)) : mediaBase;
      const mediaUltimas10 = pts.length >= 10 ? mean(pts.slice(-10)) : mediaBase;
      const stdUltimas5 = pts.length >= 5 ? std(pts.slice(-5)) : 5;
      const maxUltimas5 = pts.length >= 5 ? Math.max(...pts.slice(-5)) : mediaBase;
      const pontosUltima = pts.length > 0 ? pts[pts.length - 1] : 0;
      const mediaHistorica = pts.length > 0 ? mean(pts) : mediaBase;
      
      // Sequencia jogos
      const sequenciaJogos = totalJogos > 0 ? totalJogos : (hist.entrou ? hist.entrou.filter(Boolean).length : 0);
      
      // Tendencia e momentum
      let tendencia = 0;
      let momentum = 0;
      if (pts.length >= 3) {
        tendencia = pts[pts.length - 1] > pts[pts.length - 3] ? 1 : (pts[pts.length - 1] < pts[pts.length - 3] ? -1 : 0);
        momentum = pts[pts.length - 1] - mean(pts.slice(-3));
      }
      
      // Variacao acumulada
      const variacaoAcum3 = variacao.length >= 3 ? variacao.slice(-3).reduce((a, b) => a + b, 0) : 0;
      
      // Sequencia de valorizacao
      let seqVal = 0;
      const varSlice = variacao.slice(-5);
      for (let i = varSlice.length - 1; i >= 0; i--) {
        if (varSlice[i] > 0) seqVal++;
        else break;
      }
      
      // Padrao de evolucao
      let padraoEvolucao = 0;
      if (pts.length >= 5) {
        const primeiraMetade = mean(pts.slice(0, Math.floor(pts.length / 2)));
        const segundaMetade = mean(pts.slice(Math.floor(pts.length / 2)));
        if (segundaMetade > primeiraMetade * 1.1) padraoEvolucao = 1;
        else if (segundaMetade < primeiraMetade * 0.9) padraoEvolucao = -1;
      }
      
      // Distancia da media
      const mediaRef = mediaBase > 0 ? mediaBase : 1;
      const distanciaMedia = (mediaUltimas3 - mediaRef) / mediaRef;
      const abaixoMedia = distanciaMedia < -0.1 ? 1 : 0;
      
      // Oportunidade de regressao
      const oportunidadeRegressao = (abaixoMedia === 1 && padraoEvolucao >= 0) ? 1 : 0;
      
      // Scores
      const scoreOportunidade = abaixoMedia ? mediaBase * (1 + Math.abs(distanciaMedia)) : 0;
      const scoreRecuperacao = (padraoEvolucao === 0 && abaixoMedia === 1) ? mediaBase * 1.2 : 0;
      const riscoRegressao = (distanciaMedia > 0.2 && padraoEvolucao === 1) ? 1 : 0;
      
      // Custo beneficio
      const custoBeneficio = jog.preco > 0 ? mediaBase / jog.preco : 0;
      
      // Scout features
      const posId = jog.posicao_id || 0;
      const mediaGols = golsHist.length > 0 ? mean(golsHist) : 0;
      const mediaAssist = assistHist.length > 0 ? mean(assistHist) : 0;
      const mediaPartGols = partGolsHist.length > 0 ? mean(partGolsHist) : 0;
      const mediaDesarmes = desarmesHist.length > 0 ? mean(desarmesHist) : 0;
      const mediaSg = sgHist.length > 0 ? mean(sgHist) : 0;
      
      const mediaPartGols3 = partGolsHist.length >= 3 ? mean(partGolsHist.slice(-3)) : mediaPartGols;
      const mediaDesarmes3 = desarmesHist.length >= 3 ? mean(desarmesHist.slice(-3)) : mediaDesarmes;
      const mediaSg3 = sgHist.length >= 3 ? mean(sgHist.slice(-3)) : mediaSg;
      
      // Scout regression
      let bonusScouts = 0;
      if (oportunidadeRegressao === 1) {
        if ([4, 5].includes(posId) && mediaPartGols > 0) {
          const distPartGols = (mediaPartGols3 - mediaPartGols) / mediaPartGols;
          if (distPartGols < -0.15) bonusScouts = 0.15;
        } else if ([2, 3, 4].includes(posId) && mediaDesarmes > 0) {
          const distDesarmes = (mediaDesarmes3 - mediaDesarmes) / mediaDesarmes;
          if (distDesarmes < -0.15) bonusScouts = 0.10;
        } else if ([1, 2, 3].includes(posId) && mediaSg > 0) {
          const distSg = (mediaSg3 - mediaSg) / mediaSg;
          if (distSg < -0.15) bonusScouts = 0.10;
        }
      }
      
      // Assign all features
      jog.media_base = mediaBase;
      jog.media_ultimas_3 = mediaUltimas3;
      jog.media_ultimas_5 = mediaUltimas5;
      jog.media_ultimas_10 = mediaUltimas10;
      jog.std_ultimas_5 = stdUltimas5;
      jog.max_ultimas_5 = maxUltimas5;
      jog.pontos_ultima = pontosUltima;
      jog.media_historica = mediaHistorica;
      jog.sequencia_jogos = sequenciaJogos;
      jog.tendencia = tendencia;
      jog.momentum = momentum;
      jog.variacao_acum_3 = variacaoAcum3;
      jog.seq_valorizacao = seqVal;
      jog.padrao_evolucao = padraoEvolucao;
      jog.distancia_media = distanciaMedia;
      jog.abaixo_media = abaixoMedia;
      jog.oportunidade_regressao = oportunidadeRegressao;
      jog.score_oportunidade = scoreOportunidade;
      jog.score_recuperacao = scoreRecuperacao;
      jog.risco_regressao = riscoRegressao;
      jog.custo_beneficio = custoBeneficio;
      jog.bonus_scouts = bonusScouts;
      
      // Update media in simulation mode
      if (modoSimulacao) {
        jog.media = mediaBase;
      } else if (jog.media === 0 && mediaBase > 0) {
        jog.media = mediaBase;
      }
      
      return jog;
    });
    
    // Score geral v9
    for (const jog of result) {
      jog.score_geral_v9 = (
        (jog.score_oportunidade || 0) * 0.3 +
        (jog.score_recuperacao || 0) * 0.2 +
        (jog.media || 0) * 0.2 +
        (jog.seq_valorizacao || 0) * 0.1 +
        clip(jog.sequencia_jogos || 0, 0, 5) * 0.1 +
        (jog.custo_beneficio || 0) * 0.1
      );
      
      // Bonus for regression opportunity
      if (jog.oportunidade_regressao === 1) {
        jog.score_geral_v9 *= 1.2;
      }
      
      // Cross bonus: scoring + scouts
      jog.score_geral_v9 *= (1 + (jog.bonus_scouts || 0));
      
      // Power ranking (neutral for now - 50)
      jog.power_ranking_time = 50;
      jog.bonus_power_ranking = 0;
      
      // Priority columns for deterministic tiebreaking
      jog.prioridade_padrao = jog.padrao_evolucao || 0;
      jog.prioridade_tendencia = (jog.momentum || 0) > 0.1 ? 1 : ((jog.momentum || 0) < -0.1 ? -1 : 0);
      jog.prioridade_regressao = jog.oportunidade_regressao === 1 ? 1 : (jog.risco_regressao === 1 ? -1 : 0);
    }
    
    return result;
  }

  // ========== ESCALAR TIME ==========
  async escalarTime(
    dfMercado: Jogador[],
    formacao: string = '4-3-3',
    orcamento: number = 100.0,
    incluirExplicacao: boolean = true,
    modoSimulacao: boolean = false,
    rodada?: number,
    ano?: number
  ): Promise<Escalacao> {
    const df = await this.prepararFeaturesV9(dfMercado, modoSimulacao, ano, rodada);
    
    // ML prediction: use linear approximation of RandomForest model
    // Weights derived from the Python modelo_v9.joblib (R² = 0.91)
    const ML_WEIGHTS = [
      -0.012584, 0.539435, -0.006851, 0.021807, 0.002066,
      0.04188, 0.021061, -0.004741, -0.025558, 0.002699,
      -0.053687, -0.007847, -0.007744, -0.002544, -0.001674,
      -0.003559, -0.001435, -0.000217, 0.091326, -0.009103,
      -0.00633, -0.034095, 0.043335
    ];
    const ML_BIAS = -0.134553;
    
    // Apply linear ML model to all players
    for (const j of df) {
      const features = [
        j.media || 0, j.preco || 0, j.media_ultimas_3 || 0,
        j.media_ultimas_5 || 0, j.media_ultimas_10 || 0,
        j.std_ultimas_5 || 0, j.max_ultimas_5 || 0,
        j.pontos_ultima || 0, j.media_historica || 0,
        j.sequencia_jogos || 0, j.custo_beneficio || 0,
        j.tendencia || 0, j.momentum || 0,
        j.variacao_acum_3 || 0, j.seq_valorizacao || 0,
        j.padrao_evolucao || 0, j.distancia_media || 0,
        j.abaixo_media || 0, j.oportunidade_regressao || 0,
        j.score_oportunidade || 0, j.score_recuperacao || 0,
        j.risco_regressao || 0, j.score_geral_v9 || 0
      ];
      let mlPred = ML_BIAS;
      for (let i = 0; i < 23; i++) {
        mlPred += features[i] * ML_WEIGHTS[i];
      }
      j.pred = Math.max(0, mlPred);
      j.score = j.pred;
    }
    
    // In non-simulation mode, also try DB predictions and use if available
    if (!modoSimulacao) {
      try {
        const { neonQuery } = await import('./neonDb');
        const mlPreds = await neonQuery<{atleta_id: string, pred: number}>(
          'SELECT atleta_id, pred FROM ml_predictions'
        );
        const predMap = new Map(mlPreds.map(p => [String(p.atleta_id), Number(p.pred)]));
        let mlCount = 0;
        for (const j of df) {
          const dbPred = predMap.get(String(j.atleta_id));
          if (dbPred !== undefined && dbPred > 0) {
            j.pred = dbPred;
            j.score = dbPred;
            mlCount++;
          }
        }
        console.log(`[ML] Loaded ${mlPreds.length} DB predictions, matched ${mlCount} jogadores`);
      } catch (err) {
        console.log('[ML] DB predictions unavailable, using linear model');
      }
    }
    
    // ========== BÔNUS DE PROVÁVEIS (Site provaveisdocartola.com.br) ==========
    // MUST be applied BEFORE other adjustments (same order as Python)
    if (!modoSimulacao) {
      try {
        const provaveisResp = await fetch('https://provaveisdocartola.com.br/assets/data/lineups.json', { signal: AbortSignal.timeout(10000) });
        if (provaveisResp.ok) {
          const provaveisData = await provaveisResp.json();
          const idsProvaveis = new Set<number>();
          const idsDuvida = new Set<number>();
          const teams = provaveisData.teams || {};
          
          for (const teamName of Object.keys(teams)) {
            const teamData = teams[teamName];
            const titulares = teamData.titulares || [];
            for (const jogador of titulares) {
              const atletaId = jogador.id;
              if (atletaId) {
                const sit = jogador.sit || '';
                if (sit === 'provavel') {
                  idsProvaveis.add(Number(atletaId));
                } else if (sit === 'duvida') {
                  idsDuvida.add(Number(atletaId));
                  if (jogador.duvida_com) {
                    idsDuvida.add(Number(jogador.duvida_com));
                  }
                }
              }
            }
          }
          
          let totalBonus = 0, totalPenalizado = 0, totalNeutro = 0;
          for (const j of df) {
            const atletaId = Number(j.atleta_id);
            if (idsDuvida.has(atletaId)) {
              j.score = (j.score || 0) * 0.85; // -15% para dúvida
              totalPenalizado++;
            } else if (idsProvaveis.has(atletaId)) {
              j.score = (j.score || 0) * 1.15; // +15% para prováveis do site
              totalBonus++;
            } else if (j.status_id === 7) { // Provável na API mas ausente do site
              j.score = (j.score || 0) * 0.85; // -15% para ausentes do site
              totalPenalizado++;
            } else {
              totalNeutro++;
            }
          }
          console.log(`[PROVÁVEIS] Prováveis site: ${totalBonus} | Penalizados: ${totalPenalizado} | Neutros: ${totalNeutro}`);
        }
      } catch (err) {
        console.warn('[PROVÁVEIS] Erro ao obter dados:', err);
      }
    }
    
    // Apply position weights (after provaveis)
    for (const j of df) {
      const posSigla = POSICAO_MAP[j.posicao_id] || '';
      const peso = this.pesosAprendidos[posSigla] || 1.0;
      j.score = (j.score || 0) * peso;
    }
    
    // Premium bonus for MEI and ATA
    for (const j of df) {
      if (j.preco >= 12 && j.media >= 6 && [4, 5].includes(j.posicao_id)) {
        j.score = (j.score || 0) + this.bonusPremium;
      }
    }
    
    // Justification multipliers
    for (const j of df) {
      const mult = this._classificarJustificativa(j);
      j.mult_justificativa = mult;
      j.score = (j.score || 0) * mult;
    }
    
    // Mando de campo
    if (rodada) {
      const mandoDict = await obterMandoApi(rodada);
      if (Object.keys(mandoDict).length > 0) {
        for (const j of df) {
          const mando = mandoDict[j.clube_id];
          if (mando && MULT_MANDO_POR_POSICAO[j.posicao_id]) {
            j.score = (j.score || 0) * (MULT_MANDO_POR_POSICAO[j.posicao_id][mando] || 1);
          }
        }
      }
    }
    
    // Valorization strategy for round 1
    if (rodada === 1 && !modoSimulacao) {
      for (const j of df) {
        const minimoValorizar = j.preco * 0.50;
        const deltaValorizacao = (j.score || 0) - minimoValorizar;
        const probValorizacao = clip(deltaValorizacao / 5, 0, 1);
        
        const bonusR1 = Math.max(0, deltaValorizacao) * 0.15 + (1 / (minimoValorizar + 1)) * 0.5;
        j.score = (j.score || 0) + bonusR1;
        
        if (probValorizacao > 0.6) j.score *= 1.05;
        if (j.preco > 15) j.score *= 0.95;
      }
    }
    
    // Filter available players
    const temMedias = df.some(j => j.media > 0);
    let dfFiltrado: Jogador[];
    
    if (modoSimulacao) {
      dfFiltrado = df.filter(j => j.media > 0 && j.entrou_em_campo !== false);
    } else {
      if (temMedias) {
        dfFiltrado = df.filter(j => j.media > 0 && j.status_ok === 1 && (j.sequencia_jogos || 0) >= 1);
      } else {
        dfFiltrado = df.filter(j => j.status_ok === 1 && (j.sequencia_jogos || 0) >= 1);
      }
    }
    
    // Relax filter if not enough players
    if (dfFiltrado.length < 50) {
      dfFiltrado = temMedias ? df.filter(j => j.media > 0) : df.filter(j => j.status_ok === 1);
    }
    
    // Remove traps
    const armadilhas = this.identificarArmadilhas(df);
    if (armadilhas.size > 0) {
      dfFiltrado = dfFiltrado.filter(j => !armadilhas.has(String(j.atleta_id)));
    }
    
    const configFormacao = FORMACOES[formacao] || FORMACOES['4-3-3'];
    
    // ========== ILP OPTIMIZATION (like Python PuLP) ==========
    // Try ILP first, fall back to greedy if it fails
    const idsOtimizados = otimizarEscalacaoILP(
      dfFiltrado.map(j => ({ ...j, score: j.score || 0 })),
      configFormacao, orcamento, 50
    );
    const totalEsperado = Object.values(configFormacao).reduce((a, b) => a + b, 0);
    
    if (idsOtimizados.length === totalEsperado) {
      // ILP succeeded - use optimized solution
      const titulares: JogadorFormatado[] = [];
      let custoTotal = 0;
      const idsUsados = new Set<string>();
      
      for (const atletaId of idsOtimizados) {
        const row = dfFiltrado.find(j => String(j.atleta_id) === atletaId);
        if (row) {
          titulares.push(this._formatarJogador(row, incluirExplicacao));
          custoTotal += row.preco;
          idsUsados.add(atletaId);
        }
      }
      
      // Sort by position for display
      titulares.sort((a, b) => {
        const ordem = [1, 3, 2, 4, 5, 6];
        return ordem.indexOf(a.pos_id) - ordem.indexOf(b.pos_id);
      });
      
      console.log(`[ESCALACAO] ILP solution: ${titulares.length} players, C$ ${custoTotal.toFixed(2)}`);
      
      // Finalize with ILP solution
      return this._finalizarEscalacao(
        titulares, custoTotal, idsUsados, df, dfFiltrado,
        orcamento, formacao, configFormacao, incluirExplicacao
      );
    }
    
    // ========== GREEDY FALLBACK ==========
    console.log('[ESCALACAO] ILP failed, using greedy fallback');
    const { titulares, custoTotal, idsUsados } = this._greedySelection(dfFiltrado, df, configFormacao, orcamento);
    
    // Budget optimization
    const { titulares: titularesOtimizados, custoTotal: custoOtimizado } = 
      this._reotimizarOrcamento(titulares, dfFiltrado, orcamento, idsUsados);
    
    // Finalize
    return this._finalizarEscalacao(
      titularesOtimizados, custoOtimizado, idsUsados, df, dfFiltrado,
      orcamento, formacao, configFormacao, incluirExplicacao
    );
  }

  // ========== GREEDY SELECTION ==========
  private _greedySelection(
    dfFiltrado: Jogador[], dfAll: Jogador[],
    configFormacao: Record<number, number>, orcamento: number
  ): { titulares: JogadorFormatado[]; custoTotal: number; idsUsados: Set<string> } {
    const titulares: JogadorFormatado[] = [];
    let custoTotal = 0;
    const idsUsados = new Set<string>();
    const ordemPosicoes = [1, 3, 2, 4, 5, 6];
    
    for (const posId of ordemPosicoes) {
      const qtd = configFormacao[posId] || 0;
      if (qtd === 0) continue;
      
      let posDf = dfFiltrado
        .filter(j => j.posicao_id === posId)
        .sort((a, b) => (b.score || 0) - (a.score || 0));
      
      if (posDf.length < qtd) {
        posDf = dfAll
          .filter(j => j.posicao_id === posId)
          .sort((a, b) => (b.score || 0) - (a.score || 0));
      }
      
      let selected = 0;
      for (const row of posDf) {
        if (selected >= qtd) break;
        const aid = String(row.atleta_id);
        if (idsUsados.has(aid)) continue;
        
        // Calculate minimum remaining cost
        let custoMinimoRestante = 0;
        for (const p of ordemPosicoes) {
          let qtdRestante = 0;
          if (p === posId) {
            qtdRestante = qtd - selected - 1;
          } else if (ordemPosicoes.indexOf(p) > ordemPosicoes.indexOf(posId)) {
            qtdRestante = configFormacao[p] || 0;
          }
          
          if (qtdRestante > 0) {
            const disponiveis = dfFiltrado
              .filter(j => j.posicao_id === p && !idsUsados.has(String(j.atleta_id)) && String(j.atleta_id) !== aid)
              .sort((a, b) => a.preco - b.preco)
              .slice(0, qtdRestante);
            custoMinimoRestante += disponiveis.reduce((sum, j) => sum + j.preco, 0);
          }
        }
        
        const orcamentoRestante = orcamento - custoTotal - row.preco;
        if (orcamentoRestante >= custoMinimoRestante) {
          titulares.push(this._formatarJogador(row, true));
          custoTotal += row.preco;
          idsUsados.add(aid);
          selected++;
        }
      }
    }
    
    // Ensure 12 players
    const totalEsperado = Object.values(configFormacao).reduce((a, b) => a + b, 0);
    if (titulares.length < totalEsperado) {
      for (const posId of ordemPosicoes) {
        const qtd = configFormacao[posId] || 0;
        let atual = titulares.filter(t => t.pos_id === posId).length;
        
        while (atual < qtd) {
          const disponiveis = dfAll
            .filter(j => j.posicao_id === posId && !idsUsados.has(String(j.atleta_id)))
            .sort((a, b) => (b.score || 0) - (a.score || 0));
          
          let encontrou = false;
          for (const row of disponiveis) {
            if (custoTotal + row.preco <= orcamento) {
              titulares.push(this._formatarJogador(row, true));
              custoTotal += row.preco;
              idsUsados.add(String(row.atleta_id));
              atual++;
              encontrou = true;
              break;
            }
          }
          if (!encontrou) break;
        }
      }
    }
    
    return { titulares, custoTotal, idsUsados };
  }

  // ========== REOTIMIZAR ORCAMENTO ==========
  private _reotimizarOrcamento(
    titulares: JogadorFormatado[], df: Jogador[],
    orcamento: number, idsUsados: Set<string>
  ): { titulares: JogadorFormatado[]; custoTotal: number } {
    let custoTotal = titulares.reduce((sum, t) => sum + t.preco, 0);
    let orcamentoRestante = orcamento - custoTotal;
    
    if (orcamentoRestante < 0.5) return { titulares, custoTotal };
    
    // Stage 1: Score upgrades
    let melhorou = true;
    let iteracao = 0;
    while (melhorou && iteracao < 20) {
      melhorou = false;
      iteracao++;
      const idsAtuais = new Set(titulares.map(t => t.atleta_id));
      
      for (let i = 0; i < titulares.length; i++) {
        const titular = titulares[i];
        const orcamentoUpgrade = orcamentoRestante + titular.preco;
        
        const candidatos = df
          .filter(j => 
            j.posicao_id === titular.pos_id &&
            !idsAtuais.has(String(j.atleta_id)) &&
            j.preco <= orcamentoUpgrade &&
            (j.score || 0) > titular.score
          )
          .sort((a, b) => (b.score || 0) - (a.score || 0));
        
        if (candidatos.length > 0) {
          const melhor = candidatos[0];
          const ganhoScore = (melhor.score || 0) - titular.score;
          
          if (ganhoScore > 0.1) {
            const novoJogador = this._formatarJogador(melhor, true);
            idsAtuais.delete(titular.atleta_id);
            idsUsados.delete(titular.atleta_id);
            
            titulares[i] = novoJogador;
            custoTotal = custoTotal - titular.preco + melhor.preco;
            orcamentoRestante = orcamento - custoTotal;
            idsAtuais.add(novoJogador.atleta_id);
            idsUsados.add(novoJogador.atleta_id);
            
            melhorou = true;
            break;
          }
        }
      }
    }
    
    // Stage 2: Price upgrades (use remaining budget)
    orcamentoRestante = orcamento - custoTotal;
    if (orcamentoRestante > 2.0) {
      melhorou = true;
      iteracao = 0;
      while (melhorou && iteracao < 20) {
        melhorou = false;
        iteracao++;
        const idsAtuais = new Set(titulares.map(t => t.atleta_id));
        
        const titularesOrdenados = titulares
          .map((t, i) => ({ t, i }))
          .sort((a, b) => a.t.preco - b.t.preco);
        
        for (const { t: titular, i: idx } of titularesOrdenados) {
          const orcamentoUpgrade = orcamentoRestante + titular.preco;
          const scoreMinimo = titular.score * 0.95;
          
          const candidatos = df
            .filter(j =>
              j.posicao_id === titular.pos_id &&
              !idsAtuais.has(String(j.atleta_id)) &&
              j.preco <= orcamentoUpgrade &&
              j.preco > titular.preco &&
              (j.score || 0) >= scoreMinimo
            )
            .sort((a, b) => b.preco - a.preco);
          
          if (candidatos.length > 0) {
            const melhor = candidatos[0];
            const difPreco = melhor.preco - titular.preco;
            
            if (difPreco >= 1.0) {
              const novoJogador = this._formatarJogador(melhor, true);
              idsAtuais.delete(titular.atleta_id);
              idsUsados.delete(titular.atleta_id);
              
              titulares[idx] = novoJogador;
              custoTotal = custoTotal - titular.preco + melhor.preco;
              orcamentoRestante = orcamento - custoTotal;
              idsAtuais.add(novoJogador.atleta_id);
              idsUsados.add(novoJogador.atleta_id);
              
              melhorou = true;
              break;
            }
          }
        }
      }
    }
    
    return { titulares, custoTotal };
  }

  // ========== FINALIZAR ESCALACAO ==========
  private _finalizarEscalacao(
    titulares: JogadorFormatado[], custoTotal: number, idsUsados: Set<string>,
    df: Jogador[], dfFiltrado: Jogador[],
    orcamento: number, formacao: string, configFormacao: Record<number, number>,
    incluirExplicacao: boolean
  ): Escalacao {
    // Captain selection
    const capitao = titulares.length > 0
      ? titulares.reduce((best, t) => this._calcularScoreCapitao(t) > this._calcularScoreCapitao(best) ? t : best)
      : null;
    
    // Vice-captain selection (second best captain score)
    const viceCapitao = titulares.length > 1 && capitao
      ? titulares.filter(t => t.atleta_id !== capitao.atleta_id)
          .reduce((best, t) => this._calcularScoreCapitao(t) > this._calcularScoreCapitao(best) ? t : best)
      : null;
    
    // Luxury reserve
    let reservaLuxo: JogadorFormatado | null = null;
    let posCapitao: number | null = null;
    
    if (capitao) {
      posCapitao = capitao.pos_id;
      const jogadoresPosCapitao = titulares.filter(t => t.pos_id === posCapitao);
      const precoMaxLuxo = jogadoresPosCapitao.length > 0
        ? Math.min(...jogadoresPosCapitao.map(j => j.preco))
        : 0;
      
      let luxoDf = dfFiltrado
        .filter(j => j.posicao_id === posCapitao && !idsUsados.has(String(j.atleta_id)) && j.preco <= precoMaxLuxo)
        .sort((a, b) => (b.score || 0) - (a.score || 0));
      
      if (luxoDf.length === 0) {
        luxoDf = df
          .filter(j => j.posicao_id === posCapitao && !idsUsados.has(String(j.atleta_id)) && j.preco <= precoMaxLuxo)
          .sort((a, b) => (b.score || 0) - (a.score || 0));
      }
      
      if (luxoDf.length > 0) {
        reservaLuxo = this._formatarJogador(luxoDf[0], incluirExplicacao);
      }
    }
    
    // Regular reserves
    const idsUsadosReservas = new Set(idsUsados);
    if (reservaLuxo) idsUsadosReservas.add(reservaLuxo.atleta_id);
    
    const reservas: Record<number, JogadorFormatado> = {};
    for (const posId of [1, 2, 3, 4, 5]) {
      if ((configFormacao[posId] || 0) === 0) continue;
      if (posId === posCapitao && reservaLuxo) continue;
      
      const titularesPosicao = titulares.filter(t => t.pos_id === posId);
      const precoMinTitular = titularesPosicao.length > 0
        ? Math.min(...titularesPosicao.map(t => t.preco))
        : Infinity;
      
      let resDf = dfFiltrado
        .filter(j => j.posicao_id === posId && !idsUsadosReservas.has(String(j.atleta_id)) && j.preco <= precoMinTitular)
        .sort((a, b) => (b.score || 0) - (a.score || 0));
      
      if (resDf.length === 0) {
        resDf = df
          .filter(j => j.posicao_id === posId && !idsUsadosReservas.has(String(j.atleta_id)) && j.preco <= precoMinTitular)
          .sort((a, b) => (b.score || 0) - (a.score || 0));
      }
      
      if (resDf.length > 0) {
        const reservaSelecionada = this._formatarJogador(resDf[0], incluirExplicacao);
        reservas[posId] = reservaSelecionada;
        idsUsadosReservas.add(reservaSelecionada.atleta_id);
      }
    }
    
    // Expected score
    let pontuacaoEsperada = titulares.reduce((sum, t) => sum + t.pontuacao_esperada, 0);
    if (capitao) {
      pontuacaoEsperada += capitao.pontuacao_esperada * 0.5;
    }
    
    // Total valorization
    const valorizacaoTotal = titulares.reduce((sum, t) => sum + t.valorizacao_prevista, 0);
    
    // Position rankings
    for (const posId of [1, 2, 3, 4, 5, 6]) {
      const posDf = df.filter(j => j.posicao_id === posId).sort((a, b) => (b.score || 0) - (a.score || 0));
      posDf.forEach((j, idx) => {
        j.ranking_posicao = idx + 1;
        j.total_posicao = posDf.length;
      });
    }
    
    // Top 5 per position
    const top5PorPosicao: Record<number, JogadorFormatado[]> = {};
    for (const posId of [1, 2, 3, 4, 5, 6]) {
      const posDf = df.filter(j => j.posicao_id === posId).sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, 10);
      top5PorPosicao[posId] = posDf.map(j => this._formatarJogador(j, false));
    }
    
    return {
      titulares,
      reservas,
      reserva_luxo: reservaLuxo,
      capitao,
      vice_capitao: viceCapitao,
      custo_total: custoTotal,
      orcamento_restante: orcamento - custoTotal,
      pontuacao_esperada: pontuacaoEsperada,
      valorizacao_total: Math.round(valorizacaoTotal * 100) / 100,
      formacao,
      top5_por_posicao: top5PorPosicao,
    };
  }

  // ========== CLASSIFICAR JUSTIFICATIVA ==========
  private _classificarJustificativa(j: Jogador): number {
    const oportunidade = j.oportunidade_regressao || 0;
    const padrao = j.padrao_evolucao || 0;
    const media = j.media || 0;
    const preco = j.preco || 0;
    const score = j.score || 0;
    const custoBen = preco > 0 ? media / preco : 0;
    
    if (oportunidade === 1) return MULT_JUSTIFICATIVA.recuperacao;
    if (padrao > 0.5 || padrao === 1) return MULT_JUSTIFICATIVA.boa_fase;
    if (padrao < -0.3 || padrao === -1) return MULT_JUSTIFICATIVA.em_queda;
    if (media >= 6) return MULT_JUSTIFICATIVA.premium;
    if (custoBen >= 0.5) return MULT_JUSTIFICATIVA.custo_beneficio;
    if (score > media * 1.2 && media > 0) return MULT_JUSTIFICATIVA.aposta;
    return MULT_JUSTIFICATIVA.consistente;
  }

  // ========== CALCULAR SCORE CAPITAO ==========
  private _calcularScoreCapitao(jogador: JogadorFormatado): number {
    const scoreBase = jogador.score || 0;
    const posId = jogador.pos_id || 0;
    const preco = jogador.preco || 0;
    const media = jogador.media || 0;
    
    const bonusPosicao = BONUS_CAPITAO[posId] || 1.0;
    
    let bonusPreco = 1.0;
    if (preco >= 15) bonusPreco = 1.4;
    else if (preco >= 12) bonusPreco = 1.25;
    else if (preco >= 9) bonusPreco = 1.1;
    
    let bonusMedia = 1.0;
    if (media >= 7) bonusMedia = 1.2;
    else if (media >= 5) bonusMedia = 1.1;
    
    return scoreBase * bonusPosicao * bonusPreco * bonusMedia;
  }

  // ========== FORMATAR JOGADOR ==========
  private _formatarJogador(j: Jogador | Record<string, any>, incluirExplicacao: boolean): JogadorFormatado {
    const score = parseFloat(String(j.score || j.pred || j.score_geral_v9 || 0));
    const pontuacaoPrevista = parseFloat(String(j.score_original || j.pred || j.score_geral_v9 || 0));
    const media = parseFloat(String(j.media || 0));
    const preco = parseFloat(String(j.preco || 0));
    
    let valorizacaoPrevista = -0.3;
    if (pontuacaoPrevista > 0) {
      valorizacaoPrevista = (pontuacaoPrevista - preco * 0.5) / 8;
    }
    
    const pontosReais = parseFloat(String(j.pontos || j.pontos_num || 0)) || 0;
    
    const res: JogadorFormatado = {
      atleta_id: String(j.atleta_id || ''),
      apelido: j.apelido || 'N/A',
      pos_id: parseInt(String(j.posicao_id || 0)),
      posicao: POSICAO_MAP[parseInt(String(j.posicao_id || 0))] || '',
      preco,
      media,
      score,
      pontuacao_esperada: Math.round(pontuacaoPrevista * 100) / 100,
      clube: j.clube_nome || j.clube || '',
      clube_id: parseInt(String(j.clube_id || 0)),
      valorizacao_prevista: Math.round(valorizacaoPrevista * 100) / 100,
      pontos_reais: pontosReais,
      foto: j.foto || undefined,
    };
    
    if (incluirExplicacao) {
      const padrao = j.padrao_evolucao || 0;
      const oportunidade = j.oportunidade_regressao || 0;
      const distancia = j.distancia_media || 0;
      const custoBeneficio = preco > 0 ? media / preco : 0;
      
      const media3 = j.media_ultimas_3 || 0;
      const media5 = j.media_ultimas_5 || 0;
      const media10 = j.media_ultimas_10 || 0;
      const mediaGeral = j.media_historica || media;
      
      // Tendencia text
      let tendenciaTexto: string;
      let tendenciaDesc: string;
      if (padrao > 0.5) {
        tendenciaTexto = '📈 CRESCENTE';
        tendenciaDesc = 'em boa fase, vem pontuando acima da média';
      } else if (padrao > 0) {
        tendenciaTexto = '↗️ Levemente crescente';
        tendenciaDesc = 'com leve melhora nas últimas rodadas';
      } else if (padrao < -0.3) {
        tendenciaTexto = '📉 DECRESCENTE';
        tendenciaDesc = 'em má fase, vem pontuando abaixo da média';
      } else if (padrao < 0) {
        tendenciaTexto = '↘️ Levemente decrescente';
        tendenciaDesc = 'com leve queda nas últimas rodadas';
      } else {
        tendenciaTexto = '➡️ Estável';
        tendenciaDesc = 'mantendo desempenho regular';
      }
      
      const fatores: string[] = [];
      fatores.push(`📊 Score previsto: ${res.pontuacao_esperada.toFixed(2)} pts`);
      fatores.push(`${tendenciaTexto} - ${tendenciaDesc}`);
      
      if (oportunidade === 1) fatores.push('🎯 Oportunidade de Regressão à Média: SIM');
      if (distancia < -0.1) fatores.push(`📉 Abaixo da média histórica (${(distancia * 100).toFixed(0)}%)`);
      else if (distancia > 0.1) fatores.push(`📈 Acima da média histórica (+${(distancia * 100).toFixed(0)}%)`);
      
      // Justification
      let resumo: string, significado: string, motivo: string;
      if (oportunidade === 1) {
        resumo = `🔄 Jogador em recuperação - oportunidade de regressão à média | ${tendenciaTexto}`;
        significado = `O jogador teve pontuações ruins recentemente, mas seu histórico geral é muito bom. Tendência atual: ${tendenciaDesc}.`;
        motivo = `O sistema identifica uma 'regressão à média'. Acredita que a má fase é temporária e que ele tem grandes chances de voltar a pontuar bem.`;
      } else if (padrao > 0.5) {
        resumo = `📈 Boa fase - consistência | ${tendenciaTexto}`;
        significado = `O jogador vem de uma sequência de boas pontuações nas últimas rodadas. Tendência: ${tendenciaDesc}.`;
        motivo = `É uma escolha segura e confiável, com alta probabilidade de manter o bom desempenho.`;
      } else if (padrao < -0.3) {
        resumo = `📉 Jogador em queda - atenção | ${tendenciaTexto}`;
        significado = `Alerta! As últimas pontuações do jogador estão abaixo de sua média histórica. Tendência: ${tendenciaDesc}.`;
        motivo = `Mesmo em má fase, a pontuação prevista para esta rodada específica ainda é alta. O sistema considera que ele pode se recuperar.`;
      } else if (media >= 6) {
        resumo = `⭐ Jogador premium - alta média | ${tendenciaTexto}`;
        significado = `É um dos melhores jogadores do campeonato, com média de pontuação elevada. Tendência: ${tendenciaDesc}.`;
        motivo = `Jogadores premium são escolhas naturais quando o orçamento permite.`;
      } else if (custoBeneficio >= 0.5) {
        resumo = `💰 Custo-benefício - bom preço | ${tendenciaTexto}`;
        significado = `O jogador tem uma boa relação entre pontuação esperada e preço. Tendência: ${tendenciaDesc}.`;
        motivo = `Quando o orçamento é limitado, o sistema prioriza jogadores que entregam boas pontuações por um preço acessível.`;
      } else if (score > media * 1.2 && media > 0) {
        resumo = `🎲 Aposta da rodada - alto potencial | ${tendenciaTexto}`;
        significado = `O jogador não é uma escolha óbvia, mas o modelo identificou uma oportunidade específica. Tendência: ${tendenciaDesc}.`;
        motivo = `O cérebro digital identificou variáveis que indicam um potencial diferenciado para esta rodada.`;
      } else {
        resumo = `✅ Jogador consistente | ${tendenciaTexto}`;
        significado = `O jogador mantém um desempenho estável ao longo das rodadas. Tendência: ${tendenciaDesc}.`;
        motivo = `Consistência é valorizada pelo sistema, pois reduz o risco de pontuações muito baixas.`;
      }
      
      // Media analysis
      const mediaRef2 = mediaGeral !== 0 ? mediaGeral : media;
      const varVsGeral = mediaRef2 !== 0 ? ((media3 - mediaRef2) / Math.abs(mediaRef2)) * 100 : 0;
      
      let emojiSituacao: string;
      if (varVsGeral > 10) emojiSituacao = '🟢';
      else if (varVsGeral < -10) emojiSituacao = '🔴';
      else emojiSituacao = '🟡';
      
      let analiseMedias = `${emojiSituacao} Médias históricas: Últimas 3R: ${media3.toFixed(2)} pts | Últimas 5R: ${media5.toFixed(2)} pts | Últimas 10R: ${media10.toFixed(2)} pts | Geral: ${mediaGeral.toFixed(2)} pts. `;
      if (varVsGeral > 10) {
        analiseMedias += `O jogador está +${varVsGeral.toFixed(0)}% acima de sua média histórica, indicando boa fase.`;
      } else if (varVsGeral < -10) {
        analiseMedias += `O jogador está ${varVsGeral.toFixed(0)}% abaixo de sua média histórica, indicando momento de baixa.`;
      } else {
        analiseMedias += `O jogador está dentro de sua média histórica (${varVsGeral >= 0 ? '+' : ''}${varVsGeral.toFixed(0)}%), mantendo regularidade.`;
      }
      
      res.explicacao = {
        fatores,
        resumo,
        significado,
        motivo,
        tendencia: tendenciaTexto,
        analise_medias: analiseMedias,
        medias: {
          ultimas_3: Math.round(media3 * 100) / 100,
          ultimas_5: Math.round(media5 * 100) / 100,
          ultimas_10: Math.round(media10 * 100) / 100,
          geral: Math.round(mediaGeral * 100) / 100,
        },
      };
    }
    
    return res;
  }

  // ========== ANALISAR TODAS FORMACOES ==========
  async analisarTodasFormacoes(
    dfMercado: Jogador[], orcamento: number = 100.0,
    modoSimulacao: boolean = false, rodada?: number
  ): Promise<Escalacao[]> {
    const resultados: Escalacao[] = [];
    
    for (const formacao of Object.keys(FORMACOES)) {
      try {
        const escalacao = await this.escalarTime(dfMercado, formacao, orcamento, true, modoSimulacao, rodada);
        if (escalacao && escalacao.titulares.length === 12) {
          resultados.push(escalacao);
        }
      } catch (e) {
        console.error(`[EstrategiaV7] Erro na formação ${formacao}:`, e);
      }
    }
    
    resultados.sort((a, b) => b.pontuacao_esperada - a.pontuacao_esperada);
    return resultados;
  }

  // ========== ATUALIZAR AUTOMATICO ==========
  async atualizarAutomatico(escalacaoSalva: any): Promise<any> {
    try {
      // Fetch market status
      const statusResp = await fetch('https://api.cartola.globo.com/mercado/status', { signal: AbortSignal.timeout(10000) });
      if (!statusResp.ok) return { sucesso: false, erro: 'Não foi possível obter status do mercado' };
      const status = await statusResp.json();
      
      const rodadaApi = status.rodada_atual || 1;
      const mercadoPos = status.mercado_pos_rodada || false;
      const rodada = mercadoPos ? rodadaApi - 1 : rodadaApi;
      
      // Fetch market data (has real variation)
      const mercadoResp = await fetch('https://api.cartola.globo.com/atletas/mercado', { signal: AbortSignal.timeout(15000) });
      if (!mercadoResp.ok) return { sucesso: false, erro: 'Não foi possível obter dados do mercado' };
      const mercadoData = await mercadoResp.json();
      
      const atletasApi = mercadoData.atletas || [];
      const atletas: Record<string, any> = {};
      for (const a of atletasApi) {
        atletas[String(a.atleta_id)] = {
          pontuacao: a.pontos_num || 0,
          variacao: a.variacao_num || 0,
          entrou_em_campo: a.entrou_em_campo,
          scout: a.scout || {},
        };
      }
      
      if (!escalacaoSalva) return { sucesso: false, erro: 'Nenhuma escalação salva encontrada' };
      
      // Calculate total points and valorization
      let pontosTotal = 0;
      let valorizacaoTotal = 0;
      let jogadoresAtualizados = 0;
      const detalhes: any[] = [];
      
      const reservaLuxo = escalacaoSalva.reserva_luxo || {};
      const substituidoPeloLuxo = String(reservaLuxo.substituiu || '');
      
      const reservas = escalacaoSalva.reservas || {};
      const titularesSubstituidosPorReserva = new Set<string>();
      
      if (typeof reservas === 'object') {
        for (const [posId, reserva] of Object.entries(reservas)) {
          const r = reserva as any;
          if (r && r.substituiu) {
            const titularId = String(r.substituiu);
            if (atletas[titularId] && !atletas[titularId].entrou_em_campo) {
              titularesSubstituidosPorReserva.add(titularId);
            }
          }
        }
      }
      
      // Process starters
      for (const jogador of (escalacaoSalva.jogadores || escalacaoSalva.titulares || [])) {
        const atletaId = String(jogador.atleta_id);
        if (!atletas[atletaId]) continue;
        
        const dados = atletas[atletaId];
        let pontos = dados.pontuacao || 0;
        const variacao = dados.variacao || 0;
        
        const capitao = escalacaoSalva.capitao || {};
        const isCapitao = String(capitao.atleta_id) === atletaId;
        if (isCapitao) pontos *= 1.5;
        
        if (!titularesSubstituidosPorReserva.has(atletaId)) {
          pontosTotal += pontos;
        }
        
        if (atletaId !== substituidoPeloLuxo && !titularesSubstituidosPorReserva.has(atletaId)) {
          valorizacaoTotal += variacao;
        }
        
        jogadoresAtualizados++;
        detalhes.push({
          atleta_id: atletaId,
          apelido: jogador.apelido || 'N/A',
          pontos,
          variacao,
          capitao: isCapitao,
          substituido_luxo: atletaId === substituidoPeloLuxo,
        });
      }
      
      // Process reserves that replaced starters who didn't play
      if (typeof reservas === 'object') {
        for (const [posId, reserva] of Object.entries(reservas)) {
          const r = reserva as any;
          if (r && r.substituiu) {
            const titularId = String(r.substituiu);
            if (titularesSubstituidosPorReserva.has(titularId)) {
              const atletaId = String(r.atleta_id);
              if (atletas[atletaId]) {
                const dados = atletas[atletaId];
                pontosTotal += dados.pontuacao || 0;
                valorizacaoTotal += dados.variacao || 0;
                jogadoresAtualizados++;
              }
            }
          }
        }
      }
      
      // Process luxury reserve
      if (reservaLuxo && substituidoPeloLuxo && atletas[String(reservaLuxo.atleta_id)] && atletas[substituidoPeloLuxo]) {
        const dadosLuxo = atletas[String(reservaLuxo.atleta_id)];
        const dadosSubstituido = atletas[substituidoPeloLuxo];
        const ganho = (dadosLuxo.pontuacao || 0) - (dadosSubstituido.pontuacao || 0);
        if (ganho > 0) pontosTotal += ganho;
        valorizacaoTotal += dadosLuxo.variacao || 0;
      }
      
      const novoOrcamento = this.orcamento + valorizacaoTotal;
      
      return {
        sucesso: true,
        rodada,
        pontos: pontosTotal,
        valorizacao: valorizacaoTotal,
        novo_orcamento: novoOrcamento,
        total_jogadores_atualizados: jogadoresAtualizados,
        detalhes,
      };
    } catch (e: any) {
      return { sucesso: false, erro: e.message || String(e) };
    }
  }
}
