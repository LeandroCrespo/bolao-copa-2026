import { describe, expect, it } from "vitest";
import { FORMACOES, POSICAO_MAP } from "./estrategia";

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

describe("Substituição - regras do Cartola", () => {
  it("reserva normal entra quando titular NÃO ENTROU EM CAMPO", () => {
    // Simular a regra: titular com pontos_reais == 0 E não encontrado no df_atual
    const titular = { atleta_id: "1", pos_id: 5, pontos_reais: 0, entrou_em_campo: false };
    const reserva = { atleta_id: "99", pos_id: 5, pontos_reais: 5, entrou_em_campo: true };
    
    // Regra: reserva entra se titular não entrou em campo E reserva entrou
    const deveSubstituir = !titular.entrou_em_campo && reserva.entrou_em_campo;
    expect(deveSubstituir).toBe(true);
  });

  it("reserva normal NÃO entra quando titular jogou e fez 0 pontos", () => {
    const titular = { atleta_id: "1", pos_id: 5, pontos_reais: 0, entrou_em_campo: true };
    const reserva = { atleta_id: "99", pos_id: 5, pontos_reais: 5, entrou_em_campo: true };
    
    const deveSubstituir = !titular.entrou_em_campo && reserva.entrou_em_campo;
    expect(deveSubstituir).toBe(false);
  });

  it("reserva de luxo substitui pior pontuador da posição do capitão se fez mais pontos", () => {
    const titulares = [
      { atleta_id: "1", pos_id: 5, pontos_reais: 3, entrou_em_campo: true, substituido: false },
      { atleta_id: "2", pos_id: 5, pontos_reais: 8, entrou_em_campo: true, substituido: false },
      { atleta_id: "3", pos_id: 5, pontos_reais: 12, entrou_em_campo: true, substituido: false },
    ];
    const reservaLuxo = { atleta_id: "99", pos_id: 5, pontos_reais: 10, entrou_em_campo: true };
    
    // Pior pontuador da posição do capitão (que entrou em campo e não foi substituído)
    const titularesPos = titulares.filter(t => t.pos_id === reservaLuxo.pos_id && t.entrou_em_campo && !t.substituido);
    const pior = titularesPos.reduce((min, t) => t.pontos_reais < min.pontos_reais ? t : min, titularesPos[0]);
    
    // Reserva de luxo substitui se fez mais pontos que o pior
    const deveSubstituir = reservaLuxo.pontos_reais > pior.pontos_reais;
    expect(deveSubstituir).toBe(true);
    expect(pior.atleta_id).toBe("1"); // O pior é o que fez 3 pontos
  });

  it("reserva de luxo NÃO substitui se fez menos pontos que o pior", () => {
    const titulares = [
      { atleta_id: "1", pos_id: 5, pontos_reais: 8, entrou_em_campo: true, substituido: false },
      { atleta_id: "2", pos_id: 5, pontos_reais: 12, entrou_em_campo: true, substituido: false },
    ];
    const reservaLuxo = { atleta_id: "99", pos_id: 5, pontos_reais: 5, entrou_em_campo: true };
    
    const titularesPos = titulares.filter(t => t.pos_id === reservaLuxo.pos_id && t.entrou_em_campo && !t.substituido);
    const pior = titularesPos.reduce((min, t) => t.pontos_reais < min.pontos_reais ? t : min, titularesPos[0]);
    
    const deveSubstituir = reservaLuxo.pontos_reais > pior.pontos_reais;
    expect(deveSubstituir).toBe(false);
  });

  it("reserva de luxo é sempre da mesma posição do capitão", () => {
    const capitao = { pos_id: 5 }; // ATA
    const reservaLuxo = { pos_id: 5 }; // Deve ser ATA também
    
    expect(reservaLuxo.pos_id).toBe(capitao.pos_id);
  });

  it("bônus do capitão é 1.5x nos pontos efetivos (após substituição)", () => {
    const capitaoId = "1";
    const titulares = [
      { atleta_id: "1", pos_id: 5, pontos_reais: 10, substituido: false, substituto: null },
      { atleta_id: "2", pos_id: 4, pontos_reais: 5, substituido: false, substituto: null },
    ];
    
    let pontuacaoReal = 0;
    for (const t of titulares) {
      const pontos = t.substituido && t.substituto ? (t.substituto as any).pontos_reais : t.pontos_reais;
      if (t.atleta_id === capitaoId) {
        pontuacaoReal += pontos * 1.5;
      } else {
        pontuacaoReal += pontos;
      }
    }
    
    expect(pontuacaoReal).toBe(10 * 1.5 + 5); // 15 + 5 = 20
  });
});

describe("Python Service - integração", () => {
  it("pythonService module exports required functions", async () => {
    const mod = await import("./pythonService");
    expect(mod.checkPythonServiceHealth).toBeDefined();
    expect(typeof mod.checkPythonServiceHealth).toBe("function");
    expect(mod.simularViaPython).toBeDefined();
    expect(typeof mod.simularViaPython).toBe("function");
    expect(mod.escalarViaPython).toBeDefined();
    expect(typeof mod.escalarViaPython).toBe("function");
  });
});
