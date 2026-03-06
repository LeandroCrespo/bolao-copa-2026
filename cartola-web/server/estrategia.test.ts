import { describe, expect, it } from "vitest";
import { FORMACOES, POSICAO_MAP, EstrategiaV7 } from "./estrategia";

describe("FORMACOES", () => {
  it("todas as formações somam 12 jogadores (11 + técnico)", () => {
    for (const [nome, config] of Object.entries(FORMACOES)) {
      const total = Object.values(config).reduce((a, b) => a + b, 0);
      expect(total).toBe(12);
    }
  });

  it("todas as formações têm 1 goleiro e 1 técnico", () => {
    for (const [nome, config] of Object.entries(FORMACOES)) {
      expect(config[1]).toBe(1);
      expect(config[6]).toBe(1);
    }
  });

  it("contém as formações padrão", () => {
    expect(FORMACOES["4-3-3"]).toBeDefined();
    expect(FORMACOES["4-4-2"]).toBeDefined();
    expect(FORMACOES["3-5-2"]).toBeDefined();
    expect(FORMACOES["3-4-3"]).toBeDefined();
    expect(FORMACOES["4-5-1"]).toBeDefined();
    expect(FORMACOES["5-3-2"]).toBeDefined();
    expect(FORMACOES["5-4-1"]).toBeDefined();
  });

  it("4-3-3 tem distribuição correta", () => {
    const f = FORMACOES["4-3-3"];
    expect(f[1]).toBe(1); // GOL
    expect(f[2]).toBe(2); // LAT
    expect(f[3]).toBe(2); // ZAG
    expect(f[4]).toBe(3); // MEI
    expect(f[5]).toBe(3); // ATA
    expect(f[6]).toBe(1); // TEC
  });

  it("4-4-2 tem distribuição correta", () => {
    const f = FORMACOES["4-4-2"];
    expect(f[1]).toBe(1);
    expect(f[2]).toBe(2);
    expect(f[3]).toBe(2);
    expect(f[4]).toBe(4);
    expect(f[5]).toBe(2);
    expect(f[6]).toBe(1);
  });

  it("3-5-2 tem distribuição correta", () => {
    const f = FORMACOES["3-5-2"];
    expect(f[1]).toBe(1);
    expect(f[2]).toBe(0);
    expect(f[3]).toBe(3);
    expect(f[4]).toBe(5);
    expect(f[5]).toBe(2);
    expect(f[6]).toBe(1);
  });

  it("nenhuma formação tem posições negativas", () => {
    for (const [nome, config] of Object.entries(FORMACOES)) {
      for (const [pos, count] of Object.entries(config)) {
        expect(count).toBeGreaterThanOrEqual(0);
      }
    }
  });
});

describe("POSICAO_MAP", () => {
  it("mapeia todas as 6 posições", () => {
    expect(POSICAO_MAP[1]).toBe("GOL");
    expect(POSICAO_MAP[2]).toBe("LAT");
    expect(POSICAO_MAP[3]).toBe("ZAG");
    expect(POSICAO_MAP[4]).toBe("MEI");
    expect(POSICAO_MAP[5]).toBe("ATA");
    expect(POSICAO_MAP[6]).toBe("TEC");
  });

  it("tem exatamente 6 posições", () => {
    expect(Object.keys(POSICAO_MAP)).toHaveLength(6);
  });
});

describe("EstrategiaV7 - instanciação", () => {
  it("pode ser instanciada", () => {
    const engine = new EstrategiaV7(100, false);
    expect(engine).toBeDefined();
  });

  it("pode ser instanciada em modo simulação", () => {
    const engine = new EstrategiaV7(120, true);
    expect(engine).toBeDefined();
  });
});

describe("EstrategiaV7 - prepararFeaturesV9 com banco Neon", () => {
  it("retorna array com scores usando dados reais do banco", async () => {
    const engine = new EstrategiaV7(100, false);

    const jogadores = [
      {
        atleta_id: "37637",
        apelido: "Raphael Veiga",
        posicao_id: 4,
        clube_id: 275,
        clube_nome: "PAL",
        preco: 15,
        media: 7,
        pontos_num: 8,
        variacao_num: 0.5,
        status_id: 7,
        entrou_em_campo: true,
      },
      {
        atleta_id: "38286",
        apelido: "Gustavo Gómez",
        posicao_id: 3,
        clube_id: 275,
        clube_nome: "PAL",
        preco: 12,
        media: 4,
        pontos_num: 6,
        variacao_num: 0.3,
        status_id: 7,
        entrou_em_campo: true,
      },
    ];

    const resultado = await engine.prepararFeaturesV9(jogadores, false);
    expect(resultado.length).toBe(2);
    for (const j of resultado) {
      expect(j.score_geral_v9).toBeDefined();
      expect(typeof j.score_geral_v9).toBe("number");
      expect(j.score_geral_v9).toBeGreaterThanOrEqual(0);
    }
  }, 30000);
});

describe("EstrategiaV7 - escalarTime com dados mock", () => {
  it("retorna escalação válida com jogadores suficientes", async () => {
    const engine = new EstrategiaV7(500, true);

    const jogadores: any[] = [];
    const posicoes = [
      { id: 1, count: 3, prefix: "GOL" },
      { id: 2, count: 6, prefix: "LAT" },
      { id: 3, count: 6, prefix: "ZAG" },
      { id: 4, count: 10, prefix: "MEI" },
      { id: 5, count: 10, prefix: "ATA" },
      { id: 6, count: 4, prefix: "TEC" },
    ];

    let id = 1;
    for (const pos of posicoes) {
      for (let i = 0; i < pos.count; i++) {
        jogadores.push({
          atleta_id: String(id++),
          apelido: `${pos.prefix}-${i}`,
          posicao_id: pos.id,
          clube_id: 260 + i,
          clube_nome: `CLB${i}`,
          preco: 5 + Math.random() * 15,
          media: 3 + Math.random() * 7,
          pontos_num: 2 + Math.random() * 15,
          variacao_num: Math.random() * 2 - 1,
          status_id: 7,
          entrou_em_campo: true,
        });
      }
    }

    const escalacao = await engine.escalarTime(jogadores, "4-3-3", 500, true, true);

    expect(escalacao).toBeDefined();
    expect(escalacao.formacao).toBe("4-3-3");
    expect(escalacao.titulares.length).toBe(12);
    expect(escalacao.custo_total).toBeLessThanOrEqual(500);
    expect(escalacao.pontuacao_esperada).toBeGreaterThanOrEqual(0);
    expect(escalacao.capitao).toBeDefined();
    expect(escalacao.vice_capitao).toBeDefined();

    // Verify position distribution
    const posCount: Record<number, number> = {};
    for (const t of escalacao.titulares) {
      posCount[t.pos_id] = (posCount[t.pos_id] || 0) + 1;
    }
    expect(posCount[1]).toBe(1); // GOL
    expect(posCount[4]).toBe(3); // MEI
    expect(posCount[5]).toBe(3); // ATA
    expect(posCount[6]).toBe(1); // TEC
  }, 30000);

  it("respeita o orçamento máximo", async () => {
    const engine = new EstrategiaV7(80, true);

    const jogadores: any[] = [];
    let id = 1;
    const posicoes = [1, 2, 3, 4, 5, 6];
    for (const posId of posicoes) {
      for (let i = 0; i < 8; i++) {
        jogadores.push({
          atleta_id: String(id++),
          apelido: `P${posId}-${i}`,
          posicao_id: posId,
          clube_id: 260 + i,
          clube_nome: `C${i}`,
          preco: 3 + Math.random() * 8,
          media: 2 + Math.random() * 5,
          pontos_num: 1 + Math.random() * 8,
          variacao_num: 0,
          status_id: 7,
          entrou_em_campo: true,
        });
      }
    }

    const escalacao = await engine.escalarTime(jogadores, "4-3-3", 80, true, true);
    expect(escalacao.custo_total).toBeLessThanOrEqual(80);
  }, 30000);
});

describe("EstrategiaV7 - analisarTodasFormacoes", () => {
  it("retorna múltiplas formações ordenadas por pontuação", async () => {
    const engine = new EstrategiaV7(500, true);

    const jogadores: any[] = [];
    let id = 1;
    const posicoes = [
      { id: 1, count: 3 },
      { id: 2, count: 6 },
      { id: 3, count: 6 },
      { id: 4, count: 10 },
      { id: 5, count: 10 },
      { id: 6, count: 4 },
    ];

    for (const pos of posicoes) {
      for (let i = 0; i < pos.count; i++) {
        jogadores.push({
          atleta_id: String(id++),
          apelido: `J-${id}`,
          posicao_id: pos.id,
          clube_id: 260 + i,
          clube_nome: `CLB`,
          preco: 5 + Math.random() * 10,
          media: 3 + Math.random() * 5,
          pontos_num: 2 + Math.random() * 10,
          variacao_num: 0,
          status_id: 7,
          entrou_em_campo: true,
        });
      }
    }

    const resultados = await engine.analisarTodasFormacoes(jogadores, 500, true);

    expect(resultados.length).toBeGreaterThan(0);
    for (const r of resultados) {
      expect(r.formacao).toBeDefined();
      expect(r.pontuacao_esperada).toBeDefined();
      expect(r.custo_total).toBeDefined();
    }

    // Should be sorted by pontuacao_esperada descending
    for (let i = 1; i < resultados.length; i++) {
      expect(resultados[i - 1].pontuacao_esperada).toBeGreaterThanOrEqual(resultados[i].pontuacao_esperada);
    }
  }, 60000);
});
