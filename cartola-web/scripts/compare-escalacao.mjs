import { EstrategiaV7 } from '../server/estrategia.ts';

async function main() {
  const resp = await fetch('https://api.cartola.globo.com/atletas/mercado');
  const data = await resp.json();
  const jogadores = data.atletas || [];
  console.log('Jogadores do mercado:', jogadores.length);
  
  const e = new EstrategiaV7();
  const df = await e.prepararFeaturesV9(jogadores, false);
  
  // Check scores
  const withScore = df.filter(j => j.score_geral_v9 > 0);
  console.log('Jogadores com score_geral_v9 > 0:', withScore.length, 'de', df.length);
  
  const top10 = withScore.sort((a,b) => b.score_geral_v9 - a.score_geral_v9).slice(0, 10);
  console.log('\nTop 10 by score_geral_v9:');
  for (const j of top10) {
    console.log(`  ${j.apelido.padEnd(20)} score_v9: ${j.score_geral_v9?.toFixed(2).padStart(6)} media: ${(j.media||0).toFixed(2).padStart(6)} preco: ${(j.preco||0).toFixed(2).padStart(7)} pos: ${j.posicao_id} status: ${j.status_id}`);
  }
  
  // Now escalar
  const esc = await e.escalarTime(jogadores, '4-3-3', 108.93, true, false, 5, 2026);
  console.log('\n=== TYPESCRIPT ESCALACAO R5/2026 ===');
  console.log('Formacao:', esc.formacao);
  console.log('Custo:', esc.custo_total?.toFixed(2));
  console.log('\nTitulares:');
  for (const j of esc.titulares) {
    console.log(`  [${j.pos_id}] ${j.apelido.padEnd(20)} Score: ${(j.score_previsto || 0).toFixed(2).padStart(6)} Preco: ${(j.preco || 0).toFixed(2).padStart(7)}`);
  }
  console.log('\nCapitao:', esc.capitao?.apelido);
  process.exit(0);
}

main().catch(console.error);
