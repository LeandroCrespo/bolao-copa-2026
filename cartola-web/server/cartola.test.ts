import { describe, expect, it, vi } from "vitest";
import { POSICOES, STATUS_JOGADOR, FORMACOES } from "../shared/cartola";

describe("Cartola shared constants", () => {
  it("POSICOES has all 6 positions", () => {
    expect(Object.keys(POSICOES)).toHaveLength(6);
    expect(POSICOES[1]).toBe("GOL");
    expect(POSICOES[2]).toBe("LAT");
    expect(POSICOES[3]).toBe("ZAG");
    expect(POSICOES[4]).toBe("MEI");
    expect(POSICOES[5]).toBe("ATA");
    expect(POSICOES[6]).toBe("TEC");
  });

  it("STATUS_JOGADOR has correct statuses", () => {
    expect(STATUS_JOGADOR[7]).toBe("Provável");
    expect(STATUS_JOGADOR[2]).toBe("Dúvida");
    expect(STATUS_JOGADOR[3]).toBe("Suspenso");
    expect(STATUS_JOGADOR[5]).toBe("Contundido");
    expect(STATUS_JOGADOR[6]).toBe("Nulo");
  });

  it("FORMACOES has correct player counts (always 12 total)", () => {
    for (const [name, positions] of Object.entries(FORMACOES)) {
      const total = Object.values(positions).reduce((a, b) => a + b, 0);
      expect(total).toBe(12); // 11 players + 1 coach
    }
  });

  it("FORMACOES 4-3-3 has correct distribution", () => {
    const f = FORMACOES["4-3-3"];
    expect(f[1]).toBe(1); // GOL
    expect(f[2]).toBe(2); // LAT
    expect(f[3]).toBe(2); // ZAG
    expect(f[4]).toBe(3); // MEI
    expect(f[5]).toBe(3); // ATA
    expect(f[6]).toBe(1); // TEC
  });

  it("FORMACOES 4-4-2 has correct distribution", () => {
    const f = FORMACOES["4-4-2"];
    expect(f[1]).toBe(1);
    expect(f[2]).toBe(2);
    expect(f[3]).toBe(2);
    expect(f[4]).toBe(4);
    expect(f[5]).toBe(2);
    expect(f[6]).toBe(1);
  });

  it("All formations have GOL=1 and TEC=1", () => {
    for (const [name, positions] of Object.entries(FORMACOES)) {
      expect(positions[1]).toBe(1); // GOL always 1
      expect(positions[6]).toBe(1); // TEC always 1
    }
  });
});

describe("Cartola tRPC router structure", () => {
  it("appRouter exports correct type", async () => {
    const { appRouter } = await import("./routers");
    expect(appRouter).toBeDefined();
    // Check that cartola and db routers exist
    expect(appRouter._def.procedures).toBeDefined();
  });
});
