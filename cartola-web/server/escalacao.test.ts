import { describe, expect, it } from "vitest";

/**
 * Unit tests for escalação-related logic:
 * - Top 10 por posição building from df_ranqueado
 * - Valorização calculation with substitutions
 * - Manual substitution budget calculation
 */

// Replicate the top10PorPosicao building logic from routers.ts
function buildTop10PorPosicao(dfRanqueado: Record<string, Record<string, any>>, titulares: Array<{ atleta_id: string }>) {
  const top10PorPosicao: Record<number, any[]> = {};
  if (dfRanqueado && typeof dfRanqueado === 'object' && dfRanqueado.apelido) {
    const idsEscalados = new Set(titulares.map((t) => String(t.atleta_id)));
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
  return top10PorPosicao;
}

// Replicate the valorização calculation logic from routers.ts
function calcularValorizacaoComSubstituicoes(esc: any): number {
  const jogadores = esc.jogadores || [];
  const reservas = esc.reservas || {};
  const reservaLuxo = esc.reserva_luxo;

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

  // Sum valorização
  let valTotal = 0;
  for (const [, info] of Object.entries(jogInfo)) {
    if (!info.substituido) {
      valTotal += info.variacao;
    }
  }
  for (const r of reservasQueEntraram) {
    valTotal += parseFloat(r.variacao || '0') || 0;
  }

  return Math.round(valTotal * 100) / 100;
}

// Manual substitution budget logic
function calcBudgetDisponivel(orcamentoRestante: number, precoJogadorSaindo: number): number {
  return orcamentoRestante + precoJogadorSaindo;
}

describe("Top 10 por Posição", () => {
  const dfRanqueado = {
    apelido: { "0": "Jogador A", "1": "Jogador B", "2": "Jogador C", "3": "Jogador D" },
    atleta_id: { "0": "100", "1": "200", "2": "300", "3": "400" },
    posicao_id: { "0": 1, "1": 1, "2": 4, "3": 4 },
    score: { "0": 8.5, "1": 7.2, "2": 10.1, "3": 6.3 },
    preco: { "0": 5.0, "1": 3.0, "2": 12.0, "3": 8.0 },
    media: { "0": 4.0, "1": 3.5, "2": 9.0, "3": 5.0 },
    clube_id: { "0": 1, "1": 2, "2": 3, "3": 4 },
    clube_nome: { "0": "FLA", "1": "PAL", "2": "COR", "3": "SAO" },
    status_id: { "0": 7, "1": 7, "2": 7, "3": 7 },
  };

  const titulares = [{ atleta_id: "100" }, { atleta_id: "300" }];

  it("groups players by position and sorts by score descending", () => {
    const result = buildTop10PorPosicao(dfRanqueado, titulares);

    expect(result[1]).toHaveLength(2);
    expect(result[1][0].apelido).toBe("Jogador A");
    expect(result[1][0].score).toBe(8.5);
    expect(result[1][1].apelido).toBe("Jogador B");
    expect(result[1][1].score).toBe(7.2);

    expect(result[4]).toHaveLength(2);
    expect(result[4][0].apelido).toBe("Jogador C");
    expect(result[4][0].score).toBe(10.1);
  });

  it("marks escalated players correctly", () => {
    const result = buildTop10PorPosicao(dfRanqueado, titulares);

    expect(result[1][0].escalado).toBe(true); // Jogador A (id 100) is in titulares
    expect(result[1][1].escalado).toBe(false); // Jogador B (id 200) is not
    expect(result[4][0].escalado).toBe(true); // Jogador C (id 300) is in titulares
    expect(result[4][1].escalado).toBe(false); // Jogador D (id 400) is not
  });

  it("limits to 10 players per position", () => {
    const bigDf: Record<string, Record<string, any>> = {
      apelido: {},
      atleta_id: {},
      posicao_id: {},
      score: {},
      preco: {},
      media: {},
      clube_id: {},
      clube_nome: {},
      status_id: {},
    };
    for (let i = 0; i < 20; i++) {
      const idx = String(i);
      bigDf.apelido[idx] = `GOL ${i}`;
      bigDf.atleta_id[idx] = String(1000 + i);
      bigDf.posicao_id[idx] = 1;
      bigDf.score[idx] = 10 - i * 0.3;
      bigDf.preco[idx] = 5 + i;
      bigDf.media[idx] = 4;
      bigDf.clube_id[idx] = 1;
      bigDf.clube_nome[idx] = "FLA";
      bigDf.status_id[idx] = 7;
    }
    const result = buildTop10PorPosicao(bigDf, []);
    expect(result[1]).toHaveLength(10);
    expect(result[1][0].score).toBeGreaterThan(result[1][9].score);
  });

  it("filters out players with preco 0", () => {
    const dfWithFree = {
      ...dfRanqueado,
      preco: { "0": 5.0, "1": 0, "2": 12.0, "3": 8.0 },
    };
    const result = buildTop10PorPosicao(dfWithFree, []);
    expect(result[1]).toHaveLength(1); // Only Jogador A (preco 5.0)
    expect(result[1][0].apelido).toBe("Jogador A");
  });

  it("returns empty arrays for positions with no players", () => {
    const result = buildTop10PorPosicao(dfRanqueado, []);
    expect(result[2]).toHaveLength(0); // LAT
    expect(result[3]).toHaveLength(0); // ZAG
    expect(result[5]).toHaveLength(0); // ATA
    expect(result[6]).toHaveLength(0); // TEC
  });

  it("returns empty object when dfRanqueado is empty", () => {
    const result = buildTop10PorPosicao({}, []);
    expect(Object.keys(result)).toHaveLength(0);
  });
});

describe("Valorização com Substituições", () => {
  it("calculates simple valorização without substitutions", () => {
    const esc = {
      jogadores: [
        { atleta_id: "1", pos_id: 1, variacao: "0.5", pontos_real: 5, entrou_em_campo: true },
        { atleta_id: "2", pos_id: 4, variacao: "0.3", pontos_real: 8, entrou_em_campo: true },
      ],
      reservas: {},
    };
    const val = calcularValorizacaoComSubstituicoes(esc);
    expect(val).toBe(0.8);
  });

  it("excludes titular who did not play and includes reserve who entered", () => {
    const esc = {
      jogadores: [
        { atleta_id: "1", pos_id: 1, variacao: "0.5", pontos_real: null, entrou_em_campo: false },
        { atleta_id: "2", pos_id: 4, variacao: "0.3", pontos_real: 8, entrou_em_campo: true },
      ],
      reservas: {
        "1": { atleta_id: "10", variacao: "0.2", pontos_real: 3, entrou_em_campo: true },
      },
    };
    const val = calcularValorizacaoComSubstituicoes(esc);
    // Titular 1 (0.5) is substituido, so excluded
    // Reserve 10 (0.2) entered
    // Titular 2 (0.3) stays
    expect(val).toBe(0.5); // 0.3 + 0.2
  });
});

describe("Manual Substitution Budget", () => {
  it("calculates available budget correctly", () => {
    const budget = calcBudgetDisponivel(5.0, 10.0);
    expect(budget).toBe(15.0);
  });

  it("handles zero remaining budget", () => {
    const budget = calcBudgetDisponivel(0, 8.5);
    expect(budget).toBe(8.5);
  });

  it("handles negative remaining budget", () => {
    const budget = calcBudgetDisponivel(-2.0, 10.0);
    expect(budget).toBe(8.0);
  });
});
