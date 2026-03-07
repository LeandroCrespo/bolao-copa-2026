"""
FastAPI microservice that wraps the actual Python Cartola strategy code.
This ensures identical results to the Streamlit app.
"""
import os
import sys
import json
import traceback
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import math


class SafeJSONResponse(JSONResponse):
    """JSONResponse that handles NaN, Inf, -Inf values."""
    def render(self, content) -> bytes:
        content = _deep_clean(content)
        return super().render(content)


def _deep_clean(obj):
    """Recursively clean NaN/Inf from any nested structure."""
    if obj is None:
        return None
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj
    if isinstance(obj, (np.floating,)):
        v = float(obj)
        if math.isnan(v) or math.isinf(v):
            return 0.0
        return v
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, np.ndarray):
        return [_deep_clean(x) for x in obj.tolist()]
    if isinstance(obj, dict):
        return {k: _deep_clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_deep_clean(x) for x in obj]
    if isinstance(obj, pd.Timestamp):
        return str(obj)
    if isinstance(obj, (pd.Series,)):
        return {k: _deep_clean(v) for k, v in obj.to_dict().items()}
    try:
        if pd.isna(obj):
            return None
    except (TypeError, ValueError):
        pass
    return obj

# Add the cartola-fc-automacao directory to the Python path
CARTOLA_DIR = '/home/ubuntu/cartola-fc-automacao'
sys.path.insert(0, CARTOLA_DIR)

# Set the working directory so relative paths work
os.chdir(CARTOLA_DIR)

# Set Neon connection string
os.environ['NEON_CONNECTION_STRING'] = os.environ.get('NEON_DATABASE_URL', '')

# Import the actual Python modules
from estrategia_v7 import EstrategiaV7, FORMACOES, POSICAO_MAP
from db_historico import carregar_historico_completo, carregar_historico_jogador

# Import app functions (need to handle streamlit import)
import importlib
app_module = importlib.import_module('app')
gerar_todas_rodadas = app_module.gerar_todas_rodadas
escalar_com_dados_anteriores = app_module.escalar_com_dados_anteriores
obter_melhores_reais = app_module.obter_melhores_reais
carregar_dados_historicos = app_module.carregar_dados_historicos
_processar_escalacao_com_pontos_reais = app_module._processar_escalacao_com_pontos_reais

app = FastAPI(title="Cartola Python Service", default_response_class=SafeJSONResponse)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def safe_serialize(obj):
    """Safely serialize objects to JSON-compatible types."""
    if obj is None:
        return None
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        v = float(obj)
        if np.isnan(v) or np.isinf(v):
            return 0.0
        return v
    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return 0.0
        return obj
    if isinstance(obj, np.ndarray):
        return [safe_serialize(x) for x in obj.tolist()]
    if isinstance(obj, pd.Timestamp):
        return str(obj)
    if isinstance(obj, (pd.Series,)):
        return {k: safe_serialize(v) for k, v in obj.to_dict().items()}
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict()
    try:
        if pd.isna(obj):
            return None
    except (TypeError, ValueError):
        pass
    return obj


def clean_dict(d):
    """Recursively clean a dict for JSON serialization."""
    if isinstance(d, dict):
        return {k: clean_dict(v) for k, v in d.items()}
    if isinstance(d, list):
        return [clean_dict(v) for v in d]
    return safe_serialize(d)


class SimulacaoRequest(BaseModel):
    ano: int = 2025
    orcamento: float = 150.0
    formacao: str = 'auto'
    orcamento_dinamico: bool = False


class EscalacaoRequest(BaseModel):
    formacao: str = '4-3-3'
    orcamento: float = 150.0
    ano: Optional[int] = None
    rodada: Optional[int] = None
    excluir_ids: Optional[List[str]] = None


class HistoricoJogadorRequest(BaseModel):
    atleta_id: str
    anos: Optional[List[int]] = None


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/simular")
async def simular(req: SimulacaoRequest):
    """Run the full simulation using the actual Python code."""
    try:
        result = gerar_todas_rodadas(
            ano=req.ano,
            orcamento=req.orcamento,
            formacao=req.formacao,
            retornar_detalhes=True,
            orcamento_dinamico=req.orcamento_dinamico
        )
        
        if result is None:
            raise HTTPException(status_code=404, detail="No data for this year")
        
        df = result[0] if isinstance(result, tuple) else result
        detalhes = result[1] if isinstance(result, tuple) and len(result) > 1 else None
        
        if not isinstance(df, pd.DataFrame):
            raise HTTPException(status_code=500, detail="Unexpected result type")
        
        # Convert DataFrame to list of dicts
        rodadas = []
        for _, row in df.iterrows():
            rodada_data = {}
            for col in df.columns:
                val = row[col]
                rodada_data[col] = safe_serialize(val)
            rodadas.append(rodada_data)
        
        # Process details if available
        detalhes_clean = None
        if detalhes:
            detalhes_clean = {}
            for rodada_num, detail in detalhes.items():
                detalhes_clean[str(rodada_num)] = clean_dict(detail)
        
        total_pts = float(df['Pts Escalado'].sum())
        media_pts = float(df['Pts Escalado'].mean())
        total_ideal = float(df['Pts Ideal'].sum())
        
        result = {
            "rodadas": rodadas,
            "detalhes": detalhes_clean,
            "resumo": {
                "total_pontos": round(total_pts, 1),
                "media_rodada": round(media_pts, 1),
                "total_ideal": round(total_ideal, 1),
                "aproveitamento": round(total_pts / total_ideal * 100, 1) if total_ideal > 0 else 0,
                "num_rodadas": len(rodadas)
            }
        }
        return _deep_clean(result)
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/escalar")
async def escalar(req: EscalacaoRequest):
    """Run the escalation using the actual Python strategy."""
    try:
        from api_cartola import CartolaFCAPI, formatar_atletas_para_modelo
        api = CartolaFCAPI()
        
        # Get current market data
        df_mercado = api.get_atletas_mercado()
        if df_mercado is None or df_mercado.empty:
            raise HTTPException(status_code=503, detail="Market not available")
        
        # Format for the model (adds calculated columns like the Streamlit does)
        df_mercado = formatar_atletas_para_modelo(df_mercado)
        
        # Filter out excluded players if specified
        if req.excluir_ids and len(req.excluir_ids) > 0:
            excluir_set = set(str(x) for x in req.excluir_ids)
            # Column is 'id' after formatar_atletas_para_modelo, not 'atleta_id'
            id_col = 'atleta_id' if 'atleta_id' in df_mercado.columns else 'id' if 'id' in df_mercado.columns else 'atletas.atleta_id'
            df_mercado = df_mercado[~df_mercado[id_col].astype(str).isin(excluir_set)].copy()
        
        # Create strategy
        estrategia = EstrategiaV7(orcamento=req.orcamento, modo_simulacao=False)
        
        # Determine formation
        if req.formacao == 'auto':
            resultado_formacoes = estrategia.analisar_todas_formacoes(
                df_mercado, req.orcamento
            )
            if resultado_formacoes:
                melhor = max(resultado_formacoes, key=lambda x: x.get('pontuacao_esperada', 0))
                resultado = melhor  # analisar_todas_formacoes returns the full escalacao dict directly
                formacao_usada = melhor.get('formacao', '4-3-3')
            else:
                resultado = estrategia.escalar_time(
                    df_mercado, req.formacao, req.orcamento, incluir_explicacao=True
                )
                formacao_usada = req.formacao
        else:
            resultado = estrategia.escalar_time(
                df_mercado, req.formacao, req.orcamento, incluir_explicacao=True
            )
            formacao_usada = req.formacao
        
        if resultado is None:
            raise HTTPException(status_code=500, detail="Could not generate lineup")
        
        # resultado from escalar_time/analisar_todas_formacoes already contains
        # titulares, capitao, reservas, reserva_luxo, formacao, pontuacao_esperada, etc.
        return clean_dict({
            "escalacao": resultado,
            "formacao": resultado.get('formacao', formacao_usada)
        })
    except HTTPException:
        raise
    except Exception as e:
        import io
        tb_str = io.StringIO()
        traceback.print_exc(file=tb_str)
        error_msg = tb_str.getvalue()
        print(f"[ESCALAR ERROR] {error_msg}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/historico-jogador")
async def historico_jogador(req: HistoricoJogadorRequest):
    """Get player history from the Neon DB."""
    try:
        hist = carregar_historico_jogador(req.atleta_id, req.anos)
        if hist is None:
            return {"found": False, "data": None}
        return {"found": True, "data": clean_dict(hist)}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/formacoes")
async def get_formacoes():
    """Return available formations."""
    return {"formacoes": FORMACOES}


@app.get("/mercado-ranqueado")
async def mercado_ranqueado():
    """Return the full model-processed mercado with all calculated fields."""
    try:
        from api_cartola import CartolaFCAPI, formatar_atletas_para_modelo
        api = CartolaFCAPI()
        df_mercado = api.get_atletas_mercado()
        if df_mercado is None or df_mercado.empty:
            raise HTTPException(status_code=503, detail="Market not available")
        df_mercado = formatar_atletas_para_modelo(df_mercado)
        estrategia = EstrategiaV7(orcamento=150, modo_simulacao=False)
        resultado = estrategia.escalar_time(df_mercado, '4-3-3', 150, incluir_explicacao=True)
        if resultado is None:
            raise HTTPException(status_code=500, detail="Could not process market")
        df_ranqueado = resultado.get('df_ranqueado')
        if df_ranqueado is None:
            raise HTTPException(status_code=500, detail="No df_ranqueado")
        
        # Generate explicacoes for all players
        explicacoes = {}
        for _, row in df_ranqueado.iterrows():
            try:
                formatado = estrategia._formatar_jogador(row, incluir_explicacao=True)
                explicacoes[str(row.get('atleta_id', row.get('id', '')))] = formatado
            except Exception:
                pass
        
        # Extract relevant columns for each player
        jogadores = []
        for _, row in df_ranqueado.iterrows():
            atleta_id = str(row.get('atleta_id', row.get('id', '')))
            jogadores.append({
                'atleta_id': atleta_id,
                'apelido': row.get('apelido', ''),
                'posicao_id': int(row.get('posicao_id', 0)),
                'clube_nome': row.get('clube_nome', ''),
                'clube_id': int(row.get('clube_id', 0)) if row.get('clube_id') else 0,
                'preco': float(row.get('preco', 0)),
                'media': float(row.get('media', 0)),
                'media_ultimas_3': float(row.get('media_ultimas_3', 0)),
                'media_ultimas_5': float(row.get('media_ultimas_5', 0)),
                'media_ultimas_10': float(row.get('media_ultimas_10', 0)),
                'media_historica': float(row.get('media_historica', 0)),
                'tendencia': float(row.get('tendencia', 0)),
                'padrao_evolucao': float(row.get('padrao_evolucao', 0)),
                'pontuacao_esperada': float(row.get('pontuacao_esperada', row.get('score', row.get('score_original', 0)))),
                'score_original': float(row.get('score_original', row.get('pred', row.get('score_geral_v9', 0)))),
                'status_id': int(row.get('status_id', 0)),
                'variacao': float(row.get('variacao', 0)),
                'jogos': int(row.get('jogos', 0)),
            })
        
        return clean_dict({
            'jogadores': jogadores,
            'explicacoes': explicacoes,
        })
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/posicoes")
async def get_posicoes():
    """Return position mapping."""
    return {"posicoes": POSICAO_MAP}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PYTHON_SERVICE_PORT", 8100))
    uvicorn.run(app, host="0.0.0.0", port=port)
