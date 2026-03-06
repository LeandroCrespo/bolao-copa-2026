import { EstrategiaV7 } from '../server/estrategia.ts';

async function main() {
  const resp = await fetch('https://api.cartola.globo.com/atletas/mercado');
  const data = await resp.json();
  const jogadores = data.atletas || [];
  
  const e = new EstrategiaV7();
  const esc = await e.escalarTime(jogadores, '4-3-3', 108.93, true, false, 5, 2026);
  
  console.log('=== ESCALACAO RESULT ===');
  console.log('pontuacao_esperada:', esc.pontuacao_esperada);
  console.log('pontuacao_prevista:', esc.pontuacao_prevista);
  console.log('custo_total:', esc.custo_total);
  
  console.log('\nTitulares (checking all score fields):');
  for (const j of esc.titulares) {
    console.log(`  ${j.apelido.padEnd(20)} score: ${j.score?.toFixed(2)} pontuacao_esperada: ${j.pontuacao_esperada?.toFixed(2)} score_previsto: ${(j).score_previsto}`);
  }
  
  // Also check the raw df after prepararFeaturesV9
  const df = await e.prepararFeaturesV9(jogadores, false);
  const bidu = df.find(j => j.apelido === 'Matheus Bidu');
  if (bidu) {
    console.log('\n=== Matheus Bidu raw fields ===');
    console.log('score_geral_v9:', bidu.score_geral_v9);
    console.log('pred:', bidu.pred);
    console.log('score:', bidu.score);
    console.log('score_original:', bidu.score_original);
    console.log('media:', bidu.media);
    console.log('preco:', bidu.preco);
    console.log('posicao_id:', bidu.posicao_id);
    console.log('status_id:', bidu.status_id);
  }
  
  process.exit(0);
}

main().catch(console.error);
