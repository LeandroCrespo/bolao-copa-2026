/**
 * Client for the Python FastAPI microservice that wraps the actual
 * estrategia_v7.py and app.py code from the Streamlit app.
 * This ensures identical results to the Python/Streamlit version.
 */

const PYTHON_SERVICE_URL = process.env.PYTHON_SERVICE_URL || 'http://localhost:8100';

interface SimulacaoParams {
  ano: number;
  orcamento: number;
  formacao: string;
  orcamento_dinamico: boolean;
}

interface SimulacaoRodada {
  Rodada: number;
  'Pts Escalado': number;
  'Pts Previsto': number;
  'Pts Ideal': number;
  Aproveitamento: string;
  Acertos: string;
  'Capitão Escalado': string;
  'Capitão Ideal': string;
  'Cap OK': string;
  Custo: string;
  Formação: string;
  Orçamento?: string;
}

interface SimulacaoResult {
  rodadas: SimulacaoRodada[];
  detalhes: Record<string, any> | null;
  resumo: {
    total_pontos: number;
    media_rodada: number;
    total_ideal: number;
    aproveitamento: number;
    num_rodadas: number;
  };
}

interface EscalacaoParams {
  formacao: string;
  orcamento: number;
  ano?: number;
  rodada?: number;
  excluir_ids?: string[];
}

async function callPythonService<T>(endpoint: string, body: any, timeoutMs = 600000): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  
  try {
    const response = await fetch(`${PYTHON_SERVICE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Python service error (${response.status}): ${errorText}`);
    }
    
    return await response.json() as T;
  } finally {
    clearTimeout(timer);
  }
}

export async function checkPythonServiceHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${PYTHON_SERVICE_URL}/health`, {
      signal: AbortSignal.timeout(5000),
    });
    return response.ok;
  } catch {
    return false;
  }
}

export async function simularViaPython(params: SimulacaoParams): Promise<SimulacaoResult> {
  return callPythonService<SimulacaoResult>('/simular', params, 900000); // 15 min timeout
}

export async function escalarViaPython(params: EscalacaoParams): Promise<any> {
  return callPythonService<any>('/escalar', params, 120000); // 2 min timeout
}

export async function getHistoricoJogadorViaPython(atletaId: string, anos?: number[]): Promise<any> {
  return callPythonService<any>('/historico-jogador', { atleta_id: atletaId, anos }, 30000);
}

export async function getMercadoRanqueado(): Promise<any> {
  try {
    const response = await fetch(`${PYTHON_SERVICE_URL}/mercado-ranqueado`, {
      signal: AbortSignal.timeout(120000),
    });
    if (!response.ok) {
      throw new Error(`Python service error (${response.status})`);
    }
    return await response.json();
  } catch {
    return null;
  }
}
