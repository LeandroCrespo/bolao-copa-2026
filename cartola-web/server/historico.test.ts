import { describe, expect, it } from "vitest";

/**
 * Unit tests for Histórico features:
 * - Aproveitamento acumulado calculation
 * - Análise evolutiva (2026 vs 2025 reference data)
 * - Justificativa classification
 * - Gauge (aproveitamento por justificativa) calculation
 * - Top 5 jogadores calculation
 * - Formação frequency counting
 * - Tabela de resultados building
 * - Time ideal formation mapping
 */

// ===== REFERENCE DATA (subset for testing) =====
const REF_2025_FIXO: Record<number, { pts: number; orc: number }> = {
  1: { pts: 30.6, orc: 100.0 },
  2: { pts: 87.0, orc: 87.8 },
  3: { pts: 56.4, orc: 98.0 },
  4: { pts: 107.8, orc: 102.1 },
};

// ===== HELPER FUNCTIONS (replicated from Historico.tsx) =====

function calcAprovAcum(processadas: Array<{ pontos_reais: number; pontuacao_ideal?: number }>) {
  let ptsAcum = 0;
  let idealAcum = 0;
  return processadas.map((e) => {
    const pts = e.pontos_reais;
    const ptsIdeal = e.pontuacao_ideal || (pts * 2);
    ptsAcum += pts;
    idealAcum += ptsIdeal;
    const aprovAcum = idealAcum > 0 ? (ptsAcum / idealAcum * 100) : 0;
    const aprovRodada = ptsIdeal > 0 ? (pts / ptsIdeal * 100) : 0;
    return { aprovAcum, aprovRodada };
  });
}

function classifyJustificativa(resumo: string): string {
  const lower = resumo.toLowerCase();
  if (lower.includes('recuperação')) return 'Recuperação';
  if (lower.includes('boa fase')) return 'Boa Fase';
  if (lower.includes('queda')) return 'Em Queda';
  if (lower.includes('premium')) return 'Premium';
  if (lower.includes('custo')) return 'Custo-Benefício';
  if (lower.includes('aposta')) return 'Aposta';
  return 'Consistente';
}

function calcJustGauges(
  parsedRows: Array<{ jogadores: Array<{ pontos_real?: number; media?: number; explicacao?: { resumo?: string; medias?: { geral?: number } } }> }>
) {
  const stats: Record<string, { acertos: number; total: number }> = {};
  for (const e of parsedRows) {
    for (const j of e.jogadores) {
      const ptsReal = j.pontos_real;
      if (ptsReal == null) continue;
      const explicacao = j.explicacao || {};
      const medias = explicacao.medias || {};
      const mediaHist = Number(medias.geral || j.media || 0);
      const resumo = (explicacao.resumo || '').toLowerCase();
      const just = classifyJustificativa(resumo);
      if (!stats[just]) stats[just] = { acertos: 0, total: 0 };
      stats[just].total++;
      if (Number(ptsReal) >= mediaHist) stats[just].acertos++;
    }
  }
  return stats;
}

function calcTop5(
  processadas: Array<{ jogadores: Array<{ apelido: string; pontos_real?: number }> }>
) {
  const stats: Record<string, { pontos: number; escalacoes: number }> = {};
  for (const e of processadas) {
    for (const j of e.jogadores) {
      const nome = j.apelido || 'Desconhecido';
      const ptsReal = Number(j.pontos_real ?? 0);
      if (!stats[nome]) stats[nome] = { pontos: 0, escalacoes: 0 };
      stats[nome].pontos += ptsReal;
      stats[nome].escalacoes++;
    }
  }
  return Object.entries(stats)
    .sort((a, b) => b[1].pontos - a[1].pontos)
    .slice(0, 5)
    .map(([nome, s]) => ({ nome, ...s }));
}

function countFormacoes(rows: Array<{ formacao: string }>) {
  const counts: Record<string, number> = {};
  for (const e of rows) {
    counts[e.formacao] = (counts[e.formacao] || 0) + 1;
  }
  return counts;
}

const FORMACAO_MAP: Record<string, Record<string, number>> = {
  '4-3-3': { '1': 1, '3': 2, '2': 2, '4': 3, '5': 3, '6': 1 },
  '4-4-2': { '1': 1, '3': 2, '2': 2, '4': 4, '5': 2, '6': 1 },
  '3-5-2': { '1': 1, '3': 3, '2': 0, '4': 5, '5': 2, '6': 1 },
};

// ===== TESTS =====

describe("Aproveitamento Acumulado", () => {
  it("calculates cumulative and per-round approval correctly", () => {
    const data = [
      { pontos_reais: 50, pontuacao_ideal: 100 },
      { pontos_reais: 80, pontuacao_ideal: 100 },
      { pontos_reais: 60, pontuacao_ideal: 100 },
    ];
    const result = calcAprovAcum(data);

    // R1: 50/100 = 50%
    expect(result[0].aprovAcum).toBeCloseTo(50, 1);
    expect(result[0].aprovRodada).toBeCloseTo(50, 1);

    // R2: (50+80)/(100+100) = 130/200 = 65%
    expect(result[1].aprovAcum).toBeCloseTo(65, 1);
    expect(result[1].aprovRodada).toBeCloseTo(80, 1);

    // R3: (50+80+60)/(100+100+100) = 190/300 = 63.33%
    expect(result[2].aprovAcum).toBeCloseTo(63.33, 1);
    expect(result[2].aprovRodada).toBeCloseTo(60, 1);
  });

  it("handles zero ideal points", () => {
    const data = [{ pontos_reais: 50, pontuacao_ideal: 0 }];
    const result = calcAprovAcum(data);
    // When ideal is 0, fallback to pts * 2 = 100
    expect(result[0].aprovRodada).toBeCloseTo(50, 1);
  });

  it("handles empty data", () => {
    const result = calcAprovAcum([]);
    expect(result).toHaveLength(0);
  });
});

describe("Justificativa Classification", () => {
  it("classifies 'Recuperação' correctly", () => {
    expect(classifyJustificativa("Em recuperação de lesão")).toBe("Recuperação");
  });

  it("classifies 'Boa Fase' correctly", () => {
    expect(classifyJustificativa("Boa fase recente")).toBe("Boa Fase");
  });

  it("classifies 'Em Queda' correctly", () => {
    expect(classifyJustificativa("Em queda de rendimento")).toBe("Em Queda");
  });

  it("classifies 'Premium' correctly", () => {
    expect(classifyJustificativa("Jogador premium")).toBe("Premium");
  });

  it("classifies 'Custo-Benefício' correctly", () => {
    expect(classifyJustificativa("Bom custo-benefício")).toBe("Custo-Benefício");
  });

  it("classifies 'Aposta' correctly", () => {
    expect(classifyJustificativa("Aposta da rodada")).toBe("Aposta");
  });

  it("defaults to 'Consistente' for unknown", () => {
    expect(classifyJustificativa("Jogador regular")).toBe("Consistente");
    expect(classifyJustificativa("")).toBe("Consistente");
  });
});

describe("Justificativa Gauges", () => {
  it("calculates acertos/total correctly", () => {
    const rows = [{
      jogadores: [
        { pontos_real: 8, media: 5, explicacao: { resumo: "Boa fase", medias: { geral: 5 } } },
        { pontos_real: 3, media: 6, explicacao: { resumo: "Boa fase", medias: { geral: 6 } } },
        { pontos_real: 10, media: 4, explicacao: { resumo: "Aposta", medias: { geral: 4 } } },
      ],
    }];
    const result = calcJustGauges(rows);

    // Boa Fase: 1 acerto (8 >= 5), 1 miss (3 < 6) = 1/2
    expect(result["Boa Fase"].total).toBe(2);
    expect(result["Boa Fase"].acertos).toBe(1);

    // Aposta: 1 acerto (10 >= 4) = 1/1
    expect(result["Aposta"].total).toBe(1);
    expect(result["Aposta"].acertos).toBe(1);
  });

  it("skips players without pontos_real", () => {
    const rows = [{
      jogadores: [
        { pontos_real: undefined, media: 5, explicacao: { resumo: "Boa fase" } },
        { pontos_real: 8, media: 5, explicacao: { resumo: "Boa fase" } },
      ],
    }];
    const result = calcJustGauges(rows);
    expect(result["Boa Fase"].total).toBe(1);
  });
});

describe("Top 5 Jogadores", () => {
  it("ranks players by total points", () => {
    const data = [
      { jogadores: [
        { apelido: "A", pontos_real: 10 },
        { apelido: "B", pontos_real: 20 },
      ]},
      { jogadores: [
        { apelido: "A", pontos_real: 15 },
        { apelido: "C", pontos_real: 30 },
      ]},
    ];
    const result = calcTop5(data);

    expect(result[0].nome).toBe("C");
    expect(result[0].pontos).toBe(30);
    expect(result[0].escalacoes).toBe(1);

    expect(result[1].nome).toBe("A");
    expect(result[1].pontos).toBe(25);
    expect(result[1].escalacoes).toBe(2);

    expect(result[2].nome).toBe("B");
    expect(result[2].pontos).toBe(20);
    expect(result[2].escalacoes).toBe(1);
  });

  it("limits to 5 players", () => {
    const jogadores = Array.from({ length: 10 }, (_, i) => ({
      apelido: `Player ${i}`, pontos_real: 10 - i,
    }));
    const data = [{ jogadores }];
    const result = calcTop5(data);
    expect(result).toHaveLength(5);
    expect(result[0].nome).toBe("Player 0");
  });
});

describe("Formação Counting", () => {
  it("counts formations correctly", () => {
    const rows = [
      { formacao: "4-3-3" },
      { formacao: "4-4-2" },
      { formacao: "4-3-3" },
      { formacao: "3-5-2" },
      { formacao: "4-3-3" },
    ];
    const result = countFormacoes(rows);
    expect(result["4-3-3"]).toBe(3);
    expect(result["4-4-2"]).toBe(1);
    expect(result["3-5-2"]).toBe(1);
  });
});

describe("Time Ideal Formation Mapping", () => {
  it("4-3-3 has correct position counts", () => {
    const f = FORMACAO_MAP["4-3-3"];
    expect(f["1"]).toBe(1); // GOL
    expect(f["2"]).toBe(2); // LAT
    expect(f["3"]).toBe(2); // ZAG
    expect(f["4"]).toBe(3); // MEI
    expect(f["5"]).toBe(3); // ATA
    expect(f["6"]).toBe(1); // TEC
    // Total: 1+2+2+3+3+1 = 12
    expect(Object.values(f).reduce((a, b) => a + b, 0)).toBe(12);
  });

  it("3-5-2 has correct position counts", () => {
    const f = FORMACAO_MAP["3-5-2"];
    expect(f["1"]).toBe(1); // GOL
    expect(f["2"]).toBe(0); // LAT (none in 3-5-2)
    expect(f["3"]).toBe(3); // ZAG
    expect(f["4"]).toBe(5); // MEI
    expect(f["5"]).toBe(2); // ATA
    expect(f["6"]).toBe(1); // TEC
    expect(Object.values(f).reduce((a, b) => a + b, 0)).toBe(12);
  });

  it("all formations sum to 12 players", () => {
    for (const [name, f] of Object.entries(FORMACAO_MAP)) {
      const total = Object.values(f).reduce((a, b) => a + b, 0);
      expect(total, `Formation ${name} should have 12 players`).toBe(12);
    }
  });
});

describe("Análise Evolutiva Reference Data", () => {
  it("2025 reference data has correct structure", () => {
    for (const [rodada, data] of Object.entries(REF_2025_FIXO)) {
      expect(data.pts).toBeGreaterThan(0);
      expect(data.orc).toBeGreaterThan(0);
      expect(Number(rodada)).toBeGreaterThanOrEqual(1);
    }
  });

  it("cumulative comparison works correctly", () => {
    const processadas = [
      { rodada: 1, pontos_reais: 40 },
      { rodada: 2, pontos_reais: 90 },
    ];
    let acum2026 = 0;
    let acum2025 = 0;
    const result = processadas.map((e) => {
      acum2026 += e.pontos_reais;
      const ref = REF_2025_FIXO[e.rodada];
      acum2025 += ref?.pts || 0;
      return { rodada: e.rodada, pts2026: acum2026, pts2025: acum2025 };
    });

    expect(result[0].pts2026).toBe(40);
    expect(result[0].pts2025).toBe(30.6);
    expect(result[1].pts2026).toBe(130);
    expect(result[1].pts2025).toBeCloseTo(117.6, 1);
  });
});
