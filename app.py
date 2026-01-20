"""
Dervé FC - Escalação Automática
Estratégia v9 validada com 94.1 pts/rodada (+24.4% vs v6)

Design moderno com cores do Dervé FC
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import requests
from datetime import datetime
from typing import Dict, List, Optional
from glob import glob

from estrategia_v7 import EstrategiaV7, FORMACOES, POSICAO_MAP

from io import BytesIO
import plotly.graph_objects as go
import plotly.express as px

# Módulo de persistência (Neon PostgreSQL)
try:
    from database import (
        is_database_configured, salvar_jogadores_rodada, salvar_escalacao,
        carregar_jogadores_rodada, verificar_rodada_processada, obter_estatisticas_db
    )
    DB_DISPONIVEL = is_database_configured()
except ImportError:
    DB_DISPONIVEL = False
from aprendizagem_continua import AprendizagemContinua
from api_cartola import CartolaFCAPI
from reotimizar_orcamento import reotimizar_orcamento
from verificar_melhor_formacao import verificar_melhor_formacao
from recalcular_reservas import recalcular_reservas

# Configuração da página
st.set_page_config(
    page_title="Dervé FC - Escalação Automática",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado com cores do Dervé FC
st.markdown("""
<style>
    /* Importar fonte */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');
    
    /* Variáveis de cores do Dervé FC */
    :root {
        --derve-blue-light: #54b4f7;
        --derve-blue-dark: #0b1d33;
        --derve-blue-medium: #15367b;
        --derve-gold: #D4A84B;
        --derve-white: #FFFFFF;
        --derve-gray: #6C757D;
    }
    
    /* Fundo geral */
    .stApp {
        background: linear-gradient(135deg, #0b1d33 0%, #152744 100%);
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1d33 0%, #061222 100%);
        border-right: 3px solid #54b4f7;
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #FFFFFF;
    }
    
    [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }
    
    /* Títulos */
    h1 {
        color: #54b4f7 !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700 !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    h2, h3 {
        color: #FFFFFF !important;
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
    }
    
    /* Cards de métricas */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #152744 0%, #1e3a5f 100%);
        padding: 15px;
        border-radius: 15px;
        border-left: 4px solid #54b4f7;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        min-width: 100px;
    }
    
    [data-testid="stMetric"] label {
        color: #FFFFFF !important;
        font-weight: 500;
        font-size: 0.85rem !important;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #54b4f7 !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
        white-space: nowrap;
    }
    
    /* Botões */
    .stButton > button {
        background: linear-gradient(135deg, #54b4f7 0%, #3a9fe0 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
        font-family: 'Poppins', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(84, 180, 247, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #3a9fe0 0%, #2589c9 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(84, 180, 247, 0.4);
    }
    
    /* Inputs */
    .stNumberInput input, .stTextInput input, .stSelectbox select {
        background-color: #3D3D3D !important;
        color: #FFFFFF !important;
        border: 2px solid #4D4D4D !important;
        border-radius: 10px !important;
    }
    
    .stNumberInput input:focus, .stTextInput input:focus {
        border-color: #54b4f7 !important;
        box-shadow: 0 0 10px rgba(84, 180, 247, 0.3) !important;
    }
    
    /* Tabelas */
    .stDataFrame {
        background-color: #2D2D2D;
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Cards de jogadores */
    .jogador-card {
        background: linear-gradient(135deg, #152744 0%, #1e3a5f 100%);
        padding: 15px;
        border-radius: 12px;
        margin: 8px 0;
        border-left: 4px solid #15367b;
        transition: all 0.3s ease;
    }
    
    .jogador-card:hover {
        transform: translateX(5px);
        border-left-color: #54b4f7;
    }
    
    .capitao-card {
        background: linear-gradient(135deg, #3D3D3D 0%, #4D4D4D 100%);
        border-left: 4px solid #FFD700 !important;
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.2);
    }
    
    .reserva-luxo-card {
        background: linear-gradient(135deg, #2D4D3D 0%, #3D5D4D 100%);
        border-left: 4px solid #00FF00 !important;
    }
    
    /* Posição badge */
    .posicao-badge {
        background: linear-gradient(135deg, #15367b 0%, #1e4a9f 100%);
        color: white;
        padding: 5px 15px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
        display: inline-block;
        margin: 10px 0;
    }
    
    /* Formação recomendada */
    .formacao-recomendada {
        background: linear-gradient(135deg, #15367b 0%, #1e4a9f 100%);
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #54b4f7;
        box-shadow: 0 0 30px rgba(84, 180, 247, 0.2);
    }
    
    /* Alertas */
    .stAlert {
        border-radius: 10px;
    }
    
    /* Info boxes */
    .info-box {
        background: linear-gradient(135deg, #15367b 0%, #1e4a9f 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 15px 0;
    }
    
    .warning-box {
        background: linear-gradient(135deg, #D4A84B 0%, #b8923f 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin: 15px 0;
    }
    
    /* Comparação lado a lado */
    .comparison-card {
        background: linear-gradient(135deg, #152744 0%, #1e3a5f 100%);
        padding: 20px;
        border-radius: 15px;
        border-top: 4px solid #54b4f7;
        height: 100%;
    }
    
    .comparison-card-green {
        border-top: 4px solid #15367b;
    }
    
    /* Distintivo Dervé FC */
    [data-testid="stSidebar"] img[src*="base64"] {
        width: 180px !important;
        height: 180px !important;
        max-width: 180px !important;
        display: block !important;
        margin: 0 auto !important;
    }
    
    /* Scrollbar customizada */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #2D2D2D;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #54b4f7;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #3a9fe0;
    }
    
    /* Radio buttons na sidebar */
    [data-testid="stSidebar"] .stRadio label {
        color: #FFFFFF !important;
        padding: 10px 15px;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    [data-testid="stSidebar"] .stRadio label:hover {
        background-color: rgba(84, 180, 247, 0.2);
    }
    
    /* Divider */
    hr {
        border-color: #54b4f7 !important;
        opacity: 0.3;
    }
    
    /* Texto geral */
    p, span, div {
        font-family: 'Poppins', sans-serif;
    }
    
    /* Logo header */
    .logo-header {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 20px;
    }
    
    .logo-icon {
        font-size: 3rem;
    }
    
    /* Pontuação destaque */
    .pontuacao-destaque {
        font-size: 3rem;
        font-weight: 700;
        color: #54b4f7;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    /* Gráficos */
    .stLineChart {
        background-color: #152744;
        border-radius: 15px;
        padding: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Arquivos de configuração
CONFIG_FILE = "config_cartola.json"
STATE_FILE = "estado_cartola.json"

# API oficial (fonte de dados)
API_BASE = "https://api.cartola.globo.com"

# Diretório de dados históricos
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# ============================================
# ESCUDOS DOS TIMES
# ============================================
@st.cache_data(ttl=3600)  # Cache por 1 hora
def carregar_escudos_times() -> Dict[int, Dict]:
    """Carrega escudos dos times da API do Cartola FC."""
    try:
        response = requests.get(f"{API_BASE}/clubes", timeout=10)
        response.raise_for_status()
        clubes = response.json()
        
        # Criar mapeamento: clube_id -> {nome, escudo_url}
        escudos = {}
        for clube_id, dados in clubes.items():
            escudos[int(clube_id)] = {
                'nome': dados.get('nome', ''),
                'nome_fantasia': dados.get('nome_fantasia', ''),
                'abreviacao': dados.get('abreviacao', ''),
                'escudo_30': dados.get('escudos', {}).get('30x30', ''),
                'escudo_45': dados.get('escudos', {}).get('45x45', ''),
                'escudo_60': dados.get('escudos', {}).get('60x60', '')
            }
        return escudos
    except Exception as e:
        print(f"Erro ao carregar escudos: {e}")
        return {}

def get_escudo_html(clube_nome: str, clube_id: int = None, tamanho: int = 20) -> str:
    """Retorna HTML com escudo + nome do clube."""
    escudos = carregar_escudos_times()
    
    # Tentar encontrar o clube pelo ID ou nome
    escudo_url = ''
    if clube_id and clube_id in escudos:
        escudo_url = escudos[clube_id].get('escudo_30', '')
    else:
        # Buscar pelo nome
        for cid, dados in escudos.items():
            if dados.get('nome', '').upper() == clube_nome.upper() or \
               dados.get('abreviacao', '').upper() == clube_nome.upper() or \
               dados.get('nome_fantasia', '').upper() == clube_nome.upper():
                escudo_url = dados.get('escudo_30', '')
                break
    
    if escudo_url:
        return f'<img src="{escudo_url}" style="width: {tamanho}px; height: {tamanho}px; vertical-align: middle; margin-right: 5px;"><span style="color: #6C757D;">{clube_nome}</span>'
    else:
        return f'<span style="color: #6C757D;">{clube_nome}</span>'


def carregar_config() -> Dict:
    """Carrega configurações do arquivo."""
    config_padrao = {
        "orcamento": 100.0,
        "formacao_preferida": None,
        "rodada_atual": 1,
        "ultima_atualizacao": None
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                for key in config_padrao:
                    if key not in config:
                        config[key] = config_padrao[key]
                return config
        except:
            return config_padrao
    return config_padrao


def salvar_config(config: Dict):
    """Salva configurações no arquivo."""
    config['ultima_atualizacao'] = datetime.now().isoformat()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def carregar_dados_historicos(ano: int, rodada: int) -> Optional[pd.DataFrame]:
    """Carrega dados históricos de uma rodada específica."""
    arquivo = os.path.join(DATA_DIR, str(ano), f"rodada-{rodada}.csv")
    
    if not os.path.exists(arquivo):
        return None
    
    try:
        df = pd.read_csv(arquivo)
        
        col_map = {
            'atletas.atleta_id': 'atleta_id',
            'atletas.apelido': 'apelido',
            'atletas.pontos_num': 'pontos_num',
            'atletas.preco_num': 'preco_num',
            'atletas.media_num': 'media_num',
            'atletas.variacao_num': 'variacao_num',
            'atletas.clube.id.full.name': 'clube_nome',
            'atletas.clube_id': 'clube_id',
            'atletas.posicao_id': 'posicao_id',
            'atletas.entrou_em_campo': 'entrou_em_campo'
        }
        
        df = df.rename(columns=col_map)
        
        if 'pontos_num' in df.columns:
            df['pontos_num'] = pd.to_numeric(df['pontos_num'], errors='coerce').fillna(0)
        if 'preco_num' in df.columns:
            df['preco_num'] = pd.to_numeric(df['preco_num'], errors='coerce').fillna(0)
        if 'media_num' in df.columns:
            df['media_num'] = pd.to_numeric(df['media_num'], errors='coerce').fillna(0)
        if 'posicao_id' in df.columns:
            df['posicao_id'] = pd.to_numeric(df['posicao_id'], errors='coerce').fillna(0).astype(int)
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None


def carregar_dados_rodada_anterior(ano: int, rodada: int) -> Optional[pd.DataFrame]:
    """Carrega dados da rodada anterior para fazer a escalação."""
    if rodada <= 1:
        ano_anterior = ano - 1
        arquivos = glob(os.path.join(DATA_DIR, str(ano_anterior), "rodada-*.csv"))
        if arquivos:
            ultima_rodada = max([int(f.split('-')[-1].replace('.csv', '')) for f in arquivos])
            return carregar_dados_historicos(ano_anterior, ultima_rodada)
        return None
    
    return carregar_dados_historicos(ano, rodada - 1)


def gerar_justificativa_nao_escalado(jogador_ideal: Dict, escalacao: Dict, df_mercado: pd.DataFrame = None) -> Dict:
    """
    Gera justificativa explicando por que um jogador do time ideal não foi escalado.
    
    Args:
        jogador_ideal: Dados do jogador do time ideal
        escalacao: Escalação sugerida pelo sistema
        df_mercado: DataFrame com dados do mercado (opcional, para mais contexto)
    
    Returns:
        Dict com 'resumo', 'motivo' e 'cor' (para exibição)
    """
    if not escalacao or not jogador_ideal:
        return {'resumo': '❓ Sem dados', 'motivo': 'Dados insuficientes para análise', 'cor': '#6C757D'}
    
    atleta_id = str(jogador_ideal.get('atleta_id', ''))
    pos_id = jogador_ideal.get('pos_id', 0)
    preco_ideal = jogador_ideal.get('preco', 0)
    pontos_ideal = jogador_ideal.get('pontos', jogador_ideal.get('pontos_reais', 0))
    
    # Verificar se foi escalado
    ids_escalados = set(str(t.get('atleta_id', '')) for t in escalacao.get('titulares', []))
    if atleta_id in ids_escalados:
        return {'resumo': '✅ Escalado', 'motivo': 'Este jogador foi escalado pelo sistema', 'cor': '#15367b'}
    
    # Obter jogadores escalados na mesma posição
    escalados_posicao = [t for t in escalacao.get('titulares', []) if t.get('pos_id') == pos_id]
    
    if not escalados_posicao:
        return {'resumo': '❓ Posição não usada', 'motivo': 'Nenhum jogador desta posição foi escalado na formação escolhida', 'cor': '#6C757D'}
    
    # Calcular scores e preços dos escalados
    scores_escalados = [t.get('score', 0) for t in escalados_posicao]
    precos_escalados = [t.get('preco', 0) for t in escalados_posicao]
    max_score_escalado = max(scores_escalados) if scores_escalados else 0
    min_preco_escalado = min(precos_escalados) if precos_escalados else 0
    max_preco_escalado = max(precos_escalados) if precos_escalados else 0
    
    # Buscar score previsto do jogador ideal (se disponível no df_mercado)
    score_previsto = 0
    status_jogador = None
    if df_mercado is not None and len(df_mercado) > 0:
        jogador_mercado = df_mercado[df_mercado['atleta_id'].astype(str) == atleta_id]
        if len(jogador_mercado) > 0:
            score_previsto = jogador_mercado.iloc[0].get('score', jogador_mercado.iloc[0].get('pred', 0))
            status_jogador = jogador_mercado.iloc[0].get('status_id', None)
    
    # Determinar motivo principal
    
    # 1. Jogador suspenso ou contundido
    if status_jogador in [3, 5]:  # 3=Suspenso, 5=Contundido
        status_nome = 'Suspenso' if status_jogador == 3 else 'Contundido'
        return {
            'resumo': f'🚫 {status_nome}',
            'motivo': f'O jogador estava {status_nome.lower()} e não pôde ser escalado.',
            'cor': '#DC3545'
        }
    
    # 2. Preço muito alto para o orçamento
    custo_total_escalacao = escalacao.get('custo_total', 0)
    orcamento_restante = escalacao.get('orcamento_restante', 0)
    
    if preco_ideal > max_preco_escalado * 1.5:
        return {
            'resumo': '💰 Preço elevado',
            'motivo': f'Preço de C$ {preco_ideal:.1f} é muito alto. O sistema priorizou jogadores mais baratos para otimizar o orçamento.',
            'cor': '#FFC107'
        }
    
    # 3. Score previsto menor que os escalados
    if score_previsto > 0 and score_previsto < max_score_escalado * 0.8:
        return {
            'resumo': '📉 Score previsto baixo',
            'motivo': f'O score previsto ({score_previsto:.2f}) era menor que dos jogadores escalados. O modelo não previa uma boa pontuação.',
            'cor': '#FFC107'
        }
    
    # 4. Custo-benefício desfavorável
    if preco_ideal > 0:
        cb_ideal = pontos_ideal / preco_ideal
        cb_escalados = [t.get('score', 0) / t.get('preco', 1) for t in escalados_posicao if t.get('preco', 0) > 0]
        media_cb_escalados = sum(cb_escalados) / len(cb_escalados) if cb_escalados else 0
        
        if cb_ideal < media_cb_escalados * 0.7:
            return {
                'resumo': '⚖️ Custo-benefício',
                'motivo': f'Relação pontos/preço ({cb_ideal:.2f}) era inferior aos jogadores escalados. O sistema priorizou melhor custo-benefício.',
                'cor': '#FFC107'
            }
    
    # 5. Jogador não estava entre os melhores previstos
    if score_previsto > 0:
        return {
            'resumo': '🎯 Previsão diferente',
            'motivo': f'O modelo previa score de {score_previsto:.2f}, mas outros jogadores tinham previsões melhores para a rodada.',
            'cor': '#17A2B8'
        }
    
    # 6. Motivo genérico
    return {
        'resumo': '🔄 Otimização',
        'motivo': 'O sistema escolheu outros jogadores com melhor combinação de previsão, preço e consistência.',
        'cor': '#6C757D'
    }


def obter_melhores_reais(df: pd.DataFrame, formacao: str, orcamento: float, respeitar_orcamento: bool = False) -> Dict:
    """Obtém os melhores pontuadores reais da rodada seguindo a formação.
    
    Se respeitar_orcamento=True, calcula o melhor time possível dentro do orçamento.
    """
    if df is None or len(df) == 0:
        return None
    
    config_formacao = FORMACOES.get(formacao, FORMACOES['4-3-3'])
    
    df_jogou = df[df['entrou_em_campo'] == True].copy() if 'entrou_em_campo' in df.columns else df.copy()
    
    if not respeitar_orcamento:
        # Lógica original: pegar os melhores sem limite de orçamento
        titulares = []
        custo_total = 0
        
        for pos_id, qtd in config_formacao.items():
            pos_jogadores = df_jogou[df_jogou['posicao_id'] == pos_id].nlargest(qtd, 'pontos_num')
            
            for _, jogador in pos_jogadores.iterrows():
                titulares.append({
                    'atleta_id': str(jogador.get('atleta_id', '')),
                    'apelido': jogador.get('apelido', 'N/A'),
                    'posicao': POSICAO_MAP.get(pos_id, 'N/A'),
                    'pos_id': pos_id,
                    'pontos': jogador.get('pontos_num', 0),
                    'pontos_reais': jogador.get('pontos_num', 0),
                    'media': jogador.get('media_num', 0),
                    'preco': jogador.get('preco_num', 0),
                    'clube': jogador.get('clube_nome', '')
                })
                custo_total += jogador.get('preco_num', 0)
    else:
        # Nova lógica: melhor time possível DENTRO do orçamento
        # Usar programação dinâmica simplificada (greedy com substituições)
        titulares = []
        custo_total = 0
        ids_usados = []
        
        # Primeiro, tentar escalar os melhores de cada posição
        for pos_id, qtd in config_formacao.items():
            pos_jogadores = df_jogou[df_jogou['posicao_id'] == pos_id].sort_values('pontos_num', ascending=False)
            
            selecionados = 0
            for _, jogador in pos_jogadores.iterrows():
                if selecionados >= qtd:
                    break
                
                atleta_id = str(jogador.get('atleta_id', ''))
                preco = jogador.get('preco_num', 0)
                
                if atleta_id not in ids_usados:
                    # Calcular custo mínimo restante
                    pos_restantes = sum(config_formacao.get(p, 0) for p in config_formacao if p > pos_id)
                    pos_restantes += (qtd - selecionados - 1)
                    custo_minimo_restante = pos_restantes * 1.0  # Estimativa conservadora
                    
                    if custo_total + preco + custo_minimo_restante <= orcamento:
                        titulares.append({
                            'atleta_id': atleta_id,
                            'apelido': jogador.get('apelido', 'N/A'),
                            'posicao': POSICAO_MAP.get(pos_id, 'N/A'),
                            'pos_id': pos_id,
                            'pontos': jogador.get('pontos_num', 0),
                            'pontos_reais': jogador.get('pontos_num', 0),
                            'media': jogador.get('media_num', 0),
                            'preco': preco,
                            'clube': jogador.get('clube_nome', '')
                        })
                        custo_total += preco
                        ids_usados.append(atleta_id)
                        selecionados += 1
        
        # Se não conseguiu escalar 12, completar com os mais baratos
        total_esperado = sum(config_formacao.values())
        if len(titulares) < total_esperado:
            for pos_id, qtd in config_formacao.items():
                atual = len([t for t in titulares if t['pos_id'] == pos_id])
                while atual < qtd:
                    pos_jogadores = df_jogou[
                        (df_jogou['posicao_id'] == pos_id) & 
                        (~df_jogou['atleta_id'].astype(str).isin(ids_usados))
                    ].sort_values('preco_num')
                    
                    if len(pos_jogadores) == 0:
                        break
                    
                    for _, jogador in pos_jogadores.iterrows():
                        preco = jogador.get('preco_num', 0)
                        if custo_total + preco <= orcamento:
                            atleta_id = str(jogador.get('atleta_id', ''))
                            titulares.append({
                                'atleta_id': atleta_id,
                                'apelido': jogador.get('apelido', 'N/A'),
                                'posicao': POSICAO_MAP.get(pos_id, 'N/A'),
                                'pos_id': pos_id,
                                'pontos': jogador.get('pontos_num', 0),
                                'pontos_reais': jogador.get('pontos_num', 0),
                                'media': jogador.get('media_num', 0),
                                'preco': preco,
                                'clube': jogador.get('clube_nome', '')
                            })
                            custo_total += preco
                            ids_usados.append(atleta_id)
                            atual += 1
                            break
                    else:
                        break
    
    titulares.sort(key=lambda x: x.get('pontos', 0), reverse=True)
    
    capitao = titulares[0] if titulares else None
    
    pontuacao_total = sum(t.get('pontos', 0) for t in titulares)
    if capitao:
        pontuacao_total += capitao.get('pontos', 0)
    
    return {
        'formacao': formacao,
        'titulares': titulares,
        'capitao': capitao,
        'pontuacao_total': pontuacao_total,
        'custo_total': custo_total
    }


def escalar_com_dados_anteriores(df_anterior: pd.DataFrame, df_atual: pd.DataFrame, 
                                  formacao: str, orcamento: float, 
                                  ano: int = None, rodada: int = None) -> Dict:
    """Escala time usando a estratégia v8 e verifica pontuação real com substituições.
    
    IMPORTANTE: Para simulação histórica, usa df_atual (rodada N) para escalar,
    pois contém o status correto dos jogadores (Provável, Suspenso, etc.).
    O histórico é carregado até a rodada N-1.
    """
    # Para simulação histórica, usar df_atual (rodada N) para escalar
    # Para mercado real, usar df_anterior (dados mais recentes disponíveis)
    df_escalar = df_atual if (ano and rodada and df_atual is not None and len(df_atual) > 0) else df_anterior
    
    if df_escalar is None or len(df_escalar) == 0:
        return None
    
    # Determinar se é simulação histórica (ano e rodada definidos)
    modo_simulacao = ano is not None and rodada is not None
    
    # Usar a estratégia v9 com modelo apropriado:
    # - modo_simulacao=True: usa modelo_v9.joblib (2022-2024) para simulação histórica
    # - modo_simulacao=False: usa modelo_v9_2026.joblib (2022-2025) para escalação real
    estrategia = EstrategiaV7(modo_simulacao=modo_simulacao)
    
    # Carregar histórico para ter explicações corretas
    if ano and rodada:
        # SEMPRE carregar dados do ano anterior primeiro para ter histórico base
        # IMPORTANTE: Usar atualizar_historico() para que os dados sejam usados nas features
        ano_anterior = ano - 1
        for r in range(1, 39):
            df_hist = carregar_dados_historicos(ano_anterior, r)
            if df_hist is not None:
                estrategia.atualizar_historico(df_hist)
        
        # Depois carregar rodadas anteriores do ano atual (até N-1)
        if rodada > 1:
            for r in range(1, rodada):
                df_hist = carregar_dados_historicos(ano, r)
                if df_hist is not None:
                    estrategia.atualizar_historico(df_hist)
        
        # Ajustar rodada atual para cálculo correto
        estrategia.rodada_atual = rodada
    
    # Escalar time (modo_simulacao já definido acima)
    resultado = estrategia.escalar_time(df_escalar, formacao=formacao, orcamento=orcamento, incluir_explicacao=True, modo_simulacao=modo_simulacao)
    
    if resultado is None or len(resultado.get('titulares', [])) < 12:
        return None
    
    # Função para obter pontuação real de um jogador
    def obter_pontos_reais(atleta_id):
        if df_atual is None:
            return 0, False
        jogador = df_atual[df_atual['atleta_id'].astype(str) == str(atleta_id)]
        if len(jogador) > 0:
            return jogador.iloc[0].get('pontos_num', 0), True
        return 0, False
    
    # Processar titulares com pontuação real
    titulares = []
    for t in resultado['titulares']:
        atleta_id = str(t.get('atleta_id', ''))
        pontos_reais, encontrado = obter_pontos_reais(atleta_id)
        
        titulares.append({
            'atleta_id': atleta_id,
            'apelido': t.get('apelido', 'N/A'),
            'posicao': t.get('posicao', 'N/A'),
            'pos_id': t.get('pos_id', 0),
            'score': t.get('score', 0),
            'preco': t.get('preco', 0),
            'media': t.get('media', 0),
            'clube': t.get('clube', ''),
            'pontos_reais': pontos_reais,
            'substituido': False,
            'substituto': None,
            'explicacao': t.get('explicacao', {})
        })
    
    # Processar reservas com pontuação real
    reservas = {}
    for pos_id, reserva in resultado.get('reservas', {}).items():
        if reserva:
            atleta_id = str(reserva.get('atleta_id', ''))
            pontos_reais, _ = obter_pontos_reais(atleta_id)
            reservas[pos_id] = {
                'atleta_id': atleta_id,
                'apelido': reserva.get('apelido', 'N/A'),
                'posicao': reserva.get('posicao', 'N/A'),
                'pos_id': pos_id,
                'score': reserva.get('score', 0),
                'preco': reserva.get('preco', 0),
                'media': reserva.get('media', 0),
                'clube': reserva.get('clube', ''),
                'pontos_reais': pontos_reais,
                'explicacao': reserva.get('explicacao', {})
            }
    
    # Processar reserva de luxo com pontuação real
    reserva_luxo = None
    if resultado.get('reserva_luxo'):
        rl = resultado['reserva_luxo']
        atleta_id = str(rl.get('atleta_id', ''))
        pontos_reais, _ = obter_pontos_reais(atleta_id)
        reserva_luxo = {
            'atleta_id': atleta_id,
            'apelido': rl.get('apelido', 'N/A'),
            'posicao': rl.get('posicao', 'N/A'),
            'pos_id': rl.get('pos_id', 0),
            'score': rl.get('score', 0),
            'preco': rl.get('preco', 0),
            'media': rl.get('media', 0),
            'clube': rl.get('clube', ''),
            'pontos_reais': pontos_reais,
            'explicacao': rl.get('explicacao', {})
        }
    
    # SUBSTITUIÇÃO 1: Reservas substituem titulares que NÃO JOGARAM (pontos = 0)
    substituicoes = []
    for i, titular in enumerate(titulares):
        if titular['pontos_reais'] == 0:  # Titular não jogou
            pos_id = titular['pos_id']
            if pos_id in reservas and reservas[pos_id]:
                reserva = reservas[pos_id]
                if reserva['pontos_reais'] > 0:  # Reserva jogou
                    titulares[i]['substituido'] = True
                    titulares[i]['substituto'] = reserva
                    substituicoes.append({
                        'tipo': 'reserva',
                        'saiu': titular,
                        'entrou': reserva
                    })
                    # Remover reserva usado
                    reservas[pos_id] = None
    
    # SUBSTITUIÇÃO 2: Reserva de luxo substitui o PIOR PONTUADOR da sua posição
    if reserva_luxo:
        pos_luxo = reserva_luxo['pos_id']
        # Encontrar titulares da mesma posição que não foram substituídos
        titulares_pos = [t for t in titulares if t['pos_id'] == pos_luxo and not t['substituido']]
        
        if titulares_pos:
            # Encontrar o pior pontuador da posição
            pior_pontuador = min(titulares_pos, key=lambda x: x['pontos_reais'])
            
            # Substituir se reserva de luxo fez mais pontos
            if reserva_luxo['pontos_reais'] > pior_pontuador['pontos_reais']:
                for i, titular in enumerate(titulares):
                    if titular['atleta_id'] == pior_pontuador['atleta_id']:
                        titulares[i]['substituido'] = True
                        titulares[i]['substituto'] = reserva_luxo
                        substituicoes.append({
                            'tipo': 'reserva_luxo',
                            'saiu': pior_pontuador,
                            'entrou': reserva_luxo
                        })
                        break
    
    # Identificar capitão
    capitao_id = str(resultado['capitao']['atleta_id']) if resultado.get('capitao') else None
    capitao = None
    for t in titulares:
        if t['atleta_id'] == capitao_id:
            capitao = t
            break
    
    if capitao is None and titulares:
        capitao = max(titulares, key=lambda x: x['score'])
    
    # Calcular pontuação PREVISTA (soma das médias dos titulares)
    capitao_id = capitao['atleta_id'] if capitao else None
    pontuacao_prevista = 0
    for t in titulares:
        media_jogador = t['media']
        # Capitão conta 1.5x
        if t['atleta_id'] == capitao_id:
            media_jogador *= 1.5
        pontuacao_prevista += media_jogador
    
    # Calcular pontuação real COM substituições
    pontuacao_real = 0
    capitao_id = capitao['atleta_id'] if capitao else None
    
    for t in titulares:
        pontos_jogador = 0
        if t['substituido'] and t['substituto']:
            pontos_jogador = t['substituto']['pontos_reais']
        else:
            pontos_jogador = t['pontos_reais']
        
        # Capitão conta 1.5x
        if t['atleta_id'] == capitao_id:
            pontos_jogador *= 1.5
        
        pontuacao_real += pontos_jogador
    
    custo_total = sum(t['preco'] for t in titulares)
    
    return {
        'formacao': formacao,
        'titulares': titulares,
        'reservas': reservas,
        'reserva_luxo': reserva_luxo,
        'capitao': capitao,
        'substituicoes': substituicoes,
        'pontuacao_prevista': pontuacao_prevista,
        'pontuacao_real': pontuacao_real,
        'custo_total': custo_total,
        'orcamento_restante': orcamento - custo_total
    }


@st.cache_data(ttl=300)
def buscar_mercado() -> Optional[pd.DataFrame]:
    """Busca dados do mercado da API oficial."""
    try:
        response = requests.get(f"{API_BASE}/atletas/mercado", timeout=30)
        if response.status_code == 200:
            data = response.json()
            atletas = data.get('atletas', [])
            
            if not atletas:
                return None
            
            df = pd.DataFrame(atletas)
            
            df['atleta_id'] = df['atleta_id'].astype(str)
            df['posicao_id'] = df['posicao_id'].astype(int)
            df['preco_num'] = pd.to_numeric(df['preco_num'], errors='coerce').fillna(0)
            df['media_num'] = pd.to_numeric(df['media_num'], errors='coerce').fillna(0)
            df['pontos_num'] = pd.to_numeric(df.get('pontos_num', 0), errors='coerce').fillna(0)
            
            clubes = {c['id']: c['nome'] for c in data.get('clubes', {}).values()}
            df['clube_nome'] = df['clube_id'].map(clubes)
            
            return df
    except Exception as e:
        pass
    
    return None


@st.cache_data(ttl=300)
def buscar_rodada_atual() -> int:
    """Busca a rodada atual da API."""
    try:
        response = requests.get(f"{API_BASE}/mercado/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('rodada_atual', 1)
    except:
        pass
    return 38


def exibir_jogador_card(jogador: Dict, is_capitao: bool = False, is_reserva_luxo: bool = False, 
                        mostrar_pontos_reais: bool = False, mostrar_previsto_vs_real: bool = False,
                        substituido: bool = False, mostrar_explicacao: bool = True):
    """Exibe card de jogador com estilo moderno e explicação da escolha."""
    card_class = "jogador-card"
    if is_capitao:
        card_class += " capitao-card"
    elif is_reserva_luxo:
        card_class += " reserva-luxo-card"
    elif substituido:
        card_class += " substituido-card"
    
    badge = ""
    if is_capitao:
        badge = "👑 "
    elif is_reserva_luxo:
        badge = "⭐ "
    elif substituido:
        badge = "🔄 "
    
    # Pontuação prevista (média) e real
    media = jogador.get('media', 0)
    pontos_reais = jogador.get('pontos_reais', jogador.get('pontos', 0))
    
    # Capitão tem pontuação multiplicada por 1.5
    if is_capitao:
        media_display = media * 1.5
        pontos_reais_display = pontos_reais * 1.5
    else:
        media_display = media
        pontos_reais_display = pontos_reais
    
    if mostrar_previsto_vs_real:
        pontos_display = f"📊 {media_display:.1f} → ⚽ {pontos_reais_display:.1f}"
        cor_pontos = "#FFFFFF" if pontos_reais_display > 0 else "#DC3545"
    elif mostrar_pontos_reais:
        pontos_display = f"⚽ {pontos_reais_display:.1f}"
        cor_pontos = "#FFFFFF" if pontos_reais_display > 0 else "#DC3545"
    else:
        pontos_display = f"📊 {media_display:.1f}"
        cor_pontos = "#FFFFFF"
    
    # Explicação da escolha
    explicacao = jogador.get('explicacao', {})
    resumo = explicacao.get('resumo', '') if explicacao else ''
    significado = explicacao.get('significado', '') if explicacao else ''
    motivo = explicacao.get('motivo', '') if explicacao else ''
    
    # Formatar classificação com cores baseadas no tipo
    explicacao_html = ''
    if resumo:
        # Definir cor baseada no tipo de justificativa
        if 'Boa fase' in resumo or 'recuperação' in resumo or 'premium' in resumo:
            cor_resumo = '#D4A84B'  # Dourado
        elif 'queda' in resumo:
            cor_resumo = '#DC3545'  # Vermelho
        elif 'Aposta' in resumo:
            cor_resumo = '#FFC107'  # Amarelo
        else:
            cor_resumo = '#ADB5BD'  # Cinza
        
        explicacao_html = f'<div style="font-size: 0.85rem; color: {cor_resumo}; margin-top: 8px; font-weight: 600;">{resumo}</div>'
        
        if significado:
            explicacao_html += f'<div style="font-size: 0.75rem; color: #E5E7EB; margin-top: 4px;">📝 {significado}</div>'
        
        if motivo:
            explicacao_html += f'<div style="font-size: 0.75rem; color: #D1D5DB; margin-top: 4px; font-style: italic;">💡 {motivo}</div>'
    
    # Valorização prevista
    valorizacao = jogador.get('valorizacao_prevista', 0)
    if valorizacao > 0:
        val_display = f"📈 +{valorizacao:.1f}"
        cor_val = "#28A745"  # Verde
    elif valorizacao < 0:
        val_display = f"📉 {valorizacao:.1f}"
        cor_val = "#DC3545"  # Vermelho
    else:
        val_display = f"🔹 {valorizacao:.1f}"
        cor_val = "#6C757D"  # Cinza
    
    st.markdown(f"""
    <div class="{card_class}">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 1.1rem; font-weight: 600; color: #FFFFFF;">{badge}{jogador.get('apelido', 'N/A')}</span>
                <span style="margin-left: 10px;">{get_escudo_html(jogador.get('clube', ''), jogador.get('clube_id'))}</span>
            </div>
            <div style="text-align: right;">
                <span style="color: #FFFFFF; font-weight: 600;">C$ {jogador.get('preco', 0):.1f}</span>
                <span style="color: {cor_pontos}; margin-left: 15px; font-weight: 700; font-size: 1.1rem;">{pontos_display}</span>
            </div>
        </div>
        <div style="margin-top: 6px; font-size: 0.85rem;">
            <span style="color: {cor_val}; font-weight: 600;">{val_display}</span>
            <span style="color: #6C757D; margin-left: 5px;">valorização prevista</span>
        </div>
        {explicacao_html if mostrar_explicacao else ''}
    </div>
    """, unsafe_allow_html=True)




def gerar_todas_rodadas(ano: int, orcamento: float, formacao: str = '4-3-3', progress_bar=None, status_text=None, retornar_detalhes: bool = False):
    """Gera escalação para todas as rodadas de um ano.
    
    Se formacao='auto', testa todas as formações e escolhe a melhor para cada rodada.
    Se retornar_detalhes=True, retorna também os dados detalhados de cada escalação.
    
    Returns:
        Se retornar_detalhes=False: pd.DataFrame com resumo
        Se retornar_detalhes=True: (pd.DataFrame, dict) com resumo e detalhes
    """
    resultados = []
    detalhes_rodadas = {}  # Armazena dados detalhados de cada rodada
    total_rodadas = 37  # Rodadas 2 a 38
    
    # Lista de formações para testar quando modo automático
    formacoes_disponiveis = list(FORMACOES.keys())
    usar_formacao_automatica = formacao == 'auto'
    
    for i, rodada in enumerate(range(2, 39)):
        # Atualizar barra de progresso
        if progress_bar is not None:
            progress_bar.progress((i + 1) / total_rodadas)
        if status_text is not None:
            if usar_formacao_automatica:
                status_text.text(f"⏳ Rodada {rodada}/38 - Testando {len(formacoes_disponiveis)} formações...")
            else:
                status_text.text(f"⏳ Processando rodada {rodada}/38... ({i+1}/{total_rodadas})")
        
        df_anterior = carregar_dados_rodada_anterior(ano, rodada)
        df_atual = carregar_dados_historicos(ano, rodada)
        
        if df_anterior is None or df_atual is None:
            continue
        
        try:
            melhor_escalacao = None
            melhor_formacao = formacao
            melhor_pontuacao = -float('inf')
            
            if usar_formacao_automatica:
                # Testar todas as formações e escolher a melhor PELA PREVISÃO (não pelo resultado real)
                # Isso simula o comportamento real onde não sabemos o resultado ainda
                for form in formacoes_disponiveis:
                    esc = escalar_com_dados_anteriores(df_anterior, df_atual, form, orcamento, ano=ano, rodada=rodada)
                    pontuacao_prevista = esc.get('pontuacao_prevista', esc.get('pontuacao_esperada', 0)) if esc else 0
                    if esc and pontuacao_prevista > melhor_pontuacao:
                        melhor_pontuacao = pontuacao_prevista
                        melhor_escalacao = esc
                        melhor_formacao = form
            else:
                melhor_escalacao = escalar_com_dados_anteriores(df_anterior, df_atual, formacao, orcamento, ano=ano, rodada=rodada)
                melhor_formacao = formacao
            
            # Obter melhores reais com a mesma formação usada
            melhores = obter_melhores_reais(df_atual, melhor_formacao, orcamento, respeitar_orcamento=True)
            
            if melhor_escalacao and melhores:
                ids_escalados = set(t['atleta_id'] for t in melhor_escalacao['titulares'])
                ids_melhores = set(t['atleta_id'] for t in melhores['titulares'])
                acertos = len(ids_escalados.intersection(ids_melhores))
                
                cap_escalado = melhor_escalacao['capitao']['apelido'] if melhor_escalacao.get('capitao') else ''
                cap_ideal = melhores['capitao']['apelido'] if melhores.get('capitao') else ''
                cap_ok = 1 if cap_escalado == cap_ideal else 0
                
                pts_ideal = melhores['pontuacao_total'] if melhores['pontuacao_total'] > 0 else 1
                
                resultados.append({
                    'Rodada': rodada,
                    'Pts Escalado': round(melhor_escalacao['pontuacao_real'], 1),
                    'Pts Previsto': round(melhor_escalacao.get('pontuacao_prevista', melhor_escalacao.get('pontuacao_esperada', 0)), 1),
                    'Pts Ideal': round(melhores['pontuacao_total'], 1),
                    'Aproveitamento': f"{(melhor_escalacao['pontuacao_real'] / pts_ideal * 100):.1f}%",
                    'Acertos': f"{acertos}/12",
                    'Capitão Escalado': cap_escalado,
                    'Capitão Ideal': cap_ideal,
                    'Cap OK': '✓' if cap_ok else '✗',
                    'Custo': f"C$ {melhor_escalacao['custo_total']:.1f}",
                    'Formação': melhor_formacao
                })
                
                # Armazenar detalhes se solicitado
                if retornar_detalhes:
                    detalhes_rodadas[rodada] = {
                        'escalacao': melhor_escalacao,
                        'melhores': melhores,
                        'formacao': melhor_formacao,
                        'acertos': acertos,
                        'cap_ok': cap_ok
                    }
        except Exception as e:
            continue
    
    df_resultados = pd.DataFrame(resultados)
    
    if retornar_detalhes:
        return df_resultados, detalhes_rodadas
    return df_resultados


def substituir_jogador_manual(escalacao: dict, jogador_id, df_mercado: pd.DataFrame, orcamento: float, estrategia=None, ids_a_excluir: set = None) -> dict:
    """Substitui um jogador que não vai jogar por outro disponível.
    
    NOVA LÓGICA: Usa o DataFrame já ranqueado pela escalação original.
    Simplesmente pega o próximo jogador da lista que:
    - É da mesma posição
    - Não está escalado
    - Não está na lista de jogadores a excluir (outros sendo substituídos)
    - Cabe no orçamento
    
    Args:
        ids_a_excluir: IDs de jogadores que estão sendo substituídos em lote (para evitar reselecionar)
    """
    if not escalacao:
        return escalacao
    
    # Converter jogador_id para string para comparação consistente
    jogador_id_str = str(jogador_id)
    
    # Encontrar o jogador a ser substituído
    jogador_substituir = None
    idx_substituir = -1
    for i, t in enumerate(escalacao['titulares']):
        if str(t['atleta_id']) == jogador_id_str:
            jogador_substituir = t
            idx_substituir = i
            break
    
    if jogador_substituir is None:
        return escalacao
    
    pos_id = jogador_substituir['pos_id']
    preco_liberado = jogador_substituir['preco']
    orcamento_disponivel = escalacao.get('orcamento_restante', 0) + preco_liberado
    
    # IDs já escalados (exceto o que será substituído)
    ids_escalados = set(str(t['atleta_id']) for t in escalacao['titulares'] if str(t['atleta_id']) != jogador_id_str)
    
    # Adicionar IDs das reservas também
    for pos, reserva in escalacao.get('reservas', {}).items():
        if reserva:
            ids_escalados.add(str(reserva.get('atleta_id', '')))
    if escalacao.get('reserva_luxo'):
        ids_escalados.add(str(escalacao['reserva_luxo'].get('atleta_id', '')))
    
    # Adicionar IDs de jogadores sendo substituídos em lote (para evitar reselecionar)
    if ids_a_excluir:
        ids_escalados.update(str(id) for id in ids_a_excluir)
    
    # NOVA LÓGICA: Usar o DataFrame já ranqueado da escalação original
    df_ranqueado = escalacao.get('df_ranqueado')
    
    if df_ranqueado is not None and len(df_ranqueado) > 0:
        # Usar o DataFrame já ranqueado (com scores calculados)
        candidatos = df_ranqueado[
            (df_ranqueado['posicao_id'] == pos_id) &
            (~df_ranqueado['atleta_id'].astype(str).isin(ids_escalados)) &
            (df_ranqueado['preco'] <= orcamento_disponivel)
        ].copy()
        
        # Já está ordenado por score, então só precisamos pegar o primeiro
        if not candidatos.empty:
            # Ordenar por score (garantir ordem)
            candidatos = candidatos.sort_values('score', ascending=False)
    else:
        # Fallback: usar df_mercado e calcular scores
        if df_mercado is None or len(df_mercado) == 0:
            return escalacao
        
        candidatos = df_mercado[
            (df_mercado['posicao_id'] == pos_id) &
            (~df_mercado['atleta_id'].astype(str).isin(ids_escalados)) &
            (df_mercado['preco_num'] <= orcamento_disponivel)
        ].copy()
        
        if candidatos.empty:
            return escalacao
        
        # Usar estratégia para calcular scores se disponível
        if estrategia is not None:
            try:
                candidatos = estrategia.preparar_features_v9(candidatos)
                if 'score_geral_v9' in candidatos.columns:
                    candidatos['score'] = candidatos['score_geral_v9']
                    candidatos = candidatos.sort_values('score', ascending=False)
                else:
                    candidatos['score'] = candidatos.get('media_num', candidatos.get('media', 0))
                    candidatos = candidatos.sort_values('score', ascending=False)
            except:
                candidatos['score'] = candidatos.get('media_num', candidatos.get('media', 0))
                candidatos = candidatos.sort_values('score', ascending=False)
        else:
            candidatos['score'] = candidatos.get('media_num', candidatos.get('media', 0))
            candidatos = candidatos.sort_values('score', ascending=False)
    
    # Pegar o melhor candidato
    if candidatos.empty:
        escalacao['erro_substituicao'] = {
            'jogador_id': jogador_id_str,
            'motivo': 'Nenhum candidato disponível para substituição nesta posição'
        }
        return escalacao
    
    substituto = candidatos.iloc[0]
    
    # Calcular score e dados para explicação
    # Priorizar 'score' (do DataFrame ranqueado) sobre 'score_geral_v9'
    score = float(substituto.get('score', substituto.get('score_geral_v9', substituto.get('media', 0))))
    media = float(substituto.get('media', substituto.get('media_num', 0)))
    preco = float(substituto.get('preco', substituto.get('preco_num', 0)))
    jogos = int(substituto.get('jogos_num', substituto.get('jogos', 0)))
    custo_beneficio = score / preco if preco > 0 else 0  # Usar score ao invés de média
    
    # Gerar explicação detalhada
    fatores = []
    fatores.append(f"📊 Score: {score:.2f}")
    fatores.append(f"📈 Média: {media:.2f} pts")
    fatores.append(f"💰 Preço: C$ {preco:.1f}")
    if jogos > 0:
        fatores.append(f"⚽ Jogos: {jogos}")
    fatores.append(f"📊 Custo-benefício: {custo_beneficio:.2f}")
    
    # Determinar resumo e motivo baseado no score calculado
    if score >= 5:
        resumo = "⭐ Melhor substituto disponível - alto score preditivo"
        significado = f"Este jogador tem o maior score preditivo ({score:.2f}) entre os disponíveis na posição."
        motivo = "Próximo da lista de jogadores ranqueados pela IA. Mesmo critério usado na escalação original."
    elif score >= 3:
        resumo = "✅ Substituto recomendado - bom score preditivo"
        significado = f"Entre os jogadores disponíveis no orçamento, este tem o melhor score ({score:.2f})."
        motivo = "Próximo da lista de jogadores ranqueados pela IA. Considerando orçamento e jogadores já escalados."
    elif score > 0:
        resumo = "📊 Substituto válido - score positivo"
        significado = f"Score de {score:.2f} pontos previstos."
        motivo = "Melhor opção disponível na posição considerando o orçamento restante."
    elif media >= 5:
        resumo = "⭐ Substituto de qualidade - boa média histórica"
        significado = f"Jogador com média de {media:.2f} pontos por rodada."
        motivo = "Escolhido por ter a melhor média histórica entre os candidatos disponíveis no orçamento."
    else:
        resumo = "🔄 Substituto disponível - melhor opção no orçamento"
        significado = f"Média de {media:.2f} pontos."
        motivo = "Escolhido como a melhor opção disponível considerando o orçamento restante."
    
    # Adicionar informação sobre outros candidatos
    n_candidatos = len(candidatos)
    if n_candidatos > 1:
        segundo_melhor = candidatos.iloc[1]
        segundo_nome = segundo_melhor.get('apelido', 'N/A')
        segundo_score = float(segundo_melhor.get('score', segundo_melhor.get('score_geral_v9', segundo_melhor.get('media', 0))))
        fatores.append(f"📋 Analisados {n_candidatos} candidatos na posição")
        fatores.append(f"🥈 2º melhor: {segundo_nome} (score: {segundo_score:.2f})")
    
    novo_jogador = {
        'atleta_id': str(substituto['atleta_id']),
        'apelido': substituto['apelido'],
        'pos_id': int(substituto['posicao_id']),
        'posicao': POSICAO_MAP.get(int(substituto['posicao_id']), ''),
        'preco': preco,
        'media': media,
        'score': score,
        'clube': substituto.get('clube_nome', ''),
        'clube_id': int(substituto.get('clube_id', 0)),
        'pontos_reais': 0,
        'substituido': False,
        'substituto': None,
        'valorizacao_prevista': round((score - media * 0.3) / 8, 2) if score > 0 else 0,
        'explicacao': {
            'fatores': fatores,
            'resumo': resumo,
            'significado': significado,
            'motivo': motivo
        }
    }
    
    escalacao['titulares'][idx_substituir] = novo_jogador
    escalacao['custo_total'] = sum(t['preco'] for t in escalacao['titulares'])
    escalacao['orcamento_restante'] = orcamento - escalacao['custo_total']
    
    return escalacao


def pagina_simulacao():
    """Página de simulação histórica com opção de gerar todas as rodadas."""
    st.markdown('<h1>🔬 Simulação Histórica</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #6C757D; font-size: 1.1rem;">Compare a escalação sugerida com os melhores pontuadores reais</p>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown('<h3 style="color: #54b4f7;">⚙️ Configurações</h3>', unsafe_allow_html=True)
        
        ano = st.selectbox("📅 Ano", [2025, 2024, 2023, 2022], index=0)
        
        modo = st.radio("📊 Modo", ["Rodada Específica", "Todas as Rodadas"], index=0)
        
        if modo == "Rodada Específica":
            rodada = st.number_input("🔢 Rodada", min_value=1, max_value=38, value=38)
        else:
            rodada = None
        
        orcamento = st.number_input("💰 Orçamento (C$)", min_value=50.0, max_value=300.0, value=150.0, step=5.0)
        
        formacao_opcoes = ['Automática (Melhor)'] + list(FORMACOES.keys())
        formacao_selecionada = st.selectbox("📋 Formação", formacao_opcoes, index=0)
    
    # Modo: Todas as Rodadas
    if modo == "Todas as Rodadas":
        st.markdown('<h2>📊 Análise de Todas as Rodadas</h2>', unsafe_allow_html=True)
        
        # Inicializar session_state para persistir resultados
        if 'simulacao_gerada' not in st.session_state:
            st.session_state['simulacao_gerada'] = False
        
        if st.button("🚀 Gerar Análise Completa", type="primary", use_container_width=True):
            formacao_usar = 'auto' if formacao_selecionada == 'Automática (Melhor)' else formacao_selecionada
            
            # Barra de progresso visual
            progress_bar = st.progress(0)
            status_text = st.empty()
            status_text.text("⏳ Iniciando processamento...")
            
            # Gerar com detalhes para exibir layout completo
            resultado = gerar_todas_rodadas(ano, orcamento, formacao_usar, progress_bar, status_text, retornar_detalhes=True)
            
            # Desempacotar resultado
            if isinstance(resultado, tuple):
                df_resultados, detalhes_rodadas = resultado
            else:
                df_resultados = resultado
                detalhes_rodadas = {}
            
            # Limpar barra de progresso
            progress_bar.empty()
            status_text.text("✅ Processamento concluído!")
            
            if df_resultados.empty:
                st.error("Não foi possível gerar os resultados. Verifique se os dados do ano estão disponíveis.")
                return
            
            # Salvar detalhes no session_state para persistência
            st.session_state['detalhes_rodadas'] = detalhes_rodadas
            st.session_state['df_resultados_simulacao'] = df_resultados
            st.session_state['simulacao_gerada'] = True
            st.session_state['simulacao_ano'] = ano
            st.session_state['simulacao_orcamento'] = orcamento
            st.session_state['simulacao_formacao'] = formacao_selecionada
            
            # Métricas resumidas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_pts = df_resultados['Pts Escalado'].sum()
                st.metric("Total Pontos", f"{total_pts:.1f}")
            with col2:
                media_pts = df_resultados['Pts Escalado'].mean()
                st.metric("Média/Rodada", f"{media_pts:.1f}")
            with col3:
                caps_ok = (df_resultados['Cap OK'] == '✓').sum()
                st.metric("Capitães OK", f"{caps_ok}/{len(df_resultados)}")
            with col4:
                total_ideal = df_resultados['Pts Ideal'].sum()
                aproveit = (total_pts / total_ideal * 100) if total_ideal > 0 else 0
                st.metric("Aproveitamento", f"{aproveit:.1f}%")
            
            st.divider()
            
            # Gráfico de Linhas: Previsto vs Real vs Ideal
            st.markdown('<h3>📈 Evolução por Rodada</h3>', unsafe_allow_html=True)
            
            fig = go.Figure()
            
            # Linha do Time Ideal (dourada)
            fig.add_trace(go.Scatter(
                x=df_resultados['Rodada'],
                y=df_resultados['Pts Ideal'],
                mode='lines+markers',
                name='Time Ideal',
                line=dict(color='#FFD700', width=2, dash='dot'),
                marker=dict(size=6),
                hovertemplate='Rodada %{x}<br>Ideal: %{y:.1f} pts<extra></extra>'
            ))
            
            # Linha de Previsão (azul claro)
            if 'Pts Previsto' in df_resultados.columns:
                fig.add_trace(go.Scatter(
                    x=df_resultados['Rodada'],
                    y=df_resultados['Pts Previsto'],
                    mode='lines+markers',
                    name='Previsão',
                    line=dict(color='#28A745', width=2, dash='dash'),
                    marker=dict(size=6, symbol='diamond'),
                    hovertemplate='Rodada %{x}<br>Previsão: %{y:.1f} pts<extra></extra>'
                ))
            
            # Linha do Escalado (laranja - cor do Dervé FC)
            fig.add_trace(go.Scatter(
                x=df_resultados['Rodada'],
                y=df_resultados['Pts Escalado'],
                mode='lines+markers',
                name='Escalado (Real)',
                line=dict(color='#54b4f7', width=3),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(255, 107, 0, 0.1)',
                hovertemplate='Rodada %{x}<br>Escalado: %{y:.1f} pts<extra></extra>'
            ))
            
            # Linha de meta (90 pts)
            fig.add_hline(y=90, line_dash="dash", line_color="#DC3545", 
                         annotation_text="Meta: 90 pts", annotation_position="right")
            
            # Layout do gráfico
            fig.update_layout(
                title=dict(text='Pontuação por Rodada', font=dict(size=16, color='#FFFFFF')),
                xaxis=dict(
                    title='Rodada',
                    tickmode='linear',
                    dtick=5,
                    gridcolor='rgba(255,255,255,0.1)',
                    color='#FFFFFF'
                ),
                yaxis=dict(
                    title='Pontos',
                    gridcolor='rgba(255,255,255,0.1)',
                    color='#FFFFFF'
                ),
                legend=dict(
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='center',
                    x=0.5,
                    font=dict(color='#FFFFFF')
                ),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                hovermode='x unified',
                margin=dict(l=40, r=40, t=60, b=40)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Análise por Posição e Justificativas
            if detalhes_rodadas:
                st.divider()
                
                col_pos, col_just = st.columns(2)
                
                with col_pos:
                    # Calcular aproveitamento por posição
                    st.markdown('<h3>🎯 Aproveitamento por Posição</h3>', unsafe_allow_html=True)
                    
                    pos_stats = {pos: {'escalado': 0, 'ideal': 0} for pos in ['GOL', 'ZAG', 'LAT', 'MEI', 'ATA', 'TEC']}
                    pos_map_inv = {1: 'GOL', 2: 'LAT', 3: 'ZAG', 4: 'MEI', 5: 'ATA', 6: 'TEC'}
                    
                    for rodada_num, detalhe in detalhes_rodadas.items():
                        for t in detalhe['escalacao'].get('titulares', []):
                            pos = pos_map_inv.get(t.get('pos_id'), 'N/A')
                            if pos in pos_stats:
                                pos_stats[pos]['escalado'] += t.get('pontos_reais', 0)
                        for t in detalhe['melhores'].get('titulares', []):
                            pos = pos_map_inv.get(t.get('pos_id'), 'N/A')
                            if pos in pos_stats:
                                pos_stats[pos]['ideal'] += t.get('pontos', 0)
                    
                    posicoes = list(pos_stats.keys())
                    aproveitamentos = []
                    for pos in posicoes:
                        if pos_stats[pos]['ideal'] > 0:
                            aproveitamentos.append((pos_stats[pos]['escalado'] / pos_stats[pos]['ideal']) * 100)
                        else:
                            aproveitamentos.append(0)
                    
                    cores = ['#54b4f7' if a >= 50 else '#DC3545' for a in aproveitamentos]
                    
                    fig_pos = go.Figure(data=[
                        go.Bar(
                            x=posicoes,
                            y=aproveitamentos,
                            marker_color=cores,
                            text=[f'{a:.0f}%' for a in aproveitamentos],
                            textposition='outside',
                            hovertemplate='%{x}<br>Aproveitamento: %{y:.1f}%<extra></extra>'
                        )
                    ])
                    
                    fig_pos.add_hline(y=50, line_dash="dash", line_color="#FFD700", 
                                     annotation_text="50%", annotation_position="right")
                    
                    fig_pos.update_layout(
                        xaxis=dict(title='', color='#FFFFFF'),
                        yaxis=dict(title='Aproveitamento (%)', range=[0, 100], color='#FFFFFF', gridcolor='rgba(255,255,255,0.1)'),
                        plot_bgcolor='rgba(30, 40, 60, 0.3)',
                        paper_bgcolor='rgba(30, 40, 60, 0.3)',
                        margin=dict(l=40, r=40, t=20, b=40),
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig_pos, use_container_width=True)
                
                with col_just:
                    # Distribuição de Justificativas
                    st.markdown('<h3>📊 Distribuição de Justificativas</h3>', unsafe_allow_html=True)
                    
                    justificativas_count = {
                        'Recuperação': 0,
                        'Boa Fase': 0,
                        'Em Queda': 0,
                        'Premium': 0,
                        'Custo-Benefício': 0,
                        'Aposta': 0,
                        'Consistente': 0
                    }
                    
                    for rodada_num, detalhe in detalhes_rodadas.items():
                        for t in detalhe['escalacao'].get('titulares', []):
                            explicacao = t.get('explicacao', {})
                            resumo = explicacao.get('resumo', '') if explicacao else ''
                            if 'recuperação' in resumo.lower():
                                justificativas_count['Recuperação'] += 1
                            elif 'boa fase' in resumo.lower():
                                justificativas_count['Boa Fase'] += 1
                            elif 'queda' in resumo.lower():
                                justificativas_count['Em Queda'] += 1
                            elif 'premium' in resumo.lower():
                                justificativas_count['Premium'] += 1
                            elif 'custo' in resumo.lower():
                                justificativas_count['Custo-Benefício'] += 1
                            elif 'aposta' in resumo.lower():
                                justificativas_count['Aposta'] += 1
                            else:
                                justificativas_count['Consistente'] += 1
                    
                    # Filtrar apenas justificativas com contagem > 0
                    labels = [k for k, v in justificativas_count.items() if v > 0]
                    values = [v for v in justificativas_count.values() if v > 0]
                    colors = ['#15367b', '#28A745', '#DC3545', '#FFD700', '#17A2B8', '#FFC107', '#6C757D']
                    
                    fig_just = go.Figure(data=[go.Pie(
                        labels=labels,
                        values=values,
                        hole=0.4,
                        marker_colors=colors[:len(labels)],
                        textinfo='label+percent',
                        textfont=dict(color='#FFFFFF'),
                        hovertemplate='%{label}<br>Quantidade: %{value}<br>%{percent}<extra></extra>'
                    )])
                    
                    fig_just.update_layout(
                        plot_bgcolor='rgba(30, 40, 60, 0.3)',
                        paper_bgcolor='rgba(30, 40, 60, 0.3)',
                        margin=dict(l=20, r=20, t=20, b=20),
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig_just, use_container_width=True)
                
                st.divider()
                
                # Gráficos de Formações e Top Jogadores
                col_form, col_top = st.columns(2)
                
                with col_form:
                    # Formações Mais Escaladas
                    st.markdown('<h3>⚽ Formações Mais Escaladas</h3>', unsafe_allow_html=True)
                    
                    formacoes_count = {}
                    for rodada_num, detalhe in detalhes_rodadas.items():
                        formacao = detalhe.get('formacao', 'N/A')
                        formacoes_count[formacao] = formacoes_count.get(formacao, 0) + 1
                    
                    # Ordenar por quantidade
                    formacoes_sorted = sorted(formacoes_count.items(), key=lambda x: x[1], reverse=True)
                    formacoes_labels = [f[0] for f in formacoes_sorted]
                    formacoes_values = [f[1] for f in formacoes_sorted]
                    
                    fig_form = go.Figure(data=[
                        go.Bar(
                            x=formacoes_labels,
                            y=formacoes_values,
                            marker_color='#54b4f7',
                            text=formacoes_values,
                            textposition='outside',
                            hovertemplate='%{x}<br>Escalada: %{y} vezes<extra></extra>'
                        )
                    ])
                    
                    fig_form.update_layout(
                        xaxis=dict(title='', color='#FFFFFF'),
                        yaxis=dict(title='Quantidade', color='#FFFFFF', gridcolor='rgba(255,255,255,0.1)'),
                        plot_bgcolor='rgba(30, 40, 60, 0.3)',
                        paper_bgcolor='rgba(30, 40, 60, 0.3)',
                        margin=dict(l=40, r=40, t=20, b=40),
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig_form, use_container_width=True)
                
                with col_top:
                    # Top 5 Jogadores Mais Escalados
                    st.markdown('<h3>🏆 Top 5 Jogadores Mais Escalados</h3>', unsafe_allow_html=True)
                    
                    jogadores_stats = {}  # {nome: {'pontos': total, 'escalacoes': count}}
                    for rodada_num, detalhe in detalhes_rodadas.items():
                        for t in detalhe['escalacao'].get('titulares', []):
                            nome = t.get('apelido', 'Desconhecido')
                            pontos = t.get('pontos_reais', 0)
                            if nome not in jogadores_stats:
                                jogadores_stats[nome] = {'pontos': 0, 'escalacoes': 0}
                            jogadores_stats[nome]['pontos'] += pontos
                            jogadores_stats[nome]['escalacoes'] += 1
                    
                    # Top 5 por pontos totais
                    top5 = sorted(jogadores_stats.items(), key=lambda x: x[1]['pontos'], reverse=True)[:5]
                    
                    # Medalhas
                    medalhas = ['🥇', '🥈', '🥉', '🏅', '🏅']
                    
                    # Exibir lista estilizada
                    for i, (nome, stats) in enumerate(top5):
                        cor_borda = '#FFD700' if i == 0 else '#C0C0C0' if i == 1 else '#CD7F32' if i == 2 else '#54b4f7'
                        st.markdown(f'''
                        <div style="
                            background: linear-gradient(135deg, rgba(30, 40, 60, 0.5), rgba(30, 40, 60, 0.3));
                            border-left: 4px solid {cor_borda};
                            border-radius: 8px;
                            padding: 12px 16px;
                            margin-bottom: 10px;
                            display: flex;
                            align-items: center;
                            justify-content: space-between;
                        ">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <span style="font-size: 24px;">{medalhas[i]}</span>
                                <div>
                                    <div style="color: #FFFFFF; font-size: 16px; font-weight: 600;">{nome}</div>
                                    <div style="color: #ADB5BD; font-size: 13px;">{stats['escalacoes']} escalações</div>
                                </div>
                            </div>
                            <div style="text-align: right;">
                                <div style="color: {cor_borda}; font-size: 20px; font-weight: 700;">{stats['pontos']:.1f}</div>
                                <div style="color: #ADB5BD; font-size: 12px;">pontos</div>
                            </div>
                        </div>
                        ''', unsafe_allow_html=True)
            
            st.divider()
            
            # Tabela com resultados
            st.markdown('<h3>📋 Resultados por Rodada</h3>', unsafe_allow_html=True)
            st.dataframe(df_resultados, use_container_width=True, hide_index=True)
            
            # Exibir detalhes de cada rodada em expanders
            if detalhes_rodadas:
                st.divider()
                st.markdown('<h3>🔍 Detalhes por Rodada</h3>', unsafe_allow_html=True)
                st.markdown('<p style="color: #6C757D;">Clique em uma rodada para ver a escalação completa</p>', unsafe_allow_html=True)
                
                for rodada_num in sorted(detalhes_rodadas.keys()):
                    detalhe = detalhes_rodadas[rodada_num]
                    escalacao = detalhe['escalacao']
                    melhores = detalhe['melhores']
                    formacao_rod = detalhe['formacao']
                    
                    # Resumo para o título do expander
                    pts_real = escalacao.get('pontuacao_real', 0)
                    pts_ideal = melhores.get('pontuacao_total', 0)
                    cap_nome = escalacao.get('capitao', {}).get('apelido', 'N/A')
                    
                    with st.expander(f"🏆 Rodada {rodada_num} | {pts_real:.1f} pts | Formação: {formacao_rod} | Cap: {cap_nome}"):
                        col_esc, col_ideal = st.columns(2)
                        
                        with col_esc:
                            st.markdown('<div class="comparison-card comparison-card-orange">', unsafe_allow_html=True)
                            st.markdown('<h4>🎯 Escalação Sugerida</h4>', unsafe_allow_html=True)
                            
                            # Métricas
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                st.metric("Prevista", f"{escalacao.get('pontuacao_prevista', 0):.1f}")
                            with c2:
                                st.metric("Real", f"{pts_real:.1f}")
                            with c3:
                                st.metric("Custo", f"C$ {escalacao.get('custo_total', 0):.1f}")
                            
                            # Substituições
                            if escalacao.get('substituicoes'):
                                st.markdown('<p style="color: #54b4f7; font-size: 0.9rem;">🔄 Substituições:</p>', unsafe_allow_html=True)
                                for sub in escalacao['substituicoes']:
                                    tipo = '⭐ Luxo' if sub['tipo'] == 'reserva_luxo' else '🔄'
                                    st.markdown(f'<p style="color: #6C757D; font-size: 0.85rem;">{tipo}: {sub["saiu"]["apelido"]} → {sub["entrou"]["apelido"]}</p>', unsafe_allow_html=True)
                            
                            # Jogadores por posição
                            for pos_id in [1, 3, 2, 4, 5, 6]:
                                pos_jogadores = [t for t in escalacao.get('titulares', []) if t.get('pos_id') == pos_id]
                                if pos_jogadores:
                                    st.markdown(f'<span class="posicao-badge">{POSICAO_MAP.get(pos_id, "N/A")}</span>', unsafe_allow_html=True)
                                    for jogador in pos_jogadores:
                                        is_cap = jogador.get('atleta_id') == escalacao.get('capitao', {}).get('atleta_id')
                                        if jogador.get('substituido') and jogador.get('substituto'):
                                            exibir_jogador_card(jogador['substituto'], is_capitao=is_cap, 
                                                               mostrar_previsto_vs_real=True, substituido=True, mostrar_explicacao=True)
                                        else:
                                            exibir_jogador_card(jogador, is_capitao=is_cap, mostrar_previsto_vs_real=True, mostrar_explicacao=True)
                            
                            # Capitão
                            cap = escalacao.get('capitao', {})
                            if cap:
                                st.markdown(f'<p style="color: #FFD700; margin-top: 10px;">👑 Capitão: <strong>{cap.get("apelido", "N/A")}</strong> ({cap.get("pontos_reais", 0):.1f} pts x1.5)</p>', unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
                        
                        with col_ideal:
                            st.markdown('<div class="comparison-card comparison-card-green">', unsafe_allow_html=True)
                            st.markdown('<h4>🏆 Melhor Time Possível</h4>', unsafe_allow_html=True)
                            
                            # Métricas
                            c1, c2 = st.columns(2)
                            with c1:
                                st.metric("Pontuação", f"{pts_ideal:.1f}")
                            with c2:
                                st.metric("Custo", f"C$ {melhores.get('custo_total', 0):.1f}")
                            
                            # Jogadores por posição
                            for pos_id in [1, 3, 2, 4, 5, 6]:
                                pos_jogadores = [t for t in melhores.get('titulares', []) if t.get('pos_id') == pos_id]
                                if pos_jogadores:
                                    st.markdown(f'<span class="posicao-badge">{POSICAO_MAP.get(pos_id, "N/A")}</span>', unsafe_allow_html=True)
                                    for jogador in pos_jogadores:
                                        is_cap = melhores.get('capitao') and jogador.get('atleta_id') == melhores['capitao'].get('atleta_id')
                                        # Gerar justificativa de por que não foi escalado
                                        justificativa = gerar_justificativa_nao_escalado(jogador, escalacao)
                                        foi_escalado = justificativa['resumo'] == '✅ Escalado'
                                        cor_justificativa = justificativa['cor']
                                        
                                        st.markdown(f"""
                                        <div class="jogador-card {'capitao-card' if is_cap else ''}" style="border-left: 3px solid {cor_justificativa};">
                                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                                <div>
                                                    <span style="font-size: 1rem; font-weight: 600; color: #FFFFFF;">{"👑 " if is_cap else ""}{jogador.get('apelido', 'N/A')}</span>
                                                    <span style="margin-left: 8px;">{get_escudo_html(jogador.get('clube', ''), jogador.get('clube_id'), 18)}</span>
                                                </div>
                                                <div style="text-align: right;">
                                                    <span style="color: #FFFFFF; font-weight: 600;">C$ {jogador.get('preco', 0):.1f}</span>
                                                    <span style="color: #D4A84B; margin-left: 10px; font-weight: 700;">⚽ {jogador.get('pontos', 0):.1f}</span>
                                                </div>
                                            </div>
                                            <div style="margin-top: 5px; padding-top: 5px; border-top: 1px solid #333;">
                                                <span style="color: {cor_justificativa}; font-size: 0.85rem;">{justificativa['resumo']}</span>
                                                <p style="color: #9CA3AF; font-size: 0.75rem; margin: 2px 0 0 0;">{justificativa['motivo']}</p>
                                            </div>
                                        </div>
                                        """, unsafe_allow_html=True)
                            
                            # Capitão ideal
                            cap_ideal = melhores.get('capitao', {})
                            if cap_ideal:
                                st.markdown(f'<p style="color: #FFD700; margin-top: 10px;">👑 Capitão ideal: <strong>{cap_ideal.get("apelido", "N/A")}</strong> ({cap_ideal.get("pontos", 0):.1f} pts x1.5)</p>', unsafe_allow_html=True)
                            
                            st.markdown('</div>', unsafe_allow_html=True)
            
            # Botão para exportar Excel
            st.divider()
            st.markdown('<h3>📥 Exportar Resultados</h3>', unsafe_allow_html=True)
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_resultados.to_excel(writer, sheet_name='Resultados', index=False)
                
                # Adicionar aba de resumo
                resumo = pd.DataFrame({
                    'Métrica': ['Total Pontos', 'Média/Rodada', 'Capitães OK', 'Aproveitamento', 'Ano', 'Orçamento'],
                    'Valor': [f"{total_pts:.1f}", f"{media_pts:.1f}", f"{caps_ok}/{len(df_resultados)}", f"{aproveit:.1f}%", ano, f"C$ {orcamento:.1f}"]
                })
                resumo.to_excel(writer, sheet_name='Resumo', index=False)
            
            output.seek(0)
            st.download_button(
                label="📥 Baixar Excel",
                data=output,
                file_name=f"cartola_simulacao_{ano}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="download_excel_simulacao"
            )
        
        # Exibir resultados persistentes do session_state (após download ou rerun)
        elif st.session_state.get('simulacao_gerada', False):
            # Recuperar dados do session_state
            df_resultados = st.session_state.get('df_resultados_simulacao', pd.DataFrame())
            detalhes_rodadas = st.session_state.get('detalhes_rodadas', {})
            ano_salvo = st.session_state.get('simulacao_ano', ano)
            orcamento_salvo = st.session_state.get('simulacao_orcamento', orcamento)
            
            if not df_resultados.empty:
                st.success("✅ Processamento concluído!")
                
                # Métricas resumidas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    total_pts = df_resultados['Pts Escalado'].sum()
                    st.metric("Total Pontos", f"{total_pts:.1f}")
                with col2:
                    media_pts = df_resultados['Pts Escalado'].mean()
                    st.metric("Média/Rodada", f"{media_pts:.1f}")
                with col3:
                    caps_ok = (df_resultados['Cap OK'] == '✓').sum()
                    st.metric("Capitães OK", f"{caps_ok}/{len(df_resultados)}")
                with col4:
                    total_ideal = df_resultados['Pts Ideal'].sum()
                    aproveit = (total_pts / total_ideal * 100) if total_ideal > 0 else 0
                    st.metric("Aproveitamento", f"{aproveit:.1f}%")
                
                st.divider()
                
                # Gráfico de Linhas
                st.markdown('<h3>📈 Evolução por Rodada</h3>', unsafe_allow_html=True)
                
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=df_resultados['Rodada'],
                    y=df_resultados['Pts Ideal'],
                    mode='lines+markers',
                    name='Time Ideal',
                    line=dict(color='#FFD700', width=2, dash='dot'),
                    marker=dict(size=6)
                ))
                
                if 'Pts Previsto' in df_resultados.columns:
                    fig.add_trace(go.Scatter(
                        x=df_resultados['Rodada'],
                        y=df_resultados['Pts Previsto'],
                        mode='lines+markers',
                        name='Previsão',
                        line=dict(color='#28A745', width=2, dash='dash'),
                        marker=dict(size=6, symbol='diamond')
                    ))
                
                fig.add_trace(go.Scatter(
                    x=df_resultados['Rodada'],
                    y=df_resultados['Pts Escalado'],
                    mode='lines+markers',
                    name='Escalado (Real)',
                    line=dict(color='#54b4f7', width=3),
                    marker=dict(size=8),
                    fill='tozeroy',
                    fillcolor='rgba(255, 107, 0, 0.1)'
                ))
                
                fig.add_hline(y=90, line_dash="dash", line_color="#DC3545", annotation_text="Meta: 90")
                
                fig.update_layout(
                    title="Pontuação por Rodada",
                    xaxis_title="Rodada",
                    yaxis_title="Pontos",
                    template="plotly_dark",
                    height=400,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Análise por Posição e Justificativas
                if detalhes_rodadas:
                    st.divider()
                    
                    col_pos, col_just = st.columns(2)
                    
                    with col_pos:
                        # Calcular aproveitamento por posição
                        st.markdown('<h3>🎯 Aproveitamento por Posição</h3>', unsafe_allow_html=True)
                        
                        pos_stats = {pos: {'escalado': 0, 'ideal': 0} for pos in ['GOL', 'ZAG', 'LAT', 'MEI', 'ATA', 'TEC']}
                        pos_map_inv = {1: 'GOL', 2: 'LAT', 3: 'ZAG', 4: 'MEI', 5: 'ATA', 6: 'TEC'}
                        
                        for rodada_num, detalhe in detalhes_rodadas.items():
                            for t in detalhe['escalacao'].get('titulares', []):
                                pos = pos_map_inv.get(t.get('pos_id'), 'N/A')
                                if pos in pos_stats:
                                    pos_stats[pos]['escalado'] += t.get('pontos_reais', 0)
                            for t in detalhe['melhores'].get('titulares', []):
                                pos = pos_map_inv.get(t.get('pos_id'), 'N/A')
                                if pos in pos_stats:
                                    pos_stats[pos]['ideal'] += t.get('pontos', 0)
                        
                        posicoes = list(pos_stats.keys())
                        aproveitamentos = []
                        for pos in posicoes:
                            if pos_stats[pos]['ideal'] > 0:
                                aproveitamentos.append((pos_stats[pos]['escalado'] / pos_stats[pos]['ideal']) * 100)
                            else:
                                aproveitamentos.append(0)
                        
                        cores = ['#54b4f7' if a >= 50 else '#DC3545' for a in aproveitamentos]
                        
                        fig_pos = go.Figure(data=[
                            go.Bar(
                                x=posicoes,
                                y=aproveitamentos,
                                marker_color=cores,
                                text=[f'{a:.0f}%' for a in aproveitamentos],
                                textposition='outside',
                                hovertemplate='%{x}<br>Aproveitamento: %{y:.1f}%<extra></extra>'
                            )
                        ])
                        
                        fig_pos.add_hline(y=50, line_dash="dash", line_color="#FFD700", 
                                         annotation_text="50%", annotation_position="right")
                        
                        fig_pos.update_layout(
                            xaxis=dict(title='', color='#FFFFFF'),
                            yaxis=dict(title='Aproveitamento (%)', range=[0, 100], color='#FFFFFF', gridcolor='rgba(255,255,255,0.1)'),
                            plot_bgcolor='rgba(30, 40, 60, 0.3)',
                            paper_bgcolor='rgba(30, 40, 60, 0.3)',
                            margin=dict(l=40, r=40, t=20, b=40),
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig_pos, use_container_width=True)
                    
                    with col_just:
                        # Distribuição de Justificativas
                        st.markdown('<h3>📊 Distribuição de Justificativas</h3>', unsafe_allow_html=True)
                        
                        justificativas_count = {
                            'Recuperação': 0,
                            'Boa Fase': 0,
                            'Em Queda': 0,
                            'Premium': 0,
                            'Custo-Benefício': 0,
                            'Aposta': 0,
                            'Consistente': 0
                        }
                        
                        for rodada_num, detalhe in detalhes_rodadas.items():
                            for t in detalhe['escalacao'].get('titulares', []):
                                explicacao = t.get('explicacao', {})
                                resumo = explicacao.get('resumo', '') if explicacao else ''
                                if 'recuperação' in resumo.lower():
                                    justificativas_count['Recuperação'] += 1
                                elif 'boa fase' in resumo.lower():
                                    justificativas_count['Boa Fase'] += 1
                                elif 'queda' in resumo.lower():
                                    justificativas_count['Em Queda'] += 1
                                elif 'premium' in resumo.lower():
                                    justificativas_count['Premium'] += 1
                                elif 'custo' in resumo.lower():
                                    justificativas_count['Custo-Benefício'] += 1
                                elif 'aposta' in resumo.lower():
                                    justificativas_count['Aposta'] += 1
                                else:
                                    justificativas_count['Consistente'] += 1
                        
                        # Filtrar apenas justificativas com contagem > 0
                        labels = [k for k, v in justificativas_count.items() if v > 0]
                        values = [v for v in justificativas_count.values() if v > 0]
                        colors = ['#15367b', '#28A745', '#DC3545', '#FFD700', '#17A2B8', '#FFC107', '#6C757D']
                        
                        fig_just = go.Figure(data=[go.Pie(
                            labels=labels,
                            values=values,
                            hole=0.4,
                            marker_colors=colors[:len(labels)],
                            textinfo='label+percent',
                            textfont=dict(color='#FFFFFF'),
                            hovertemplate='%{label}<br>Quantidade: %{value}<br>%{percent}<extra></extra>'
                        )])
                        
                        fig_just.update_layout(
                            plot_bgcolor='rgba(30, 40, 60, 0.3)',
                            paper_bgcolor='rgba(30, 40, 60, 0.3)',
                            margin=dict(l=20, r=20, t=20, b=20),
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig_just, use_container_width=True)
                    
                    st.divider()
                    
                    # Gráficos de Formações e Top Jogadores
                    col_form, col_top = st.columns(2)
                    
                    with col_form:
                        # Formações Mais Escaladas
                        st.markdown('<h3>⚽ Formações Mais Escaladas</h3>', unsafe_allow_html=True)
                        
                        formacoes_count = {}
                        for rodada_num, detalhe in detalhes_rodadas.items():
                            formacao = detalhe.get('formacao', 'N/A')
                            formacoes_count[formacao] = formacoes_count.get(formacao, 0) + 1
                        
                        # Ordenar por quantidade
                        formacoes_sorted = sorted(formacoes_count.items(), key=lambda x: x[1], reverse=True)
                        formacoes_labels = [f[0] for f in formacoes_sorted]
                        formacoes_values = [f[1] for f in formacoes_sorted]
                        
                        fig_form = go.Figure(data=[
                            go.Bar(
                                x=formacoes_labels,
                                y=formacoes_values,
                                marker_color='#54b4f7',
                                text=formacoes_values,
                                textposition='outside',
                                hovertemplate='%{x}<br>Escalada: %{y} vezes<extra></extra>'
                            )
                        ])
                        
                        fig_form.update_layout(
                            xaxis=dict(title='', color='#FFFFFF'),
                            yaxis=dict(title='Quantidade', color='#FFFFFF', gridcolor='rgba(255,255,255,0.1)'),
                            plot_bgcolor='rgba(30, 40, 60, 0.3)',
                            paper_bgcolor='rgba(30, 40, 60, 0.3)',
                            margin=dict(l=40, r=40, t=20, b=40),
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig_form, use_container_width=True)
                    
                    with col_top:
                        # Top 5 Jogadores Mais Escalados
                        st.markdown('<h3>🏆 Top 5 Jogadores Mais Escalados</h3>', unsafe_allow_html=True)
                        
                        jogadores_stats = {}  # {nome: {'pontos': total, 'escalacoes': count}}
                        for rodada_num, detalhe in detalhes_rodadas.items():
                            for t in detalhe['escalacao'].get('titulares', []):
                                nome = t.get('apelido', 'Desconhecido')
                                pontos = t.get('pontos_reais', 0)
                                if nome not in jogadores_stats:
                                    jogadores_stats[nome] = {'pontos': 0, 'escalacoes': 0}
                                jogadores_stats[nome]['pontos'] += pontos
                                jogadores_stats[nome]['escalacoes'] += 1
                        
                        # Top 5 por pontos totais
                        top5 = sorted(jogadores_stats.items(), key=lambda x: x[1]['pontos'], reverse=True)[:5]
                        
                        # Medalhas
                        medalhas = ['🥇', '🥈', '🥉', '🏅', '🏅']
                        
                        # Exibir lista estilizada
                        for i, (nome, stats) in enumerate(top5):
                            cor_borda = '#FFD700' if i == 0 else '#C0C0C0' if i == 1 else '#CD7F32' if i == 2 else '#54b4f7'
                            st.markdown(f'''
                            <div style="
                                background: linear-gradient(135deg, rgba(30, 40, 60, 0.5), rgba(30, 40, 60, 0.3));
                                border-left: 4px solid {cor_borda};
                                border-radius: 8px;
                                padding: 12px 16px;
                                margin-bottom: 10px;
                                display: flex;
                                align-items: center;
                                justify-content: space-between;
                            ">
                                <div style="display: flex; align-items: center; gap: 12px;">
                                    <span style="font-size: 24px;">{medalhas[i]}</span>
                                    <div>
                                        <div style="color: #FFFFFF; font-size: 16px; font-weight: 600;">{nome}</div>
                                        <div style="color: #ADB5BD; font-size: 13px;">{stats['escalacoes']} escalações</div>
                                    </div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="color: {cor_borda}; font-size: 20px; font-weight: 700;">{stats['pontos']:.1f}</div>
                                    <div style="color: #ADB5BD; font-size: 12px;">pontos</div>
                                </div>
                            </div>
                            ''', unsafe_allow_html=True)
                
                st.divider()
                
                # Tabela com resultados
                st.markdown('<h3>📋 Resultados por Rodada</h3>', unsafe_allow_html=True)
                st.dataframe(df_resultados, use_container_width=True, hide_index=True)
                
                # Botão para exportar Excel
                st.divider()
                st.markdown('<h3>📥 Exportar Resultados</h3>', unsafe_allow_html=True)
                
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_resultados.to_excel(writer, sheet_name='Resultados', index=False)
                    resumo = pd.DataFrame({
                        'Métrica': ['Total Pontos', 'Média/Rodada', 'Capitães OK', 'Aproveitamento', 'Ano', 'Orçamento'],
                        'Valor': [f"{total_pts:.1f}", f"{media_pts:.1f}", f"{caps_ok}/{len(df_resultados)}", f"{aproveit:.1f}%", ano_salvo, f"C$ {orcamento_salvo:.1f}"]
                    })
                    resumo.to_excel(writer, sheet_name='Resumo', index=False)
                
                output.seek(0)
                st.download_button(
                    label="📥 Baixar Excel",
                    data=output,
                    file_name=f"cartola_simulacao_{ano_salvo}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="download_excel_persistente"
                )
        
        return
    
    # Modo: Rodada Específica (código original)
    
    # Carregar dados fora das colunas para usar em ambas as seções
    df_anterior = carregar_dados_rodada_anterior(ano, rodada)
    df_atual = carregar_dados_historicos(ano, rodada)
    
    # Calcular escalação uma única vez para usar em ambas as seções
    escalacao_calculada = None
    formacao_usada = '4-3-3'
    
    if df_anterior is not None and df_atual is not None:
        if formacao_selecionada == 'Automática (Melhor)':
            # Testar todas as formações e escolher a melhor
            melhor_escalacao = None
            melhor_pontuacao = -1
            melhor_formacao = '4-3-3'
            
            for form in FORMACOES.keys():
                try:
                    esc = escalar_com_dados_anteriores(df_anterior, df_atual, form, orcamento, ano=ano, rodada=rodada)
                    if esc and esc.get('pontuacao_real', 0) > melhor_pontuacao:
                        melhor_pontuacao = esc.get('pontuacao_real', 0)
                        melhor_escalacao = esc
                        melhor_formacao = form
                except:
                    continue
            
            escalacao_calculada = melhor_escalacao
            formacao_usada = melhor_formacao
        else:
            formacao_usada = formacao_selecionada
            escalacao_calculada = escalar_com_dados_anteriores(df_anterior, df_atual, formacao_usada, orcamento, ano=ano, rodada=rodada)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="comparison-card">', unsafe_allow_html=True)
        st.markdown('<h3>🎯 Escalação Sugerida</h3>', unsafe_allow_html=True)
        st.markdown('<p style="color: #6C757D;">Baseada nos dados da rodada anterior</p>', unsafe_allow_html=True)
        
        if df_anterior is None:
            st.warning(f"Dados da rodada {rodada-1} não disponíveis")
        elif df_atual is None:
            st.warning(f"Dados da rodada {rodada} não disponíveis")
        else:
            # Usar a escalação já calculada
            escalacao = escalacao_calculada
            formacao = formacao_usada
            
            if formacao_selecionada == 'Automática (Melhor)' and escalacao:
                st.info(f"🏆 Melhor formação encontrada: **{formacao}**")
            
            if escalacao:
                col_m1, col_m2, col_m3 = st.columns([1.2, 1.2, 1])
                with col_m1:
                    st.metric("Prevista", f"{escalacao['pontuacao_prevista']:.1f} pts")
                with col_m2:
                    st.metric("Real", f"{escalacao['pontuacao_real']:.1f} pts")
                with col_m3:
                    st.metric("Custo", f"C$ {escalacao['custo_total']:.1f}")
                
                st.divider()
                
                # Mostrar substituições se houver
                if escalacao.get('substituicoes'):
                    st.markdown('<p style="color: #54b4f7; font-size: 0.9rem;">🔄 Substituições aplicadas:</p>', unsafe_allow_html=True)
                    for sub in escalacao['substituicoes']:
                        tipo = '⭐ Luxo' if sub['tipo'] == 'reserva_luxo' else '🔄'
                        st.markdown(f'<p style="color: #6C757D; font-size: 0.85rem;">{tipo}: {sub["saiu"]["apelido"]} → {sub["entrou"]["apelido"]}</p>', unsafe_allow_html=True)
                    st.divider()
                
                for pos_id in [1, 3, 2, 4, 5, 6]:
                    pos_jogadores = [t for t in escalacao['titulares'] if t['pos_id'] == pos_id]
                    if pos_jogadores:
                        st.markdown(f'<span class="posicao-badge">{POSICAO_MAP[pos_id]}</span>', unsafe_allow_html=True)
                        for jogador in pos_jogadores:
                            is_cap = jogador['atleta_id'] == escalacao['capitao']['atleta_id']
                            # Se foi substituído, mostrar o substituto
                            if jogador.get('substituido') and jogador.get('substituto'):
                                exibir_jogador_card(jogador['substituto'], is_capitao=is_cap, 
                                                   mostrar_previsto_vs_real=True, substituido=True)
                            else:
                                exibir_jogador_card(jogador, is_capitao=is_cap, mostrar_previsto_vs_real=True)
                
                st.markdown(f'<p style="color: #FFD700; margin-top: 15px;">👑 Capitão: <strong>{escalacao["capitao"]["apelido"]}</strong> ({escalacao["capitao"]["pontos_reais"]:.1f} pts x1.5)</p>', unsafe_allow_html=True)
                
                # Mostrar reservas
                if escalacao.get('reservas'):
                    with st.expander("💺 Reservas"):
                        for pos_id, reserva in escalacao['reservas'].items():
                            if reserva:
                                st.markdown(f"**{POSICAO_MAP.get(pos_id, 'N/A')}**: {reserva['apelido']} (C$ {reserva['preco']:.1f}) - {reserva['pontos_reais']:.1f} pts")
                
                # Mostrar reserva de luxo
                if escalacao.get('reserva_luxo'):
                    rl = escalacao['reserva_luxo']
                    st.markdown(f'<p style="color: #FFD700; margin-top: 10px;">⭐ Reserva de Luxo: <strong>{rl["apelido"]}</strong> ({rl["pontos_reais"]:.1f} pts)</p>', unsafe_allow_html=True)
            else:
                st.error("Não foi possível escalar o time com o orçamento disponível")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="comparison-card comparison-card-green">', unsafe_allow_html=True)
        st.markdown('<h3>🏆 Melhor Time Possível</h3>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: #6C757D;">Melhor escalação possível dentro do orçamento (C$ {orcamento:.0f})</p>', unsafe_allow_html=True)
        
        if df_atual is not None:
            # Melhor time possível DENTRO do orçamento
            melhores = obter_melhores_reais(df_atual, formacao, orcamento, respeitar_orcamento=True)
            
            if melhores:
                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.metric("Pontuação Máxima", f"{melhores['pontuacao_total']:.1f} pts")
                with col_m2:
                    st.metric("Custo Total", f"C$ {melhores['custo_total']:.1f}")
                
                st.divider()
                
                for pos_id in [1, 3, 2, 4, 5, 6]:
                    pos_jogadores = [t for t in melhores['titulares'] if t['pos_id'] == pos_id]
                    if pos_jogadores:
                        st.markdown(f'<span class="posicao-badge">{POSICAO_MAP[pos_id]}</span>', unsafe_allow_html=True)
                        for jogador in pos_jogadores:
                            is_cap = melhores['capitao'] and jogador['atleta_id'] == melhores['capitao']['atleta_id']
                            # Gerar justificativa de por que não foi escalado
                            justificativa = gerar_justificativa_nao_escalado(jogador, escalacao_calculada, df_anterior)
                            cor_justificativa = justificativa['cor']
                            
                            st.markdown(f"""
                            <div class="jogador-card {'capitao-card' if is_cap else ''}" style="border-left: 3px solid {cor_justificativa};">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <span style="font-size: 1.1rem; font-weight: 600; color: #FFFFFF;">{'👑 ' if is_cap else ''}{jogador['apelido']}</span>
                                        <span style="margin-left: 10px;">{get_escudo_html(jogador.get('clube', ''), jogador.get('clube_id'))}</span>
                                    </div>
                                    <div style="text-align: right;">
                                        <span style="color: #FFFFFF; font-weight: 600;">C$ {jogador['preco']:.1f}</span>
                                        <span style="color: #D4A84B; margin-left: 15px; font-weight: 700; font-size: 1.2rem;">⚽ {jogador['pontos']:.1f}</span>
                                    </div>
                                </div>
                                <div style="margin-top: 5px; padding-top: 5px; border-top: 1px solid #333;">
                                    <span style="color: {cor_justificativa}; font-size: 0.85rem;">{justificativa['resumo']}</span>
                                    <p style="color: #9CA3AF; font-size: 0.75rem; margin: 2px 0 0 0;">{justificativa['motivo']}</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                if melhores['capitao']:
                    st.markdown(f'<p style="color: #FFD700; margin-top: 15px;">👑 Capitão ideal: <strong>{melhores["capitao"]["apelido"]}</strong> ({melhores["capitao"]["pontos"]:.1f} pts x1.5)</p>', unsafe_allow_html=True)
        else:
            st.warning("Dados não disponíveis")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    st.markdown('<h3>📊 Comparação</h3>', unsafe_allow_html=True)
    
    if df_anterior is not None and df_atual is not None and escalacao_calculada is not None:
        # Usar a mesma escalação já calculada para consistência
        escalacao = escalacao_calculada
        melhores = obter_melhores_reais(df_atual, formacao_usada, orcamento, respeitar_orcamento=True)
        
        if escalacao and melhores:
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Pontuação Prevista", f"{escalacao['pontuacao_prevista']:.1f} pts")
            
            with col2:
                st.metric("Pontuação Real", f"{escalacao['pontuacao_real']:.1f} pts")
            
            with col3:
                st.metric("Pontuação Máxima", f"{melhores['pontuacao_total']:.1f} pts")
            
            with col4:
                aproveitamento = (escalacao['pontuacao_real'] / melhores['pontuacao_total'] * 100) if melhores['pontuacao_total'] > 0 else 0
                st.metric("Aproveitamento", f"{aproveitamento:.1f}%")
            
            with col5:
                ids_escalados = set(t['atleta_id'] for t in escalacao['titulares'])
                ids_melhores = set(t['atleta_id'] for t in melhores['titulares'])
                acertos = ids_escalados.intersection(ids_melhores)
                st.metric("Acertos", f"{len(acertos)}/12")
            
            if acertos:
                nomes_acertos = [t['apelido'] for t in escalacao['titulares'] if t['atleta_id'] in acertos]
                st.success(f"🎯 Jogadores acertados: {', '.join(nomes_acertos)}")


def pagina_escalacao():
    """Página principal de escalação."""
    st.markdown('<h1>🎩 Escalação Automática</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #6C757D; font-size: 1.1rem;">Estratégia v7 - Validada com <span style="color: #54b4f7; font-weight: 600;">94.1 pts/rodada</span> (+24.4% vs v6)</p>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown('<h3 style="color: #54b4f7;">⚙️ Configurações</h3>', unsafe_allow_html=True)
        
        config = carregar_config()
        
        st.markdown('<p style="color: #FFFFFF; font-weight: 500;">💰 Orçamento</p>', unsafe_allow_html=True)
        orcamento = st.number_input(
            "Cartoletas disponíveis (C$)",
            min_value=0.0,
            max_value=500.0,
            value=float(config.get('orcamento', 100.0)),
            step=0.5,
            help="Informe o valor de cartoletas que você tem disponível",
            label_visibility="collapsed"
        )
        
        st.markdown('<p style="color: #FFFFFF; font-weight: 500; margin-top: 15px;">📋 Formação</p>', unsafe_allow_html=True)
        opcoes_formacao = ["Automático (Recomendada)"] + list(FORMACOES.keys())
        formacao_selecionada = st.selectbox(
            "Escolha a formação",
            opcoes_formacao,
            index=0,
            help="Deixe em 'Automático' para o sistema recomendar a melhor formação",
            label_visibility="collapsed"
        )
        
        formacao_preferida = None if formacao_selecionada == "Automático (Recomendada)" else formacao_selecionada
        
        if st.button("💾 Salvar Configurações", use_container_width=True):
            config['orcamento'] = orcamento
            config['formacao_preferida'] = formacao_preferida
            salvar_config(config)
            st.success("✅ Configurações salvas!")
        
        st.divider()
        
        rodada = buscar_rodada_atual()
        st.metric("📅 Rodada Atual", rodada)
    
    with st.spinner("🔄 Buscando dados do mercado..."):
        mercado = buscar_mercado()
    
    if mercado is None or len(mercado) == 0:
        st.markdown("""
        <div class="warning-box">
            <h4>⚠️ Mercado Fechado</h4>
            <p>Não foi possível carregar os dados do mercado. O mercado pode estar fechado.</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="info-box">
            <h4>💡 Dica</h4>
            <p>Use a página <strong>Simulação Histórica</strong> para testar a estratégia com dados de 2025!</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.success(f"✅ {len(mercado)} jogadores disponíveis no mercado")
    
    estrategia = EstrategiaV7()
    estrategia.orcamento = orcamento
    
    # Determinar ano atual baseado na data
    from datetime import datetime
    ano_atual = datetime.now().year
    ano_anterior = ano_atual - 1
    
    # Carregar histórico usando MESMA LÓGICA da simulação histórica
    # 1. Primeiro carregar TODO o histórico do ANO ANTERIOR como base
    for r in range(1, 39):
        df_hist = carregar_dados_historicos(ano_anterior, r)
        if df_hist is not None:
            estrategia.atualizar_historico(df_hist)
    
    # 2. Carregar rodadas anteriores do ANO ATUAL (se houver)
    if rodada > 1:
        for r in range(1, rodada):
            df_hist = carregar_dados_historicos(ano_atual, r)
            if df_hist is not None:
                estrategia.atualizar_historico(df_hist)
    
    estrategia.rodada_atual = rodada
    
    # Botão para gerar nova escalação
    col_escalar, col_limpar = st.columns([3, 1])
    with col_escalar:
        if st.button("🎯 Escalar Time", type="primary", use_container_width=True):
            with st.spinner("🔄 Analisando formações e escalando time..."):
                resultados = estrategia.analisar_todas_formacoes(mercado, orcamento)
            
            if not resultados:
                st.error("❌ Não foi possível escalar o time. Verifique o orçamento.")
            else:
                if formacao_preferida:
                    escalacao = next(
                        (r for r in resultados if r['formacao'] == formacao_preferida),
                        resultados[0]
                    )
                else:
                    escalacao = resultados[0]
                
                # Armazenar escalação atual no session_state
                st.session_state.escalacao_para_confirmar = escalacao
                st.session_state.escalacao_ano = ano_atual
                st.session_state.escalacao_rodada = rodada
                st.session_state.escalacao_orcamento = orcamento
                st.session_state.mercado_atual = mercado
                st.session_state.estrategia_atual = estrategia  # Salvar estratégia com histórico
                # Limpar escalação atualizada anterior
                if 'escalacao_atualizada' in st.session_state:
                    del st.session_state.escalacao_atualizada
                st.rerun()
    
    with col_limpar:
        if st.session_state.get('escalacao_para_confirmar'):
            if st.button("🗑️ Limpar", use_container_width=True):
                if 'escalacao_para_confirmar' in st.session_state:
                    del st.session_state.escalacao_para_confirmar
                if 'escalacao_atualizada' in st.session_state:
                    del st.session_state.escalacao_atualizada
                if 'escalacao_confirmada' in st.session_state:
                    del st.session_state.escalacao_confirmada
                st.rerun()
    
    # Exibir escalação se existir no session_state
    if st.session_state.get('escalacao_para_confirmar'):
        escalacao = st.session_state.escalacao_para_confirmar
        mercado = st.session_state.get('mercado_atual', mercado)
        
        st.markdown(f'<h2>🏆 Escalação Recomendada: {escalacao["formacao"]}</h2>', unsafe_allow_html=True)
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Pontuação Esperada", f"{escalacao['pontuacao_esperada']:.1f} pts")
        with col2:
            st.metric("Custo Total", f"C$ {escalacao['custo_total']:.2f}")
        with col3:
            st.metric("Orçamento Restante", f"C$ {escalacao['orcamento_restante']:.2f}")
        with col4:
            valorizacao_total = escalacao.get('valorizacao_total', 0)
            delta_color = "normal" if valorizacao_total >= 0 else "inverse"
            st.metric("Valorização Total", f"{valorizacao_total:+.1f}", delta_color=delta_color)
        with col5:
            st.metric("Jogadores", len(escalacao['titulares']))
        
        st.divider()
        
        st.markdown('<h3>📋 Titulares</h3>', unsafe_allow_html=True)
        
        for pos_id in [1, 3, 2, 4, 5, 6]:
            pos_jogadores = [t for t in escalacao['titulares'] if t['pos_id'] == pos_id]
            if pos_jogadores:
                st.markdown(f'<span class="posicao-badge">{POSICAO_MAP[pos_id]}</span>', unsafe_allow_html=True)
                for jogador in pos_jogadores:
                    is_cap = escalacao['capitao'] and jogador['atleta_id'] == escalacao['capitao']['atleta_id']
                    exibir_jogador_card(jogador, is_capitao=is_cap)
        
        # Seção de Reservas
        st.divider()
        st.markdown('<h3>💺 Reservas</h3>', unsafe_allow_html=True)
        
        # Exibir reservas por posição (apenas posições que existem na formação)
        if escalacao.get('reservas'):
            reservas = escalacao['reservas']
            # Filtrar apenas posições que têm reserva (baseado na formação)
            pos_map_reservas = {1: 'GOL', 2: 'LAT', 3: 'ZAG', 4: 'MEI', 5: 'ATA'}
            posicoes_com_reserva = [pos_id for pos_id in [1, 2, 3, 4, 5] 
                                    if reservas.get(pos_id) or reservas.get(str(pos_id))]
            
            if posicoes_com_reserva:
                cols_reservas = st.columns(len(posicoes_com_reserva))
                for idx, pos_id in enumerate(posicoes_com_reserva):
                    with cols_reservas[idx]:
                        reserva = reservas.get(pos_id) or reservas.get(str(pos_id))
                        pos_nome = pos_map_reservas.get(pos_id, 'N/A')
                        
                        # Verificar se é reserva de luxo
                        is_luxo = reserva.get('is_reserva_luxo', False)
                        
                        # Obter nome do clube
                        clube_nome = reserva.get('clube', '')
                        
                        if is_luxo:
                            # Card especial para reserva de luxo
                            st.markdown(f'''
                            <div style="background: linear-gradient(135deg, #744210 0%, #5C3D0E 100%); 
                                        border: 2px solid #D69E2E; border-radius: 10px; padding: 10px; text-align: center; margin: 5px 0;">
                                <span style="color: #F6E05E; font-size: 0.8em;">⭐ {pos_nome}</span><br>
                                <span style="color: #FEFCBF; font-weight: bold;">{reserva['apelido']}</span><br>
                                <span style="font-size: 0.75em;">{get_escudo_html(clube_nome, reserva.get('clube_id'), 16)}</span><br>
                                <span style="color: #68D391;">C$ {reserva['preco']:.1f}</span>
                            </div>
                            ''', unsafe_allow_html=True)
                        else:
                            # Card normal para reserva
                            st.markdown(f'''
                            <div style="background: linear-gradient(135deg, #2D3748 0%, #1A202C 100%); 
                                        border-radius: 10px; padding: 10px; text-align: center; margin: 5px 0;">
                                <span style="color: #A0AEC0; font-size: 0.8em;">{pos_nome}</span><br>
                                <span style="color: #E2E8F0; font-weight: bold;">{reserva['apelido']}</span><br>
                                <span style="font-size: 0.75em;">{get_escudo_html(clube_nome, reserva.get('clube_id'), 16)}</span><br>
                                <span style="color: #68D391;">C$ {reserva['preco']:.1f}</span>
                            </div>
                            ''', unsafe_allow_html=True)
            else:
                st.info("Nenhum reserva disponível")
        else:
            st.info("Nenhum reserva disponível")
        
        # Seção de Substituição Manual
        st.divider()
        st.markdown('<h3>🔄 Substituição Manual</h3>', unsafe_allow_html=True)
        st.markdown('<p style="color: #6C757D;">Se algum jogador não vai jogar, selecione-o para substituir:</p>', unsafe_allow_html=True)
        
        # Criar lista de jogadores para seleção
        jogadores_escalados = [(t['atleta_id'], f"{t['apelido']} ({POSICAO_MAP.get(t['pos_id'], '')})") for t in escalacao['titulares']]
        
        # Inicializar session_state para substituições se não existir
        if 'substituicoes_manuais' not in st.session_state:
            st.session_state.substituicoes_manuais = {}
        
        # Multiselect para escolher jogadores a substituir
        jogadores_para_substituir = st.multiselect(
            "Selecione os jogadores que NÃO vão jogar:",
            options=[j[0] for j in jogadores_escalados],
            format_func=lambda x: next((j[1] for j in jogadores_escalados if j[0] == x), x),
            key="jogadores_substituir"
        )
        
        if jogadores_para_substituir:
            col_aplicar, col_cancelar = st.columns(2)
            with col_aplicar:
                if st.button("🔄 Aplicar Substituições", type="secondary", use_container_width=True):
                    import copy
                    escalacao_atualizada = copy.deepcopy(escalacao)
                    
                    # Usar orçamento salvo no session_state
                    orcamento_salvo = st.session_state.get('escalacao_orcamento', orcamento)
                    
                    # Usar estratégia salva (com histórico carregado) ou criar nova
                    estrategia_subst = st.session_state.get('estrategia_atual')
                    if estrategia_subst is None:
                        # Fallback: criar nova estratégia e carregar histórico
                        estrategia_subst = EstrategiaV7()
                        ano_atual = st.session_state.get('escalacao_ano', datetime.now().year)
                        ano_anterior = ano_atual - 1
                        # Carregar histórico do ano anterior
                        for r in range(1, 39):
                            df_hist = carregar_dados_historicos(ano_anterior, r)
                            if df_hist is not None:
                                estrategia_subst.atualizar_historico(df_hist)
                    
                    erros_substituicao = []
                    
                    # Criar set com todos os IDs sendo substituídos (para evitar reselecionar)
                    ids_sendo_substituidos = set(str(jid) for jid in jogadores_para_substituir)
                    
                    for jogador_id in jogadores_para_substituir:
                        # Aplicar substituição com estratégia para justificativa
                        # Passa todos os IDs sendo substituídos para evitar reselecionar
                        escalacao_atualizada = substituir_jogador_manual(
                            escalacao_atualizada, 
                            jogador_id, 
                            mercado, 
                            orcamento_salvo,
                            estrategia=estrategia_subst,
                            ids_a_excluir=ids_sendo_substituidos
                        )
                        
                        # Verificar se houve erro na substituição
                        if 'erro_substituicao' in escalacao_atualizada:
                            erro = escalacao_atualizada.pop('erro_substituicao')
                            # Encontrar nome do jogador
                            nome_jogador = next(
                                (t['apelido'] for t in escalacao['titulares'] if str(t['atleta_id']) == str(erro['jogador_id'])),
                                'Jogador'
                            )
                            erros_substituicao.append(f"{nome_jogador}: {erro['motivo']}")
                    
                    # REOTIMIZAÇÃO: Se sobrou orçamento, verificar se há upgrades possíveis
                    df_ranqueado = escalacao_atualizada.get('df_ranqueado')
                    
                    # Fallback: se df_ranqueado não existe, usar mercado
                    if df_ranqueado is None and mercado is not None:
                        df_ranqueado = mercado.copy()
                        # Adicionar coluna score se não existir
                        if 'score' not in df_ranqueado.columns:
                            df_ranqueado['score'] = df_ranqueado.get('media_num', df_ranqueado.get('media', 0))
                    
                    if df_ranqueado is not None and escalacao_atualizada.get('orcamento_restante', 0) > 0:
                        escalacao_atualizada = reotimizar_orcamento(
                            escalacao_atualizada,
                            df_ranqueado,
                            orcamento_salvo
                        )
                    
                    # RECALCULAR RESERVAS: Após substituições, recalcular reservas e reserva de luxo
                    if df_ranqueado is not None:
                        try:
                            escalacao_atualizada = recalcular_reservas(
                                escalacao_atualizada,
                                df_ranqueado,
                                estrategia=st.session_state.get('estrategia_atual')
                            )
                        except Exception as e:
                            print(f"Erro ao recalcular reservas: {e}")
                    else:
                        print("AVISO: df_ranqueado não disponível para recalcular reservas")
                    
                    # VERIFICAR MELHOR FORMAÇÃO: Após substituições, outra formação pode ser melhor
                    formacao_atual = escalacao_atualizada.get('formacao', '4-3-3')
                    estrategia_salva = st.session_state.get('estrategia_atual')
                    ids_removidos = [str(jid) for jid in jogadores_para_substituir]
                    
                    if estrategia_salva and df_ranqueado is not None:
                        try:
                            resultado_formacao = verificar_melhor_formacao(
                                df_mercado=df_ranqueado,
                                orcamento=orcamento_salvo,
                                formacao_atual=formacao_atual,
                                estrategia=estrategia_salva,
                                jogadores_excluidos=ids_removidos
                            )
                            
                            if resultado_formacao.get('mudou_formacao') and resultado_formacao.get('melhor_escalacao'):
                                # Guardar sugestão de nova formação para exibir
                                st.session_state.sugestao_formacao = resultado_formacao
                        except Exception as e:
                            # Se falhar, continuar sem sugestão de formação
                            pass
                    
                    # Salvar escalação atualizada
                    st.session_state.escalacao_atualizada = escalacao_atualizada
                    
                    # Mostrar resultado
                    melhorias = escalacao_atualizada.get('melhorias_orcamento', [])
                    sugestao_formacao = st.session_state.get('sugestao_formacao')
                    
                    if erros_substituicao:
                        st.warning(f"⚠️ Não foi possível substituir alguns jogadores:\n" + "\n".join(erros_substituicao))
                        st.info("💡 Dica: Na primeira rodada, não há dados históricos para previsão. Aguarde as próximas rodadas para substituições mais precisas.")
                    elif melhorias:
                        msg_melhorias = "\n".join([f"⬆️ {m['de']} → {m['para']} (+{m['ganho_score']:.2f} score)" for m in melhorias])
                        st.success(f"✅ Substituições aplicadas!\n\n💰 Orçamento liberado permitiu upgrades:\n{msg_melhorias}")
                    else:
                        st.success("✅ Substituições aplicadas!")
                    
                    # Mostrar sugestão de formação se houver
                    if sugestao_formacao and sugestao_formacao.get('mudou_formacao'):
                        st.info(sugestao_formacao.get('mensagem', ''))
                    
                    st.rerun()
            with col_cancelar:
                if st.button("❌ Cancelar Seleção", type="primary", use_container_width=True):
                    # Limpar a seleção do multiselect
                    st.session_state.jogadores_substituir = []
                    st.rerun()
        
        # Mostrar sugestão de nova formação se houver
        if 'sugestao_formacao' in st.session_state and st.session_state.sugestao_formacao.get('mudou_formacao'):
            sugestao = st.session_state.sugestao_formacao
            st.divider()
            st.markdown('<h3>💡 Sugestão de Formação</h3>', unsafe_allow_html=True)
            
            # Mensagem principal
            st.info(sugestao.get('mensagem', ''))
            
            # Comparativo de formações
            comparativo = sugestao.get('comparativo', [])
            if comparativo:
                st.markdown('**Comparativo de Formações:**')
                for item in comparativo[:5]:  # Top 5 formações
                    icone = '🏆' if item.get('melhor') else ('👉' if item.get('atual') else '')
                    st.markdown(f"{icone} **{item['formacao']}**: {item['score']:.2f} pts (C$ {item['custo']:.2f})")
            
            # Botões para aceitar ou ignorar
            col_aceitar, col_ignorar = st.columns(2)
            with col_aceitar:
                if st.button('✅ Aceitar Nova Formação', type='primary', use_container_width=True):
                    # Aplicar a nova escalação
                    nova_escalacao = sugestao.get('melhor_escalacao')
                    if nova_escalacao:
                        st.session_state.escalacao_atualizada = nova_escalacao
                        del st.session_state.sugestao_formacao
                        st.success(f"✅ Formação alterada para {sugestao.get('melhor_formacao')}!")
                        st.rerun()
            with col_ignorar:
                if st.button('❌ Manter Formação Atual', use_container_width=True):
                    del st.session_state.sugestao_formacao
                    st.rerun()
        
        # Mostrar escalação atualizada se houver
        if 'escalacao_atualizada' in st.session_state:
            st.divider()
            st.markdown('<h3>📋 Escalação Atualizada</h3>', unsafe_allow_html=True)
            
            esc_atual = st.session_state.escalacao_atualizada
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Pontuação Esperada", f"{esc_atual.get('pontuacao_esperada', 0):.1f} pts")
            with col2:
                st.metric("Custo Total", f"C$ {esc_atual.get('custo_total', 0):.2f}")
            with col3:
                st.metric("Orçamento Restante", f"C$ {esc_atual.get('orcamento_restante', 0):.2f}")
            with col4:
                valorizacao_total = esc_atual.get('valorizacao_total', 0)
                delta_color = "normal" if valorizacao_total >= 0 else "inverse"
                st.metric("Valorização Total", f"{valorizacao_total:+.1f}", delta_color=delta_color)
            
            for pos_id in [1, 3, 2, 4, 5, 6]:
                pos_jogadores = [t for t in esc_atual['titulares'] if t['pos_id'] == pos_id]
                if pos_jogadores:
                    st.markdown(f'<span class="posicao-badge">{POSICAO_MAP[pos_id]}</span>', unsafe_allow_html=True)
                    for jogador in pos_jogadores:
                        is_cap = esc_atual.get('capitao') and jogador['atleta_id'] == esc_atual['capitao']['atleta_id']
                        exibir_jogador_card(jogador, is_capitao=is_cap)
            
            # Exibir reservas se houver
            reservas = esc_atual.get('reservas', {})
            reserva_luxo = esc_atual.get('reserva_luxo')
            
            # Debug: mostrar se há reservas
            st.divider()
            if reservas or reserva_luxo:
                st.markdown('<h4>🔄 Reservas</h4>', unsafe_allow_html=True)
                
                # Exibir reservas normais
                for pos_id, reserva in reservas.items():
                    if reserva and not reserva.get('is_reserva_luxo'):
                        exibir_jogador_card(reserva, is_capitao=False)
                
                # Exibir reserva de luxo
                if reserva_luxo:
                    st.markdown('<h4>⭐ Reserva de Luxo</h4>', unsafe_allow_html=True)
                    exibir_jogador_card(reserva_luxo, is_capitao=False)
            else:
                st.info('💡 Reservas serão calculados após a substituição.')
            
            if st.button("🗑️ Limpar Substituições", use_container_width=True):
                del st.session_state.escalacao_atualizada
                st.rerun()
        
        # Botão de confirmação da escalação final
        st.divider()
        st.markdown('<h3>✅ Confirmar Escalação Final</h3>', unsafe_allow_html=True)
        st.markdown('<p style="color: #6C757D;">Clique no botão abaixo para salvar a escalação que será utilizada na rodada. Isso registra para o aprendizado contínuo.</p>', unsafe_allow_html=True)
        
        # Determinar qual escalação confirmar (atualizada ou original)
        escalacao_final = st.session_state.get('escalacao_atualizada', st.session_state.get('escalacao_para_confirmar'))
        
        if escalacao_final:
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ Confirmar Escalação Final", type="primary", use_container_width=True):
                    try:
                        aprendizagem = AprendizagemContinua()
                        arquivo_salvo = aprendizagem.salvar_escalacao_detalhada(
                            ano=st.session_state.get('escalacao_ano', 2026),
                            rodada=st.session_state.get('escalacao_rodada', 1),
                            escalacao=escalacao_final,
                            formacao=escalacao_final.get('formacao', '4-3-3'),
                            orcamento=st.session_state.get('escalacao_orcamento', 100)
                        )
                        st.success("📊 Escalação confirmada e salva para aprendizado contínuo!")
                        st.session_state.escalacao_confirmada = True
                    except Exception as e:
                        st.error(f"Erro ao salvar escalação: {e}")
            
            with col_btn2:
                if st.session_state.get('escalacao_confirmada'):
                    st.info("🎯 Escalação já confirmada para esta rodada")


def carregar_escalacao_salva(ano: int, rodada: int) -> Dict:
    """Carrega a escalação salva para uma rodada específica."""
    arquivo = Path(f'escalacoes_detalhadas/{ano}/rodada-{rodada}.json')
    if arquivo.exists():
        with open(arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def calcular_time_ideal(ano: int, rodada: int, orcamento: float) -> Dict:
    """Calcula o time ideal para uma rodada com base nos pontos reais."""
    from app import carregar_dados_historicos, carregar_dados_rodada_anterior
    
    # Carregar dados reais da rodada
    df_atual = carregar_dados_historicos(ano, rodada)
    if df_atual is None:
        return None
    
    # Carregar histórico anterior
    df_anterior = carregar_dados_rodada_anterior(ano, rodada)
    
    # Escalar usando a estratégia com dados reais
    # modo_simulacao=True pois estamos calculando time ideal histórico
    estrategia = EstrategiaV7(modo_simulacao=True)
    if df_anterior is not None:
        estrategia.carregar_stats_ano_anterior(df_anterior)
    
    # Testar todas as formações e pegar a melhor
    from estrategia_v7 import FORMACOES
    melhor_escalacao = None
    melhor_pontuacao = -float('inf')
    
    for formacao in FORMACOES.keys():
        try:
            escalacao = estrategia.escalar_time(
                df_atual, 
                formacao=formacao, 
                orcamento=orcamento,
                modo_simulacao=True,
                incluir_explicacao=False
            )
            
            if escalacao and escalacao.get('titulares'):
                # Calcular pontuação real
                pontuacao_real = sum(j.get('pontos', 0) for j in escalacao['titulares'])
                
                # Adicionar bônus do capitão
                capitao = escalacao.get('capitao')
                if capitao:
                    pontuacao_real += capitao.get('pontos', 0) * 0.5
                
                if pontuacao_real > melhor_pontuacao:
                    melhor_pontuacao = pontuacao_real
                    melhor_escalacao = escalacao
                    melhor_escalacao['pontuacao_real'] = pontuacao_real
        except:
            continue
    
    return melhor_escalacao


def exibir_comparacao_escalacoes(escalacao_sugerida: Dict, time_ideal: Dict, rodada: int):
    """Exibe comparação lado a lado entre escalação sugerida e time ideal."""
    
    st.markdown(f'<h2>📊 Rodada {rodada} - Comparação Detalhada</h2>', unsafe_allow_html=True)
    
    # Métricas de comparação
    pts_sugerido = escalacao_sugerida.get('pontuacao_real', 0)
    pts_ideal = time_ideal.get('pontuacao_real', 0) if time_ideal else 0
    diferenca = pts_sugerido - pts_ideal
    aproveitamento = (pts_sugerido / pts_ideal * 100) if pts_ideal > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Escalação Sugerida", f"{pts_sugerido:.1f} pts")
    with col2:
        st.metric("Time Ideal", f"{pts_ideal:.1f} pts")
    with col3:
        st.metric("Diferença", f"{diferenca:+.1f} pts", 
                 delta_color="normal" if diferenca >= 0 else "inverse")
    with col4:
        st.metric("Aproveitamento", f"{aproveitamento:.1f}%")
    
    st.divider()
    
    # Comparação dos jogadores
    col_sug, col_ideal = st.columns(2)
    
    with col_sug:
        st.markdown('<h3>🎯 Escalação Sugerida</h3>', unsafe_allow_html=True)
        exibir_time_completo(escalacao_sugerida, mostrar_pontos_reais=True)
    
    with col_ideal:
        st.markdown('<h3>🏆 Time Ideal</h3>', unsafe_allow_html=True)
        if time_ideal:
            exibir_time_completo(time_ideal, mostrar_pontos_reais=True)
        else:
            st.info("Dados não disponíveis")


def exibir_time_completo(escalacao: Dict, mostrar_pontos_reais: bool = False):
    """Exibe o time completo com titulares organizados por posição."""
    from app import exibir_jogador_card
    
    capitao_id = escalacao.get('capitao', {}).get('atleta_id')
    
    for pos_id in [1, 3, 2, 4, 5, 6]:  # GOL, ZAG, LAT, MEI, ATA, TEC
        pos_jogadores = [t for t in escalacao.get('titulares', []) if t.get('pos_id') == pos_id]
        
        if pos_jogadores:
            st.markdown(f'<span class="posicao-badge">{POSICAO_MAP.get(pos_id, "")}</span>', 
                       unsafe_allow_html=True)
            
            for jogador in pos_jogadores:
                is_cap = jogador.get('atleta_id') == capitao_id
                exibir_jogador_card(
                    jogador, 
                    is_capitao=is_cap,
                    mostrar_previsto_vs_real=mostrar_pontos_reais,
                    mostrar_explicacao=True
                )




def pagina_historico():
    """Nova página de histórico com comparação detalhada."""
    st.markdown('<h1>📜 Histórico de Resultados</h1>', unsafe_allow_html=True)
    
    # Carregar dados
    estrategia = EstrategiaV7()
    aprendizado = AprendizagemContinua()
    
    if not estrategia.resultados:
        st.markdown("""
        <div class="info-box">
            <h4>📊 Nenhum resultado registrado</h4>
            <p>Registre os resultados das rodadas na página "Atualizar Resultados" para acompanhar sua evolução.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    df = pd.DataFrame(estrategia.resultados)
    
    # ========== MÉTRICAS GERAIS ==========
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Pontos", f"{df['pontos'].sum():.1f}")
    with col2:
        st.metric("Média/Rodada", f"{df['pontos'].mean():.1f}")
    with col3:
        st.metric("Melhor Rodada", f"{df['pontos'].max():.1f}")
    with col4:
        st.metric("Orçamento Atual", f"C$ {df['orcamento'].iloc[-1]:.1f}")
    
    st.divider()
    
    # ========== GRÁFICOS DE EVOLUÇÃO ==========
    st.markdown('<h3>📈 Evolução por Rodada</h3>', unsafe_allow_html=True)
    
    # Carregar rodadas com ajustes
    rodadas_ajustes = aprendizado.obter_rodadas_com_ajustes()
    rodadas_com_ajuste = [a['rodada'] for a in rodadas_ajustes if a.get('rodada')]
    
    fig = go.Figure()
    
    # Linha de pontuação
    fig.add_trace(go.Scatter(
        x=df['rodada'],
        y=df['pontos'],
        mode='lines+markers',
        name='Pontos',
        line=dict(color='#54b4f7', width=3),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor='rgba(84, 180, 247, 0.1)',
        hovertemplate='Rodada %{x}<br>Pontos: %{y:.1f}<extra></extra>'
    ))
    
    # Marcação de ajustes
    for rodada_ajuste in rodadas_com_ajuste:
        desc = next((a['descricao'] for a in rodadas_ajustes if a.get('rodada') == rodada_ajuste), 'Ajuste')
        fig.add_vline(
            x=rodada_ajuste, 
            line_dash="dash", 
            line_color="#FFC107", 
            line_width=2,
            annotation_text=f"🔧 {desc}",
            annotation_position="top",
            annotation_font_size=10,
            annotation_font_color="#FFC107"
        )
    
    # Linha de média
    media = df['pontos'].mean()
    fig.add_hline(y=media, line_dash="dash", line_color="#15367b", 
                 annotation_text=f"Média: {media:.1f}", annotation_position="right")
    
    # Linha de meta
    fig.add_hline(y=90, line_dash="dot", line_color="#FFD700", 
                 annotation_text="Meta: 90 pts", annotation_position="left")
    
    fig.update_layout(
        xaxis=dict(title='Rodada', tickmode='linear', dtick=5, gridcolor='rgba(255,255,255,0.1)', color='#FFFFFF'),
        yaxis=dict(title='Pontos', gridcolor='rgba(255,255,255,0.1)', color='#FFFFFF'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified',
        margin=dict(l=40, r=40, t=20, b=40),
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Gráfico de Orçamento
    st.markdown('<h3>💰 Evolução do Orçamento</h3>', unsafe_allow_html=True)
    
    fig_orc = go.Figure()
    
    fig_orc.add_trace(go.Scatter(
        x=df['rodada'],
        y=df['orcamento'],
        mode='lines+markers',
        name='Orçamento',
        line=dict(color='#28A745', width=3),
        marker=dict(size=8),
        fill='tozeroy',
        fillcolor='rgba(40, 167, 69, 0.1)',
        hovertemplate='Rodada %{x}<br>Orçamento: C$ %{y:.1f}<extra></extra>'
    ))
    
    fig_orc.update_layout(
        xaxis=dict(title='Rodada', tickmode='linear', dtick=5, gridcolor='rgba(255,255,255,0.1)', color='#FFFFFF'),
        yaxis=dict(title='Orçamento (C$)', gridcolor='rgba(255,255,255,0.1)', color='#FFFFFF'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified',
        margin=dict(l=40, r=40, t=20, b=40),
        showlegend=False,
        height=400
    )
    
    st.plotly_chart(fig_orc, use_container_width=True)
    
    st.divider()
    
    # ========== DETALHES POR RODADA ==========
    st.markdown('<h3>🔍 Detalhes por Rodada</h3>', unsafe_allow_html=True)
    st.markdown('<p style="color: #6C757D;">Selecione uma rodada para ver a comparação entre sua escalação e o time ideal</p>', unsafe_allow_html=True)
    
    # Seletor de rodada
    rodadas_disponiveis = sorted(df['rodada'].unique())
    rodada_selecionada = st.selectbox(
        "Rodada",
        rodadas_disponiveis,
        index=len(rodadas_disponiveis) - 1  # Última rodada por padrão
    )
    
    if rodada_selecionada:
        # Carregar escalação salva
        ano_atual = 2026  # TODO: pegar do contexto
        escalacao_salva = carregar_escalacao_salva(ano_atual, rodada_selecionada)
        
        if escalacao_salva:
            # Calcular time ideal
            orcamento = escalacao_salva.get('orcamento', 100)
            
            with st.spinner("Calculando time ideal..."):
                time_ideal = calcular_time_ideal(ano_atual, rodada_selecionada, orcamento)
            
            # Exibir comparação
            exibir_comparacao_escalacoes(escalacao_salva, time_ideal, rodada_selecionada)
        else:
            st.info(f"Escalação da rodada {rodada_selecionada} não encontrada. Confirme a escalação antes do fechamento do mercado.")
    
    st.divider()
    
    # ========== TABELA DE RESULTADOS ==========
    st.markdown('<h3>📋 Tabela de Resultados</h3>', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)
    
    st.divider()
    
    # ========== HISTÓRICO DE AJUSTES ==========
    st.markdown('<h3>🔧 Histórico de Ajustes Automáticos</h3>', unsafe_allow_html=True)
    st.markdown('<p style="color: #6C757D;">Ajustes realizados pelo sistema de aprendizado contínuo</p>', unsafe_allow_html=True)
    
    ajustes = aprendizado.obter_historico_ajustes_completo()
    
    if not ajustes:
        st.markdown("""
        <div class="info-box">
            <h4>ℹ️ Nenhum ajuste realizado ainda</h4>
            <p>O sistema fará ajustes automáticos após analisar os resultados das rodadas.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        for i, ajuste in enumerate(reversed(ajustes)):
            rodada = ajuste.get('rodada', 'N/A')
            ano = ajuste.get('ano', 'N/A')
            data = ajuste.get('data', '')[:10]
            descricao = ajuste.get('descricao', 'Ajuste de parâmetros')
            detalhes = ajuste.get('ajustes', [])
            
            with st.expander(f"📅 Rodada {rodada} ({ano}) - {descricao}", expanded=(i == 0)):
                st.markdown(f"**Data:** {data}")
                st.markdown("**Detalhes dos ajustes:**")
                
                for det in detalhes:
                    pos = det.get('posicao', 'N/A')
                    tipo = det.get('tipo', 'N/A')
                    anterior = det.get('peso_anterior', 0)
                    novo = det.get('peso_novo', 0)
                    motivo = det.get('motivo', '')
                    
                    icone = "⬇️" if tipo == 'redução' else "⬆️"
                    cor = "#DC3545" if tipo == 'redução' else "#28A745"
                    
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #1a2744 0%, #0b1d33 100%); 
                                padding: 10px 15px; border-radius: 8px; margin: 5px 0;
                                border-left: 3px solid {cor};">
                        <span style="font-size: 1.2rem;">{icone}</span>
                        <strong style="color: #FFFFFF;">{pos}</strong>: 
                        <span style="color: #ADB5BD;">{anterior:.2f} → {novo:.2f}</span>
                        <br><small style="color: #6C757D;">{motivo}</small>
                    </div>
                    """, unsafe_allow_html=True)

def pagina_atualizar():
    """Página para atualizar resultados (aprendizado contínuo)."""
    st.markdown('<h1>🔄 Atualizar Resultados</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #6C757D; font-size: 1.1rem;">Atualize os resultados da rodada para o aprendizado contínuo</p>', unsafe_allow_html=True)
    
    estrategia = EstrategiaV7()
    api = CartolaFCAPI()
    
    # Mostrar status atual
    col_status1, col_status2, col_status3 = st.columns(3)
    with col_status1:
        st.metric("📅 Rodada Atual", estrategia.rodada_atual)
    with col_status2:
        st.metric("💰 Orçamento", f"C$ {estrategia.orcamento:.2f}")
    with col_status3:
        total_pts = sum(r.get('pontos', 0) for r in estrategia.resultados)
        st.metric("⚽ Total Pontos", f"{total_pts:.1f}")
    
    st.divider()
    
    # Tabs para atualização automática e manual
    tab_auto, tab_manual = st.tabs(["🤖 Atualização Automática", "✏️ Atualização Manual"])
    
    with tab_auto:
        st.markdown('<h3>🤖 Atualização Automática via API</h3>', unsafe_allow_html=True)
        st.markdown('<p style="color: #6C757D;">Busca automaticamente os resultados da rodada na API oficial</p>', unsafe_allow_html=True)
        
        # Verificar status do mercado
        status = api.get_mercado_status()
        if status:
            rodada_api = status.get('rodada_atual', 1)
            status_mercado = status.get('status_mercado', 0)
            
            status_texto = "🟢 Aberto" if status_mercado == 1 else "🔴 Fechado"
            st.info(f"📊 Status do Mercado: {status_texto} | Rodada API: {rodada_api}")
            
            if status_mercado != 1:  # Mercado fechado
                st.success("✅ Mercado fechado! Você pode atualizar os resultados.")
                
                # Carregar escalação salva (se existir)
                escalacao_salva = None
                if os.path.exists('escalacao_atual.json'):
                    try:
                        with open('escalacao_atual.json', 'r') as f:
                            escalacao_salva = json.load(f)
                        st.info(f"📋 Escalação salva encontrada para a rodada {escalacao_salva.get('rodada', 'N/A')}")
                    except:
                        pass
                
                if st.button("🔄 Atualizar Automaticamente", type="primary", use_container_width=True):
                    with st.spinner("Buscando resultados da API..."):
                        resultado = estrategia.atualizar_automatico(api, escalacao_salva)
                        
                        if resultado.get('sucesso'):
                            st.success(f"✅ Rodada {resultado['rodada']} atualizada com sucesso!")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("⚽ Pontuação", f"{resultado['pontos']:.1f} pts")
                            with col2:
                                st.metric("📈 Valorização", f"C$ {resultado['valorizacao']:.2f}")
                            with col3:
                                st.metric("💰 Novo Orçamento", f"C$ {resultado['novo_orcamento']:.2f}")
                            
                            st.info(f"📊 {resultado['total_jogadores_atualizados']} jogadores atualizados no histórico")
                            
                            # APRENDIZADO CONTÍNUO: Atualizar resultado detalhado
                            try:
                                aprendizagem = AprendizagemContinua()
                                ano_atual = datetime.now().year
                                
                                # Criar dict de resultados por jogador
                                resultados_jogadores = {}
                                for jog in resultado.get('detalhes', []):
                                    if 'atleta_id' in jog:
                                        resultados_jogadores[jog['atleta_id']] = jog['pontos']
                                
                                # Atualizar resultado da rodada
                                analise = aprendizagem.atualizar_resultado_rodada(
                                    ano=ano_atual,
                                    rodada=resultado['rodada'],
                                    resultados_jogadores=resultados_jogadores,
                                    pontuacao_total=resultado['pontos']
                                )
                                
                                if analise.get('sucesso'):
                                    st.success(f"🧠 Aprendizado: Acurácia {analise['acuracia']:.1f}% ({analise['acertos']}/12 jogadores)")
                            except Exception as e:
                                pass  # Não interromper se falhar
                            
                            # Mostrar detalhes dos jogadores
                            if resultado.get('detalhes'):
                                with st.expander("📋 Detalhes dos Jogadores"):
                                    for jog in resultado['detalhes']:
                                        emoji = "👑" if jog.get('capitao') else "🔄" if jog.get('substituicao') else "⚽"
                                        st.markdown(f"{emoji} **{jog['apelido']}**: {jog['pontos']:.1f} pts (C$ {jog['variacao']:.2f})")
                            
                            st.rerun()
                        else:
                            st.error(f"❌ Erro: {resultado.get('erro', 'Erro desconhecido')}")
            else:
                st.warning("⏳ O mercado ainda está aberto. Aguarde o fechamento para atualizar os resultados.")
        else:
            st.error("❌ Não foi possível conectar à API oficial")
    
    with tab_manual:
        st.markdown('<h3>✏️ Atualização Manual</h3>', unsafe_allow_html=True)
        st.markdown('<p style="color: #6C757D;">Insira manualmente os resultados da rodada</p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            rodada = st.number_input("📅 Rodada", min_value=1, max_value=38, value=estrategia.rodada_atual)
            pontos = st.number_input("⚽ Pontuação Real", min_value=-50.0, max_value=300.0, value=0.0, step=0.1)
        
        with col2:
            valorizacao = st.number_input("📈 Valorização (C$)", min_value=-50.0, max_value=50.0, value=0.0, step=0.1)
            formacao_usada = st.selectbox("📋 Formação Usada", list(FORMACOES.keys()))
        
        if st.button("📝 Registrar Resultado", type="primary", use_container_width=True):
            estrategia.registrar_resultado(
                rodada=rodada,
                pontos=pontos,
                valorizacao=valorizacao,
                escalacao={'formacao': formacao_usada}
            )
            st.success(f"✅ Resultado da rodada {rodada} registrado!")
            st.info(f"💰 Novo orçamento: C$ {estrategia.orcamento:.2f}")
            st.rerun()
    
    st.divider()
    
    # Histórico de resultados
    if estrategia.resultados:
        st.markdown('<h3>📜 Histórico de Resultados</h3>', unsafe_allow_html=True)
        
        df_resultados = pd.DataFrame(estrategia.resultados)
        if not df_resultados.empty:
            df_display = df_resultados[['rodada', 'pontos', 'valorizacao']].copy()
            df_display.columns = ['Rodada', 'Pontos', 'Valorização']
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    st.divider()
    
    st.markdown('<h3>⚠️ Resetar Temporada</h3>', unsafe_allow_html=True)
    st.warning("Isso irá apagar todo o histórico e reiniciar o orçamento para C$ 100,00")
    
    if st.button("🗑️ Resetar Temporada"):
        estrategia.resetar_temporada()
        # Remover escalação salva
        if os.path.exists('escalacao_atual.json'):
            os.remove('escalacao_atual.json')
        st.success("✅ Temporada resetada!")
        st.rerun()


def main():
    """Função principal."""
    # Verificar e executar atualização automática ao carregar
    try:
        estrategia = EstrategiaV7()
        api = CartolaFCAPI()
        resultado_auto = estrategia.verificar_e_atualizar_automatico(api)
        if resultado_auto and resultado_auto.get('sucesso'):
            st.toast(f"🔄 Rodada {resultado_auto['rodada']} atualizada automaticamente! Pontos: {resultado_auto['pontos']:.1f}", icon="✅")
    except Exception as e:
        pass  # Silenciosamente ignora erros na atualização automática
    
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 20px 0;">
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADwAAAA8CAIAAAC1nk4lAAAPwElEQVR4nNVaeZgV1ZU/595br97W73U/mt4QmmYV0EQIOBJRTPxckpgYxTgyJn4qjolhMInfJIOZqCOJKzqZMYkx6oy4L4njFlwgKriwKCJIA6JD6JamaXrv12+vuufMH1X1lqY3gT8y54/uelW3zv3dc88993fOLSTSAAgAAFx0MZSg9xSHbTag/YhqR6MHEBGAmUl5GmGwiyHfH0WzI24/gjCDKrJEifXyJuIB9xGBgQEQgZkLcBCBwW2IyFykFIqmB6DwmtPUReI8R68te9fs3i8aMubdY8CDv1lhIlH49f8BMQAAQhHoo1ooA0VrrbU+hgo9YQBWRb+PmamZWUoJAEyM4pjPILqWPlbuzMyaCBEffeq5Z55bjQKPvb25YGk+Jpa2tTaUuu2u396zuYeyqf6+niWXf9eybMNQI788KsGCpY+JoS3bNpS674FVv3+v2+xpiprwqxd3rV79smEoy7KPQQcAAFy8EI8KNTM7Nr7/wYdvWf2JSHSEaiZ2NW5UZuDHD7yxbt26Y4q7JHqMHmPJLyICQCXlyl//7tY1zYadKqsaP/2SnxLDwTeeNGLHXf3rF9e8+pphKNu2SzaWw7WNLoAdEeiiWbFtLYTQufR1N9z+2829umOfFHDilT/LxrtRCDDM/WtWiWjND+5d+/gTTyulGJA0DaVtdPPN4ojZDBERs1Ly0493n//9Xzy7F3yJts7Gd0N1U5jYtagQKH0tax8xwpHrn2284Vd3gc4KKWxbD2LyUQqDKGz1oxatSWsSQgigB//7kUU3PrxH11LTB+POWFQ5c34u0QvoEDJAYkAUZnD/2idUuu/RPXj+93+xfesHSklEtLVmppH7O0xKo8fQg2diIrK1BgAphZTi7fXrLlq6YsUrTf2pbO+mZ4+/9Od188+wknEhFLDDgAr8SIXLD76/Nrv7rZ25qktueWbFHfd0tLUqKRGF1qS1JmdyRsd21YDfg8B1+heIgALAzqTWv7vp8Vc3v7UvmdXsz3ba2iZphKrGWwlCIZ2o5HI3BHToH5FRVh5vbUq1t4z54hkPbE38edt/XnTK5Iu/ccbEKdPyfREzssObhxaGkWO+o6K7ve3jT/e9s3X3mx81727PaEbu/kwoNfOHt/S3HtjyH8u0bfukYOTSN73uEYC0NAPM3Pbey6HKuo5pJ9/zTvujGx76u4kVC0+aPO8Lx08YXxeMVIyIB2BY0EQkhNiydfvylQ+mglUHu/ozWvgNCYnOivFTmxvXTf76FdGG8Z07t6MQjhsjI7OzvSIXc3NwqA4BghGMZuK9qXef98eqsX7ma3vNV/fuiL60o7rM8CU7bv3nJXNOOtHpeigrqiKVAyeFiIWAtzd9sCURi8XblZS+/q6uvY0LbnqqfPr09l2brWSccoxS5Vm8t6wZtBbg3S6JxMykEaUKRXOp/sy2dVIZZvnYnoqqZEV1XFS8tWnrnJNOdLoeSobdEREAoC1uhShp+oNzrr1lwlcWS3/YjNVYCc22BSgBsQCUSQpAIGWiCMUsLYTAQTYPREBwoQciaPgz8e743sauTa9EfHigu38oOHlMwr0YbNk63tzWHbdyudj0OUY4ZGfTzJq1BcIJ8MxMQqASaPr9bIqufrJEqHN/V/Ofbh7jO5TMkEBUEoVwgiq6hBI96EwMjFLKQAhNfzaTOtSTAADE4XY94Y4fB0EthAC2e9I2soWGnzU7BItBMKNjW+UXySx291n79jQ1rfrXb81oiXX8BZ5e/Nj3Mh/8z7Ibr6jp68319Gb705wnwcVG93wTgZlsC0n3pmwgWwzLwvOJ7cBGzIAIOptLZ20phPAFgdzw5fovsy8U2bdhe93O2y+5pm5349XXLJo975v3d3+6NZvYXzvv3wBg+Y/K0/23jq2Z9OZ7+1993w4FFHHR4mHvrxfQUetUVutcVvrVMGR5mIXIAGhr29aEDNIwC4NDAABpqN6ueMOHdzx253cCUy6Fvi1QNkeLitiM2QBAmhBZVJ57292TITD1R4dWf+uKf//Lhxw0UXMRZC70xgBAtkVs2bYcluB7Pj1EA2YmZgBGWShfOMUCZZidn+1dOEMGpvwgZUc5eiZhhcgPVyCiUL4yCszJUpmsvuhLM2O5XksIJzRCqX+7NAIFMHu8ZejtUXhjHFyklEogCkG25Q4D3Q3atnKxuvqNn1jc+nhQpXJ9uwSSTv41c+h1ndrvVkIAONut7C7r4LMhIz13Tiid07bmAiB0XA5d26GQAp38chjGp9ynh02GEzqUYZg+g4jtVBLB64wYgW3LrqsZ0zJ+2cXX/vyfLlw9NfoZ+et18lCq+5OqExaPmbvS6v8U0Jfr2da9faVWFRcuiC39tnz5vcQ/3t2lCYVw6z3OTuQIoPQrYfgMGDZtFW7gGCx6EDEqM+KXmsFO9UsfAgpglFIJiShENhE//uxTt4xbvur5j5Wd7N63OZ3o0hTu/HRN2ztXH3p3qU7ttzXIzIEHXsnMXtJ82o9bzpwdvvycSDKhJTLbFmsNwKwtsi1gQGVGAgqVScOSJ+Hwm0HF4Y1jI35Gme46kInH7XSSgbP9Pdl4HxORlUu094VUOhz2E0MgNq6ibhJzzh+MJtu297XuVMGxKA0lRcaCpAhs25V9c2tyzlQfMAvD5yuLqUAYAIxw1BepUIEQKmNsNAiATEOigkL0GGytOuthXCzkK4u1bHjps02vsm2RbW2480oAtFOJlo2rO7a/3t2V+eo3/MwJYGLWAKwCQRUoyybbUwdeyyS6SLOvrGzGoiv2PHmnEAzSB6zr5p93/OKlrRvXf/TwL+f95N5QzXEfP76yM54aXz0JBpT7BgPNyAiDsUHn3rT6OikOSMOf6WwThg8E2v19AABCUC6ds1I6DYhRZ+AMAhiYiIG0DR07HkqnsrGgKaRCZQIDCsEAQKx8AX8k4lo6VKF8ITuT9BnGlHFjAUbIu4bbLZ21OHNqfQByvoo6AEapkBGlQqkQEYUUygDhBToG9GYMAYE4NKbBDI0BsgAkKj9lbJvAkAjEzJo0s9YAgEIk2pqz6VSZ35g1dSIAiGEptRh8DTrPBDLA5EkN48qkiIwFJk8V57cG5vwO6YRvyj9CVAAagFAalOnt3vLaCbPCC2epjz5DWTGGSKNAQGQm5Q/0Ne20CMdFjcmTJrLDIIYFPVzdX2tt+INzGmIQiBiBEBMNMnEITjUa0dvfmQGZQTOzFNiXgmu+pt5ctmvj7ya8sbHllb6F1ZMbrGzWGz0zc/++RvaXza4vN/zBEStp+QENDt1BeO6CkwTrYHW9zmUGyfgZBKJmJ82SwE7EdSKpIma/D9Zs4xv+ZF54Y+stTUumXnQtZZIIghEYSCoz2dbc39Zk+n3nfvkLMII/l4Ae4rEQzHDqKXPHm2mzdhqQjShc7yg4BmRtDgWMTH9Por1ZCpnqaUt1tSqpMt0H0vHuirD66IB/vbF4/U6a9vXLfFIykRuHNalAuP3DN2wVGh+wFpwylxmEkEcFGhG11v5g+IL5U8kXClXWkWW5NkYERCIIBMSfN6U2NFf4I7EcmCJSo1VYq7CWwb54Ilhe+dbHcmvyxJknNgQMbaXi5KWuyCCEtOJdXY3vQLD8glOmmcGw1nr4vLY4sR2yoZSCmS/7znmr3rxDTpmb2PCCCkeZtLPNErAysKNPX3xboq7Sxx5BF4ZZOfN0aQY7tq9PR0+dfe1Puz/aqAnAZV7sIEOpcvEuc+45Qer57qIlzCzkyEWvkVsgIhFVVtdcdvp07Y9GxjXoXKaYGDCDqYRAbm7L7G/L7m/LNbemW7qx/GvLqy++6WAyHB43JVIZtHM5J1sB70QJmYHtstp6Hai4bOH0qpo6TTR8sHOcclS1PCEEEV1z5T/U6YPhGaehbSEKrx6TTxLR7xOmIUyf8PvQNEBYSWlpvw/YymiL0Tv/AgYBCExCYceH66InfKXWarnm8r8nIjlspCvgyY9gmEaIyAyhssjNV30z299TO/fsXKIHlcrHa1cFuYuT2InTAlACoEOuHQM6f0nbgVhN0+trk50Hbdu6+arzwpFyHrFMcxjoEURKobU++5yzvjevKh0aG5s0y0r2o5TFGw0AADKgR9AKPJnByQOdCyIVCLbvePvghhfsivGXfDFy9tln2VrLUXizM+zPUVQXQmhNN//L0tn+9sCsr4Yra6xMEqQsHIA69RlGwJI5cLMGZgRkbUtTCOWL79tJ1dPnRhO/XL5M69E6hqNtVO7hokJERMMMPLRyeVXfrujJ5wejFTqTQnTjrndgy25jBi/L8SaDyIxWdv/vHp3srT7ryjE9jQ/cep3PH3QzgFEJDjhHHFmEQNJUWVXzxJ3XRbsaY6deEh5TayX7BvHvwjUjOMdeWpmB9m3rdz+ywjd1fkXvnmfu/llVTR1pGr5gUCoM/PlPAoQUWtPEyVOe/831Nb07giedW3X8l3LxbkREtypSUM8OI9FaKPSVlScPNTetfUzWzxlvNf/xrp/UT5qstR5NYB6IId/D6MVZlMdNmPjS/Svmhw/p2hnHnXYBWxltZVBKd6IRAIC0Jk2+SKz/4KGmNQ9POH2Rrp4+L9j24n0rJjRM0prcHPbIQH/eowQpJRFFY5VP/P62pfMitrarz7oiUtdgJ/rItlFIJxv3BaU0/a2bX97xX7dSWS2hWDY/9vR9t5fHxhDRKMPF4eJ+hYBDlz6GEadEIQRu3LDhhnv/uCsbC7CV+GRzvPWvZqz21OtXde58t+Wd52RlA/mjs8LJm64678sLTnMr50d4/MxMlAd9pOeIDJq0lNLOpv+w6qlVr+9sg3KRTVgHPzHCUctXJsoqa0TisoXTfrjkUmUGbK2VkEdxaslMjEQEbjp45JryNfDO9raHnnz+hfebmtImEdUHshec3HDl4m9XVtcWNzsKYWbKgz7ac2bnKF9JCQDJvp6X1qwDIc87c0G4PAYAttbSrYgdbT+Udw8At0qN7j8s/jCoUAouPQRjzCeYTu0XgVmTVqpwKmLbWkin+JXfFfMHMezt8aWaS8vB+Q+DAICBHEvnPwfKoyxBPFDX4XpLRwLIzKA1AYCUAhGgGGV+jxxe8yAAGBAZiKn4I5XSMZfUcAZU+w5PE0tvIqKSsrieAADsmaxEW6m/MLJXbnHweDzGmUmPcSn2UievZUEvl37K5boDFtuKvUOUQjPPwQbMrecJHtfzOsz3UlrLQKf4XjKwvDMOFfJG4W2HXQ/u+kO94pmmUOcdWrM3T8QM7HxZ4xypYlGd0rVWniOzt+Sc9VawrlvxcOseedfL3y+CiEVTVkDlscI8PcwbC5358c6XwK3vcd7SxRb2vhQcWJPMW4+BARGL2+UXb6G7Qd50l6SH0T3zL7L8wCEV3SiMCRj+DwlMFqdbqR88AAAAAElFTkSuQmCC" style="width: 180px !important; height: 180px !important; max-width: 180px; display: block; margin: 0 auto;">
            <h2 style="color: #54b4f7; margin: 10px 0;">Dervé FC</h2>
            <p style="color: #FFFFFF; font-size: 0.9rem;">Escalação Automática</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
    
    pagina = st.sidebar.radio(
        "Navegação",
        ["⚽ Escalação", "🔬 Simulação Histórica", "📜 Histórico", "🔄 Atualizar Resultados"],
        label_visibility="collapsed"
    )
    
    if pagina == "⚽ Escalação":
        pagina_escalacao()
    elif pagina == "🔬 Simulação Histórica":
        pagina_simulacao()
    elif pagina == "📜 Histórico":
        pagina_historico()
    elif pagina == "🔄 Atualizar Resultados":
        pagina_atualizar()
    
    st.sidebar.divider()
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 10px;">
        <p style="color: #6C757D; font-size: 0.8rem;">Estratégia v9</p>
        <p style="color: #54b4f7; font-size: 0.9rem; font-weight: 600;">94.1 pts/rodada</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
