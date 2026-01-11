"""
Bolão Copa do Mundo 2026
Aplicativo principal Streamlit
"""

import streamlit as st
from datetime import datetime, timedelta
import pytz
import json

from db import (
    init_database, get_session, get_engine, get_config_value, set_config_value,
    init_database_with_copa2026
)
from auth import authenticate_user, hash_password, change_password, create_user
from models import (
    User, Match, Prediction, Team, Config, 
    GroupPrediction, PodiumPrediction, TournamentResult, GroupResult, AuditLog
)
from scoring import (
    get_ranking, get_user_stats, get_scoring_config, 
    process_match_predictions, process_group_predictions, process_podium_predictions
)

SELECOES_REPESCAGEM = {
    # Repescagem Europa (4 vagas)
    "EUR_A": [
        {"code": "UKR", "name": "Ucrânia", "flag": "🇺🇦"},
        {"code": "WAL", "name": "País de Gales", "flag": "🏴󠁧󠁢󠁷󠁬󠁳󠁿"},
        {"code": "ISL", "name": "Islândia", "flag": "🇮🇸"},
        {"code": "BIH", "name": "Bósnia e Herzegovina", "flag": "🇧🇦"},
    ],
    "EUR_B": [
        {"code": "ISR", "name": "Israel", "flag": "🇮🇱"},
        {"code": "IRL", "name": "Irlanda", "flag": "🇮🇪"},
        {"code": "GEO", "name": "Geórgia", "flag": "🇬🇪"},
        {"code": "LUX", "name": "Luxemburgo", "flag": "🇱🇺"},
    ],
    "EUR_C": [
        {"code": "NOR", "name": "Noruega", "flag": "🇳🇴"},
        {"code": "CZE", "name": "República Tcheca", "flag": "🇨🇿"},
        {"code": "KAZ", "name": "Cazaquistão", "flag": "🇰🇿"},
        {"code": "BUL", "name": "Bulgária", "flag": "🇧🇬"},
    ],
    "EUR_D": [
        {"code": "TUR", "name": "Turquia", "flag": "🇹🇷"},
        {"code": "GRE", "name": "Grécia", "flag": "🇬🇷"},
        {"code": "FIN", "name": "Finlândia", "flag": "🇫🇮"},
        {"code": "KOS", "name": "Kosovo", "flag": "🇽🇰"},
    ],
    # Repescagem Intercontinental (2 vagas)
    "INT_1": [
        {"code": "IDN", "name": "Indonésia", "flag": "🇮🇩"},
        {"code": "BHR", "name": "Bahrein", "flag": "🇧🇭"},
        {"code": "TWN", "name": "Taiwan", "flag": "🇹🇼"},
        {"code": "GUI", "name": "Guiné", "flag": "🇬🇳"},
    ],
    "INT_2": [
        {"code": "NZL", "name": "Nova Zelândia", "flag": "🇳🇿"},
        {"code": "OMA", "name": "Omã", "flag": "🇴🇲"},
        {"code": "THA", "name": "Tailândia", "flag": "🇹🇭"},
        {"code": "MLI", "name": "Mali", "flag": "🇲🇱"},
    ],
}

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="Bolão Copa 2026",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =============================================================================
# CSS PERSONALIZADO - TEMA COPA DO MUNDO 2026
# =============================================================================

st.markdown("""
<style>
    /* ========================================
       HEADER FIXO COM LOGO DO BOLÃO
       ======================================== */
    
    /* Força overflow visible nos containers do Streamlit para o header fixo funcionar */
    .stApp, .stAppViewContainer, .appview-container {
        overflow: visible !important;
    }
    
    .fixed-header {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        height: 60px;
        background: linear-gradient(135deg, #1E3A5F 0%, #2A398D 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 999999;
        box-shadow: 0 2px 15px rgba(0,0,0,0.2);
        padding: 0 20px;
    }
    
    .fixed-header-content {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    .fixed-header-logo {
        width: 40px;
        height: 40px;
    }
    
    .fixed-header-title {
        color: #ffffff !important;
        font-size: 1.3rem;
        font-weight: 700;
        letter-spacing: 1px;
        margin: 0;
    }
    
    .fixed-header-subtitle {
        color: #FFD700 !important;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 2px;
    }
    
    /* Ajusta o conteúdo principal para não ficar atrás do header */
    .main .block-container {
        padding-top: 80px !important;
    }
    
    /* ========================================
       ANIMAÇÕES SUTIS NAS TRANSIÇÕES
       ======================================== */
    
    /* Animação de fade-in para o conteúdo principal */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    /* Aplica animações aos elementos */
    .main .block-container > div {
        animation: fadeInUp 0.5s ease-out;
    }
    
    .stMetric {
        animation: fadeIn 0.6s ease-out;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .stMetric:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    /* Cards com animação */
    .element-container {
        transition: all 0.3s ease;
    }
    
    /* FORÇA FUNDO TRANSPARENTE nos containers que envolvem HTML customizado */
    .element-container:has(.palpite-card-light),
    .element-container:has(.ranking-card-light),
    .stMarkdown:has(.palpite-card-light),
    .stMarkdown:has(.ranking-card-light),
    div[data-testid="stMarkdownContainer"]:has(.palpite-card-light),
    div[data-testid="stMarkdownContainer"]:has(.ranking-card-light) {
        background: transparent !important;
        background-color: transparent !important;
    }
    
    /* Sobrescreve qualquer fundo escuro em elementos pai */
    .palpite-card-light,
    .ranking-card-light {
        position: relative;
        z-index: 1;
    }
    
    /* Botões com animação de pulse no hover */
    .stButton > button:hover {
        animation: pulse 0.5s ease-in-out;
    }
    
    /* Expanders com transição suave */
    .streamlit-expanderHeader {
        transition: all 0.3s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%) !important;
    }
    
    /* Tabelas com animação de linha */
    .stDataFrame tbody tr {
        transition: background-color 0.2s ease;
    }
    
    .stDataFrame tbody tr:hover {
        background-color: rgba(52, 152, 219, 0.1) !important;
    }
    
    /* ========================================
       CORES DAS FONTES - CONTRASTE GARANTIDO
       ======================================== */
    
    /* Fundo principal mais claro */
    .stApp {
        background: #ffffff !important;
    }
    
    /* TODAS as fontes do conteúdo principal em cor escura */
    .stApp .main .block-container {
        color: #1a1a2e !important;
    }
    
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
        color: #1E3A5F !important;
    }
    
    .stApp p, .stApp span, .stApp div, .stApp label {
        color: #1a1a2e !important;
    }
    
    /* Markdown text */
    .stMarkdown, .stMarkdown p, .stMarkdown span {
        color: #1a1a2e !important;
    }
    
    /* Expander headers e conteúdo */
    .streamlit-expanderHeader {
        color: #1E3A5F !important;
        background: #f8f9fa !important;
        font-weight: 600;
    }
    
    .streamlit-expanderContent {
        color: #1a1a2e !important;
        background: #ffffff !important;
    }
    
    /* Tabs - texto visível */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px !important;
        background: transparent !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #1E3A5F !important;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
        font-weight: 700 !important;
        border-radius: 10px 10px 0 0 !important;
        padding: 12px 24px !important;
        border: 1px solid #dee2e6 !important;
        border-bottom: none !important;
        transition: all 0.3s ease !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%) !important;
        transform: translateY(-2px) !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1E3A5F 0%, #2d5a87 100%) !important;
        color: #ffffff !important;
        border-color: #1E3A5F !important;
        box-shadow: 0 4px 15px rgba(30, 58, 95, 0.3) !important;
    }
    
    .stTabs [data-baseweb="tab-panel"] {
        background: #ffffff !important;
        border-radius: 0 12px 12px 12px !important;
        padding: 1.5rem !important;
        border: 1px solid #dee2e6 !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
    }
    
    /* ========================================
       SIDEBAR - MANTÉM TEMA ESCURO
       ======================================== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E3A5F 0%, #0f1f33 100%) !important;
    }
    
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebar"] .stButton > button {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 10px;
        padding: 0.75rem 1rem;
        font-weight: 500;
        font-size: 0.9rem;
        letter-spacing: 0.2px;
        transition: all 0.25s ease;
        backdrop-filter: blur(10px);
        text-align: left !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(52, 152, 219, 0.3) !important;
        border-color: rgba(52, 152, 219, 0.5) !important;
        transform: translateX(5px);
        box-shadow: 0 4px 15px rgba(52, 152, 219, 0.2);
    }
    
    [data-testid="stSidebar"] .stButton > button:active {
        background: rgba(52, 152, 219, 0.4) !important;
        transform: translateX(3px);
    }
    
    /* Ícone de colapsar sidebar (<<) - BRANCO */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapseButton"] * {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebarCollapseButton"] svg,
    [data-testid="stSidebarCollapseButton"] svg * {
        fill: #ffffff !important;
        stroke: #ffffff !important;
        color: #ffffff !important;
    }
    
    [data-testid="stSidebarCollapseButton"] button {
        color: #ffffff !important;
        background: transparent !important;
    }
    
    /* Ícone do header da sidebar */
    [data-testid="stSidebarHeader"] svg,
    [data-testid="stSidebarHeader"] svg * {
        fill: #ffffff !important;
        stroke: #ffffff !important;
    }
    
    /* Botão de colapsar no topo */
    .css-1dp5vir,
    .css-1dp5vir svg,
    [data-testid="stSidebarNavCollapseIcon"],
    [data-testid="stSidebarNavCollapseIcon"] svg {
        fill: #ffffff !important;
        stroke: #ffffff !important;
        color: #ffffff !important;
    }
    
    /* Ícone de expandir sidebar quando fechada */
    [data-testid="collapsedControl"],
    [data-testid="collapsedControl"] * {
        color: #1E3A5F !important;
    }
    
    [data-testid="collapsedControl"] svg,
    [data-testid="collapsedControl"] svg * {
        fill: #1E3A5F !important;
        stroke: #1E3A5F !important;
    }
    
    /* Forçar TODOS os SVGs dentro da sidebar para branco */
    [data-testid="stSidebar"] svg,
    [data-testid="stSidebar"] svg * {
        fill: #ffffff !important;
        stroke: #ffffff !important;
    }
    
    /* Botão do sidebar no mobile - garantir visibilidade */
    @media (max-width: 768px) {
        /* Esconder o header fixo no mobile para não cobrir o botão */
        .fixed-header {
            display: none !important;
        }
        
        /* Ajustar padding do conteúdo principal no mobile */
        .main .block-container {
            padding-top: 1rem !important;
        }
        
        [data-testid="collapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: fixed !important;
            top: 10px !important;
            left: 10px !important;
            z-index: 9999999 !important;
            background: linear-gradient(135deg, #1E3A5F 0%, #2A398D 100%) !important;
            border-radius: 10px !important;
            padding: 10px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4) !important;
            border: 2px solid #FFD700 !important;
        }
        
        [data-testid="collapsedControl"] button {
            background: transparent !important;
            color: white !important;
            border: none !important;
            padding: 4px !important;
            min-width: auto !important;
            min-height: auto !important;
        }
        
        [data-testid="collapsedControl"] svg {
            fill: #FFD700 !important;
            stroke: #FFD700 !important;
            width: 28px !important;
            height: 28px !important;
        }
        
        /* Garantir que o sidebar abra por cima de tudo */
        [data-testid="stSidebar"] {
            z-index: 99999999 !important;
        }
    }
    
    /* ========================================
       HEADERS E TÍTULOS
       ======================================== */
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1E3A5F !important;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: #495057 !important;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 500;
    }
    
    /* ========================================
       CARDS E CONTAINERS
       ======================================== */
    .match-card {
        background: #ffffff !important;
        padding: 1.2rem;
        border-radius: 12px;
        margin-bottom: 0.8rem;
        border-left: 5px solid #D4AF37;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        color: #1a1a2e !important;
        transition: all 0.3s ease;
    }
    
    .match-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    /* Cards de estatísticas/métricas */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%) !important;
        padding: 1.2rem !important;
        border-radius: 16px !important;
        box-shadow: 0 4px 20px rgba(30, 58, 95, 0.1) !important;
        border: 1px solid rgba(30, 58, 95, 0.08) !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px) !important;
        box-shadow: 0 8px 30px rgba(30, 58, 95, 0.15) !important;
    }
    
    /* Expanders mais bonitos */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
        font-weight: 700 !important;
        border: 1px solid #dee2e6 !important;
        transition: all 0.3s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%) !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08) !important;
    }
    
    .streamlit-expanderContent {
        background: #ffffff !important;
        border-radius: 0 0 12px 12px !important;
        border: 1px solid #dee2e6 !important;
        border-top: none !important;
        padding: 1.5rem !important;
    }
    
    .team-name {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1E3A5F !important;
    }
    
    .match-info {
        color: #495057 !important;
        font-size: 0.95rem;
        font-weight: 500;
    }
    
    /* ========================================
       FORMULÁRIOS E INPUTS
       ======================================== */
    .stForm {
        background: #ffffff !important;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border: 1px solid #dee2e6;
    }
    
    .stTextInput label, .stSelectbox label, .stNumberInput label {
        color: #1E3A5F !important;
        font-weight: 600;
    }
    
    .stTextInput input, .stNumberInput input {
        color: #1a1a2e !important;
        background: #ffffff !important;
    }
    
    /* SELECTBOXES - TEXTO BRANCO EM FUNDO ESCURO */
    .stSelectbox > div > div {
        background-color: #1E3A5F !important;
        color: #ffffff !important;
    }
    
    .stSelectbox [data-baseweb="select"] > div {
        background-color: #1E3A5F !important;
        color: #ffffff !important;
    }
    
    .stSelectbox [data-baseweb="select"] span {
        color: #ffffff !important;
    }
    
    /* Forçar texto branco em TODOS os elementos do selectbox */
    .stSelectbox div[data-baseweb="select"] * {
        color: #ffffff !important;
    }
    
    .stSelectbox [data-baseweb="select"] input {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    
    .stSelectbox [role="combobox"] {
        color: #ffffff !important;
    }
    
    .stSelectbox [data-baseweb="select"] [data-testid="stMarkdownContainer"] {
        color: #ffffff !important;
    }
    
    .stSelectbox [data-baseweb="select"] p {
        color: #ffffff !important;
    }
    
    [data-baseweb="popover"] {
        background-color: #1E3A5F !important;
    }
    
    [data-baseweb="menu"] {
        background-color: #1E3A5F !important;
    }
    
    [data-baseweb="menu"] li {
        color: #ffffff !important;
        background-color: #1E3A5F !important;
    }
    
    [data-baseweb="menu"] li:hover {
        background-color: #2d5a87 !important;
    }
    
    .stSelectbox svg {
        fill: #ffffff !important;
    }
    
    /* ========================================
       BOTÕES - TEXTO BRANCO (FORÇADO)
       ======================================== */
    .stButton > button,
    .stButton > button *,
    .stButton > button p,
    .stButton > button span,
    .stButton > button div {
        width: 100%;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        background-color: #1E3A5F !important;
        color: #ffffff !important;
        border: none;
    }
    
    .stButton > button:hover,
    .stButton > button:hover * {
        background-color: #2d5a87 !important;
        color: #ffffff !important;
    }
    
    /* Botão primário (submit de formulário) */
    .stFormSubmitButton > button,
    .stFormSubmitButton > button *,
    .stFormSubmitButton > button p,
    .stFormSubmitButton > button span {
        background-color: #1E3A5F !important;
        color: #ffffff !important;
        border: none;
    }
    
    .stFormSubmitButton > button:hover,
    .stFormSubmitButton > button:hover * {
        background-color: #2d5a87 !important;
        color: #ffffff !important;
    }
    
    /* Forçar texto branco em TODOS os botões */
    button[kind="primary"],
    button[kind="primary"] *,
    button[kind="secondary"],
    button[kind="secondary"] * {
        color: #ffffff !important;
    }
    
    /* Texto dentro de botões */
    [data-testid="baseButton-secondary"],
    [data-testid="baseButton-secondary"] *,
    [data-testid="baseButton-primary"],
    [data-testid="baseButton-primary"] * {
        color: #ffffff !important;
    }
    
    /* ========================================
       RANKING
       ======================================== */
    .ranking-gold { 
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%) !important;
        color: #1E3A5F !important;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5rem;
    }
    .ranking-silver { 
        background: linear-gradient(135deg, #C0C0C0 0%, #A8A8A8 100%) !important;
        color: #1E3A5F !important;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5rem;
    }
    .ranking-bronze { 
        background: linear-gradient(135deg, #CD7F32 0%, #B8860B 100%) !important;
        color: #ffffff !important;
        font-weight: bold;
        border-radius: 8px;
        padding: 0.5rem;
    }
    
    /* ========================================
       MÉTRICAS
       ======================================== */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 900 !important;
        color: #1E3A5F !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.05) !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.95rem !important;
        font-weight: 700 !important;
        color: #495057 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.9rem !important;
        font-weight: 600 !important;
    }
    
    /* ========================================
       DATAFRAMES E TABELAS
       ======================================== */
    .stDataFrame {
        color: #1a1a2e !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08) !important;
    }
    
    .stDataFrame th {
        background: linear-gradient(135deg, #1E3A5F 0%, #2d5a87 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        padding: 1rem !important;
        text-transform: uppercase !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.5px !important;
    }
    
    .stDataFrame td {
        color: #1a1a2e !important;
        background: #ffffff !important;
        padding: 0.8rem !important;
        border-bottom: 1px solid #e9ecef !important;
        transition: background 0.2s ease !important;
    }
    
    .stDataFrame tr:nth-child(even) td {
        background: #f8f9fa !important;
    }
    
    .stDataFrame tr:hover td {
        background: #e3f2fd !important;
    }
    
    /* ========================================
       ALERTAS
       ======================================== */
    .stAlert {
        border-radius: 12px !important;
        border-left-width: 5px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05) !important;
        padding: 1rem 1.2rem !important;
    }
    
    /* Info alert */
    div[data-testid="stAlert"] {
        color: #1a1a2e !important;
        border-radius: 12px !important;
    }
    
    /* Success alert */
    .stSuccess {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%) !important;
        border-left-color: #28a745 !important;
    }
    
    /* Warning alert */
    .stWarning {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%) !important;
        border-left-color: #ffc107 !important;
    }
    
    /* Error alert */
    .stError {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%) !important;
        border-left-color: #dc3545 !important;
    }
    
    /* ========================================
       DIVIDERS
       ======================================== */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #D4AF37, transparent);
        margin: 1.5rem 0;
    }
    
    /* ========================================
       CAPTIONS E TEXTOS MENORES
       ======================================== */
    .stCaption, small, .caption {
        color: #6c757d !important;
    }

    /* SIDEBAR - FORÇAR TEXTO BRANCO EM TUDO */
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stMarkdown * {
        color: #ffffff !important;
    }
    
    /* Ícone de colapsar/expandir sidebar */
    button[data-testid="baseButton-headerNoPadding"],
    button[data-testid="baseButton-headerNoPadding"] * {
        color: #ffffff !important;
    }
    
    button[data-testid="baseButton-headerNoPadding"] svg,
    button[data-testid="baseButton-headerNoPadding"] svg * {
        fill: #ffffff !important;
        stroke: #ffffff !important;
    }
    
    /* Ícone >> quando sidebar está fechada */
    [data-testid="collapsedControl"] button,
    [data-testid="collapsedControl"] button * {
        color: #ffffff !important;
        background: #1E3A5F !important;
    }
    
    [data-testid="collapsedControl"] svg,
    [data-testid="collapsedControl"] svg * {
        fill: #ffffff !important;
        stroke: #ffffff !important;
    }
    
    /* Área do ícone de colapsar no topo da sidebar */
    [data-testid="stSidebarHeader"] {
        background: transparent !important;
    }
    
    [data-testid="stSidebarHeader"] button,
    [data-testid="stSidebarHeader"] button * {
        color: #ffffff !important;
    }
    
    [data-testid="stSidebarHeader"] svg,
    [data-testid="stSidebarHeader"] svg * {
        fill: #ffffff !important;
        stroke: #ffffff !important;
    }


    /* ========================================
       ÍCONE DA SIDEBAR - FORÇAR BRANCO
       ======================================== */
    
    /* Ícone >> quando sidebar está fechada - PRECISA SER VISÍVEL */
    [data-testid="collapsedControl"] {
        background: #1E3A5F !important;
        border-radius: 0 8px 8px 0;
        padding: 8px;
    }
    
    [data-testid="collapsedControl"] button {
        color: #ffffff !important;
        background: transparent !important;
    }
    
    [data-testid="collapsedControl"] svg,
    [data-testid="collapsedControl"] svg *,
    [data-testid="collapsedControl"] span {
        fill: #ffffff !important;
        stroke: #ffffff !important;
        color: #ffffff !important;
    }
    
    /* Ícone << quando sidebar está aberta */
    [data-testid="stSidebar"] button[kind="header"],
    [data-testid="stSidebar"] [data-testid="baseButton-header"],
    [data-testid="stSidebar"] [data-testid="baseButton-headerNoPadding"] {
        color: #ffffff !important;
        background: transparent !important;
    }
    
    [data-testid="stSidebar"] button[kind="header"] svg,
    [data-testid="stSidebar"] button[kind="header"] svg *,
    [data-testid="stSidebar"] [data-testid="baseButton-header"] svg,
    [data-testid="stSidebar"] [data-testid="baseButton-header"] svg *,
    [data-testid="stSidebar"] [data-testid="baseButton-headerNoPadding"] svg,
    [data-testid="stSidebar"] [data-testid="baseButton-headerNoPadding"] svg * {
        fill: #ffffff !important;
        stroke: #ffffff !important;
        color: #ffffff !important;
    }
    
    /* Material icons dentro da sidebar */
    [data-testid="stSidebar"] .material-icons,
    [data-testid="stSidebar"] span[class*="icon"],
    [data-testid="stSidebar"] span[data-testid*="icon"] {
        color: #ffffff !important;
    }
    
    /* Texto "keyboard_double_arrow_left" que aparece */
    [data-testid="stSidebar"] button span {
        color: #ffffff !important;
    }


    /* ========================================
       ÍCONE DA SIDEBAR FECHADA - SUPER VISÍVEL
       ======================================== */
    
    /* Container do botão quando sidebar está fechada */
    [data-testid="collapsedControl"] {
        background-color: #3498db !important;
        border-radius: 0 12px 12px 0 !important;
        padding: 12px 8px !important;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.3) !important;
        margin-top: 10px !important;
    }
    
    [data-testid="collapsedControl"]:hover {
        background-color: #2980b9 !important;
    }
    
    /* Botão dentro do container */
    [data-testid="collapsedControl"] > button,
    [data-testid="collapsedControl"] button {
        color: #ffffff !important;
        background: transparent !important;
    }
    
    /* SVG e ícones dentro */
    [data-testid="collapsedControl"] svg,
    [data-testid="collapsedControl"] svg path,
    [data-testid="collapsedControl"] svg *,
    [data-testid="collapsedControl"] span,
    [data-testid="collapsedControl"] * {
        fill: #ffffff !important;
        stroke: #ffffff !important;
        color: #ffffff !important;
    }
    
    /* Header escuro no topo quando sidebar fechada */
    header[data-testid="stHeader"] {
        background-color: #1E3A5F !important;
    }

</style>
""", unsafe_allow_html=True)

# Header fixo com logo do bolão
LOGO_URL = "https://raw.githubusercontent.com/LeandroCrespo/bolao-copa-2026/main/logo_copa2026.png"
st.markdown(f'''
<div class="fixed-header">
    <div class="fixed-header-content">
        <img src="{LOGO_URL}" class="fixed-header-logo" alt="Logo Copa 2026">
        <div>
            <div class="fixed-header-title">⚽ Bolão Copa 2026</div>
            <div class="fixed-header-subtitle">#WeAre26</div>
        </div>
    </div>
</div>
''', unsafe_allow_html=True)

# =============================================================================
# CABEÇALHO PADRÃO DAS PÁGINAS
# =============================================================================
MASCOTES_IMG = "https://raw.githubusercontent.com/LeandroCrespo/bolao-copa-2026/main/mascotes.png"

def render_page_header():
    """Renderiza o cabeçalho padrão com banner, mascotes e título"""
    # Banner decorativo com ícones dos países sede
    st.markdown('''
    <div style="
        background: linear-gradient(90deg, #E61D25 0%, #3CAC3B 25%, #2A398D 50%, #3CAC3B 75%, #E61D25 100%);
        padding: 8px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.15);
    ">
        <span style="font-size: 1.3rem; letter-spacing: 8px;">
            🍁 🇨🇦 • 🦅 🇲🇽 • ⭐ 🇺🇸
        </span>
    </div>
    ''', unsafe_allow_html=True)
    
    # Imagem dos mascotes
    st.markdown(f'''
    <div style="text-align: center; margin-bottom: 0.5rem;">
        <img src="{MASCOTES_IMG}" alt="Mascotes Copa 2026" style="max-width: 200px; height: auto;">
    </div>
    ''', unsafe_allow_html=True)
    
    # Título principal
    st.markdown('<h1 class="main-header">⚽ Bolão Copa do Mundo 2026</h1>', unsafe_allow_html=True)

# =============================================================================
# CONSTANTES
# =============================================================================
GRUPOS = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]
FASES = {
    "Grupos": "Fase de Grupos",
    "Oitavas32": "Oitavas de Final (32)",
    "Oitavas16": "Oitavas de Final (16)",
    "Quartas": "Quartas de Final",
    "Semifinal": "Semifinal",
    "Terceiro": "Disputa 3º Lugar",
    "Final": "Final"
}

# Mapeamento de códigos do mata-mata para nomes amigáveis
MATA_MATA_CODES = {
    "1A": "1º Grupo A", "2A": "2º Grupo A",
    "1B": "1º Grupo B", "2B": "2º Grupo B",
    "1C": "1º Grupo C", "2C": "2º Grupo C",
    "1D": "1º Grupo D", "2D": "2º Grupo D",
    "1E": "1º Grupo E", "2E": "2º Grupo E",
    "1F": "1º Grupo F", "2F": "2º Grupo F",
    "1G": "1º Grupo G", "2G": "2º Grupo G",
    "1H": "1º Grupo H", "2H": "2º Grupo H",
    "1I": "1º Grupo I", "2I": "2º Grupo I",
    "1J": "1º Grupo J", "2J": "2º Grupo J",
    "1K": "1º Grupo K", "2K": "2º Grupo K",
    "1L": "1º Grupo L", "2L": "2º Grupo L",
    "3AFJ": "3º (A/F/J)", "3BHJ": "3º (B/H/J)", "3BFJ": "3º (B/F/J)",
    "3CEF": "3º (C/E/F)", "3ADGF": "3º (A/D/G/F)", "3EFIK": "3º (E/F/I/K)",
    "W97": "Venc. Jogo 97", "W98": "Venc. Jogo 98", "W99": "Venc. Jogo 99", "W100": "Venc. Jogo 100",
    "W101": "Venc. Jogo 101", "W102": "Venc. Jogo 102", "W103": "Venc. Jogo 103", "W104": "Venc. Jogo 104",
    "W105": "Venc. Jogo 105", "W106": "Venc. Jogo 106", "W107": "Venc. Jogo 107", "W108": "Venc. Jogo 108",
    "W109": "Venc. Jogo 109", "W110": "Venc. Jogo 110", "W111": "Venc. Jogo 111", "W112": "Venc. Jogo 112",
    "W113": "Venc. Jogo 113", "W114": "Venc. Jogo 114", "W115": "Venc. Jogo 115", "W116": "Venc. Jogo 116",
    "W117": "Venc. Jogo 117", "W118": "Venc. Jogo 118", "W119": "Venc. Jogo 119", "W120": "Venc. Jogo 120",
    "W121": "Venc. Jogo 121", "W122": "Venc. Jogo 122", "W123": "Venc. Jogo 123", "W124": "Venc. Jogo 124",
    "W125": "Venc. Semi 1", "W126": "Venc. Semi 2",
    "L125": "Perd. Semi 1", "L126": "Perd. Semi 2",
}

# =============================================================================
# INICIALIZAÇÃO
# =============================================================================
@st.cache_resource
def init_app():
    """Inicializa o banco de dados com dados da Copa 2026"""
    return init_database_with_copa2026()

engine = init_app()

# =============================================================================
# GERENCIAMENTO DE SESSÃO
# =============================================================================
def init_session_state():
    """Inicializa variáveis de sessão"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    if 'show_register' not in st.session_state:
        st.session_state.show_register = False

init_session_state()

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================
def get_brazil_time():
    """Retorna a hora atual no fuso horário de Brasília"""
    tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(tz)

def format_datetime(dt):
    """Formata data/hora para exibição"""
    if dt is None:
        return "A definir"
    return dt.strftime("%d/%m/%Y %H:%M")

def format_date(dt):
    """Formata apenas a data"""
    if dt is None:
        return "A definir"
    return dt.strftime("%d/%m/%Y")

def format_time(dt):
    """Formata apenas a hora"""
    if dt is None:
        return "A definir"
    return dt.strftime("%H:%M")

def get_team_display(team, code=None):
    """Retorna nome do time para exibição com bandeira"""
    if team:
        # Mostra código + bandeira + nome para garantir visualização em todos os dispositivos
        return f"{team.code} {team.flag} {team.name}"
    elif code:
        # Verifica se é um código do mata-mata
        if code in MATA_MATA_CODES:
            return f"🏳️ {MATA_MATA_CODES[code]}"
        return f"🏳️ {code}"
    return "🏳️ A definir"

def can_predict_match(match):
    """Verifica se ainda é possível fazer palpite para um jogo"""
    if match.status != 'scheduled':
        return False
    now = get_brazil_time().replace(tzinfo=None)
    return now < match.datetime

def can_predict_podium(session):
    """Verifica se ainda é possível fazer palpite de pódio"""
    data_inicio = get_config_value(session, 'data_inicio_copa')
    if not data_inicio:
        return True
    try:
        dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d %H:%M")
        now = get_brazil_time().replace(tzinfo=None)
        return now < dt_inicio
    except:
        return True

def log_action(session, user_id, action, target_user_id=None, details=None):
    """Registra uma ação no log de auditoria"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        target_user_id=target_user_id,
        details=details
    )
    session.add(log)
    session.commit()

# =============================================================================
# PÁGINA DE LOGIN
# =============================================================================
def page_login():
    """Página de login e cadastro"""
    # Imagem dos mascotes embutida em base64
    MASCOTES_IMG = "https://raw.githubusercontent.com/LeandroCrespo/bolao-copa-2026/main/mascotes.png"
    
    # Imagem dos mascotes
    st.markdown(f'''
    <div style="text-align: center; margin-bottom: 1rem;">
        <img src="{MASCOTES_IMG}" alt="Mascotes Copa 2026" style="max-width: 350px; height: auto;">
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">Bolão Copa do Mundo 2026</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">🇺🇸 Estados Unidos • 🇨🇦 Canadá • 🇲🇽 México</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if not st.session_state.show_register:
            with st.form("login_form"):
                username = st.text_input("Usuário", placeholder="Digite seu usuário")
                password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
                submit = st.form_submit_button("Entrar", use_container_width=True)
                
                if submit:
                    if username and password:
                        session = get_session(engine)
                        user = authenticate_user(session, username, password)
                        session.close()
                        
                        if user:
                            st.session_state.user = {
                                'id': user.id,
                                'name': user.name,
                                'username': user.username,
                                'role': user.role
                            }
                            st.success(f"Bem-vindo(a), {user.name}!")
                            st.rerun()
                        else:
                            st.error("Usuário ou senha incorretos!")
                    else:
                        st.warning("Preencha todos os campos!")
            
            st.divider()
            st.markdown("<p style='text-align: center;'>Não tem conta?</p>", unsafe_allow_html=True)
            if st.button("📝 Criar minha conta", use_container_width=True):
                st.session_state.show_register = True
                st.rerun()
        
        else:
            st.markdown("### 📝 Criar Nova Conta")
            
            with st.form("register_form"):
                new_name = st.text_input("Nome completo", placeholder="Digite seu nome completo")
                new_username = st.text_input("Usuário", placeholder="Escolha um nome de usuário")
                new_password = st.text_input("Senha", type="password", placeholder="Escolha uma senha")
                confirm_password = st.text_input("Confirmar senha", type="password", placeholder="Digite a senha novamente")
                
                submit_register = st.form_submit_button("Criar Conta", use_container_width=True)
                
                if submit_register:
                    if not all([new_name, new_username, new_password, confirm_password]):
                        st.warning("Preencha todos os campos!")
                    elif new_password != confirm_password:
                        st.error("As senhas não coincidem!")
                    elif len(new_password) < 4:
                        st.error("A senha deve ter pelo menos 4 caracteres!")
                    elif len(new_username) < 3:
                        st.error("O usuário deve ter pelo menos 3 caracteres!")
                    else:
                        session = get_session(engine)
                        user = create_user(session, new_name, new_username, new_password, 'player')
                        session.close()
                        
                        if user:
                            st.success(f"Conta criada com sucesso! Faça login com o usuário '{new_username}'.")
                            st.session_state.show_register = False
                            st.rerun()
                        else:
                            st.error("Este nome de usuário já está em uso. Escolha outro.")
            
            st.divider()
            st.markdown("<p style='text-align: center;'>Já tem conta?</p>", unsafe_allow_html=True)
            if st.button("🔑 Fazer login", use_container_width=True):
                st.session_state.show_register = False
                st.rerun()

# =============================================================================
# PÁGINA INICIAL (DASHBOARD)
# =============================================================================
def page_home():
    """Página inicial com resumo do bolão"""
    # Cabeçalho padrão
    render_page_header()
    
    session = get_session(engine)
    
    try:
        user_stats = get_user_stats(session, st.session_state.user['id'])
        ranking = get_ranking(session)
        
        user_position = next(
            (r['posicao'] for r in ranking if r['user_id'] == st.session_state.user['id']),
            '-'
        )
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🏆 Sua Posição", f"{user_position}º" if user_position != '-' else '-')
        with col2:
            st.metric("⭐ Total de Pontos", user_stats.get('total_pontos', 0))
        with col3:
            st.metric("🎯 Placares Exatos", user_stats.get('placares_exatos', 0))
        with col4:
            st.metric("✅ Palpites Feitos", user_stats.get('total_palpites', 0))
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📅 Próximos Jogos")
            
            now = get_brazil_time().replace(tzinfo=None)
            proximos_jogos = session.query(Match).filter(
                Match.status == 'scheduled',
                Match.datetime > now
            ).order_by(Match.datetime).limit(5).all()
            
            if proximos_jogos:
                for match in proximos_jogos:
                    team1_display = get_team_display(match.team1, match.team1_code)
                    team2_display = get_team_display(match.team2, match.team2_code)
                    
                    # Verifica se já tem palpite
                    pred = session.query(Prediction).filter_by(
                        user_id=st.session_state.user['id'],
                        match_id=match.id
                    ).first()
                    
                    palpite_icon = "✅" if pred else "❌"
                    
                    st.markdown(f"""
                    <div class="match-card">
                        <strong>{team1_display}</strong> vs <strong>{team2_display}</strong><br>
                        <span class="match-info">🕐 {format_datetime(match.datetime)} | 📍 {match.city} | {palpite_icon} Palpite</span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Nenhum jogo programado.")
        
        with col2:
            st.subheader("🏆 Top 5 Ranking")
            
            if ranking:
                for r in ranking[:5]:
                    medal = ""
                    if r['posicao'] == 1:
                        medal = "🥇"
                    elif r['posicao'] == 2:
                        medal = "🥈"
                    elif r['posicao'] == 3:
                        medal = "🥉"
                    
                    st.markdown(f"{medal} **{r['posicao']}º** {r['nome']} - **{r['total_pontos']}** pts")
            else:
                st.info("Nenhum participante no ranking ainda.")
    
    finally:
        session.close()

# =============================================================================
# PÁGINA DE PALPITES - JOGOS
# =============================================================================
def page_palpites_jogos():
    """Página para fazer palpites nos jogos"""
    render_page_header()
    st.markdown("## 📝 Palpites dos Jogos")
    
    session = get_session(engine)
    
    try:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            fases_opcoes = ["Todas as Fases"] + list(FASES.keys())
            fase_selecionada = st.selectbox("Fase", fases_opcoes)
        with col2:
            grupos_opcoes = ["Todos os Grupos"] + GRUPOS
            grupo_selecionado = st.selectbox("Grupo", grupos_opcoes)
        
        # Query de jogos
        query = session.query(Match).order_by(Match.datetime)
        
        if fase_selecionada != "Todas as Fases":
            query = query.filter(Match.phase == fase_selecionada)
        
        if grupo_selecionado != "Todos os Grupos":
            query = query.filter(Match.group == grupo_selecionado)
        
        jogos = query.all()
        
        # Agrupa por data
        jogos_por_data = {}
        for jogo in jogos:
            data = jogo.datetime.strftime("%d/%m/%Y (%A)")
            if data not in jogos_por_data:
                jogos_por_data[data] = []
            jogos_por_data[data].append(jogo)
        
        # Exibe jogos agrupados
        for data, jogos_data in jogos_por_data.items():
            st.markdown(f"### 📅 {data}")
            
            for match in jogos_data:
                team1_display = get_team_display(match.team1, match.team1_code)
                team2_display = get_team_display(match.team2, match.team2_code)
                
                can_predict = can_predict_match(match)
                status_icon = "🟢" if can_predict else "🔴"
                
                with st.expander(f"{status_icon} {format_time(match.datetime)} - {team1_display} vs {team2_display}"):
                    st.markdown(f"**{team1_display}** VS **{team2_display}**")
                    st.markdown(f"📍 {match.city} | {FASES.get(match.phase, match.phase)} - Grupo {match.group or 'N/A'}")

                    
                    # Busca palpite existente
                    pred = session.query(Prediction).filter_by(
                        user_id=st.session_state.user['id'],
                        match_id=match.id
                    ).first()
                    
                    # Mostra indicação de palpite salvo
                    if pred:
                        data_salvo = pred.updated_at or pred.created_at
                        if data_salvo:
                            # Converter para horário de Brasília
                            import pytz
                            tz_brazil = pytz.timezone('America/Sao_Paulo')
                            if data_salvo.tzinfo is None:
                                data_salvo = pytz.utc.localize(data_salvo)
                            data_brazil = data_salvo.astimezone(tz_brazil)
                            st.success(f"✅ Palpite salvo em {data_brazil.strftime('%d/%m/%Y às %H:%M')}")
                    
                    if can_predict:
                        col1, col2 = st.columns(2)
                        with col1:
                            gols1 = st.number_input(
                                f"Gols {team1_display}",
                                min_value=0, max_value=20,
                                value=pred.pred_team1_score if pred else 0,
                                key=f"gols1_{match.id}"
                            )
                        with col2:
                            gols2 = st.number_input(
                                f"Gols {team2_display}",
                                min_value=0, max_value=20,
                                value=pred.pred_team2_score if pred else 0,
                                key=f"gols2_{match.id}"
                            )
                        
                        if st.button("💾 Salvar Palpite", key=f"save_{match.id}"):
                            if pred:
                                pred.pred_team1_score = gols1
                                pred.pred_team2_score = gols2
                            else:
                                pred = Prediction(
                                    user_id=st.session_state.user['id'],
                                    match_id=match.id,
                                    pred_team1_score=gols1,
                                    pred_team2_score=gols2
                                )
                                session.add(pred)
                            session.commit()
                            st.success("✅ Palpite salvo com sucesso!")
                            st.rerun()
                    else:
                        if pred:
                            st.info(f"Seu palpite: **{pred.pred_team1_score}** x **{pred.pred_team2_score}**")
                            if match.status == 'finished':
                                st.markdown(f"Resultado: **{match.team1_score}** x **{match.team2_score}**")
                                if pred.points_awarded is not None:
                                    st.markdown(f"Pontos: **{pred.points_awarded}**")
                        else:
                            st.warning("⏰ Prazo encerrado - Você não fez palpite para este jogo")
    
    finally:
        session.close()

# =============================================================================
# PÁGINA DE PALPITES - GRUPOS
# =============================================================================
def page_palpites_grupos():
    """Página para fazer palpites de classificação dos grupos"""
    render_page_header()
    st.markdown("## 🏅 Palpites de Classificação dos Grupos")
    
    session = get_session(engine)
    
    try:
        # Verifica se ainda pode fazer palpites (usa mesma lógica do pódio)
        can_predict = can_predict_podium(session)
        
        if can_predict:
            st.info("Escolha quem será o 1º e 2º colocado de cada grupo")
        else:
            st.warning("⏰ O prazo para palpites de grupos já encerrou! A Copa já começou.")
        
        teams = session.query(Team).order_by(Team.name).all()
        
        # Organiza em colunas de 3
        cols = st.columns(3)
        
        for idx, grupo in enumerate(GRUPOS):
            with cols[idx % 3]:
                st.markdown(f"### Grupo {grupo}")
                
                grupo_teams = [t for t in teams if t.group == grupo]
                
                if not grupo_teams:
                    st.warning(f"Nenhuma seleção no grupo {grupo}")
                    continue
                
                team_options = {t.id: f"{t.flag} {t.name}" for t in grupo_teams}
                team_ids = [None] + list(team_options.keys())
                
                # Busca palpite existente
                pred = session.query(GroupPrediction).filter_by(
                    user_id=st.session_state.user['id'],
                    group_name=grupo
                ).first()
                
                # Calcula classificação sugerida baseada nos palpites dos jogos
                from group_standings import get_predicted_group_standings
                standings = get_predicted_group_standings(session, st.session_state.user['id'], grupo)
                
                if standings and len(standings) >= 2:
                    st.markdown("**📊 Classificação baseada nos seus palpites:**")
                    for i, team_stat in enumerate(standings[:4], 1):
                        st.caption(f"{i}º {team_stat['team'].flag} {team_stat['team'].name} - {team_stat['points']} pts ({team_stat['wins']}V {team_stat['draws']}E {team_stat['losses']}D) | Saldo: {team_stat['goal_difference']:+d}")
                    st.caption("⚠️ Sugestão: Você pode usar essa classificação ou escolher manualmente")
                    st.divider()
                
                with st.form(f"grupo_{grupo}"):
                    # Define valores padrão baseados na classificação sugerida ou palpite existente
                    default_first = None
                    default_second = None
                    
                    if pred:
                        default_first = pred.first_place_team_id
                        default_second = pred.second_place_team_id
                    elif standings and len(standings) >= 2:
                        default_first = standings[0]['team'].id
                        default_second = standings[1]['team'].id
                    
                    primeiro = st.selectbox(
                        "1º Lugar",
                        options=team_ids,
                        format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                        index=team_ids.index(default_first) if default_first and default_first in team_ids else 0,
                        key=f"g{grupo}_1"
                    )
                    
                    segundo = st.selectbox(
                        "2º Lugar",
                        options=team_ids,
                        format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                        index=team_ids.index(default_second) if default_second and default_second in team_ids else 0,
                        key=f"g{grupo}_2"
                    )
                    
                    # Mostra indicação de palpite salvo
                    if pred:
                        data_salvo = pred.updated_at or pred.created_at
                        if data_salvo:
                            import pytz
                            tz_brazil = pytz.timezone('America/Sao_Paulo')
                            if data_salvo.tzinfo is None:
                                data_salvo = pytz.utc.localize(data_salvo)
                            data_brazil = data_salvo.astimezone(tz_brazil)
                            st.success(f"✅ Salvo em {data_brazil.strftime('%d/%m/%Y às %H:%M')}")
                    
                    if st.form_submit_button("💾 Salvar", disabled=not can_predict):
                        if not can_predict:
                            st.error("⏰ O prazo para palpites já encerrou!")
                        elif primeiro and segundo and primeiro != segundo:
                            if pred:
                                pred.first_place_team_id = primeiro
                                pred.second_place_team_id = segundo
                            else:
                                pred = GroupPrediction(
                                    user_id=st.session_state.user['id'],
                                    group_name=grupo,
                                    first_place_team_id=primeiro,
                                    second_place_team_id=segundo
                                )
                                session.add(pred)
                            session.commit()
                            st.success("Palpite salvo!")
                        else:
                            st.error("Selecione dois times diferentes!")
    
    finally:
        session.close()

# =============================================================================
# PÁGINA DE PALPITES - PÓDIO
# =============================================================================
def page_palpites_podio():
    """Página para fazer palpites do pódio"""
    render_page_header()
    st.markdown("## 🏆 Palpites do Pódio")
    
    session = get_session(engine)
    
    try:
        can_predict = can_predict_podium(session)
        
        if can_predict:
            st.info("Escolha quem será o Campeão, Vice-Campeão e 3º Lugar da Copa do Mundo 2026")
        else:
            st.warning("⏰ O prazo para palpites de pódio já encerrou!")
        
        teams = session.query(Team).order_by(Team.name).all()
        team_options = {t.id: f"{t.flag} {t.name}" for t in teams}
        team_ids = [None] + list(team_options.keys())
        
        # Busca palpite existente
        pred = session.query(PodiumPrediction).filter_by(
            user_id=st.session_state.user['id']
        ).first()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🥇 Campeão")
            campeao = st.selectbox(
                "Selecione o Campeão",
                options=team_ids,
                format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                index=team_ids.index(pred.champion_team_id) if pred and pred.champion_team_id in team_ids else 0,
                disabled=not can_predict,
                key="podio_campeao"
            )
        
        with col2:
            st.markdown("### 🥈 Vice-Campeão")
            vice = st.selectbox(
                "Selecione o Vice",
                options=team_ids,
                format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                index=team_ids.index(pred.runner_up_team_id) if pred and pred.runner_up_team_id in team_ids else 0,
                disabled=not can_predict,
                key="podio_vice"
            )
        
        with col3:
            st.markdown("### 🥉 3º Lugar")
            terceiro = st.selectbox(
                "Selecione o 3º Lugar",
                options=team_ids,
                format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                index=team_ids.index(pred.third_place_team_id) if pred and pred.third_place_team_id in team_ids else 0,
                disabled=not can_predict,
                key="podio_terceiro"
            )
        
        # Mostra indicação de palpite salvo
        if pred and (pred.champion_team_id or pred.runner_up_team_id or pred.third_place_team_id):
            data_salvo = pred.updated_at or pred.created_at
            if data_salvo:
                import pytz
                tz_brazil = pytz.timezone('America/Sao_Paulo')
                if data_salvo.tzinfo is None:
                    data_salvo = pytz.utc.localize(data_salvo)
                data_brazil = data_salvo.astimezone(tz_brazil)
                st.success(f"✅ Palpite de pódio salvo em {data_brazil.strftime('%d/%m/%Y às %H:%M')}")
        
        if can_predict:
            if st.button("💾 Salvar Palpite de Pódio", use_container_width=True):
                if campeao and vice and terceiro and len(set([campeao, vice, terceiro])) == 3:
                    if pred:
                        pred.champion_team_id = campeao
                        pred.runner_up_team_id = vice
                        pred.third_place_team_id = terceiro
                    else:
                        pred = PodiumPrediction(
                            user_id=st.session_state.user['id'],
                            champion_team_id=campeao,
                            runner_up_team_id=vice,
                            third_place_team_id=terceiro
                        )
                        session.add(pred)
                    session.commit()
                    st.success("Palpite de pódio salvo!")
                    st.rerun()
                else:
                    st.error("Selecione três times diferentes!")
    
    finally:
        session.close()



# =============================================================================
# PÁGINA DE DICAS - POWER RANKING FIFA
# =============================================================================
def page_dicas():
    """Página de Dicas com Power Ranking FIFA"""
    render_page_header()
    st.header("💡 Dicas para seus Palpites")
    
    # Texto explicativo sobre o ranking
    st.markdown("""
    ### 📊 Sobre o Ranking FIFA
    
    O **Ranking FIFA/Coca-Cola** é a classificação oficial das seleções masculinas de futebol, 
    atualizado mensalmente pela FIFA. Ele considera os resultados das partidas internacionais, 
    a importância dos jogos e a força dos adversários enfrentados.
    
    """)
    
    # Alerta destacado com cores chamativas
    st.markdown('''
    <div style="
        background: linear-gradient(135deg, #FF6B35 0%, #F7931E 50%, #FFD700 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(255, 107, 53, 0.4);
        border-left: 6px solid #E61D25;
    ">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 2.5rem;">⚠️</span>
            <div>
                <h3 style="color: #1E3A5F; margin: 0 0 8px 0; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">
                    IMPORTANTE - LEIA ANTES DE PALPITAR!
                </h3>
                <p style="color: #2A398D; margin: 0; font-size: 1.1rem; line-height: 1.6;">
                    Este ranking serve como uma <strong>referência</strong> para auxiliar nos seus palpites, 
                    mas <strong style="color: #E61D25;">NÃO deve ser seguido à risca</strong>! 
                    O futebol é imprevisível e grandes surpresas acontecem em toda Copa do Mundo. 
                    Seleções bem posicionadas podem tropeçar, enquanto equipes menos cotadas frequentemente surpreendem.
                </p>
                <p style="color: #1E3A5F; margin: 10px 0 0 0; font-size: 1.05rem; font-weight: 600;">
                    🎯 Use estas informações como um <strong>guia</strong>, mas confie também na sua 
                    <strong style="color: #3CAC3B;">intuição</strong> e 
                    <strong style="color: #3CAC3B;">conhecimento do futebol</strong>!
                </p>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown("""
    
    ---
    """)
    
    # Power Ranking das seleções da Copa 2026
    st.subheader("🏆 Power Ranking - Copa do Mundo 2026")
    
    # Dados do ranking FIFA (dezembro 2025)
    import pandas as pd
    
    # Tier 1 - Favoritas
    st.markdown("### ⭐ FAVORITAS")
    tier1 = pd.DataFrame([
        {"#": 1, "Seleção": "🇪🇸 Espanha", "Ranking FIFA": "#1", "Pontos": 1877, "Grupo": "H"},
        {"#": 2, "Seleção": "🇦🇷 Argentina", "Ranking FIFA": "#2", "Pontos": 1873, "Grupo": "J"},
        {"#": 3, "Seleção": "🇫🇷 França", "Ranking FIFA": "#3", "Pontos": 1870, "Grupo": "I"},
        {"#": 4, "Seleção": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Inglaterra", "Ranking FIFA": "#4", "Pontos": 1834, "Grupo": "L"},
        {"#": 5, "Seleção": "🇧🇷 Brasil", "Ranking FIFA": "#5", "Pontos": 1760, "Grupo": "C"},
    ])
    st.dataframe(tier1, use_container_width=True, hide_index=True)
    st.markdown("---")
    
    # Tier 2 - Fortes Candidatas
    st.markdown("### 🥇 FORTES CANDIDATAS")
    tier2 = pd.DataFrame([
        {"#": 6, "Seleção": "🇵🇹 Portugal", "Ranking FIFA": "#6", "Pontos": 1760, "Grupo": "K"},
        {"#": 7, "Seleção": "🇳🇱 Holanda", "Ranking FIFA": "#7", "Pontos": 1756, "Grupo": "F"},
        {"#": 8, "Seleção": "🇧🇪 Bélgica", "Ranking FIFA": "#8", "Pontos": 1731, "Grupo": "G"},
        {"#": 9, "Seleção": "🇩🇪 Alemanha", "Ranking FIFA": "#9", "Pontos": 1724, "Grupo": "E"},
        {"#": 10, "Seleção": "🇭🇷 Croácia", "Ranking FIFA": "#10", "Pontos": 1717, "Grupo": "L"},
    ])
    st.dataframe(tier2, use_container_width=True, hide_index=True)
    st.markdown("---")
    
    # Tier 3 - Competitivas
    st.markdown("### 🥈 COMPETITIVAS")
    tier3 = pd.DataFrame([
        {"#": 11, "Seleção": "🇲🇦 Marrocos", "Ranking FIFA": "#11", "Pontos": 1716, "Grupo": "C"},
        {"#": 12, "Seleção": "🇨🇴 Colômbia", "Ranking FIFA": "#13", "Pontos": 1701, "Grupo": "K"},
        {"#": 13, "Seleção": "🇺🇸 Estados Unidos", "Ranking FIFA": "#14", "Pontos": 1682, "Grupo": "D"},
        {"#": 14, "Seleção": "🇲🇽 México", "Ranking FIFA": "#15", "Pontos": 1676, "Grupo": "A"},
        {"#": 15, "Seleção": "🇺🇾 Uruguai", "Ranking FIFA": "#16", "Pontos": 1673, "Grupo": "H"},
        {"#": 16, "Seleção": "🇨🇭 Suíça", "Ranking FIFA": "#17", "Pontos": 1655, "Grupo": "B"},
        {"#": 17, "Seleção": "🇯🇵 Japão", "Ranking FIFA": "#18", "Pontos": 1650, "Grupo": "F"},
        {"#": 18, "Seleção": "🇸🇳 Senegal", "Ranking FIFA": "#19", "Pontos": 1648, "Grupo": "I"},
        {"#": 19, "Seleção": "🇮🇷 Irã", "Ranking FIFA": "#20", "Pontos": 1617, "Grupo": "G"},
        {"#": 20, "Seleção": "🇰🇷 Coreia do Sul", "Ranking FIFA": "#22", "Pontos": 1599, "Grupo": "A"},
    ])
    st.dataframe(tier3, use_container_width=True, hide_index=True)
    st.markdown("---")
    
    # Tier 4 - Médias
    st.markdown("### 🥉 MÉDIAS")
    tier4 = pd.DataFrame([
        {"#": 21, "Seleção": "🇪🇨 Equador", "Ranking FIFA": "#23", "Pontos": 1592, "Grupo": "E"},
        {"#": 22, "Seleção": "🇦🇹 Áustria", "Ranking FIFA": "#24", "Pontos": 1586, "Grupo": "J"},
        {"#": 23, "Seleção": "🇦🇺 Austrália", "Ranking FIFA": "#26", "Pontos": 1574, "Grupo": "D"},
        {"#": 24, "Seleção": "🇨🇦 Canadá", "Ranking FIFA": "#27", "Pontos": 1559, "Grupo": "B"},
        {"#": 25, "Seleção": "🇳🇴 Noruega", "Ranking FIFA": "#29", "Pontos": 1553, "Grupo": "I"},
        {"#": 26, "Seleção": "🇵🇦 Panamá", "Ranking FIFA": "#30", "Pontos": 1540, "Grupo": "L"},
        {"#": 27, "Seleção": "🇩🇿 Argélia", "Ranking FIFA": "#34", "Pontos": 1518, "Grupo": "J"},
        {"#": 28, "Seleção": "🇪🇬 Egito", "Ranking FIFA": "#35", "Pontos": 1515, "Grupo": "G"},
        {"#": 29, "Seleção": "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Escócia", "Ranking FIFA": "#36", "Pontos": 1507, "Grupo": "C"},
        {"#": 30, "Seleção": "🇵🇾 Paraguai", "Ranking FIFA": "#39", "Pontos": 1502, "Grupo": "D"},
    ])
    st.dataframe(tier4, use_container_width=True, hide_index=True)
    st.markdown("---")
    
    # Tier 5 - Zebras Potenciais
    st.markdown("### 🦓 ZEBRAS POTENCIAIS")
    tier5 = pd.DataFrame([
        {"#": 31, "Seleção": "🇹🇳 Tunísia", "Ranking FIFA": "#41", "Pontos": 1495, "Grupo": "F"},
        {"#": 32, "Seleção": "🇨🇮 Costa do Marfim", "Ranking FIFA": "#42", "Pontos": 1490, "Grupo": "E"},
        {"#": 33, "Seleção": "🇺🇿 Uzbequistão", "Ranking FIFA": "#50", "Pontos": 1462, "Grupo": "K"},
        {"#": 34, "Seleção": "🇶🇦 Qatar", "Ranking FIFA": "#54", "Pontos": 1455, "Grupo": "B"},
        {"#": 35, "Seleção": "🇸🇦 Arábia Saudita", "Ranking FIFA": "#60", "Pontos": 1429, "Grupo": "H"},
        {"#": 36, "Seleção": "🇿🇦 África do Sul", "Ranking FIFA": "#61", "Pontos": 1427, "Grupo": "A"},
        {"#": 37, "Seleção": "🇯🇴 Jordânia", "Ranking FIFA": "#64", "Pontos": 1389, "Grupo": "J"},
        {"#": 38, "Seleção": "🇨🇻 Cabo Verde", "Ranking FIFA": "#67", "Pontos": 1370, "Grupo": "H"},
        {"#": 39, "Seleção": "🇬🇭 Gana", "Ranking FIFA": "#72", "Pontos": 1351, "Grupo": "L"},
        {"#": 40, "Seleção": "🇨🇼 Curaçao", "Ranking FIFA": "#82", "Pontos": 1303, "Grupo": "E"},
        {"#": 41, "Seleção": "🇭🇹 Haiti", "Ranking FIFA": "#84", "Pontos": 1294, "Grupo": "C"},
        {"#": 42, "Seleção": "🇳🇿 Nova Zelândia", "Ranking FIFA": "#87", "Pontos": 1279, "Grupo": "G"},
    ])
    st.dataframe(tier5, use_container_width=True, hide_index=True)
    st.markdown("---")
    
    # Seleções da Repescagem
    st.subheader("🎯 Seleções da Repescagem (A Definir)")
    
    st.markdown("""
    Estas seleções ainda disputarão a repescagem para definir as últimas vagas:
    
    **🇪🇺 Repescagem Europa:**
    | Chave | Seleções |
    |-------|----------|
    | Europa A | 🇮🇹 Itália, 🇮🇪 Irlanda do Norte, 🏴󠁧󠁢󠁷󠁬󠁳󠁿 País de Gales, 🇧🇦 Bósnia |
    | Europa B | 🇺🇦 Ucrânia, 🇸🇪 Suécia, 🇵🇱 Polônia, 🇦🇱 Albânia |
    | Europa C | 🇹🇷 Turquia, 🇷🇴 Romênia, 🇸🇰 Eslováquia, 🇽🇰 Kosovo |
    | Europa D | 🇨🇿 Rep. Tcheca, 🇮🇪 Irlanda, 🇩🇰 Dinamarca, 🇲🇰 Macedônia do Norte |
    
    **🌍 Repescagem Intercontinental:**
    | Chave | Seleções |
    |-------|----------|
    | Intercon. 1 | 🇨🇩 Congo DR, 🇯🇲 Jamaica, 🇳🇨 Nova Caledônia |
    | Intercon. 2 | 🇧🇴 Bolívia, 🇸🇷 Suriname, 🇮🇶 Iraque |
    """)
    
    # Dicas extras
    st.subheader("📝 Dicas Extras")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🏠 Fator Casa:**
        - 🇺🇸 EUA, 🇨🇦 Canadá e 🇲🇽 México jogam em casa
        - Seleções anfitriãs costumam ter desempenho acima do esperado
        - Torcida e clima familiar fazem diferença!
        """)
        
        st.markdown("""
        **📈 Seleções em Alta:**
        - 🇲🇦 Marrocos: Semifinalista em 2022
        - 🇯🇵 Japão: Eliminando potências europeias
        - 🇦🇺 Austrália: Crescimento consistente
        """)
    
    with col2:
        st.markdown("""
        **⚠️ Atenção aos Grupos:**
        - **Grupo C** (Brasil, Marrocos, Escócia, Haiti): Grupo da morte!
        - **Grupo L** (Inglaterra, Croácia, Gana, Panamá): Muito equilibrado
        - **Grupo J** (Argentina, Argélia, Áustria, Jordânia): Argentina favorita
        """)
        
        st.markdown("""
        **🎲 Zebras Históricas:**
        - Coreia do Sul 2002 (4º lugar)
        - Croácia 2018 (Vice-campeã)
        - Marrocos 2022 (4º lugar)
        """)
    
    # Rodapé
    st.markdown("---")
    st.caption("📅 Ranking FIFA atualizado em Dezembro/2025 | Fonte: FIFA.com")


# =============================================================================
# PÁGINA DE RANKING
# =============================================================================
def page_ranking():
    """
    Página de ranking com visual aprimorado:
    - Pódio para os 3 primeiros
    - Destaque para zona de rebaixamento
    - Configuração de quantos serão rebaixados
    """
    import streamlit as st
    from db import get_session, get_config_value, set_config_value
    from scoring import get_ranking
    
    render_page_header()
    st.header("🏆 Ranking do Bolão")
    
    with get_session(engine) as session:
        ranking = get_ranking(session)
        
        if not ranking:
            st.info("Nenhum participante no ranking ainda.")
            return
        
        # Configuração de rebaixamento (apenas admin vê)
        qtd_rebaixados = int(get_config_value(session, 'qtd_rebaixados', '2'))
        
        if st.session_state.user.get('role') == 'admin':
            with st.expander("⚙️ Configurar Zona de Rebaixamento"):
                nova_qtd = st.number_input(
                    "Quantidade de rebaixados:",
                    min_value=0,
                    max_value=10,
                    value=qtd_rebaixados,
                    help="Define quantos participantes estarão na zona de rebaixamento"
                )
                if st.button("💾 Salvar Configuração"):
                    set_config_value(session, 'qtd_rebaixados', str(nova_qtd))
                    st.success("✅ Configuração salva!")
                    st.rerun()
        
        # CSS para o pódio e ranking
        st.markdown("""
        <style>
            /* Marca d'água do logo Copa 2026 */
            .ranking-watermark {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 400px;
                height: 400px;
                background-image: url('https://raw.githubusercontent.com/LeandroCrespo/bolao-copa-2026/main/logo_copa2026.png');
                background-size: contain;
                background-repeat: no-repeat;
                background-position: center;
                opacity: 0.06;
                pointer-events: none;
                z-index: 0;
            }
            
            .podio-container {
                display: flex;
                justify-content: center;
                align-items: flex-end;
                gap: 20px;
                margin: 30px 0;
                padding: 20px;
                position: relative;
                z-index: 1;
            }
            
            .podio-item {
                text-align: center;
                border-radius: 15px;
                padding: 20px;
                min-width: 150px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                background: transparent !important;
            }
            
            .podio-1 {
                background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%) !important;
                height: 200px;
                order: 2;
            }
            
            .podio-2 {
                background: linear-gradient(135deg, #C0C0C0 0%, #A8A8A8 100%) !important;
                height: 160px;
                order: 1;
            }
            
            .podio-3 {
                background: linear-gradient(135deg, #CD7F32 0%, #B8860B 100%) !important;
                height: 130px;
                order: 3;
            }
            
            /* Forçar cores corretas no pódio */
            .podio-item.podio-1,
            .podio-item.podio-2,
            .podio-item.podio-3 {
                color: #1a1a2e !important;
            }
            
            .podio-item.podio-1 *,
            .podio-item.podio-2 *,
            .podio-item.podio-3 * {
                background: transparent !important;
                color: #1a1a2e !important;
            }
            
            .podio-posicao {
                font-size: 2.5rem;
                font-weight: bold;
                margin-bottom: 10px;
                background: transparent !important;
            }
            
            .podio-nome {
                font-size: 1.1rem;
                font-weight: 600;
                color: #1a1a2e !important;
                margin-bottom: 5px;
                background: transparent !important;
            }
            
            .podio-pontos {
                font-size: 1.3rem;
                font-weight: bold;
                color: #1E3A5F !important;
                background: transparent !important;
            }
            
            .ranking-row {
                display: flex;
                align-items: center;
                padding: 12px 20px;
                margin: 5px 0;
                border-radius: 10px;
                background: #ffffff;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            
            .ranking-row-rebaixado {
                background: linear-gradient(90deg, #ffebee 0%, #ffffff 100%);
                border-left: 4px solid #E63946;
            }
            
            .ranking-posicao {
                font-size: 1.5rem;
                font-weight: bold;
                width: 50px;
                color: #1E3A5F;
            }
            
            .ranking-nome {
                flex: 1;
                font-size: 1.1rem;
                font-weight: 600;
                color: #1a1a2e;
            }
            
            .ranking-pontos {
                font-size: 1.2rem;
                font-weight: bold;
                color: #1E3A5F;
                background: #e9ecef;
                padding: 5px 15px;
                border-radius: 20px;
            }
            
            /* CSS da zona de rebaixamento removido - usando estilo inline */
            
            /* ========================================
               PÓDIO RESPONSIVO - MOBILE
               Espaçamento uniforme entre os cards
               ======================================== */
            
            /* Desktop: manter efeito de pódio escalonado */
            @media (min-width: 769px) {
                .podio-2 {
                    margin-top: 50px !important;
                }
                .podio-3 {
                    margin-top: 80px !important;
                }
            }
            
            /* Mobile: espaçamento uniforme e altura adequada */
            @media (max-width: 768px) {
                .podio-card {
                    margin-top: 0 !important;
                    margin-bottom: 15px !important;
                    min-height: auto !important;
                    height: auto !important;
                    padding-bottom: 20px !important;
                    overflow: visible !important;
                }
                
                .podio-1, .podio-2, .podio-3 {
                    margin-top: 0 !important;
                    min-height: auto !important;
                    height: auto !important;
                }
                
                /* Garantir que o conteúdo não seja cortado */
                [data-testid="column"] {
                    overflow: visible !important;
                }
                
                [data-testid="column"] > div {
                    overflow: visible !important;
                }
            }
        
    /* ========================================
       ÍCONE DA SIDEBAR - FORÇAR BRANCO
       ======================================== */
    
    /* Ícone >> quando sidebar está fechada - PRECISA SER VISÍVEL */
    [data-testid="collapsedControl"] {
        background: #1E3A5F !important;
        border-radius: 0 8px 8px 0;
        padding: 8px;
    }
    
    [data-testid="collapsedControl"] button {
        color: #ffffff !important;
        background: transparent !important;
    }
    
    [data-testid="collapsedControl"] svg,
    [data-testid="collapsedControl"] svg *,
    [data-testid="collapsedControl"] span {
        fill: #ffffff !important;
        stroke: #ffffff !important;
        color: #ffffff !important;
    }
    
    /* Ícone << quando sidebar está aberta */
    [data-testid="stSidebar"] button[kind="header"],
    [data-testid="stSidebar"] [data-testid="baseButton-header"],
    [data-testid="stSidebar"] [data-testid="baseButton-headerNoPadding"] {
        color: #ffffff !important;
        background: transparent !important;
    }
    
    [data-testid="stSidebar"] button[kind="header"] svg,
    [data-testid="stSidebar"] button[kind="header"] svg *,
    [data-testid="stSidebar"] [data-testid="baseButton-header"] svg,
    [data-testid="stSidebar"] [data-testid="baseButton-header"] svg *,
    [data-testid="stSidebar"] [data-testid="baseButton-headerNoPadding"] svg,
    [data-testid="stSidebar"] [data-testid="baseButton-headerNoPadding"] svg * {
        fill: #ffffff !important;
        stroke: #ffffff !important;
        color: #ffffff !important;
    }
    
    /* Material icons dentro da sidebar */
    [data-testid="stSidebar"] .material-icons,
    [data-testid="stSidebar"] span[class*="icon"],
    [data-testid="stSidebar"] span[data-testid*="icon"] {
        color: #ffffff !important;
    }
    
    /* Texto "keyboard_double_arrow_left" que aparece */
    [data-testid="stSidebar"] button span {
        color: #ffffff !important;
    }


    /* ========================================
       ÍCONE DA SIDEBAR FECHADA - SUPER VISÍVEL
       ======================================== */
    
    /* Container do botão quando sidebar está fechada */
    [data-testid="collapsedControl"] {
        background-color: #3498db !important;
        border-radius: 0 12px 12px 0 !important;
        padding: 12px 8px !important;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.3) !important;
        margin-top: 10px !important;
    }
    
    [data-testid="collapsedControl"]:hover {
        background-color: #2980b9 !important;
    }
    
    /* Botão dentro do container */
    [data-testid="collapsedControl"] > button,
    [data-testid="collapsedControl"] button {
        color: #ffffff !important;
        background: transparent !important;
    }
    
    /* SVG e ícones dentro */
    [data-testid="collapsedControl"] svg,
    [data-testid="collapsedControl"] svg path,
    [data-testid="collapsedControl"] svg *,
    [data-testid="collapsedControl"] span,
    [data-testid="collapsedControl"] * {
        fill: #ffffff !important;
        stroke: #ffffff !important;
        color: #ffffff !important;
    }
    
    /* Header escuro no topo quando sidebar fechada */
    header[data-testid="stHeader"] {
        background-color: #1E3A5F !important;
    }

</style>
        """, unsafe_allow_html=True)
        
        # Adiciona marca d'água do logo Copa 2026
        st.markdown('<div class="ranking-watermark"></div>', unsafe_allow_html=True)
        
        # ========================================
        # PÓDIO - TOP 3
        # ========================================
        st.subheader("🥇 Pódio")
        
        if len(ranking) >= 3:
            # Pódio visual usando st.columns do Streamlit
            # No desktop: 2º | 1º | 3º (formato tradicional de pódio)
            # No mobile: os cards empilham automaticamente
            
            col_space1, col2, col1, col3, col_space2 = st.columns([0.5, 1, 1.2, 1, 0.5])
            
            # 2º lugar (esquerda no desktop)
            with col2:
                st.markdown(f'''
                <div class="podio-card podio-2" style="
                    background: linear-gradient(135deg, #E8E8E8 0%, #C0C0C0 50%, #A8A8A8 100%);
                    border-radius: 20px;
                    padding: 35px 20px 25px 20px;
                    text-align: center;
                    box-shadow: 0 8px 30px rgba(192,192,192,0.4), inset 0 2px 10px rgba(255,255,255,0.5);
                    border: 3px solid #d4d4d4;
                    position: relative;
                    min-height: 220px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                ">
                    <div style="
                        position: absolute;
                        top: 8px;
                        left: 50%;
                        transform: translateX(-50%);
                        background: linear-gradient(135deg, #1E3A5F 0%, #2d5a87 100%);
                        color: white;
                        padding: 5px 15px;
                        border-radius: 15px;
                        font-size: 0.75rem;
                        font-weight: bold;
                        white-space: nowrap;
                    ">2º LUGAR</div>
                    <div style="font-size: 3rem; margin: 15px 0 10px 0;">🥈</div>
                    <div style="font-size: 1.1rem; font-weight: 700; color: #1a1a2e; margin-bottom: 12px;">{ranking[1]['nome']}</div>
                    <div style="
                        font-size: 1.5rem;
                        font-weight: 800;
                        color: #1E3A5F;
                        background: rgba(255,255,255,0.5);
                        padding: 8px 15px;
                        border-radius: 10px;
                        display: inline-block;
                        margin: 0 auto;
                    ">{ranking[1]['total_pontos']} pts</div>
                </div>
                ''', unsafe_allow_html=True)
            
            # 1º lugar (centro, mais alto)
            with col1:
                st.markdown(f'''
                <div class="podio-card podio-1" style="
                    background: linear-gradient(135deg, #FFE55C 0%, #FFD700 30%, #FFA500 70%, #FF8C00 100%);
                    border-radius: 20px;
                    padding: 40px 25px 30px 25px;
                    text-align: center;
                    box-shadow: 0 10px 40px rgba(255,215,0,0.5), inset 0 2px 15px rgba(255,255,255,0.6);
                    border: 4px solid #FFD700;
                    position: relative;
                    min-height: 240px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                ">
                    <div style="
                        position: absolute;
                        top: 8px;
                        left: 50%;
                        transform: translateX(-50%);
                        background: linear-gradient(135deg, #1E3A5F 0%, #2d5a87 100%);
                        color: white;
                        padding: 6px 18px;
                        border-radius: 15px;
                        font-size: 0.85rem;
                        font-weight: bold;
                        white-space: nowrap;
                    ">🏆 CAMPEÃO</div>
                    <div style="font-size: 4rem; margin: 20px 0 10px 0;">🥇</div>
                    <div style="font-size: 1.3rem; font-weight: 800; color: #1a1a2e; margin-bottom: 12px;">{ranking[0]['nome']}</div>
                    <div style="
                        font-size: 1.8rem;
                        font-weight: 900;
                        color: #1E3A5F;
                        background: rgba(255,255,255,0.6);
                        padding: 10px 20px;
                        border-radius: 12px;
                        display: inline-block;
                        margin: 0 auto;
                    ">{ranking[0]['total_pontos']} pts</div>
                </div>
                ''', unsafe_allow_html=True)
            
            # 3º lugar (direita no desktop)
            with col3:
                st.markdown(f'''
                <div class="podio-card podio-3" style="
                    background: linear-gradient(135deg, #E6A86E 0%, #CD7F32 50%, #B8860B 100%);
                    border-radius: 20px;
                    padding: 35px 15px 25px 15px;
                    text-align: center;
                    box-shadow: 0 8px 30px rgba(205,127,50,0.4), inset 0 2px 10px rgba(255,255,255,0.4);
                    border: 3px solid #CD7F32;
                    position: relative;
                    min-height: 220px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                ">
                    <div style="
                        position: absolute;
                        top: 8px;
                        left: 50%;
                        transform: translateX(-50%);
                        background: linear-gradient(135deg, #1E3A5F 0%, #2d5a87 100%);
                        color: white;
                        padding: 5px 15px;
                        border-radius: 15px;
                        font-size: 0.75rem;
                        font-weight: bold;
                        white-space: nowrap;
                    ">3º LUGAR</div>
                    <div style="font-size: 2.5rem; margin: 15px 0 10px 0;">🥉</div>
                    <div style="font-size: 1rem; font-weight: 700; color: #ffffff; margin-bottom: 12px;">{ranking[2]['nome']}</div>
                    <div style="
                        font-size: 1.3rem;
                        font-weight: 800;
                        color: #1E3A5F;
                        background: rgba(255,255,255,0.5);
                        padding: 8px 15px;
                        border-radius: 10px;
                        display: inline-block;
                        margin: 0 auto;
                    ">{ranking[2]['total_pontos']} pts</div>
                </div>
                ''', unsafe_allow_html=True)
        
        elif len(ranking) > 0:
            # Menos de 3 participantes - mostra o que tem
            for i, r in enumerate(ranking[:3]):
                medalha = ["🥇", "🥈", "🥉"][i]
                st.markdown(f"**{medalha} {r['nome']}** - {r['total_pontos']} pts")
        
        st.divider()
        
        # ========================================
        # RANKING COMPLETO
        # ========================================
        st.subheader("📊 Classificação Completa")
        
        # Determina a posição de início da zona de rebaixamento
        total_participantes = len(ranking)
        inicio_rebaixamento = total_participantes - qtd_rebaixados
        
        # Mostra ranking - separado em duas partes (antes e depois da zona de rebaixamento)
        ranking_html_normal = ""
        ranking_html_rebaixados = ""
        
        for i, r in enumerate(ranking):
            posicao = i + 1
            nome = r['nome']
            pontos = r['total_pontos']
            
            # Verifica se está na zona de rebaixamento
            is_rebaixado = posicao > inicio_rebaixamento and qtd_rebaixados > 0
            
            # Classe CSS
            row_class = "ranking-row-rebaixado" if is_rebaixado else ""
            
            # Ícone de posição
            if posicao == 1:
                icone = "🥇"
            elif posicao == 2:
                icone = "🥈"
            elif posicao == 3:
                icone = "🥉"
            elif is_rebaixado:
                icone = f"⬇️ {posicao}º"
            else:
                icone = f"{posicao}º"
            
            row_html = f'''
            <div class="ranking-row {row_class}">
                <div class="ranking-posicao">{icone}</div>
                <div class="ranking-nome">{nome}</div>
                <div class="ranking-pontos">{pontos} pts</div>
            </div>
            '''
            
            if is_rebaixado:
                ranking_html_rebaixados += row_html
            else:
                ranking_html_normal += row_html
        
        # Renderiza ranking normal
        st.markdown(ranking_html_normal, unsafe_allow_html=True)
        
        # Renderiza zona de rebaixamento (se houver)
        if qtd_rebaixados > 0 and ranking_html_rebaixados:
            st.warning(f"⚠️ ZONA DE REBAIXAMENTO ({qtd_rebaixados} {'vaga' if qtd_rebaixados == 1 else 'vagas'})")
            st.markdown(ranking_html_rebaixados, unsafe_allow_html=True)
        
        # ========================================
        # ESTATÍSTICAS ADICIONAIS
        # ========================================
        st.divider()
        st.subheader("📈 Estatísticas")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Participantes", total_participantes)
        
        with col2:
            if ranking:
                maior_pontuacao = max(r['total_pontos'] for r in ranking)
                st.metric("🏆 Maior Pontuação", f"{maior_pontuacao} pts")
        
        with col3:
            if ranking:
                media = sum(r['total_pontos'] for r in ranking) / len(ranking)
                st.metric("📊 Média", f"{media:.1f} pts")
        
        with col4:
            st.metric("⬇️ Zona de Rebaixamento", f"{qtd_rebaixados} vagas")
        
        # ========================================
        # CRITÉRIOS DE DESEMPATE
        # ========================================
        with st.expander("📋 Critérios de Desempate"):
            st.markdown("""
            Em caso de empate em pontos, os critérios de desempate são:
            
            1. **Maior número de placares exatos** (20 pts)
            2. **Maior número de acerto de Vencedores com gols corretos** (15 pts)
            3. **Maior número de acerto de Vencedores** (10 pts)
            4. **Maior número de acerto de classificados no grupo**
            5. **Maior número de acerto de pódio**
            6. **Maior número de acerto de gols de um time** (5 pts)
            7. **Menos palpites zerados**
            8. **Ordem de inscrição** (quem se inscreveu primeiro)
            """)


# =============================================================================
# PÁGINA DE ESTATÍSTICAS
# =============================================================================
def page_estatisticas():
    """Página com estatísticas do usuário"""
    import plotly.graph_objects as go
    import plotly.express as px
    from datetime import datetime, timedelta
    
    render_page_header()
    st.markdown("## 📈 Suas Estatísticas")
    
    session = get_session(engine)
    
    try:
        stats = get_user_stats(session, st.session_state.user['id'])
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("⭐ Total de Pontos", stats.get('total_pontos', 0))
            st.metric("🎯 Placares Exatos", stats.get('placares_exatos', 0))
        
        with col2:
            st.metric("✅ Resultados Corretos", stats.get('resultados_corretos', 0))
            st.metric("📝 Total de Palpites", stats.get('total_palpites', 0))
        
        with col3:
            st.metric("🏅 Pontos de Grupos", stats.get('pontos_grupos', 0))
            st.metric("🏆 Pontos de Pódio", stats.get('pontos_podio', 0))
        
        st.divider()
        
        # ========================================
        # GRÁFICO DE EVOLUÇÃO DE PONTOS
        # ========================================
        st.subheader("📈 Evolução de Pontos")
        
        # Busca todos os palpites do usuário com pontos de jogos que já iniciaram
        from datetime import datetime
        import pytz
        
        now = datetime.now(pytz.timezone('America/Sao_Paulo'))
        
        # Busca palpites com pontos
        user_predictions = session.query(Prediction).filter(
            Prediction.user_id == st.session_state.user['id'],
            Prediction.points_awarded > 0
        ).all()
        
        if user_predictions:
            # Agrupa pontos por data do jogo (apenas jogos que já iniciaram)
            pontos_por_data = {}
            for pred in user_predictions:
                match = session.query(Match).get(pred.match_id)
                if match and match.datetime:
                    # Só considera se o jogo já iniciou
                    match_time = match.datetime
                    if match_time.tzinfo is None:
                        match_time = pytz.timezone('America/Sao_Paulo').localize(match_time)
                    
                    if match_time <= now:
                        data_str = match.datetime.strftime('%d/%m')
                        if data_str not in pontos_por_data:
                            pontos_por_data[data_str] = 0
                        pontos_por_data[data_str] += pred.points_awarded
            
            if pontos_por_data:
                # Ordena por data
                datas = list(pontos_por_data.keys())
                pontos = list(pontos_por_data.values())
                
                # Calcula pontos acumulados
                pontos_acumulados = []
                acumulado = 0
                for p in pontos:
                    acumulado += p
                    pontos_acumulados.append(acumulado)
                
                # Calcula limites dinâmicos para os eixos
                max_acumulado = max(pontos_acumulados) if pontos_acumulados else 0
                max_dia = max(pontos) if pontos else 0
                
                # Usa o maior valor entre os dois para ter a mesma escala
                y_max = max(max_acumulado, max_dia) * 1.2 if max(max_acumulado, max_dia) > 0 else 10
                
                # Cria gráfico com Plotly
                fig = go.Figure()
                
                # Linha de evolução
                fig.add_trace(go.Scatter(
                    x=datas,
                    y=pontos_acumulados,
                    mode='lines+markers',
                    name='Pontos Acumulados',
                    line=dict(color='#3498db', width=3),
                    marker=dict(size=10, color='#2980b9'),
                    fill='tozeroy',
                    fillcolor='rgba(52, 152, 219, 0.2)'
                ))
                
                # Barras de pontos por dia
                fig.add_trace(go.Bar(
                    x=datas,
                    y=pontos,
                    name='Pontos no Dia',
                    marker_color='rgba(46, 204, 113, 0.7)',
                    yaxis='y2',
                    width=0.4,  # Largura mais fina das barras
                    opacity=0.6
                ))
                
                fig.update_layout(
                    title='🏆 Sua Evolução no Bolão',
                    xaxis_title='Data',
                    yaxis=dict(
                        title='Pontos Acumulados',
                        range=[0, y_max]
                    ),
                    yaxis2=dict(
                        title='Pontos no Dia',
                        overlaying='y',
                        side='right',
                        range=[0, y_max]  # Mesma escala do eixo esquerdo
                    ),
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=1.02,
                        xanchor='right',
                        x=1
                    ),
                    hovermode='x unified',
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                
                # Atualiza cores dos eixos e linhas de grade
                fig.update_xaxes(
                    title_font_color='black', 
                    tickfont_color='black',
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.3)',
                    gridwidth=1
                )
                fig.update_yaxes(
                    title_font_color='black', 
                    tickfont_color='black',
                    showgrid=True,
                    gridcolor='rgba(200, 200, 200, 0.3)',
                    gridwidth=1
                )
                # Remove linhas de grade do eixo Y secundário para evitar duplicação
                fig.update_yaxes(showgrid=False, selector=dict(overlaying='y'))
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 Ainda não há dados suficientes para o gráfico de evolução.")
        else:
            st.info("📊 Você ainda não pontuou em nenhum jogo. Aguarde os resultados!")
        
        st.divider()
        
        # ========================================
        # GRÁFICO DE DISTRIBUIÇÃO DE PONTOS
        # ========================================
        st.subheader("🎯 Distribuição de Acertos")
        
        # Conta tipos de acertos baseado no campo points_type
        # SÓ considera jogos que já começaram E têm placar registrado
        from sqlalchemy import func
        from datetime import datetime
        import pytz
        
        brazil_tz = pytz.timezone('America/Sao_Paulo')
        now_br = datetime.now(brazil_tz)
        now_naive = now_br.replace(tzinfo=None)
        
        # Busca IDs de jogos que já começaram E têm placar registrado
        jogos_com_resultado = session.query(Match.id).filter(
            Match.datetime <= now_naive,
            Match.team1_score.isnot(None),
            Match.team2_score.isnot(None)
        ).all()
        jogos_com_resultado_ids = [j[0] for j in jogos_com_resultado]
        
        # Busca contagem por tipo de acerto apenas de jogos com resultado
        if jogos_com_resultado_ids:
            tipos_acertos = session.query(
                Prediction.points_type,
                func.count(Prediction.id).label('count')
            ).filter(
                Prediction.user_id == st.session_state.user['id'],
                Prediction.match_id.in_(jogos_com_resultado_ids),
                Prediction.points_awarded > 0,
                Prediction.points_type.isnot(None)
            ).group_by(Prediction.points_type).all()
        else:
            tipos_acertos = []
        
        # Mapeamento de tipos para labels e cores
        tipo_config = {
            'placar_exato': ('Placar Exato (20pts)', '#3CAC3B'),
            'resultado_gols': ('Resultado + Gols (15pts)', '#2ECC71'),
            'apenas_resultado': ('Resultado Correto (10pts)', '#2A398D'),
            'apenas_gols': ('Gols de um Time (5pts)', '#F39C12'),
        }
        
        if tipos_acertos:
            labels = []
            values = []
            colors = []
            
            for tipo, count in tipos_acertos:
                if tipo in tipo_config:
                    label, color = tipo_config[tipo]
                    labels.append(label)
                    values.append(count)
                    colors.append(color)
            
            # Só mostra o gráfico se houver dados válidos
            if values and sum(values) > 0:
                # Ajusta pull dinamicamente baseado no número de categorias
                pull_values = [0.05] + [0.02] * (len(values) - 1) if len(values) > 1 else [0.05]
                
                fig_pie = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.4,
                    marker_colors=colors,
                    textinfo='percent',
                    textposition='inside',
                    insidetextfont=dict(size=14, color='white'),
                    pull=pull_values
                )])
                
                fig_pie.update_layout(
                    title='Tipos de Acertos',
                    showlegend=True,
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=-0.2,
                        xanchor='center',
                        x=0.5,
                        font=dict(size=12, color='#333333'),
                        bgcolor='rgba(255,255,255,0.9)',
                        bordercolor='#E0E0E0',
                        borderwidth=1
                    ),
                    plot_bgcolor='#FAFAFA',
                    paper_bgcolor='#FAFAFA',
                    font=dict(color='#333333'),
                    margin=dict(t=50, b=100, l=20, r=20)
                )
                
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("🎯 Ainda não há acertos para mostrar no gráfico.")
        else:
            st.info("🎯 Ainda não há acertos para mostrar no gráfico.")
    
    finally:
        session.close()

# =============================================================================
# PÁGINA DE CONFIGURAÇÕES
# =============================================================================
def page_configuracoes():
    """Página de configurações do usuário"""
    render_page_header()
    st.markdown("## ⚙️ Configurações")
    
    session = get_session(engine)
    
    try:
        st.subheader("🔐 Alterar Senha")
        
        with st.form("change_password"):
            current_password = st.text_input("Senha atual", type="password")
            new_password = st.text_input("Nova senha", type="password")
            confirm_password = st.text_input("Confirmar nova senha", type="password")
            
            if st.form_submit_button("Alterar Senha"):
                if not all([current_password, new_password, confirm_password]):
                    st.warning("Preencha todos os campos!")
                elif new_password != confirm_password:
                    st.error("As senhas não coincidem!")
                elif len(new_password) < 4:
                    st.error("A senha deve ter pelo menos 4 caracteres!")
                else:
                    user = session.query(User).get(st.session_state.user['id'])
                    if change_password(session, user, current_password, new_password):
                        st.success("Senha alterada com sucesso!")
                    else:
                        st.error("Senha atual incorreta!")
    
    finally:
        session.close()

def admin_gerenciar_repescagem(session):
    """
    Página de administração para definir os times classificados da repescagem
    """
    st.subheader("🔄 Gerenciar Times da Repescagem")
    
    st.info("""
    **Instruções:**
    Selecione as seleções que se classificaram em cada vaga da repescagem.
    Após selecionar, clique em "Salvar" para atualizar os jogos automaticamente.
    """)
    
    if True:  # Mantém a indentação
        # Para cada vaga de repescagem
        for vaga, opcoes in SELECOES_REPESCAGEM.items():
            with st.expander(f"📋 Vaga: {vaga}", expanded=False):
                # Verifica se já existe um time definido para essa vaga
                team_atual = session.query(Team).filter(Team.code == vaga).first()
                
                if team_atual and team_atual.name != vaga:
                    st.success(f"✅ Definido: {team_atual.flag} {team_atual.name}")
                else:
                    st.warning(f"⏳ Aguardando definição")
                
                # Cria opções para o selectbox
                opcoes_select = [{"code": "", "name": "Selecione...", "flag": ""}] + opcoes
                
                selecao = st.selectbox(
                    f"Selecione a seleção classificada para {vaga}:",
                    options=range(len(opcoes_select)),
                    format_func=lambda i: f"{opcoes_select[i]['flag']} {opcoes_select[i]['name']}" if opcoes_select[i]['code'] else "Selecione...",
                    key=f"repescagem_{vaga}"
                )
                
                if st.button(f"💾 Salvar {vaga}", key=f"btn_salvar_{vaga}"):
                    if selecao > 0:
                        selecao_escolhida = opcoes_select[selecao]
                        
                        # Atualiza ou cria o time
                        if team_atual:
                            team_atual.code = selecao_escolhida['code']
                            team_atual.name = selecao_escolhida['name']
                            team_atual.flag = selecao_escolhida['flag']
                        else:
                            novo_team = Team(
                                code=selecao_escolhida['code'],
                                name=selecao_escolhida['name'],
                                flag=selecao_escolhida['flag'],
                                group=None  # Será definido pelo jogo
                            )
                            session.add(novo_team)
                            session.flush()
                            
                            # Atualiza os jogos que usam essa vaga
                            jogos_team1 = session.query(Match).filter(Match.team1_code == vaga).all()
                            for jogo in jogos_team1:
                                jogo.team1_id = novo_team.id
                                jogo.team1_code = selecao_escolhida['code']
                            
                            jogos_team2 = session.query(Match).filter(Match.team2_code == vaga).all()
                            for jogo in jogos_team2:
                                jogo.team2_id = novo_team.id
                                jogo.team2_code = selecao_escolhida['code']
                        
                        session.commit()
                        st.success(f"✅ {selecao_escolhida['flag']} {selecao_escolhida['name']} definido para {vaga}!")
                        st.rerun()
                    else:
                        st.error("Selecione uma seleção válida!")
        
        st.divider()
        
        # Resumo das vagas
        st.subheader("📊 Resumo das Vagas de Repescagem")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🇪🇺 Repescagem Europa:**")
            for vaga in ["EUR_A", "EUR_B", "EUR_C", "EUR_D"]:
                team = session.query(Team).filter(Team.code == vaga).first()
                if team and team.name != vaga:
                    st.write(f"• {vaga}: {team.flag} {team.name}")
                else:
                    st.write(f"• {vaga}: ⏳ Aguardando")
        
        with col2:
            st.markdown("**🌍 Repescagem Intercontinental:**")
            for vaga in ["INT_1", "INT_2"]:
                team = session.query(Team).filter(Team.code == vaga).first()
                if team and team.name != vaga:
                    st.write(f"• {vaga}: {team.flag} {team.name}")
                else:
                    st.write(f"• {vaga}: ⏳ Aguardando")



def admin_repescagem(session):
    """Aba de gerenciamento de repescagem no painel admin"""
    admin_gerenciar_repescagem(session)


# =============================================================================
# PÁGINA DE ADMINISTRAÇÃO
# =============================================================================
def page_admin():
    """Página de administração"""
    if st.session_state.user['role'] != 'admin':
        st.error("Acesso negado!")
        return
    
    render_page_header()
    st.markdown("## 🔧 Painel Administrativo")
    
    session = get_session(engine)
    
    try:
        tabs = st.tabs([
            "👥 Participantes",
            "🏳️ Seleções",
            "⚽ Jogos",
            "📝 Resultados",
            "🏅 Grupos",
            "🏆 Pódio",
            "⭐ Pontuação",
            "💰 Premiação",
            "📋 Palpites",
            "🔄 Repescagem"
        ])
        
        with tabs[0]:
            admin_participantes(session)
        
        with tabs[1]:
            admin_selecoes(session)
        
        with tabs[2]:
            admin_jogos(session)
        
        with tabs[3]:
            admin_resultados(session)
        
        with tabs[4]:
            admin_grupos(session)
        
        with tabs[5]:
            admin_podio(session)
        
        with tabs[6]:
            admin_pontuacao(session)
        
        with tabs[7]:
            admin_premiacao(session)
        
        with tabs[8]:
            admin_palpites(session)
        
        with tabs[9]:
            admin_repescagem(session)
    
    finally:
        session.close()


def admin_participantes(session):
    """Gerenciamento de participantes"""
    st.subheader("👥 Gerenciar Participantes")
    
    # Formulário para novo participante
    with st.expander("➕ Adicionar Participante"):
        with st.form("new_participant"):
            name = st.text_input("Nome completo")
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            
            if st.form_submit_button("Criar Participante"):
                if name and username and password:
                    user = create_user(session, name, username, password, 'player')
                    if user:
                        st.success(f"Participante '{name}' criado com sucesso!")
                        log_action(session, st.session_state.user['id'], 'participante_criado', user.id)
                        st.rerun()
                    else:
                        st.error("Usuário já existe!")
                else:
                    st.warning("Preencha todos os campos!")
    
    # Lista de participantes
    users = session.query(User).filter(User.role == 'player').order_by(User.name).all()
    
    for user in users:
        status = "✅ Ativo" if user.active else "❌ Inativo"
        
        with st.expander(f"{user.name} (@{user.username}) - {status}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if user.active:
                    if st.button(f"🚫 Desativar", key=f"deactivate_{user.id}"):
                        user.active = False
                        session.commit()
                        log_action(session, st.session_state.user['id'], 'participante_desativado', user.id)
                        st.rerun()
                else:
                    if st.button(f"✅ Ativar", key=f"activate_{user.id}"):
                        user.active = True
                        session.commit()
                        log_action(session, st.session_state.user['id'], 'participante_ativado', user.id)
                        st.rerun()
            
            with col2:
                if st.button(f"🔑 Resetar Senha", key=f"reset_{user.id}"):
                    user.password_hash = hash_password("123456")
                    session.commit()
                    st.success(f"Senha resetada para '123456'")
                    log_action(session, st.session_state.user['id'], 'senha_resetada', user.id)
            
            with col3:
                # Botão de excluir com confirmação
                if st.button(f"🗑️ Excluir", key=f"delete_{user.id}", type="secondary"):
                    st.session_state[f'confirm_delete_{user.id}'] = True
                
                # Confirmação de exclusão
                if st.session_state.get(f'confirm_delete_{user.id}', False):
                    st.warning(f"⚠️ Tem certeza que deseja EXCLUIR '{user.name}'?")
                    st.caption("Esta ação é irreversível! Todos os palpites serão perdidos.")
                    
                    confirm_col1, confirm_col2 = st.columns(2)
                    with confirm_col1:
                        if st.button("✅ Sim, excluir", key=f"confirm_yes_{user.id}", type="primary"):
                            # Deletar palpites do usuário
                            session.query(Prediction).filter(Prediction.user_id == user.id).delete()
                            session.query(GroupPrediction).filter(GroupPrediction.user_id == user.id).delete()
                            session.query(PodiumPrediction).filter(PodiumPrediction.user_id == user.id).delete()
                            
                            # Registrar ação antes de deletar
                            log_action(session, st.session_state.user['id'], 'participante_excluido', user.id, 
                                      f"Excluído: {user.name} (@{user.username})")
                            
                            # Deletar usuário
                            session.delete(user)
                            session.commit()
                            
                            st.success(f"Participante '{user.name}' excluído com sucesso!")
                            st.session_state[f'confirm_delete_{user.id}'] = False
                            st.rerun()
                    
                    with confirm_col2:
                        if st.button("❌ Cancelar", key=f"confirm_no_{user.id}"):
                            st.session_state[f'confirm_delete_{user.id}'] = False
                            st.rerun()


def admin_selecoes(session):
    """Gerenciamento de seleções"""
    st.subheader("🏳️ Gerenciar Seleções")
    
    teams = session.query(Team).order_by(Team.group, Team.name).all()
    
    for team in teams:
        with st.expander(f"{team.flag} {team.name} - Grupo {team.group}"):
            with st.form(f"team_{team.id}"):
                new_name = st.text_input("Nome", value=team.name, key=f"team_name_{team.id}")
                new_flag = st.text_input("Bandeira (emoji)", value=team.flag, key=f"team_flag_{team.id}")
                new_group = st.selectbox(
                    "Grupo",
                    options=GRUPOS,
                    index=GRUPOS.index(team.group) if team.group in GRUPOS else 0,
                    key=f"team_group_{team.id}"
                )
                
                if st.form_submit_button("💾 Salvar"):
                    team.name = new_name
                    team.flag = new_flag
                    team.group = new_group
                    session.commit()
                    st.success("Seleção atualizada!")
                    st.rerun()


def admin_jogos(session):
    """Gerenciamento de jogos"""
    st.subheader("⚽ Gerenciar Jogos")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        fase_filter = st.selectbox(
            "Filtrar por Fase",
            options=["Todas"] + list(FASES.keys()),
            key="admin_fase_filter"
        )
    with col2:
        grupo_filter = st.selectbox(
            "Filtrar por Grupo",
            options=["Todos"] + GRUPOS + ["Mata-mata"],
            key="admin_grupo_filter"
        )
    
    query = session.query(Match).order_by(Match.match_number)
    
    if fase_filter != "Todas":
        query = query.filter(Match.phase == fase_filter)
    if grupo_filter != "Todos":
        if grupo_filter == "Mata-mata":
            query = query.filter(Match.group.is_(None))
        else:
            query = query.filter(Match.group == grupo_filter)
    
    jogos = query.all()
    
    st.markdown(f"**Total de jogos:** {len(jogos)}")
    
    teams = session.query(Team).order_by(Team.name).all()
    team_options = {t.id: f"{t.flag} {t.name}" for t in teams}
    team_ids = [None] + list(team_options.keys())
    
    for match in jogos:
        team1_display = get_team_display(match.team1, match.team1_code)
        team2_display = get_team_display(match.team2, match.team2_code)
        
        with st.expander(f"#{match.match_number} - {team1_display} vs {team2_display} | {format_datetime(match.datetime)}"):
            with st.form(f"match_{match.id}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    current_team1_idx = team_ids.index(match.team1_id) if match.team1_id in team_ids else 0
                    new_team1 = st.selectbox(
                        "Time 1",
                        options=team_ids,
                        format_func=lambda x: team_options.get(x, f"🏳️ {match.team1_code}") if x else f"🏳️ {match.team1_code}",
                        index=current_team1_idx,
                        key=f"match_t1_{match.id}"
                    )
                    
                    new_date = st.date_input(
                        "Data",
                        value=match.datetime.date(),
                        key=f"match_date_{match.id}"
                    )
                
                with col2:
                    current_team2_idx = team_ids.index(match.team2_id) if match.team2_id in team_ids else 0
                    new_team2 = st.selectbox(
                        "Time 2",
                        options=team_ids,
                        format_func=lambda x: team_options.get(x, f"🏳️ {match.team2_code}") if x else f"🏳️ {match.team2_code}",
                        index=current_team2_idx,
                        key=f"match_t2_{match.id}"
                    )
                    
                    new_time = st.time_input(
                        "Horário",
                        value=match.datetime.time(),
                        key=f"match_time_{match.id}"
                    )
                
                new_city = st.text_input("Cidade", value=match.city or "", key=f"match_city_{match.id}")
                
                if st.form_submit_button("💾 Salvar Alterações"):
                    match.team1_id = new_team1
                    match.team2_id = new_team2
                    match.datetime = datetime.combine(new_date, new_time)
                    match.city = new_city
                    session.commit()
                    st.success("Jogo atualizado!")
                    log_action(session, st.session_state.user['id'], 'jogo_editado', details=f"Jogo #{match.match_number}")
                    st.rerun()


def _auto_update_group_result(session, group_name):
    """
    Atualiza automaticamente o resultado do grupo baseado nos resultados dos jogos.
    Chamada sempre que um resultado de jogo da fase de grupos é atualizado.
    """
    from group_standings import get_official_group_standings
    
    standings = get_official_group_standings(session, group_name)
    if standings and len(standings) >= 2:
        result = session.query(GroupResult).filter_by(group_name=group_name).first()
        if result:
            result.first_place_team_id = standings[0]['team'].id
            result.second_place_team_id = standings[1]['team'].id
        else:
            result = GroupResult(
                group_name=group_name,
                first_place_team_id=standings[0]['team'].id,
                second_place_team_id=standings[1]['team'].id
            )
            session.add(result)
        
        session.commit()
        
        # Processa pontuação dos palpites de grupo
        process_group_predictions(session, group_name)


def admin_resultados(session):
    """Lançamento de resultados"""
    st.subheader("📝 Lançar Resultados")
    
    # Filtros
    col1, col2 = st.columns(2)
    with col1:
        fase_filter = st.selectbox("Fase", ["Todas as Fases", "Grupos", "Oitavas32", "Oitavas16", "Quartas", "Semifinal", "Terceiro", "Final"])
    with col2:
        grupo_filter = st.selectbox("Grupo", ["Todos os Grupos", "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"])
    
    # Todos os jogos pendentes de resultado
    query = session.query(Match).filter(Match.status == 'scheduled')
    
    # Aplica filtros
    if fase_filter != "Todas as Fases":
        query = query.filter(Match.phase == fase_filter)
    if grupo_filter != "Todos os Grupos":
        query = query.filter(Match.group == grupo_filter)
    
    jogos_pendentes = query.order_by(Match.datetime).all()
    
    st.markdown(f"**Total de jogos pendentes:** {len(jogos_pendentes)}")
    
    # Mostra todos os jogos pendentes (podem receber resultado mesmo com placeholder)
    if jogos_pendentes:
        st.markdown("### ⚽ Jogos prontos para resultado")
        
        for match in jogos_pendentes:
            team1_display = get_team_display(match.team1, match.team1_code)
            team2_display = get_team_display(match.team2, match.team2_code)
            
            with st.expander(f"#{match.match_number} - {team1_display} vs {team2_display} | {format_datetime(match.datetime)}"):
                with st.form(f"result_{match.id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        gols1 = st.number_input(f"Gols {team1_display}", min_value=0, max_value=20, value=match.team1_score if match.team1_score is not None else 0, key=f"res_gols1_{match.id}")
                    with col2:
                        gols2 = st.number_input(f"Gols {team2_display}", min_value=0, max_value=20, value=match.team2_score if match.team2_score is not None else 0, key=f"res_gols2_{match.id}")
                    
                    # Mostra placar atual se existir
                    if match.team1_score is not None and match.team2_score is not None:
                        st.info(f"🔴 Placar atual: {match.team1_score} x {match.team2_score} (jogo em andamento)")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.form_submit_button("🔄 Atualizar Placar", use_container_width=True):
                            match.team1_score = gols1
                            match.team2_score = gols2
                            # NÃO muda o status, continua 'scheduled'
                            session.commit()
                            
                            # Atualiza automaticamente a classificação do grupo
                            if match.phase == 'Fase de Grupos' and match.team1 and match.team1.group:
                                _auto_update_group_result(session, match.team1.group)
                            
                            st.success(f"🔴 Placar atualizado: {gols1} x {gols2} (jogo em andamento)")
                            log_action(session, st.session_state.user['id'], 'placar_atualizado', details=f"Jogo #{match.match_number}: {gols1}x{gols2}")
                            st.rerun()
                    
                    with col_btn2:
                        if st.form_submit_button("✅ Confirmar Resultado Final", use_container_width=True):
                            match.team1_score = gols1
                            match.team2_score = gols2
                            match.status = 'finished'
                            session.commit()
                            
                            # Processa pontuação dos palpites
                            process_match_predictions(session, match.id)
                            
                            # Atualiza automaticamente a classificação do grupo
                            if match.phase == 'Fase de Grupos' and match.team1 and match.team1.group:
                                _auto_update_group_result(session, match.team1.group)
                            
                            st.success(f"✅ Resultado final confirmado: {gols1} x {gols2}")
                            log_action(session, st.session_state.user['id'], 'resultado_lancado', details=f"Jogo #{match.match_number}: {gols1}x{gols2}")
                            st.rerun()
    
    st.divider()
    
    # Jogos já finalizados (para correção)
    st.subheader("📋 Jogos Finalizados")
    
    jogos_finalizados = session.query(Match).filter(
        Match.status == 'finished'
    ).order_by(Match.datetime.desc()).limit(10).all()
    
    if jogos_finalizados:
        for match in jogos_finalizados:
            team1_display = get_team_display(match.team1, match.team1_code)
            team2_display = get_team_display(match.team2, match.team2_code)
            
            with st.expander(f"#{match.match_number} - {team1_display} **{match.team1_score}** x **{match.team2_score}** {team2_display}"):
                st.info("✏️ Você pode editar o resultado caso tenha digitado errado")
                with st.form(f"edit_result_{match.id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        gols1_edit = st.number_input(f"Gols {team1_display}", min_value=0, max_value=20, value=match.team1_score, key=f"edit_gols1_{match.id}")
                    with col2:
                        gols2_edit = st.number_input(f"Gols {team2_display}", min_value=0, max_value=20, value=match.team2_score, key=f"edit_gols2_{match.id}")
                    
                    col_submit, col_delete = st.columns([3, 1])
                    
                    with col_submit:
                        submit_edit = st.form_submit_button("✏️ Atualizar Resultado", use_container_width=True)
                    
                    with col_delete:
                        delete_result = st.form_submit_button("🗑️ Apagar", type="secondary", use_container_width=True)
                    
                    if submit_edit:
                        match.team1_score = gols1_edit
                        match.team2_score = gols2_edit
                        session.commit()
                        
                        # Reprocessa pontuação dos palpites
                        process_match_predictions(session, match.id)
                        
                        # Atualiza automaticamente a classificação do grupo
                        if match.phase == 'Fase de Grupos' and match.team1 and match.team1.group:
                            _auto_update_group_result(session, match.team1.group)
                        
                        st.success(f"Resultado atualizado: {gols1_edit} x {gols2_edit}")
                        log_action(session, st.session_state.user['id'], 'resultado_editado', details=f"Jogo #{match.match_number}: {gols1_edit}x{gols2_edit}")
                        st.rerun()
                    
                    if delete_result:
                        # Guarda o grupo antes de apagar
                        grupo_do_jogo = match.team1.group if match.team1 else None
                        
                        # Apagar resultado e voltar jogo para status 'scheduled'
                        match.team1_score = None
                        match.team2_score = None
                        match.status = 'scheduled'
                        session.commit()
                        
                        # Reprocessa pontuação dos palpites (zera pontos deste jogo)
                        process_match_predictions(session, match.id)
                        
                        # Atualiza automaticamente a classificação do grupo
                        if match.phase == 'Fase de Grupos' and grupo_do_jogo:
                            _auto_update_group_result(session, grupo_do_jogo)
                        
                        st.success(f"Resultado apagado! Jogo voltou para status 'Agendado'.")
                        log_action(session, st.session_state.user['id'], 'resultado_apagado', details=f"Jogo #{match.match_number}")
                        st.rerun()
    else:
        st.info("Nenhum jogo finalizado ainda.")


def admin_grupos(session):
    """Definir classificados dos grupos"""
    st.subheader("🏅 Classificados dos Grupos")
    st.info("Defina os classificados de cada grupo após o término da fase de grupos")
    
    # Botão para preencher automaticamente todos os grupos
    from group_standings import get_official_group_standings
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("🤖 Preencher Todos Automaticamente", help="Preenche todos os grupos com base nos resultados dos jogos"):
            grupos_preenchidos = 0
            for grupo in GRUPOS:
                standings = get_official_group_standings(session, grupo)
                if standings and len(standings) >= 2:
                    result = session.query(GroupResult).filter_by(group_name=grupo).first()
                    if result:
                        result.first_place_team_id = standings[0]['team'].id
                        result.second_place_team_id = standings[1]['team'].id
                    else:
                        result = GroupResult(
                            group_name=grupo,
                            first_place_team_id=standings[0]['team'].id,
                            second_place_team_id=standings[1]['team'].id
                        )
                        session.add(result)
                    
                    session.commit()
                    process_group_predictions(session, grupo)
                    grupos_preenchidos += 1
            
            if grupos_preenchidos > 0:
                st.success(f"✅ {grupos_preenchidos} grupos preenchidos automaticamente!")
                log_action(session, st.session_state.user['id'], 'grupos_auto', details=f"{grupos_preenchidos} grupos")
                st.rerun()
            else:
                st.warning("⚠️ Nenhum grupo tem resultados suficientes para preencher automaticamente.")
    
    with col2:
        if st.button("🗑️ Apagar Todos os Grupos", type="secondary"):
            # Zera pontos de todos os palpites de grupo
            all_group_preds = session.query(GroupPrediction).all()
            for gp in all_group_preds:
                gp.points_awarded = 0
                gp.breakdown = None
            
            # Remove todos os resultados de grupo
            session.query(GroupResult).delete()
            session.commit()
            
            st.success("✅ Todos os resultados de grupos apagados!")
            log_action(session, st.session_state.user['id'], 'grupos_apagados_todos')
            st.rerun()
    
    st.divider()
    
    teams = session.query(Team).order_by(Team.name).all()
    
    for grupo in GRUPOS:
        grupo_teams = [t for t in teams if t.group == grupo]
        
        if not grupo_teams:
            continue
        
        team_options = {t.id: f"{t.flag} {t.name}" for t in grupo_teams}
        team_ids = [None] + list(team_options.keys())
        
        result = session.query(GroupResult).filter_by(group_name=grupo).first()
        
        # Calcula classificação oficial baseada nos resultados dos jogos
        from group_standings import get_official_group_standings
        standings = get_official_group_standings(session, grupo)
        
        with st.expander(f"Grupo {grupo}"):
            if standings and len(standings) >= 2:
                st.markdown("**📊 Classificação Oficial (baseada nos resultados lançados):**")
                for i, team_stat in enumerate(standings[:4], 1):
                    st.caption(f"{i}º {team_stat['team'].flag} {team_stat['team'].name} - {team_stat['points']} pts ({team_stat['wins']}V {team_stat['draws']}E {team_stat['losses']}D) | Saldo: {team_stat['goal_difference']:+d}")
                st.caption("⚠️ Sugestão: O sistema calculou automaticamente, mas você pode ajustar se necessário")
                st.divider()
            
            with st.form(f"group_result_{grupo}"):
                # Define valores padrão baseados na classificação oficial ou resultado já salvo
                default_first = None
                default_second = None
                
                if result:
                    default_first = result.first_place_team_id
                    default_second = result.second_place_team_id
                elif standings and len(standings) >= 2:
                    default_first = standings[0]['team'].id
                    default_second = standings[1]['team'].id
                
                primeiro = st.selectbox(
                    "1º Lugar",
                    options=team_ids,
                    format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                    index=team_ids.index(default_first) if default_first and default_first in team_ids else 0,
                    key=f"gr_{grupo}_1"
                )
                
                segundo = st.selectbox(
                    "2º Lugar",
                    options=team_ids,
                    format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                    index=team_ids.index(default_second) if default_second and default_second in team_ids else 0,
                    key=f"gr_{grupo}_2"
                )
                
                col_save, col_delete = st.columns([1, 1])
                
                with col_save:
                    save_btn = st.form_submit_button("💾 Salvar")
                
                if save_btn:
                    if primeiro and segundo and primeiro != segundo:
                        if result:
                            result.first_place_team_id = primeiro
                            result.second_place_team_id = segundo
                        else:
                            result = GroupResult(
                                group_name=grupo,
                                first_place_team_id=primeiro,
                                second_place_team_id=segundo
                            )
                            session.add(result)
                        
                        session.commit()
                        
                        # Processa pontuação dos palpites de grupo
                        process_group_predictions(session, grupo)
                        
                        st.success(f"Classificados do Grupo {grupo} salvos!")
                        log_action(session, st.session_state.user['id'], 'grupo_definido', details=f"Grupo {grupo}")
                        st.rerun()
                    else:
                        st.error("Selecione dois times diferentes!")
            
            # Botão de apagar fora do form
            if result:
                if st.button(f"🗑️ Apagar Grupo {grupo}", key=f"del_gr_{grupo}"):
                    # Zera pontos dos palpites de grupo
                    group_preds = session.query(GroupPrediction).filter_by(group_name=grupo).all()
                    for gp in group_preds:
                        gp.points_awarded = 0
                        gp.breakdown = None
                    
                    # Remove o resultado do grupo
                    session.delete(result)
                    session.commit()
                    
                    st.success(f"Resultado do Grupo {grupo} apagado!")
                    log_action(session, st.session_state.user['id'], 'grupo_apagado', details=f"Grupo {grupo}")
                    st.rerun()


def admin_podio(session):
    """Definir pódio do torneio"""
    st.subheader("🏆 Pódio do Torneio")
    st.info("Defina o Campeão, Vice-Campeão e 3º Lugar após o término da Copa")
    
    teams = session.query(Team).order_by(Team.name).all()
    team_options = {t.id: f"{t.flag} {t.name}" for t in teams}
    team_ids = [None] + list(team_options.keys())
    
    campeao = session.query(TournamentResult).filter_by(result_type='champion').first()
    vice = session.query(TournamentResult).filter_by(result_type='runner_up').first()
    terceiro = session.query(TournamentResult).filter_by(result_type='third_place').first()
    
    with st.form("podio_result"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_campeao = st.selectbox(
                "🥇 Campeão",
                options=team_ids,
                format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                index=team_ids.index(campeao.team_id) if campeao and campeao.team_id in team_ids else 0,
                key="podio_res_1"
            )
        
        with col2:
            new_vice = st.selectbox(
                "🥈 Vice-Campeão",
                options=team_ids,
                format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                index=team_ids.index(vice.team_id) if vice and vice.team_id in team_ids else 0,
                key="podio_res_2"
            )
        
        with col3:
            new_terceiro = st.selectbox(
                "🥉 3º Lugar",
                options=team_ids,
                format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                index=team_ids.index(terceiro.team_id) if terceiro and terceiro.team_id in team_ids else 0,
                key="podio_res_3"
            )
        
        if st.form_submit_button("💾 Salvar Pódio"):
            if new_campeao and new_vice and new_terceiro and len(set([new_campeao, new_vice, new_terceiro])) == 3:
                # Salva ou atualiza cada posição
                for result_type, team_id in [('champion', new_campeao), ('runner_up', new_vice), ('third_place', new_terceiro)]:
                    result = session.query(TournamentResult).filter_by(result_type=result_type).first()
                    if result:
                        result.team_id = team_id
                    else:
                        result = TournamentResult(result_type=result_type, team_id=team_id)
                        session.add(result)
                
                session.commit()
                
                # Processa pontuação dos palpites de pódio
                process_podium_predictions(session)
                
                st.success("Pódio salvo!")
                log_action(session, st.session_state.user['id'], 'podio_definido')
                st.rerun()
            else:
                st.error("Selecione três times diferentes!")
    
    # Botão de apagar pódio fora do form
    if campeao or vice or terceiro:
        st.divider()
        if st.button("🗑️ Apagar Pódio", key="del_podio"):
            # Zera pontos dos palpites de pódio
            podium_preds = session.query(PodiumPrediction).all()
            for pp in podium_preds:
                pp.points_awarded = 0
                pp.breakdown = None
            
            # Remove os resultados do pódio
            session.query(TournamentResult).delete()
            session.commit()
            
            st.success("Pódio apagado!")
            log_action(session, st.session_state.user['id'], 'podio_apagado')
            st.rerun()


def admin_pontuacao(session):
    """Configuração de pontuação"""
    st.subheader("⭐ Configuração de Pontuação")
    
    # Pontuação por jogo
    st.markdown("### Pontuação por Jogo")
    
    pontos_config = {
        'placar_exato': ('Placar Exato (acertou tudo)', 20),
        'resultado_gols': ('Resultado + Gols de um time', 15),
        'apenas_resultado': ('Apenas Resultado (vitória/empate)', 10),
        'apenas_gols': ('Apenas Gols de um time', 5),
        'nenhum': ('Nenhum acerto', 0),
    }
    
    with st.form("pontuacao_jogos"):
        pontos_values = {}
        for key, (label, default) in pontos_config.items():
            current = get_config_value(session, f'pontos_{key}', str(default))
            pontos_values[key] = st.number_input(label, min_value=0, max_value=100, value=int(current), key=f"pts_{key}")
        
        if st.form_submit_button("💾 Salvar Pontuação de Jogos"):
            for key, value in pontos_values.items():
                set_config_value(session, f'pontos_{key}', value, category='pontuacao')
            st.success("Pontuação de jogos salva!")
    
    # Pontuação de grupos
    st.markdown("### Pontuação de Classificação dos Grupos")
    
    grupo_config = {
        'ordem_correta': ('Acertou os 2 na ordem correta', 20),
        'ordem_invertida': ('Acertou os 2 em ordem invertida', 10),
        'um_certo': ('Acertou apenas 1 na posição errada', 5),
    }
    
    with st.form("pontuacao_grupos"):
        grupo_values = {}
        for key, (label, default) in grupo_config.items():
            current = get_config_value(session, f'grupo_{key}', str(default))
            grupo_values[key] = st.number_input(label, min_value=0, max_value=100, value=int(current), key=f"grp_{key}")
        
        if st.form_submit_button("💾 Salvar Pontuação de Grupos"):
            for key, value in grupo_values.items():
                set_config_value(session, f'grupo_{key}', value, category='grupo')
            st.success("Pontuação de grupos salva!")
    
    # Pontuação de pódio
    st.markdown("### Pontuação de Pódio")
    
    podio_config = {
        'completo': ('Acertou Campeão, Vice e 3º na ordem', 150),
        'campeao': ('Acertou o Campeão', 100),
        'vice': ('Acertou o Vice-Campeão', 50),
        'terceiro': ('Acertou o 3º Lugar', 30),
        'fora_ordem': ('Acertou posição fora de ordem', 20),
    }
    
    with st.form("pontuacao_podio"):
        podio_values = {}
        for key, (label, default) in podio_config.items():
            current = get_config_value(session, f'podio_{key}', str(default))
            podio_values[key] = st.number_input(label, min_value=0, max_value=500, value=int(current), key=f"pod_{key}")
        
        if st.form_submit_button("💾 Salvar Pontuação de Pódio"):
            for key, value in podio_values.items():
                set_config_value(session, f'podio_{key}', value, category='podio')
            st.success("Pontuação de pódio salva!")
    
    # Data de início da Copa
    st.markdown("### Data de Início da Copa")
    st.info("Após esta data, os palpites de pódio serão bloqueados")
    
    data_inicio = get_config_value(session, 'data_inicio_copa', '')
    
    col1, col2 = st.columns(2)
    with col1:
        try:
            dt = datetime.strptime(data_inicio, "%Y-%m-%d %H:%M") if data_inicio else datetime(2026, 6, 11, 13, 0)
            new_date = st.date_input("Data", value=dt.date(), key="copa_date")
        except:
            new_date = st.date_input("Data", value=datetime(2026, 6, 11).date(), key="copa_date")
    
    with col2:
        try:
            dt = datetime.strptime(data_inicio, "%Y-%m-%d %H:%M") if data_inicio else datetime(2026, 6, 11, 13, 0)
            new_time = st.time_input("Horário", value=dt.time(), key="copa_time")
        except:
            new_time = st.time_input("Horário", value=datetime(2026, 6, 11, 13, 0).time(), key="copa_time")
    
    if st.button("💾 Salvar Data de Início"):
        dt_str = datetime.combine(new_date, new_time).strftime("%Y-%m-%d %H:%M")
        set_config_value(session, 'data_inicio_copa', dt_str, category='sistema')
        st.success("Data de início salva!")


def admin_premiacao(session):
    """Configuração de premiação"""
    st.subheader("💰 Configuração de Premiação")
    
    with st.form("premiacao"):
        valor_inscricao = st.text_input(
            "Valor de Inscrição",
            value=get_config_value(session, 'premiacao_valor_inscricao', ''),
            placeholder="Ex: R$ 50,00"
        )
        
        premio_1 = st.text_input(
            "Prêmio 1º Lugar",
            value=get_config_value(session, 'premiacao_primeiro', ''),
            placeholder="Ex: 60% do total"
        )
        
        premio_2 = st.text_input(
            "Prêmio 2º Lugar",
            value=get_config_value(session, 'premiacao_segundo', ''),
            placeholder="Ex: 30% do total"
        )
        
        premio_3 = st.text_input(
            "Prêmio 3º Lugar",
            value=get_config_value(session, 'premiacao_terceiro', ''),
            placeholder="Ex: 10% do total"
        )
        
        observacoes = st.text_area(
            "Observações",
            value=get_config_value(session, 'premiacao_observacoes', ''),
            placeholder="Informações adicionais sobre a premiação..."
        )
        
        if st.form_submit_button("💾 Salvar Premiação"):
            set_config_value(session, 'premiacao_valor_inscricao', valor_inscricao, category='premiacao')
            set_config_value(session, 'premiacao_primeiro', premio_1, category='premiacao')
            set_config_value(session, 'premiacao_segundo', premio_2, category='premiacao')
            set_config_value(session, 'premiacao_terceiro', premio_3, category='premiacao')
            set_config_value(session, 'premiacao_observacoes', observacoes, category='premiacao')
            st.success("Premiação salva!")


def admin_palpites(session):
    """Edição de palpites de participantes"""
    st.subheader("📋 Editar Palpites de Participantes")
    st.info("Use esta função para corrigir palpites de participantes quando necessário")
    
    users = session.query(User).filter(User.role == 'player').order_by(User.name).all()
    
    if not users:
        st.warning("Nenhum participante cadastrado")
        return
    
    user_options = {u.id: u.name for u in users}
    selected_user_id = st.selectbox(
        "Selecione o Participante",
        options=list(user_options.keys()),
        format_func=lambda x: user_options[x]
    )
    
    if selected_user_id:
        tabs = st.tabs(["Jogos", "Grupos", "Pódio"])
        
        with tabs[0]:
            st.markdown("### Palpites de Jogos")
            
            # Filtros de Fase e Grupo
            col_fase, col_grupo = st.columns(2)
            with col_fase:
                fases_opcoes = ["Todas as Fases", "Grupos", "Oitavas32", "Oitavas16", "Quartas", "Semifinal", "Terceiro", "Final"]
                fase_filter = st.selectbox("Fase", fases_opcoes, key="admin_palpite_fase")
            with col_grupo:
                grupos_opcoes = ["Todos os Grupos"] + list(GRUPOS)
                grupo_filter = st.selectbox("Grupo", grupos_opcoes, key="admin_palpite_grupo")
            
            # Query base
            query = session.query(Match)
            
            # Aplicar filtro de fase
            if fase_filter != "Todas as Fases":
                query = query.filter(Match.phase == fase_filter)
            
            # Aplicar filtro de grupo
            if grupo_filter != "Todos os Grupos":
                query = query.filter(Match.group == grupo_filter)
            
            matches = query.order_by(Match.datetime).all()
            
            if not matches:
                st.info("Nenhum jogo encontrado com os filtros selecionados.")
            
            for match in matches:
                team1_display = get_team_display(match.team1, match.team1_code)
                team2_display = get_team_display(match.team2, match.team2_code)
                
                pred = session.query(Prediction).filter_by(
                    user_id=selected_user_id,
                    match_id=match.id
                ).first()
                
                with st.expander(f"#{match.match_number} - {team1_display} vs {team2_display}"):
                    with st.form(f"admin_pred_{match.id}_{selected_user_id}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            gols1 = st.number_input(
                                f"Gols {team1_display}",
                                min_value=0, max_value=20,
                                value=pred.pred_team1_score if pred else 0,
                                key=f"admin_g1_{match.id}_{selected_user_id}"
                            )
                        with col2:
                            gols2 = st.number_input(
                                f"Gols {team2_display}",
                                min_value=0, max_value=20,
                                value=pred.pred_team2_score if pred else 0,
                                key=f"admin_g2_{match.id}_{selected_user_id}"
                            )
                        
                        if st.form_submit_button("💾 Salvar"):
                            if pred:
                                pred.pred_team1_score = gols1
                                pred.pred_team2_score = gols2
                            else:
                                pred = Prediction(
                                    user_id=selected_user_id,
                                    match_id=match.id,
                                    pred_team1_score=gols1,
                                    pred_team2_score=gols2
                                )
                                session.add(pred)
                            session.commit()
                            log_action(session, st.session_state.user['id'], 'palpite_editado', selected_user_id, f"Jogo #{match.match_number}")
                            st.success("Palpite salvo!")
        
        with tabs[1]:
            st.markdown("### Palpites de Grupos")
            
            teams = session.query(Team).order_by(Team.name).all()
            
            for grupo in GRUPOS:
                grupo_teams = [t for t in teams if t.group == grupo]
                
                if not grupo_teams:
                    continue
                
                team_options = {t.id: f"{t.flag} {t.name}" for t in grupo_teams}
                team_ids = [None] + list(team_options.keys())
                
                pred = session.query(GroupPrediction).filter_by(
                    user_id=selected_user_id,
                    group_name=grupo
                ).first()
                
                with st.expander(f"Grupo {grupo}"):
                    with st.form(f"admin_grupo_{grupo}_{selected_user_id}"):
                        primeiro = st.selectbox(
                            "1º Lugar",
                            options=team_ids,
                            format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                            index=team_ids.index(pred.first_place_team_id) if pred and pred.first_place_team_id in team_ids else 0,
                            key=f"admin_g_{grupo}_1_{selected_user_id}"
                        )
                        
                        segundo = st.selectbox(
                            "2º Lugar",
                            options=team_ids,
                            format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                            index=team_ids.index(pred.second_place_team_id) if pred and pred.second_place_team_id in team_ids else 0,
                            key=f"admin_g_{grupo}_2_{selected_user_id}"
                        )
                        
                        if st.form_submit_button("💾 Salvar"):
                            if primeiro and segundo and primeiro != segundo:
                                if pred:
                                    pred.first_place_team_id = primeiro
                                    pred.second_place_team_id = segundo
                                else:
                                    pred = GroupPrediction(
                                        user_id=selected_user_id,
                                        group_name=grupo,
                                        first_place_team_id=primeiro,
                                        second_place_team_id=segundo
                                    )
                                    session.add(pred)
                                session.commit()
                                log_action(session, st.session_state.user['id'], 'palpite_grupo_editado', selected_user_id, f"Grupo {grupo}")
                                st.success("Palpite salvo!")
                            else:
                                st.error("Selecione dois times diferentes!")
        
        with tabs[2]:
            st.markdown("### Palpite de Pódio")
            
            teams = session.query(Team).order_by(Team.name).all()
            team_options = {t.id: f"{t.flag} {t.name}" for t in teams}
            team_ids = [None] + list(team_options.keys())
            
            pred = session.query(PodiumPrediction).filter_by(user_id=selected_user_id).first()
            
            with st.form(f"admin_podio_{selected_user_id}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    campeao = st.selectbox(
                        "🥇 Campeão",
                        options=team_ids,
                        format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                        index=team_ids.index(pred.champion_team_id) if pred and pred.champion_team_id in team_ids else 0,
                        key=f"admin_pod_c_{selected_user_id}"
                    )
                
                with col2:
                    vice = st.selectbox(
                        "🥈 Vice-Campeão",
                        options=team_ids,
                        format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                        index=team_ids.index(pred.runner_up_team_id) if pred and pred.runner_up_team_id in team_ids else 0,
                        key=f"admin_pod_v_{selected_user_id}"
                    )
                
                with col3:
                    terceiro = st.selectbox(
                        "🥉 3º Lugar",
                        options=team_ids,
                        format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                        index=team_ids.index(pred.third_place_team_id) if pred and pred.third_place_team_id in team_ids else 0,
                        key=f"admin_pod_t_{selected_user_id}"
                    )
                
                if st.form_submit_button("💾 Salvar"):
                    if campeao and vice and terceiro and len(set([campeao, vice, terceiro])) == 3:
                        if pred:
                            pred.champion_team_id = campeao
                            pred.runner_up_team_id = vice
                            pred.third_place_team_id = terceiro
                        else:
                            pred = PodiumPrediction(
                                user_id=selected_user_id,
                                champion_team_id=campeao,
                                runner_up_team_id=vice,
                                third_place_team_id=terceiro
                            )
                            session.add(pred)
                        
                        session.commit()
                        log_action(session, st.session_state.user['id'], 'palpite_podio_editado', selected_user_id)
                        st.success("Palpite de pódio salvo!")
                    else:
                        st.error("Selecione três times diferentes!")


# =============================================================================
# PÁGINA DE VISUALIZAÇÃO AO VIVO
# =============================================================================
def page_visualizacao_ao_vivo():
    """
    Página de visualização em tempo real dos jogos.
    Mostra palpites de todos os participantes e variação de ranking.
    Só mostra palpites após o jogo começar.
    """
    import streamlit as st
    from datetime import datetime
    import pytz
    from db import get_session, get_config_value
    from live_scoring import (
        get_ongoing_matches, get_live_match_predictions, 
        calculate_live_ranking, get_podium_zone_info
    )
    
    render_page_header()
    st.header("📺 Visualização ao Vivo")
    st.markdown("Acompanhe os jogos em tempo real e veja como está a pontuação de cada participante!")
    
    with get_session(engine) as session:
        # Pega jogos que já começaram
        matches = get_ongoing_matches(session)
        
        if not matches:
            st.info("Nenhum jogo disponível para visualização ainda.")
            return
        
        # Filtra apenas jogos que já começaram
        started_matches = [m for m in matches if m['has_started']]
        
        if not started_matches:
            st.info("Aguardando início dos jogos...")
            return
        
        # Seletor de jogo
        st.subheader("🎮 Selecione o Jogo")
        
        match_options = {0: "🎯 Todos os jogos"}
        for match in started_matches:
            score_display = ""
            if match['team1_score'] is not None and match['team2_score'] is not None:
                score_display = f" - {match['team1_score']} x {match['team2_score']}"
            
            status_icon = "🔴" if match['is_live'] else "✅"
            match_label = f"{status_icon} Jogo {match['match_number']}: {match['team1']} vs {match['team2']}{score_display}"
            match_options[match['id']] = match_label
        
        selected_match_id = st.selectbox(
            "Escolha o jogo:",
            options=list(match_options.keys()),
            format_func=lambda x: match_options[x],
            index=0,
            key="select_match_live"
        )
        
        # CSS específico para esta página
        st.markdown("""
        <style>
            /* Marca d'água do logo Copa 2026 */
            .live-watermark {
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 350px;
                height: 350px;
                background-image: url('https://raw.githubusercontent.com/LeandroCrespo/bolao-copa-2026/main/logo_copa2026.png');
                background-size: contain;
                background-repeat: no-repeat;
                background-position: center;
                opacity: 0.05;
                pointer-events: none;
                z-index: 0;
            }
            
            /* Corrige texto do selectbox na visualização ao vivo */
            div[data-testid="stSelectbox"] div[data-baseweb="select"] {
                background-color: #ffffff !important;
                border: 1px solid #ccc !important;
            }
            div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
                background-color: #ffffff !important;
                color: #1a1a2e !important;
            }
            div[data-testid="stSelectbox"] div[data-baseweb="select"] span {
                color: #1a1a2e !important;
            }
            div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
                color: #1a1a2e !important;
            }
            
            /* Corrige fundo da tabela de palpites */
            .live-table {
                background-color: #ffffff !important;
            }
            .live-table td {
                background-color: #ffffff !important;
                color: #1a1a2e !important;
            }
            .live-table tr {
                background-color: #ffffff !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Adiciona marca d'água do logo Copa 2026
        st.markdown('<div class="live-watermark"></div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Se selecionou "Todos os jogos"
        if selected_match_id == 0:
            # Separa jogos em andamento e finalizados
            jogos_em_andamento = [m for m in started_matches if m['is_live']]
            jogos_finalizados = [m for m in started_matches if m.get('is_finished', False)]
            
            # Mostra jogos em andamento
            if jogos_em_andamento:
                st.subheader("🔴 Jogos em Andamento")
                for match in jogos_em_andamento:
                    score = f"{match['team1_score']} x {match['team2_score']}" if match['team1_score'] is not None else "- x -"
                    st.markdown(f"🔴 **Jogo {match['match_number']}:** {match['team1']} **{score}** {match['team2']}")
            
            # Mostra jogos finalizados
            if jogos_finalizados:
                st.subheader("✅ Jogos Finalizados")
                for match in jogos_finalizados:
                    score = f"{match['team1_score']} x {match['team2_score']}" if match['team1_score'] is not None else "- x -"
                    st.markdown(f"✅ **Jogo {match['match_number']}:** {match['team1']} **{score}** {match['team2']} - **FINALIZADO**")
            
            # Se não há jogos em andamento nem finalizados
            if not jogos_em_andamento and not jogos_finalizados:
                st.info("Nenhum jogo do dia ainda.")
            
            st.divider()
            
            # Calcula soma total de pontos por participante em todos os jogos do dia
            titulo_pontuacao = "🏆 Pontuação Total (Jogos do Dia)" if jogos_finalizados else "🏆 Pontuação Total (Jogos em Andamento)"
            st.subheader(titulo_pontuacao)
            
            # Dicionário para somar pontos de cada usuário
            total_points_by_user = {}
            
            for match in started_matches:
                predictions = get_live_match_predictions(session, match['id'])
                for pred in predictions:
                    user_name = pred['user_name']
                    if user_name not in total_points_by_user:
                        total_points_by_user[user_name] = {'points': 0, 'user_id': pred['user_id']}
                    total_points_by_user[user_name]['points'] += pred['points']
            
            # Ordena por pontos (maior primeiro)
            sorted_users = sorted(total_points_by_user.items(), key=lambda x: x[1]['points'], reverse=True)
            
            # Mostra pontuação total em tabela
            if sorted_users:
                # Calcula ranking ao vivo para variação
                live_ranking = calculate_live_ranking(session, started_matches[0]['id'] if started_matches else None)
                variacao_map = {user['user_id']: user for user in live_ranking}
                
                # Pega informações de pódio e rebaixamento
                zone_info = get_podium_zone_info(session)
                total_users = len(live_ranking)
                rebaixamento_inicio = total_users - zone_info['rebaixamento_quantidade'] + 1 if zone_info['rebaixamento_quantidade'] > 0 else None
                
                # CSS para cards de ranking estilo claro
                st.markdown("""
                <style>
                .ranking-card-light {
                    background: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 12px;
                    padding: 14px 20px;
                    margin: 8px 0;
                    color: #333333;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    flex-wrap: wrap;
                    gap: 10px;
                }
                .ranking-card-light.top1 {
                    background: linear-gradient(135deg, #fffef5 0%, #fff9e6 100%);
                    border: 2px solid #FFD700;
                }
                .ranking-card-light.top2 {
                    background: linear-gradient(135deg, #fafafa 0%, #f0f0f0 100%);
                    border: 2px solid #C0C0C0;
                }
                .ranking-card-light.top3 {
                    background: linear-gradient(135deg, #fff8f2 0%, #ffe8d6 100%);
                    border: 2px solid #CD7F32;
                }
                .ranking-card-light.rebaixamento {
                    background: linear-gradient(135deg, #fff8f8 0%, #ffefef 100%);
                    border-left: 4px solid #E61D25;
                }
                .ranking-card-light .posicao {
                    font-size: 1.4em;
                    font-weight: bold;
                    min-width: 45px;
                    text-align: center;
                    color: #1a1a2e;
                }
                .ranking-card-light .info {
                    flex: 1;
                    min-width: 120px;
                }
                .ranking-card-light .nome {
                    font-size: 1.05em;
                    font-weight: 600;
                    color: #1a1a2e;
                }
                .ranking-card-light .pontos-badge {
                    background: #2A398D !important;
                    color: #ffffff !important;
                    padding: 6px 16px;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 1em;
                }
                .ranking-card-light .variacao-badge {
                    padding: 4px 10px;
                    border-radius: 12px;
                    font-size: 0.85em;
                    font-weight: 600;
                }
                .ranking-card-light .variacao-badge.up { background: #d4edda; color: #155724; }
                .ranking-card-light .variacao-badge.down { background: #f8d7da; color: #721c24; }
                .ranking-card-light .variacao-badge.same { background: #e9ecef; color: #495057; }
                .ranking-card-light .status-badge {
                    padding: 4px 10px;
                    border-radius: 12px;
                    font-size: 0.85em;
                    font-weight: 600;
                }
                .ranking-card-light .status-badge.podio { background: #FFF3CD; color: #856404; }
                .ranking-card-light .status-badge.rebaixamento { background: #F8D7DA; color: #721C24; }
                .ranking-container {
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                }
                @media (max-width: 768px) {
                    .ranking-card-light {
                        flex-direction: column;
                        text-align: center;
                        gap: 8px;
                    }
                    .ranking-card-light .posicao {
                        margin-bottom: 5px;
                    }
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Gera cards individuais usando st.markdown separado para cada um
                for i, (user_name, data) in enumerate(sorted_users):
                    pos = i + 1
                    points = data['points']
                    user_id = data['user_id']
                    
                    # Variação de posição
                    user_rank = variacao_map.get(user_id, {})
                    variacao = user_rank.get('variacao', 0)
                    posicao_atual = user_rank.get('posicao_atual', pos)
                    
                    if variacao > 0:
                        var_text = f"⬆️ +{variacao}"
                        var_class = "up"
                    elif variacao < 0:
                        var_text = f"⬇️ {variacao}"
                        var_class = "down"
                    else:
                        var_text = "➡️ 0"
                        var_class = "same"
                    
                    # Status especial e classe do card
                    status_html = ""
                    card_class = "ranking-card-light"
                    if pos == 1:
                        card_class = "ranking-card-light top1"
                        pos_display = "🥇"
                        status_html = '<span class="status-badge podio">🏆 Pódio</span>'
                    elif pos == 2:
                        card_class = "ranking-card-light top2"
                        pos_display = "🥈"
                        status_html = '<span class="status-badge podio">🏆 Pódio</span>'
                    elif pos == 3:
                        card_class = "ranking-card-light top3"
                        pos_display = "🥉"
                        status_html = '<span class="status-badge podio">🏆 Pódio</span>'
                    elif rebaixamento_inicio and pos >= rebaixamento_inicio:
                        card_class = "ranking-card-light rebaixamento"
                        pos_display = f"{pos}º"
                        status_html = '<span class="status-badge rebaixamento">⚠️ Rebaixamento</span>'
                    else:
                        pos_display = f"{pos}º"
                    
                    # Renderiza cada card individualmente
                    st.markdown(f'''
                    <div class="{card_class}">
                        <div class="posicao">{pos_display}</div>
                        <div class="info">
                            <div class="nome">{user_name}</div>
                        </div>
                        <span class="pontos-badge">{points} pts</span>
                        <span class="variacao-badge {var_class}">{var_text}</span>
                        {status_html}
                    </div>
                    ''', unsafe_allow_html=True)
            else:
                st.info("Nenhum palpite registrado para os jogos em andamento.")
            
            st.divider()
            
            # Botão de atualização
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("🔄 Atualizar", use_container_width=True, key="refresh_all"):
                    st.rerun()
            
            return
        
        # Pega informações do jogo selecionado (jogo único)
        selected_match = next((m for m in started_matches if m['id'] == selected_match_id), None)
        
        if not selected_match:
            return
        
        # Mostra placar atual
        st.subheader("⚽ Placar Atual")
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.markdown(f"### {selected_match['team1']}")
        
        with col2:
            if selected_match['team1_score'] is not None and selected_match['team2_score'] is not None:
                st.markdown(f"### <center>{selected_match['team1_score']} x {selected_match['team2_score']}</center>", unsafe_allow_html=True)
            else:
                st.markdown("### <center>- x -</center>", unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"### {selected_match['team2']}")
        
        # Status do jogo
        if selected_match['is_live']:
            st.success("🔴 **Jogo em andamento!**")
        elif selected_match['status'] == 'finished':
            st.info("✅ **Jogo finalizado**")
        else:
            st.warning("⏸️ **Aguardando atualização do placar**")
        
        st.divider()
        
        # Pega palpites de todos os participantes
        predictions = get_live_match_predictions(session, selected_match_id)
        
        if not predictions:
            st.info("Nenhum palpite registrado para este jogo.")
            return
        
        # Calcula ranking ao vivo
        live_ranking = calculate_live_ranking(session, selected_match_id)
        
        # Cria mapa de variação de posição
        variacao_map = {user['user_id']: user for user in live_ranking}
        
        # Pega informações de pódio e rebaixamento
        zone_info = get_podium_zone_info(session)
        total_users = len(live_ranking)
        rebaixamento_inicio = total_users - zone_info['rebaixamento_quantidade'] + 1 if zone_info['rebaixamento_quantidade'] > 0 else None
        
        # Mostra palpites em cards estilo escuro
        st.subheader("📊 Palpites e Pontuação")
        
        # CSS para cards estilo claro
        st.markdown("""
        <style>
        .palpite-card-light {
            background: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 12px;
            padding: 16px 20px;
            margin: 10px 0;
            color: #333333;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }
        .palpite-card-light.podio {
            border-left: 4px solid #FFD700;
            background: linear-gradient(135deg, #fffef5 0%, #fff9e6 100%);
        }
        .palpite-card-light.rebaixamento {
            border-left: 4px solid #E61D25;
            background: linear-gradient(135deg, #fff8f8 0%, #ffefef 100%);
        }
        .palpite-card-light .header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .palpite-card-light .nome {
            font-size: 1.1em;
            font-weight: 600;
            color: #1a1a2e;
        }
        .palpite-card-light .stats {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        .palpite-card-light .palpite-badge {
            background: #2A398D !important;
            color: #ffffff !important;
            padding: 4px 12px;
            border-radius: 6px;
            font-weight: bold;
        }
        .palpite-card-light .pontos-badge {
            padding: 4px 12px;
            border-radius: 6px;
            font-weight: bold;
        }
        .palpite-card-light .pontos-badge.pts-20 { background: #28a745 !important; color: #ffffff !important; }
        .palpite-card-light .pontos-badge.pts-15 { background: #20c997 !important; color: #ffffff !important; }
        .palpite-card-light .pontos-badge.pts-10 { background: #2A398D !important; color: #ffffff !important; }
        .palpite-card-light .pontos-badge.pts-5 { background: #fd7e14 !important; color: #ffffff !important; }
        .palpite-card-light .pontos-badge.pts-0 { background: #6c757d !important; color: #ffffff !important; }
        .palpite-card-light .info-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 8px;
            font-size: 0.9em;
            color: #666666;
        }
        .palpite-card-light .status-badge {
            padding: 3px 10px;
            border-radius: 6px;
            font-size: 0.85em;
            font-weight: 600;
        }
        .palpite-card-light .status-badge.podio { background: #FFF3CD !important; color: #856404 !important; }
        .palpite-card-light .status-badge.rebaixamento { background: #F8D7DA !important; color: #721C24 !important; }
        
        /* Esconde elementos vazios e garante fundo transparente */
        .palpite-card-light .status-badge:empty { display: none !important; }
        .palpite-card-light .info-row:empty { display: none !important; }
        div[data-testid="stMarkdownContainer"]:has(.palpite-card-light) {
            background: transparent !important;
            background-color: transparent !important;
        }
        .stMarkdown:has(.palpite-card-light) {
            background: transparent !important;
        }
        .palpites-container {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Gera cards individuais usando st.markdown separado para cada um
        for pred in predictions:
            user_id = pred['user_id']
            user_rank = variacao_map.get(user_id, {})
            
            # Variação de posição
            variacao = user_rank.get('variacao', 0)
            posicao_atual = user_rank.get('posicao_atual', '-')
            
            if variacao > 0:
                var_text = f"⬆️ +{variacao}"
            elif variacao < 0:
                var_text = f"⬇️ {variacao}"
            else:
                var_text = f"➡️ 0"
            
            # Status especial e classe CSS
            status_html = ""
            card_class = "palpite-card-light"
            if isinstance(posicao_atual, int):
                if posicao_atual <= 3:
                    status_html = '<span class="status-badge podio">🏆 Pódio</span>'
                    card_class = "palpite-card-light podio"
                elif rebaixamento_inicio and posicao_atual >= rebaixamento_inicio:
                    status_html = '<span class="status-badge rebaixamento">⚠️ Rebaixamento</span>'
                    card_class = "palpite-card-light rebaixamento"
            
            # Classe de pontos
            points = pred['points']
            if points >= 20:
                pts_class = "pts-20"
            elif points >= 15:
                pts_class = "pts-15"
            elif points >= 10:
                pts_class = "pts-10"
            elif points >= 5:
                pts_class = "pts-5"
            else:
                pts_class = "pts-0"
            
            # Renderiza cada card individualmente
            st.markdown(f'''
            <div class="{card_class}">
                <div class="header-row">
                    <span class="nome">{pred['user_name']}</span>
                    <div class="stats">
                        <span class="palpite-badge">{pred['prediction']}</span>
                        <span class="pontos-badge {pts_class}">⚽ {points} pts</span>
                    </div>
                </div>
                <div class="info-row">
                    <span>{var_text} → {posicao_atual}º lugar</span>
                    {status_html}
                </div>
            </div>
            ''', unsafe_allow_html=True)
        
        # Legenda de pontos
        st.markdown("""
        <div style="background: #f8f9fa; border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; margin-top: 15px; color: #666666; font-size: 0.9em;">
            <strong style="color: #333333;">Legenda:</strong>
            <span style="color: #28a745;">● 20 pts</span> Placar exato &nbsp;
            <span style="color: #20c997;">● 15 pts</span> Resultado + gols &nbsp;
            <span style="color: #2A398D;">● 10 pts</span> Resultado &nbsp;
            <span style="color: #fd7e14;">● 5 pts</span> Gols de um time &nbsp;
            <span style="color: #6c757d;">● 0 pts</span> Não pontuou
        </div>
        """, unsafe_allow_html=True)
        
        # Botão de atualização
        st.divider()
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 Atualizar", use_container_width=True):
                st.rerun()
        
        # Auto-refresh a cada 30 segundos se o jogo estiver ao vivo
        if selected_match['is_live']:
            st.markdown("<small>🔄 Página atualiza automaticamente a cada 30 segundos</small>", unsafe_allow_html=True)
            import time
            time.sleep(30)
            st.rerun()


# =============================================================================
# PÁGINA DE RESUMO DIÁRIO
# =============================================================================
def page_resumo_diario():
    """
    Página de resumo diário.
    Gera resumos automáticos com resultados, pontuadores e variações de ranking.
    Permite copiar para WhatsApp.
    """
    import streamlit as st
    from datetime import datetime, timedelta
    import pytz
    from db import get_session
    from daily_summary import generate_daily_summary, get_brazil_time
    
    st.header("📄 Resumo Diário")
    st.markdown("Gere resumos automáticos dos jogos e compartilhe no WhatsApp!")
    
    with get_session(engine) as session:
        # Seletor de data
        st.subheader("📅 Selecione a Data")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            target_date = st.date_input(
                "Data do resumo:",
                value=get_brazil_time().date(),
                help="Selecione a data para gerar o resumo"
            )
        
        with col2:
            format_type = st.selectbox(
                "Formato:",
                options=['rich', 'plain'],
                format_func=lambda x: 'Rico (com emojis)' if x == 'rich' else 'Simples (texto puro)',
                index=0
            )
        
        # Converte date para datetime
        brazil_tz = pytz.timezone('America/Sao_Paulo')
        target_datetime = datetime.combine(target_date, datetime.min.time())
        target_datetime = brazil_tz.localize(target_datetime)
        
        st.divider()
        
        # Botão para gerar resumo
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            if st.button("📝 Gerar Resumo", use_container_width=True):
                with st.spinner('Gerando resumo...'):
                    summary = generate_daily_summary(session, target_datetime, format_type)
                    st.session_state['daily_summary'] = summary
        
        # Mostra resumo se existir
        if 'daily_summary' in st.session_state:
            st.divider()
            st.subheader("📜 Resumo Gerado")
            
            # Mostra preview
            st.text_area(
                "Preview:",
                value=st.session_state['daily_summary'],
                height=400,
                help="Copie este texto e cole no WhatsApp"
            )
            
            # Botões de ação
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                # Botão de copiar (usando componente nativo do Streamlit)
                st.download_button(
                    label="📋 Baixar como TXT",
                    data=st.session_state['daily_summary'],
                    file_name=f"resumo_{target_date.strftime('%Y%m%d')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
            
            with col2:
                # JavaScript para copiar para área de transferência
                st.markdown("""
                <script>
                function copyToClipboard() {
                    const text = document.querySelector('textarea').value;
                    navigator.clipboard.writeText(text).then(function() {
                        alert('✅ Texto copiado para a área de transferência!');
                    }, function(err) {
                        alert('❌ Erro ao copiar texto');
                    });
                }
                </script>
                """, unsafe_allow_html=True)
                
                if st.button("📋 Copiar para Área de Transferência", use_container_width=True):
                    st.success("✅ Use Ctrl+C para copiar o texto acima!")
            
            with col3:
                # Link para WhatsApp Web (abre com texto pré-preenchido)
                import urllib.parse
                # Codifica o texto para URL - WhatsApp aceita UTF-8 encoded
                summary_text = st.session_state['daily_summary']
                # Usa quote diretamente na string (não em bytes)
                # O quote converte caracteres especiais e emojis corretamente
                whatsapp_text = urllib.parse.quote(summary_text)
                whatsapp_url = f"https://wa.me/?text={whatsapp_text}"
                
                st.markdown(
                    f'<a href="{whatsapp_url}" target="_blank" style="display: inline-block; padding: 0.5rem 1rem; background-color: #25D366; color: white; text-decoration: none; border-radius: 5px; text-align: center; width: 100%;">'
                    f'📱 Enviar pelo WhatsApp</a>',
                    unsafe_allow_html=True
                )
            
            st.divider()
            
            # Instruções
            with st.expander("💡 Como usar"):
                st.markdown("""
                **Opção 1: Copiar manualmente**
                1. Selecione todo o texto no campo acima
                2. Pressione Ctrl+C (ou Cmd+C no Mac)
                3. Cole no WhatsApp
                
                **Opção 2: Baixar arquivo**
                1. Clique em "Baixar como TXT"
                2. Abra o arquivo
                3. Copie e cole no WhatsApp
                
                **Opção 3: Enviar direto pelo WhatsApp**
                1. Clique em "Enviar pelo WhatsApp"
                2. Escolha o contato ou grupo
                3. Envie a mensagem
                
                💡 **Dica:** O formato "Rico" usa emojis e *negrito* que funcionam no WhatsApp!
                """)
        
        # Geração automática ao final do dia
        st.divider()
        
        with st.expander("⚙️ Geração Automática"):
            st.info("""
            🕒 **Geração Automática**
            
            O resumo pode ser gerado automaticamente ao final de cada dia de jogos.
            
            Para implementar:
            1. Configure um agendador (cron job)
            2. Execute o script de geração às 23:00
            3. O resumo será salvo e poderá ser enviado automaticamente
            
            🚧 Funcionalidade em desenvolvimento
            """)


# =============================================================================
# PÁGINA DE RESULTADOS POR GRUPO
# =============================================================================
def page_resultados_grupos():
    """
    Página que mostra os resultados dos jogos e classificação por grupo.
    Atualiza em tempo real conforme os resultados são lançados.
    """
    import pandas as pd
    from group_standings import get_official_group_standings
    
    render_page_header()
    st.header("🏆 Resultados por Grupo")
    st.markdown("Acompanhe a classificação e os jogos de cada grupo da fase de grupos.")
    
    # CSS e marca d'água do logo Copa 2026
    st.markdown("""
    <style>
        .grupos-watermark {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 350px;
            height: 350px;
            background-image: url('https://raw.githubusercontent.com/LeandroCrespo/bolao-copa-2026/main/logo_copa2026.png');
            background-size: contain;
            background-repeat: no-repeat;
            background-position: center;
            opacity: 0.05;
            pointer-events: none;
            z-index: 0;
        }
    </style>
    <div class="grupos-watermark"></div>
    """, unsafe_allow_html=True)
    
    with get_session(engine) as session:
        # Seletor de grupo
        grupos = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L']
        
        # Opção para ver todos os grupos ou selecionar um
        view_mode = st.radio(
            "Visualização:",
            ["Todos os Grupos", "Selecionar Grupo"],
            horizontal=True
        )
        
        if view_mode == "Selecionar Grupo":
            grupo_selecionado = st.selectbox(
                "Selecione o Grupo:",
                grupos,
                format_func=lambda x: f"Grupo {x}"
            )
            grupos_para_mostrar = [grupo_selecionado]
        else:
            grupos_para_mostrar = grupos
        
        st.divider()
        
        # Mostra cada grupo
        for grupo in grupos_para_mostrar:
            with st.expander(f"🏅 Grupo {grupo}", expanded=(view_mode == "Selecionar Grupo")):
                # Busca classificação do grupo
                standings = get_official_group_standings(session, grupo)
                
                # Busca jogos do grupo
                jogos_grupo = session.query(Match).filter(
                    Match.group == grupo,
                    Match.phase == 'Fase de Grupos'
                ).order_by(Match.datetime).all()
                
                if not jogos_grupo:
                    # Tenta com 'Grupos' ao invés de 'Fase de Grupos'
                    jogos_grupo = session.query(Match).filter(
                        Match.group == grupo,
                        Match.phase == 'Grupos'
                    ).order_by(Match.datetime).all()
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("#### 📊 Classificação")
                    
                    if standings:
                        # Cria tabela de classificação
                        table_data = []
                        for i, team_stats in enumerate(standings, 1):
                            team = team_stats['team']
                            
                            # Determina nome e bandeira
                            if hasattr(team, 'flag') and team.flag:
                                flag = team.flag
                            else:
                                flag = "🏳️"
                            
                            if hasattr(team, 'name') and team.name:
                                name = team.name
                            elif hasattr(team, 'code'):
                                name = team.code
                            else:
                                name = "TBD"
                            
                            # Destaque para classificados
                            if i <= 2:
                                pos_icon = "🟢" if i == 1 else "🟡"
                            else:
                                pos_icon = ""
                            
                            table_data.append({
                                "Pos": f"{pos_icon} {i}º",
                                "Seleção": f"{flag} {name}",
                                "P": team_stats['points'],
                                "J": team_stats['played'],
                                "V": team_stats['wins'],
                                "E": team_stats['draws'],
                                "D": team_stats['losses'],
                                "GP": team_stats['goals_for'],
                                "GC": team_stats['goals_against'],
                                "SG": team_stats['goal_difference']
                            })
                        
                        df = pd.DataFrame(table_data)
                        st.dataframe(
                            df,
                            hide_index=True,
                            use_container_width=True,
                            column_config={
                                "Pos": st.column_config.TextColumn("Pos", width="small"),
                                "Seleção": st.column_config.TextColumn("Seleção", width="medium"),
                                "P": st.column_config.NumberColumn("Pts", width="small"),
                                "J": st.column_config.NumberColumn("J", width="small"),
                                "V": st.column_config.NumberColumn("V", width="small"),
                                "E": st.column_config.NumberColumn("E", width="small"),
                                "D": st.column_config.NumberColumn("D", width="small"),
                                "GP": st.column_config.NumberColumn("GP", width="small"),
                                "GC": st.column_config.NumberColumn("GC", width="small"),
                                "SG": st.column_config.NumberColumn("SG", width="small")
                            }
                        )
                        
                        st.caption("🟢 1º lugar | 🟡 2º lugar | P=Pontos | J=Jogos | V=Vitórias | E=Empates | D=Derrotas | GP=Gols Pró | GC=Gols Contra | SG=Saldo")
                    else:
                        st.info("Nenhum resultado lançado ainda para este grupo.")
                
                with col2:
                    st.markdown("#### ⚽ Jogos")
                    
                    if jogos_grupo:
                        for jogo in jogos_grupo:
                            # Determina times
                            if jogo.team1:
                                team1_name = f"{jogo.team1.flag} {jogo.team1.name}"
                            elif jogo.team1_code:
                                team1_name = f"🏳️ {jogo.team1_code}"
                            else:
                                team1_name = "TBD"
                            
                            if jogo.team2:
                                team2_name = f"{jogo.team2.flag} {jogo.team2.name}"
                            elif jogo.team2_code:
                                team2_name = f"🏳️ {jogo.team2_code}"
                            else:
                                team2_name = "TBD"
                            
                            # Formata data
                            data_jogo = jogo.datetime.strftime("%d/%m %H:%M") if jogo.datetime else "TBD"
                            
                            # Determina placar e status
                            if jogo.status == 'finished':
                                placar = f"**{jogo.team1_score}** x **{jogo.team2_score}**"
                                status_icon = "✅"
                            elif jogo.team1_score is not None and jogo.team2_score is not None:
                                placar = f"**{jogo.team1_score}** x **{jogo.team2_score}**"
                                status_icon = "🔴"
                            else:
                                placar = "vs"
                                status_icon = "⏰"
                            
                            st.markdown(
                                f"{status_icon} {team1_name} {placar} {team2_name}  \n"
                                f"<small style='color: gray;'>{data_jogo}</small>",
                                unsafe_allow_html=True
                            )
                    else:
                        st.info("Nenhum jogo encontrado para este grupo.")
        
        # Legenda
        st.divider()
        st.markdown("""
        **Legenda:**
        - ✅ Jogo finalizado
        - 🔴 Jogo em andamento
        - ⏰ Jogo agendado
        - 🟢 Classificado em 1º lugar
        - 🟡 Classificado em 2º lugar
        """)


# =============================================================================
# NAVEGAÇÃO PRINCIPAL
# =============================================================================

def get_notification_badges(session, user_id):
    """Retorna contagem de notificações para badges no menu"""
    from datetime import datetime
    badges = {}
    
    try:
        now = get_brazil_time().replace(tzinfo=None)
        
        # Jogos em andamento (ao vivo)
        jogos_ao_vivo = session.query(Match).filter(
            Match.status == 'in_progress'
        ).count()
        
        # Jogos que começaram nas últimas 24h (novos resultados)
        from datetime import timedelta
        ontem = now - timedelta(hours=24)
        jogos_recentes = session.query(Match).filter(
            Match.status == 'finished',
            Match.datetime >= ontem
        ).count()
        
        # Palpites pendentes (jogos futuros sem palpite)
        jogos_futuros = session.query(Match).filter(
            Match.datetime > now,
            Match.status == 'scheduled'
        ).all()
        
        palpites_feitos = session.query(Prediction).filter(
            Prediction.user_id == user_id
        ).count()
        
        palpites_pendentes = len(jogos_futuros) - palpites_feitos
        if palpites_pendentes < 0:
            palpites_pendentes = 0
        
        badges['ao_vivo'] = jogos_ao_vivo
        badges['novos_resultados'] = jogos_recentes
        badges['palpites_pendentes'] = min(palpites_pendentes, 99)  # Max 99
        
    except Exception:
        badges = {'ao_vivo': 0, 'novos_resultados': 0, 'palpites_pendentes': 0}
    
    return badges

def main():
    """Função principal do aplicativo"""
    
    # ========================================================================
    # ========================================================================
    
    if st.session_state.user is None:
        page_login()
    else:
        # Sidebar com navegação
        with st.sidebar:
            st.markdown(f"### 👋 Olá, {st.session_state.user['name']}!")
            st.divider()
            
            # Busca badges de notificação
            with get_session(engine) as session:
                badges = get_notification_badges(session, st.session_state.user['id'])
            
            # Menu de navegação - diferente para admin e participantes
            if st.session_state.user['role'] == 'admin':
                # Admin só vê opções administrativas
                menu_options = {
                    "🏠 Início": "home",
                    "📺 Visualização ao Vivo": "visualizacao_ao_vivo",
                    "🏆 Resultados por Grupo": "resultados_grupos",
                    "📊 Ranking": "ranking",
                    "📄 Resumo Diário": "resumo_diario",
                    "📈 Estatísticas": "estatisticas",
                    "⚙️ Configurações": "configuracoes",
                    "🔧 Admin": "admin",
                }
            else:
                # Participantes veem todas as opções de palpites
                # Adiciona badges dinâmicos
                palpites_badge = f" 🔴{badges['palpites_pendentes']}" if badges['palpites_pendentes'] > 0 else ""
                ao_vivo_badge = " 🔴 AO VIVO" if badges['ao_vivo'] > 0 else ""
                
                menu_options = {
                    "🏠 Início": "home",
                    f"📝 Palpites - Jogos{palpites_badge}": "palpites_jogos",
                    "🏅 Palpites - Grupos": "palpites_grupos",
                    "🏆 Palpites - Pódio": "palpites_podio",
                    f"📺 Visualização ao Vivo{ao_vivo_badge}": "visualizacao_ao_vivo",
                    "🏆 Resultados por Grupo": "resultados_grupos",
                    "📊 Ranking": "ranking",
                    "💡 Dicas": "dicas",
                    "📈 Estatísticas": "estatisticas",
                    "⚙️ Configurações": "configuracoes",
                }
            
            for label, page in menu_options.items():
                if st.button(label, use_container_width=True):
                    st.session_state.page = page
                    st.rerun()
            
            st.divider()
            
            if st.button("🚪 Sair", use_container_width=True):
                st.session_state.user = None
                st.session_state.page = 'home'
                st.rerun()
        
        # Renderiza a página selecionada
        pages = {
            "home": page_home,
            "palpites_jogos": page_palpites_jogos,
            "palpites_grupos": page_palpites_grupos,
            "palpites_podio": page_palpites_podio,
            "visualizacao_ao_vivo": page_visualizacao_ao_vivo,
            "resultados_grupos": page_resultados_grupos,
            "ranking": page_ranking,
            "resumo_diario": page_resumo_diario,
            "dicas": page_dicas,
            "estatisticas": page_estatisticas,
            "configuracoes": page_configuracoes,
            "admin": page_admin,
        }
        
        page_func = pages.get(st.session_state.page, page_home)
        page_func()
        
        # Rodapé com identidade visual da Copa 2026
        st.markdown("""
        <div style="
            margin-top: 50px;
            padding: 20px;
            text-align: center;
            background: linear-gradient(135deg, #1E3A5F 0%, #2A398D 100%);
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        ">
            <div style="font-size: 1.5rem; margin-bottom: 10px;">
                🇨🇦 🇲🇽 🇺🇸
            </div>
            <div style="
                font-size: 1.8rem;
                font-weight: 800;
                color: #FFD700;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                letter-spacing: 3px;
                margin-bottom: 8px;
            ">
                #WeAre26
            </div>
            <div style="
                font-size: 0.9rem;
                color: #ffffff;
                opacity: 0.9;
            ">
                🏆 FIFA World Cup 2026™ | 🍁 Canadá • 🦅 México • ⭐ Estados Unidos
            </div>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()