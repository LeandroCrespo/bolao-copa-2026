/**
 * Otimizador Global de Escalação - Cartola FC
 * 
 * Usa Programação Linear Inteira (ILP) para encontrar a combinação ótima
 * de jogadores que maximiza a pontuação prevista dentro do orçamento.
 * 
 * Portado do Python (otimizador_escalacao.py) para TypeScript.
 * Usa javascript-lp-solver como substituto do PuLP.
 */

// @ts-ignore - javascript-lp-solver doesn't have types
import solver from 'javascript-lp-solver';

interface JogadorOtimizacao {
  atleta_id: string;
  posicao_id: number;
  score: number;
  preco: number;
  [key: string]: any;
}

/**
 * Encontra a combinação ótima de jogadores usando Programação Linear Inteira.
 * 
 * O objetivo é MAXIMIZAR A PONTUAÇÃO PREVISTA usando o MÁXIMO DO ORÇAMENTO.
 * 
 * @param df - Array de jogadores com scores calculados pelo modelo preditivo
 * @param configFormacao - {pos_id: quantidade} ex: {1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 1}
 * @param orcamento - Orçamento total disponível
 * @param topNPorPosicao - Quantos candidatos considerar por posição (padrão: 50)
 * @returns Lista de atleta_ids selecionados, ou array vazio se falhar
 */
export function otimizarEscalacaoILP(
  df: JogadorOtimizacao[],
  configFormacao: Record<number, number>,
  orcamento: number,
  topNPorPosicao: number = 50
): string[] {
  try {
    return _otimizarComSolver(df, configFormacao, orcamento, topNPorPosicao);
  } catch (err) {
    console.warn('[ILP] Solver failed, falling back to heuristic:', err);
    return _otimizarHeuristica(df, configFormacao, orcamento, topNPorPosicao);
  }
}

function _otimizarComSolver(
  df: JogadorOtimizacao[],
  configFormacao: Record<number, number>,
  orcamento: number,
  topNPorPosicao: number
): string[] {
  // ========== SELEÇÃO DE CANDIDATOS ==========
  // Estratégia: incluir top N por score E top N/2 por preço
  const candidatosSet = new Map<string, JogadorOtimizacao>();

  for (const [posIdStr, qtd] of Object.entries(configFormacao)) {
    const posId = Number(posIdStr);
    if (qtd <= 0) continue;

    const posDf = df.filter(j => j.posicao_id === posId);

    // Top N por score (modelo preditivo)
    const topScore = [...posDf].sort((a, b) => (b.score || 0) - (a.score || 0)).slice(0, topNPorPosicao);
    for (const j of topScore) candidatosSet.set(String(j.atleta_id), j);

    // Top N/2 por preço (correlação com pontuação)
    const topPreco = [...posDf].sort((a, b) => b.preco - a.preco).slice(0, Math.floor(topNPorPosicao / 2));
    for (const j of topPreco) candidatosSet.set(String(j.atleta_id), j);
  }

  const candidatos = Array.from(candidatosSet.values());
  console.log(`[ILP] Total de candidatos: ${candidatos.length} jogadores`);
  console.log(`[ILP] Orçamento disponível: C$ ${orcamento.toFixed(2)}`);

  if (candidatos.length === 0) return [];

  // ========== CRIAR MODELO PARA javascript-lp-solver ==========
  // O solver usa um formato JSON específico
  const model: any = {
    optimize: 'score',
    opType: 'max',
    constraints: {
      orcamento: { max: orcamento },
    },
    variables: {} as Record<string, any>,
    binaries: {} as Record<string, number>,
  };

  // Adicionar restrições por posição (exatamente qtd jogadores)
  for (const [posIdStr, qtd] of Object.entries(configFormacao)) {
    const posId = Number(posIdStr);
    if (qtd <= 0) continue;
    model.constraints[`pos_${posId}`] = { equal: qtd };
  }

  // Adicionar variáveis (uma por jogador candidato)
  for (let i = 0; i < candidatos.length; i++) {
    const j = candidatos[i];
    const varName = `x_${i}`;
    const variable: any = {
      score: j.score || 0,
      orcamento: j.preco,
    };

    // Adicionar contribuição para a restrição de posição
    variable[`pos_${j.posicao_id}`] = 1;

    model.variables[varName] = variable;
    model.binaries[varName] = 1; // Variável binária (0 ou 1)
  }

  // ========== RESOLVER ==========
  const result: any = solver.Solve(model);

  if (!result.feasible) {
    console.log('[ILP] Não encontrou solução viável, usando heurística...');
    return _otimizarHeuristica(df, configFormacao, orcamento, topNPorPosicao);
  }

  // ========== EXTRAIR SOLUÇÃO ==========
  const selecionados: string[] = [];
  let custoTotal = 0;
  let scoreTotal = 0;

  for (let i = 0; i < candidatos.length; i++) {
    const varName = `x_${i}`;
    if (result[varName] && result[varName] >= 0.5) {
      selecionados.push(String(candidatos[i].atleta_id));
      custoTotal += candidatos[i].preco;
      scoreTotal += candidatos[i].score || 0;
    }
  }

  console.log(`[ILP] Solução encontrada: ${selecionados.length} jogadores`);
  console.log(`[ILP] Custo total: C$ ${custoTotal.toFixed(2)}`);
  console.log(`[ILP] Score total: ${scoreTotal.toFixed(2)}`);
  console.log(`[ILP] Orçamento restante: C$ ${(orcamento - custoTotal).toFixed(2)}`);

  // Verificar se a solução tem o número correto de jogadores
  const totalEsperado = Object.values(configFormacao).reduce((a, b) => a + b, 0);
  if (selecionados.length !== totalEsperado) {
    console.log(`[ILP] Solução incompleta (${selecionados.length}/${totalEsperado}), usando heurística...`);
    return _otimizarHeuristica(df, configFormacao, orcamento, topNPorPosicao);
  }

  return selecionados;
}

function _otimizarHeuristica(
  df: JogadorOtimizacao[],
  configFormacao: Record<number, number>,
  orcamento: number,
  topNPorPosicao: number
): string[] {
  let melhorSolucao: string[] = [];
  let melhorScore = 0;

  // Tentar múltiplas estratégias de início
  for (const estrategia of ['score', 'custo_beneficio', 'misto', 'preco_alto']) {
    const { solucao, scoreTotal } = _gerarSolucaoInicial(df, configFormacao, orcamento, estrategia);

    if (scoreTotal > melhorScore) {
      melhorScore = scoreTotal;
      melhorSolucao = solucao;
    }

    // Melhorar com busca local
    const { solucao: solMelhorada, scoreTotal: scoreMelhorado } = _buscaLocal(df, configFormacao, orcamento, solucao);

    if (scoreMelhorado > melhorScore) {
      melhorScore = scoreMelhorado;
      melhorSolucao = solMelhorada;
    }
  }

  return melhorSolucao;
}

function _gerarSolucaoInicial(
  df: JogadorOtimizacao[],
  configFormacao: Record<number, number>,
  orcamento: number,
  estrategia: string
): { solucao: string[]; scoreTotal: number } {
  const solucao: string[] = [];
  let custoTotal = 0;
  const idsUsados = new Set<string>();

  // Ordenar posições por quantidade (menos jogadores primeiro)
  const posicoesOrdenadas = Object.entries(configFormacao)
    .map(([k, v]) => ({ posId: Number(k), qtd: v }))
    .sort((a, b) => a.qtd - b.qtd);

  for (const { posId, qtd } of posicoesOrdenadas) {
    if (qtd === 0) continue;

    let disponiveis = df.filter(j => j.posicao_id === posId && !idsUsados.has(String(j.atleta_id)));

    // Ordenar conforme estratégia
    if (estrategia === 'score') {
      disponiveis.sort((a, b) => (b.score || 0) - (a.score || 0));
    } else if (estrategia === 'custo_beneficio') {
      disponiveis.sort((a, b) => {
        const cbA = (a.score || 0) / Math.max(a.preco, 0.1);
        const cbB = (b.score || 0) / Math.max(b.preco, 0.1);
        return cbB - cbA;
      });
    } else if (estrategia === 'preco_alto') {
      disponiveis.sort((a, b) => b.preco - a.preco || (b.score || 0) - (a.score || 0));
    } else {
      // misto
      disponiveis.sort((a, b) => {
        const mistoA = (a.score || 0) * 0.7 + ((a.score || 0) / Math.max(a.preco, 0.1)) * 0.3;
        const mistoB = (b.score || 0) * 0.7 + ((b.score || 0) / Math.max(b.preco, 0.1)) * 0.3;
        return mistoB - mistoA;
      });
    }

    let selecionados = 0;
    for (const row of disponiveis) {
      if (selecionados >= qtd) break;

      // Calcular custo mínimo restante
      let custoMinimoRestante = 0;
      for (const { posId: p, qtd: q } of posicoesOrdenadas) {
        let qtdNecessaria = 0;
        if (p === posId) {
          qtdNecessaria = qtd - selecionados - 1;
        } else if (!solucao.some(id => {
          const j = df.find(j2 => String(j2.atleta_id) === id);
          return j && j.posicao_id === p;
        })) {
          const jaSelecionados = solucao.filter(id => {
            const j = df.find(j2 => String(j2.atleta_id) === id);
            return j && j.posicao_id === p;
          }).length;
          qtdNecessaria = q - jaSelecionados;
        }

        if (qtdNecessaria > 0) {
          const disp = df
            .filter(j => j.posicao_id === p && !idsUsados.has(String(j.atleta_id)) && String(j.atleta_id) !== String(row.atleta_id))
            .sort((a, b) => a.preco - b.preco)
            .slice(0, qtdNecessaria);
          custoMinimoRestante += disp.reduce((sum, j) => sum + j.preco, 0);
        }
      }

      if (custoTotal + row.preco + custoMinimoRestante <= orcamento) {
        solucao.push(String(row.atleta_id));
        custoTotal += row.preco;
        idsUsados.add(String(row.atleta_id));
        selecionados++;
      }
    }
  }

  const scoreTotal = solucao.reduce((sum, id) => {
    const j = df.find(j2 => String(j2.atleta_id) === id);
    return sum + (j?.score || 0);
  }, 0);

  return { solucao, scoreTotal };
}

function _buscaLocal(
  df: JogadorOtimizacao[],
  configFormacao: Record<number, number>,
  orcamento: number,
  solucaoInicial: string[]
): { solucao: string[]; scoreTotal: number } {
  if (solucaoInicial.length === 0) return { solucao: [], scoreTotal: 0 };

  const solucao = [...solucaoInicial];
  let scoreAtual = solucao.reduce((sum, id) => {
    const j = df.find(j2 => String(j2.atleta_id) === id);
    return sum + (j?.score || 0);
  }, 0);
  let custoAtual = solucao.reduce((sum, id) => {
    const j = df.find(j2 => String(j2.atleta_id) === id);
    return sum + (j?.preco || 0);
  }, 0);

  let melhorou = true;
  let iteracao = 0;

  while (melhorou && iteracao < 100) {
    melhorou = false;
    iteracao++;

    for (let i = 0; i < solucao.length; i++) {
      const atletaId = solucao[i];
      const jogador = df.find(j => String(j.atleta_id) === atletaId);
      if (!jogador) continue;

      // Tentar trocar por outro da mesma posição com score maior
      const candidatos = df
        .filter(j =>
          j.posicao_id === jogador.posicao_id &&
          !solucao.includes(String(j.atleta_id)) &&
          (j.score || 0) > (jogador.score || 0) &&
          custoAtual - jogador.preco + j.preco <= orcamento
        )
        .sort((a, b) => (b.score || 0) - (a.score || 0));

      if (candidatos.length > 0) {
        const melhor = candidatos[0];
        const ganho = (melhor.score || 0) - (jogador.score || 0);

        if (ganho > 0.01) {
          solucao[i] = String(melhor.atleta_id);
          scoreAtual += ganho;
          custoAtual = custoAtual - jogador.preco + melhor.preco;
          melhorou = true;
          break;
        }
      }
    }
  }

  return { solucao, scoreTotal: scoreAtual };
}
