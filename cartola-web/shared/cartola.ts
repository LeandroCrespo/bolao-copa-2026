// Cartola FC shared types and constants

export const POSICOES: Record<number, string> = {
  1: "GOL", 2: "LAT", 3: "ZAG", 4: "MEI", 5: "ATA", 6: "TEC",
};

export const STATUS_JOGADOR: Record<number, string> = {
  2: "Dúvida", 3: "Suspenso", 5: "Contundido", 6: "Nulo", 7: "Provável",
};

export const FORMACOES: Record<string, Record<number, number>> = {
  "3-4-3": { 1: 1, 2: 0, 3: 3, 4: 4, 5: 3, 6: 1 },
  "3-5-2": { 1: 1, 2: 0, 3: 3, 4: 5, 5: 2, 6: 1 },
  "4-3-3": { 1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 1 },
  "4-4-2": { 1: 1, 2: 2, 3: 2, 4: 4, 5: 2, 6: 1 },
  "4-5-1": { 1: 1, 2: 2, 3: 2, 4: 5, 5: 1, 6: 1 },
  "5-3-2": { 1: 1, 2: 2, 3: 3, 4: 3, 5: 2, 6: 1 },
  "5-4-1": { 1: 1, 2: 2, 3: 3, 4: 4, 5: 1, 6: 1 },
};

export interface MercadoStatus {
  rodada_atual: number;
  status_mercado: number;
  game_over: boolean;
  temporada: number;
  fechamento?: { timestamp: number };
  times_escalados?: number;
}

export interface AtletaMercado {
  atleta_id: number;
  apelido: string;
  nome?: string;
  posicao_id: number;
  posicao_nome: string;
  clube_id: number;
  clube_nome: string;
  clube_abreviacao: string;
  preco: number;
  media: number;
  variacao: number;
  pontos_ultima_rodada: number;
  jogos: number;
  status_id: number;
  status_nome: string;
  entrou_em_campo?: boolean;
  scout?: Record<string, number>;
  foto?: string;
}

export interface JogadorHistorico {
  id: number;
  atleta_id: string;
  apelido: string;
  posicao_id: number;
  clube_id: number;
  clube_nome: string;
  rodada: number;
  ano: number;
  pontos: number;
  media: number;
  preco: number;
  variacao: number;
  jogos: number;
  entrou_em_campo: boolean;
  status_id: number;
  data_jogo: string;
  competicao: string;
  adversario: string;
  pontuacao_simulada: number;
  gols: number;
  assistencias: number;
  finalizacoes_gol: number;
  desarmes: number;
  faltas_sofridas: number;
  faltas_cometidas: number;
  cartao_amarelo: number;
  cartao_vermelho: number;
  defesas: number;
  gols_sofridos: number;
  minutos_jogados: number;
}

export interface CompetParalela {
  atleta_id: string;
  apelido: string;
  posicao: string;
  clube_nome: string;
  competicao: string;
  temporada: number;
  data_jogo: string;
  fixture_id: number;
  adversario: string;
  pontuacao_simulada: number;
  gols: number;
  assistencias: number;
  desarmes: number;
  cartao_amarelo: number;
  cartao_vermelho: number;
  defesas: number;
  gols_sofridos: number;
  finalizacoes_gol: number;
  faltas_sofridas: number;
  faltas_cometidas: number;
  minutos_jogados: number;
}

export interface EscalacaoJogador {
  atleta_id: string;
  apelido: string;
  posicao: string;
  pos_id: number;
  preco: number;
  media: number;
  score_previsto: number;
  clube: string;
  clube_id?: number;
  e_capitao: boolean;
  pontos_real?: number;
  erro?: number;
  acertou?: boolean;
  scout?: Record<string, number>;
  variacao?: number;
  preco_pos?: number;
}

export interface EscalacaoData {
  rodada: number;
  ano: number;
  data_escalacao: string;
  formacao: string;
  orcamento_disponivel: number;
  custo_total: number;
  pontuacao_prevista: number;
  jogadores: EscalacaoJogador[];
  reservas: Record<string, EscalacaoJogador | null>;
  reserva_luxo: EscalacaoJogador | null;
  capitao: {
    atleta_id: string;
    apelido: string;
    score_previsto: number;
    pontos_real?: number;
  };
  pontuacao_real?: number;
  processado?: boolean;
  substituicoes?: Array<{
    posicao: string;
    saiu: string;
    entrou: string;
    ganho: number;
  }>;
  ganho_total_substituicoes?: number;
  acertos?: number;
  acuracia?: number;
  valorizacao_real?: number;
}

export interface RodadaProcessada {
  rodada: number;
  ano: number;
  total_jogadores: number;
  jogadores_provaveis: number;
  processado_em: string;
}

export interface DbStats {
  total_registros_historico: number;
  rodadas_processadas: number;
  escalacoes_salvas: number;
  jogadores_com_stats: number;
  ultima_rodada?: string;
  ultimo_processamento?: string;
}

export interface StatusColetaResumo {
  total_competicoes_paralelas: number;
  total_jogadores_historico: number;
  total_fixtures: number;
  competicoes: Array<{
    competicao: string;
    total: number;
    ultima_data: string;
  }>;
  ultimos_jogos: Array<{
    fixture_id: number;
    competicao: string;
    data_jogo: string;
    total_jogadores: number;
  }>;
}

export interface Partida {
  partida_id: number;
  clube_casa_id: number;
  clube_visitante_id: number;
  mandante: string;
  visitante: string;
  placar_oficial_mandante?: number;
  placar_oficial_visitante?: number;
  valida?: boolean;
  partida_data?: string;
}
