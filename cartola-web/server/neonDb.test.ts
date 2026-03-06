import { describe, expect, it, afterAll } from "vitest";
import { getNeonPool, neonQuery, neonQueryOne } from "./neonDb";

afterAll(async () => {
  const pool = getNeonPool();
  await pool.end();
});

describe("Neon Database Connection", () => {
  it("should connect to Neon and query tables", async () => {
    const result = await neonQuery<{ table_name: string }>(
      "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
    );
    expect(result.length).toBeGreaterThan(0);
    const tableNames = result.map((r) => r.table_name);
    expect(tableNames).toContain("jogadores_historico");
    expect(tableNames).toContain("competicoes_paralelas");
  });

  it("should query jogadores_historico count", async () => {
    const result = await neonQueryOne<{ count: string }>(
      "SELECT COUNT(*) as count FROM jogadores_historico"
    );
    expect(result).not.toBeNull();
    expect(Number(result!.count)).toBeGreaterThan(0);
  });

  it("should query rodadas_processadas", async () => {
    const result = await neonQuery<{ rodada: number; ano: number }>(
      "SELECT rodada, ano FROM rodadas_processadas ORDER BY ano DESC, rodada DESC LIMIT 1"
    );
    expect(result.length).toBe(1);
    expect(result[0].ano).toBeGreaterThanOrEqual(2024);
  });
});

describe("ML Predictions Table", () => {
  it("should have ml_predictions table with data", async () => {
    const result = await neonQueryOne<{ count: string }>(
      "SELECT COUNT(*) as count FROM ml_predictions"
    );
    expect(result).not.toBeNull();
    expect(Number(result!.count)).toBeGreaterThan(0);
  });

  it("should have correct columns in ml_predictions", async () => {
    const result = await neonQuery<{ column_name: string }>(
      "SELECT column_name FROM information_schema.columns WHERE table_name = 'ml_predictions' ORDER BY ordinal_position"
    );
    const columns = result.map((r) => r.column_name);
    expect(columns).toContain("atleta_id");
    expect(columns).toContain("pred");
    expect(columns).toContain("apelido");
    expect(columns).toContain("posicao_id");
  });

  it("should return ML predictions with valid pred values", async () => {
    const result = await neonQuery<{ atleta_id: string; pred: number; apelido: string }>(
      "SELECT atleta_id, pred, apelido FROM ml_predictions WHERE pred > 0 ORDER BY pred DESC LIMIT 10"
    );
    expect(result.length).toBeGreaterThan(0);
    for (const row of result) {
      expect(Number(row.pred)).toBeGreaterThan(0);
      expect(row.atleta_id).toBeTruthy();
      expect(row.apelido).toBeTruthy();
    }
  });

  it("should have ML predictions significantly different from heuristic scores", async () => {
    const result = await neonQuery<{ pred: number; score_geral_v9: number }>(
      "SELECT pred, score_geral_v9 FROM ml_predictions WHERE pred > 5 AND score_geral_v9 > 0 ORDER BY pred DESC LIMIT 5"
    );
    expect(result.length).toBeGreaterThan(0);
    for (const row of result) {
      expect(Number(row.pred)).toBeGreaterThan(Number(row.score_geral_v9));
    }
  });
});
