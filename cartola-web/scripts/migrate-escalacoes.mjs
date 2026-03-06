/**
 * Migration script: Import escalação JSON files from the GitHub repository
 * into the Neon PostgreSQL escalacoes_salvas table.
 * 
 * This reads all escalacao-*.json files from /tmp/cartola-fc-automacao/escalacoes/
 * and inserts them into the escalacoes_salvas table.
 */
import pg from 'pg';
import fs from 'fs';
import path from 'path';

const { Pool } = pg;

const pool = new Pool({
  connectionString: process.env.NEON_DATABASE_URL,
  ssl: { rejectUnauthorized: false },
});

async function migrate() {
  console.log('Starting escalação migration...');
  
  // Ensure table exists with the right structure
  await pool.query(`
    CREATE TABLE IF NOT EXISTS escalacoes_salvas (
      id SERIAL PRIMARY KEY,
      rodada INTEGER NOT NULL,
      ano INTEGER NOT NULL,
      formacao VARCHAR(10) DEFAULT '4-3-3',
      escalacao_json JSONB NOT NULL,
      pontos_reais DECIMAL(10,2),
      valorizacao_real DECIMAL(10,2),
      atualizado BOOLEAN DEFAULT FALSE,
      data_criacao TIMESTAMP DEFAULT NOW()
    )
  `);
  
  // Clear existing data to avoid duplicates
  const existing = await pool.query('SELECT COUNT(*) as cnt FROM escalacoes_salvas');
  console.log(`Existing records: ${existing.rows[0].cnt}`);
  
  if (parseInt(existing.rows[0].cnt) > 0) {
    console.log('Clearing existing escalacoes_salvas...');
    await pool.query('DELETE FROM escalacoes_salvas');
  }
  
  const baseDir = '/tmp/cartola-fc-automacao/escalacoes';
  const years = fs.readdirSync(baseDir).filter(d => 
    fs.statSync(path.join(baseDir, d)).isDirectory()
  );
  
  let imported = 0;
  
  for (const year of years.sort()) {
    const yearDir = path.join(baseDir, year);
    const files = fs.readdirSync(yearDir)
      .filter(f => f.startsWith('escalacao-') && f.endsWith('.json'))
      .sort((a, b) => {
        const numA = parseInt(a.replace('escalacao-', '').replace('.json', ''));
        const numB = parseInt(b.replace('escalacao-', '').replace('.json', ''));
        return numA - numB;
      });
    
    for (const file of files) {
      const filePath = path.join(yearDir, file);
      const raw = fs.readFileSync(filePath, 'utf-8');
      const data = JSON.parse(raw);
      
      const rodada = data.rodada || parseInt(file.replace('escalacao-', '').replace('.json', ''));
      const ano = data.ano || parseInt(year);
      const formacao = data.formacao || '4-3-3';
      const processado = data.processado || false;
      const pontosReais = processado ? (data.pontuacao_real || null) : null;
      const dataEscalacao = data.data_escalacao || null;
      
      // Store the entire JSON as escalacao_json
      await pool.query(
        `INSERT INTO escalacoes_salvas (rodada, ano, formacao, escalacao_json, pontos_reais, atualizado, data_criacao)
         VALUES ($1, $2, $3, $4, $5, $6, $7)`,
        [
          rodada,
          ano,
          formacao,
          JSON.stringify(data),
          pontosReais,
          processado,
          dataEscalacao ? new Date(dataEscalacao) : new Date(),
        ]
      );
      
      imported++;
      console.log(`  Imported: ${year}/escalacao-${rodada}.json (processado=${processado}, pts=${pontosReais || 'N/A'})`);
    }
  }
  
  console.log(`\nMigration complete! ${imported} escalações imported.`);
  
  // Verify
  const verify = await pool.query('SELECT ano, COUNT(*) as cnt, SUM(CASE WHEN atualizado THEN 1 ELSE 0 END) as processadas FROM escalacoes_salvas GROUP BY ano ORDER BY ano');
  console.log('\nVerification:');
  for (const row of verify.rows) {
    console.log(`  ${row.ano}: ${row.cnt} escalações (${row.processadas} processadas)`);
  }
  
  await pool.end();
}

migrate().catch(e => {
  console.error('Migration failed:', e);
  process.exit(1);
});
