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
    .stTabs [data-baseweb="tab"] {
        color: #1E3A5F !important;
        background: #e9ecef !important;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: #1E3A5F !important;
        color: #ffffff !important;
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
        background: linear-gradient(90deg, #3498db 0%, #2980b9 100%) !important;
        color: #ffffff !important;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(90deg, #2980b9 0%, #1f5f8b 100%) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
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
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        color: #1a1a2e !important;
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
        font-size: 2rem;
        font-weight: 800;
        color: #1E3A5F !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1rem;
        font-weight: 600;
        color: #495057 !important;
    }
    
    /* ========================================
       DATAFRAMES E TABELAS
       ======================================== */
    .stDataFrame {
        color: #1a1a2e !important;
    }
    
    .stDataFrame th {
        background: #1E3A5F !important;
        color: #ffffff !important;
    }
    
    .stDataFrame td {
        color: #1a1a2e !important;
        background: #ffffff !important;
    }
    
    /* ========================================
       ALERTAS
       ======================================== */
    .stAlert {
        border-radius: 10px;
        border-left-width: 5px;
    }
    
    /* Info alert */
    div[data-testid="stAlert"] {
        color: #1a1a2e !important;
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
    MASCOTES_IMG = "data:image/jpeg;base64,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"
    
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
    # Imagem dos mascotes embutida em base64
    MASCOTES_IMG = "data:image/jpeg;base64,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"
    
    # Imagem dos mascotes (menor na home)
    st.markdown(f'''
    <div style="text-align: center; margin-bottom: 0.5rem;">
        <img src="{MASCOTES_IMG}" alt="Mascotes Copa 2026" style="max-width: 200px; height: auto;">
    </div>
    ''', unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">⚽ Bolão Copa do Mundo 2026</h1>', unsafe_allow_html=True)
    
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
    st.markdown("## 🏅 Palpites de Classificação dos Grupos")
    st.info("Escolha quem será o 1º e 2º colocado de cada grupo")
    
    session = get_session(engine)
    
    try:
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
                    
                    if st.form_submit_button("💾 Salvar"):
                        if primeiro and segundo and primeiro != segundo:
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
    st.header("💡 Dicas para seus Palpites")
    
    # Texto explicativo sobre o ranking
    st.markdown("""
    ### 📊 Sobre o Ranking FIFA
    
    O **Ranking FIFA/Coca-Cola** é a classificação oficial das seleções masculinas de futebol, 
    atualizado mensalmente pela FIFA. Ele considera os resultados das partidas internacionais, 
    a importância dos jogos e a força dos adversários enfrentados.
    
    > **⚠️ Importante:** Este ranking serve como uma **referência** para auxiliar nos seus palpites, 
    > mas **não deve ser seguido à risca**! O futebol é imprevisível e grandes surpresas acontecem 
    > em toda Copa do Mundo. Seleções bem posicionadas podem tropeçar, enquanto equipes menos 
    > cotadas frequentemente surpreendem. Use estas informações como um **guia**, mas confie 
    > também na sua **intuição** e **conhecimento do futebol**!
    
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
    
    st.header("🏆 Ranking do Bolão")
    
    with get_session() as session:
        ranking = get_ranking(session)
        
        if not ranking:
            st.info("Nenhum participante no ranking ainda.")
            return
        
        # Configuração de rebaixamento (apenas admin vê)
        qtd_rebaixados = int(get_config_value(session, 'qtd_rebaixados', '2'))
        
        if st.session_state.user.get('is_admin'):
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
            .podio-container {
                display: flex;
                justify-content: center;
                align-items: flex-end;
                gap: 20px;
                margin: 30px 0;
                padding: 20px;
            }
            
            .podio-item {
                text-align: center;
                border-radius: 15px;
                padding: 20px;
                min-width: 150px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            }
            
            .podio-1 {
                background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                height: 200px;
                order: 2;
            }
            
            .podio-2 {
                background: linear-gradient(135deg, #C0C0C0 0%, #A8A8A8 100%);
                height: 160px;
                order: 1;
            }
            
            .podio-3 {
                background: linear-gradient(135deg, #CD7F32 0%, #B8860B 100%);
                height: 130px;
                order: 3;
            }
            
            .podio-posicao {
                font-size: 2.5rem;
                font-weight: bold;
                margin-bottom: 10px;
            }
            
            .podio-nome {
                font-size: 1.1rem;
                font-weight: 600;
                color: #1a1a2e;
                margin-bottom: 5px;
            }
            
            .podio-pontos {
                font-size: 1.3rem;
                font-weight: bold;
                color: #1E3A5F;
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
            
            .zona-rebaixamento-header {
                background: linear-gradient(90deg, #E63946 0%, #ff6b6b 100%);
                color: white;
                padding: 10px 20px;
                border-radius: 10px;
                margin: 20px 0 10px 0;
                text-align: center;
                font-weight: bold;
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
        
        # ========================================
        # PÓDIO - TOP 3
        # ========================================
        st.subheader("🥇 Pódio")
        
        if len(ranking) >= 3:
            # Pódio visual com HTML
            podio_html = '<div class="podio-container">'
            
            # 2º lugar (esquerda)
            podio_html += f'''
            <div class="podio-item podio-2">
                <div class="podio-posicao">🥈</div>
                <div class="podio-nome">{ranking[1]['user'].full_name}</div>
                <div class="podio-pontos">{ranking[1]['total_points']} pts</div>
            </div>
            '''
            
            # 1º lugar (centro, mais alto)
            podio_html += f'''
            <div class="podio-item podio-1">
                <div class="podio-posicao">🥇</div>
                <div class="podio-nome">{ranking[0]['user'].full_name}</div>
                <div class="podio-pontos">{ranking[0]['total_points']} pts</div>
            </div>
            '''
            
            # 3º lugar (direita)
            podio_html += f'''
            <div class="podio-item podio-3">
                <div class="podio-posicao">🥉</div>
                <div class="podio-nome">{ranking[2]['user'].full_name}</div>
                <div class="podio-pontos">{ranking[2]['total_points']} pts</div>
            </div>
            '''
            
            podio_html += '</div>'
            st.markdown(podio_html, unsafe_allow_html=True)
        
        elif len(ranking) > 0:
            # Menos de 3 participantes - mostra o que tem
            for i, r in enumerate(ranking[:3]):
                medalha = ["🥇", "🥈", "🥉"][i]
                st.markdown(f"**{medalha} {r['user'].full_name}** - {r['total_points']} pts")
        
        st.divider()
        
        # ========================================
        # RANKING COMPLETO
        # ========================================
        st.subheader("📊 Classificação Completa")
        
        # Determina a posição de início da zona de rebaixamento
        total_participantes = len(ranking)
        inicio_rebaixamento = total_participantes - qtd_rebaixados
        
        # Mostra ranking do 4º em diante (os 3 primeiros já estão no pódio)
        ranking_html = ""
        
        for i, r in enumerate(ranking):
            posicao = i + 1
            nome = r['user'].full_name
            pontos = r['total_points']
            
            # Verifica se está na zona de rebaixamento
            is_rebaixado = posicao > inicio_rebaixamento and qtd_rebaixados > 0
            
            # Adiciona header de zona de rebaixamento
            if is_rebaixado and posicao == inicio_rebaixamento + 1:
                ranking_html += f'''
                <div class="zona-rebaixamento-header">
                    ⚠️ ZONA DE REBAIXAMENTO ({qtd_rebaixados} {'vaga' if qtd_rebaixados == 1 else 'vagas'})
                </div>
                '''
            
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
                icone = "⬇️"
            else:
                icone = f"{posicao}º"
            
            ranking_html += f'''
            <div class="ranking-row {row_class}">
                <div class="ranking-posicao">{icone}</div>
                <div class="ranking-nome">{nome}</div>
                <div class="ranking-pontos">{pontos} pts</div>
            </div>
            '''
        
        st.markdown(ranking_html, unsafe_allow_html=True)
        
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
                maior_pontuacao = max(r['total_points'] for r in ranking)
                st.metric("🏆 Maior Pontuação", f"{maior_pontuacao} pts")
        
        with col3:
            if ranking:
                media = sum(r['total_points'] for r in ranking) / len(ranking)
                st.metric("📊 Média", f"{media:.1f} pts")
        
        with col4:
            st.metric("⬇️ Zona de Rebaixamento", f"{qtd_rebaixados} vagas")
        
        # ========================================
        # CRITÉRIOS DE DESEMPATE
        # ========================================
        with st.expander("📋 Critérios de Desempate"):
            st.markdown("""
            Em caso de empate em pontos, os critérios de desempate são:
            
            1. **Maior número de placares exatos**
            2. **Maior número de resultados corretos**
            3. **Maior número de palpites feitos**
            4. **Ordem alfabética do nome**
            """)


# =============================================================================
# PÁGINA DE ESTATÍSTICAS
# =============================================================================
def page_estatisticas():
    """Página com estatísticas do usuário"""
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
    
    finally:
        session.close()

# =============================================================================
# PÁGINA DE CONFIGURAÇÕES
# =============================================================================
def page_configuracoes():
    """Página de configurações do usuário"""
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

def admin_gerenciar_repescagem():
    """
    Página de administração para definir os times classificados da repescagem
    """
    import streamlit as st
    from db import get_session
    from models import Team, Match
    
    st.subheader("🔄 Gerenciar Times da Repescagem")
    
    st.info("""
    **Instruções:**
    Selecione as seleções que se classificaram em cada vaga da repescagem.
    Após selecionar, clique em "Salvar" para atualizar os jogos automaticamente.
    """)
    
    with get_session() as session:
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
    admin_gerenciar_repescagem()


# =============================================================================
# PÁGINA DE ADMINISTRAÇÃO
# =============================================================================
def page_admin():
    """Página de administração"""
    if st.session_state.user['role'] != 'admin':
        st.error("Acesso negado!")
        return
    
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
    
    # Separa jogos com times definidos e jogos do mata-mata sem times
    jogos_com_times = [j for j in jogos_pendentes if j.team1_id and j.team2_id]
    jogos_sem_times = [j for j in jogos_pendentes if not j.team1_id or not j.team2_id]
    
    st.markdown(f"**Total de jogos pendentes:** {len(jogos_pendentes)} ({len(jogos_com_times)} com times definidos, {len(jogos_sem_times)} aguardando definição)")
    
    # Mostra jogos com times definidos (podem receber resultado)
    if jogos_com_times:
        st.markdown("### ⚽ Jogos prontos para resultado")
        
        for match in jogos_com_times:
            team1_display = get_team_display(match.team1, match.team1_code)
            team2_display = get_team_display(match.team2, match.team2_code)
            
            with st.expander(f"#{match.match_number} - {team1_display} vs {team2_display} | {format_datetime(match.datetime)}"):
                with st.form(f"result_{match.id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        gols1 = st.number_input(f"Gols {team1_display}", min_value=0, max_value=20, key=f"res_gols1_{match.id}")
                    with col2:
                        gols2 = st.number_input(f"Gols {team2_display}", min_value=0, max_value=20, key=f"res_gols2_{match.id}")
                    
                    if st.form_submit_button("✅ Confirmar Resultado"):
                        match.team1_score = gols1
                        match.team2_score = gols2
                        match.status = 'finished'
                        session.commit()
                        
                        # Processa pontuação dos palpites
                        process_match_predictions(session, match.id)
                        
                        st.success(f"Resultado registrado: {gols1} x {gols2}")
                        log_action(session, st.session_state.user['id'], 'resultado_lancado', details=f"Jogo #{match.match_number}: {gols1}x{gols2}")
                        st.rerun()
    
    # Mostra jogos do mata-mata aguardando definição de times
    if jogos_sem_times:
        st.divider()
        st.markdown("### 🏆 Jogos do Mata-Mata (aguardando definição de times)")
        st.info("⚠️ Esses jogos precisam ter os times definidos na aba 'Jogos' antes de receber resultado.")
        
        for match in jogos_sem_times:
            team1_display = get_team_display(match.team1, match.team1_code)
            team2_display = get_team_display(match.team2, match.team2_code)
            
            st.markdown(f"#{match.match_number} - {team1_display} vs {team2_display} | {format_datetime(match.datetime)} | **{match.phase}**")
    
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
                        
                        st.success(f"Resultado atualizado: {gols1_edit} x {gols2_edit}")
                        log_action(session, st.session_state.user['id'], 'resultado_editado', details=f"Jogo #{match.match_number}: {gols1_edit}x{gols2_edit}")
                        st.rerun()
                    
                    if delete_result:
                        # Apagar resultado e voltar jogo para status 'scheduled'
                        match.team1_score = None
                        match.team2_score = None
                        match.status = 'scheduled'
                        session.commit()
                        
                        # Reprocessa pontuação dos palpites (zera pontos deste jogo)
                        process_match_predictions(session, match.id)
                        
                        st.success(f"Resultado apagado! Jogo voltou para status 'Agendado'.")
                        log_action(session, st.session_state.user['id'], 'resultado_apagado', details=f"Jogo #{match.match_number}")
                        st.rerun()
    else:
        st.info("Nenhum jogo finalizado ainda.")


def admin_grupos(session):
    """Definir classificados dos grupos"""
    st.subheader("🏅 Classificados dos Grupos")
    st.info("Defina os classificados de cada grupo após o término da fase de grupos")
    
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
                
                if st.form_submit_button("💾 Salvar"):
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
            
            matches = session.query(Match).order_by(Match.datetime).limit(20).all()
            
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
# NAVEGAÇÃO PRINCIPAL
# =============================================================================
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
            
            # Menu de navegação - diferente para admin e participantes
            if st.session_state.user['role'] == 'admin':
                # Admin só vê opções administrativas
                menu_options = {
                    "🏠 Início": "home",
                    "📊 Ranking": "ranking",
                    "📈 Estatísticas": "estatisticas",
                    "⚙️ Configurações": "configuracoes",
                    "🔧 Admin": "admin",
                }
            else:
                # Participantes veem todas as opções de palpites
                menu_options = {
                    "🏠 Início": "home",
                    "📝 Palpites - Jogos": "palpites_jogos",
                    "🏅 Palpites - Grupos": "palpites_grupos",
                    "🏆 Palpites - Pódio": "palpites_podio",
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
            "ranking": page_ranking,
            "dicas": page_dicas,
            "estatisticas": page_estatisticas,
            "configuracoes": page_configuracoes,
            "admin": page_admin,
        }
        
        page_func = pages.get(st.session_state.page, page_home)
        page_func()


if __name__ == "__main__":
    main()