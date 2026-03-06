import pg from "pg";
import { ENV } from "./_core/env";

const { Pool } = pg;

let _pool: pg.Pool | null = null;

export function getNeonPool(): pg.Pool {
  if (!_pool) {
    if (!ENV.neonDatabaseUrl) {
      throw new Error("NEON_DATABASE_URL is not configured");
    }
    _pool = new Pool({
      connectionString: ENV.neonDatabaseUrl,
      ssl: { rejectUnauthorized: false },
      max: 10,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 10000,
    });
  }
  return _pool;
}

export async function neonQuery<T = Record<string, unknown>>(
  sql: string,
  params?: unknown[]
): Promise<T[]> {
  const pool = getNeonPool();
  const result = await pool.query(sql, params);
  return result.rows as T[];
}

export async function neonQueryOne<T = Record<string, unknown>>(
  sql: string,
  params?: unknown[]
): Promise<T | null> {
  const rows = await neonQuery<T>(sql, params);
  return rows.length > 0 ? rows[0] : null;
}
