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
    MASCOTES_IMG = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAUDBAQEAwUEBAQFBQUGBwwIBwcHBw8LCwkMEQ8SEhEPERETFhwXExQaFRERGCEYGh0dHx8fExciJCIeJBweHx7/2wBDAQUFBQcGBw4ICA4eFBEUHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh7/wAARCADwAZADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD6V0K3n0a9+26nEbaDYU3tz8xxgcZPan+Io31y6in0pTdRxpsdl4w2c45x2qa4v18Sx/2bBGbdwfM3ucjA7cfWi2m/4RcNbXC/aTMfMBj4AHTHNSBbsdRsrTSE065uFjukjMbRkHIY9vTvWPodnc6Rfx32pQtbW6KVLsQQCRgDjJqaXSZ9RdtZjnjSKQ+eI2B3ADtnp2qeXU18SRf2bDA1uzkOHc5A289BQBH4jzrksD6SDdLCrCQrxtJIx1x6GtDR9Qs9O0uKwvp1guYwVeMgkgkkjpx3FU7b/ilgyXA+0m4+YeXxt2/X61FNpU2tSHV4Zo4UlO4RuCSNvHUfSkBBo9ld6VqMd/qEJt7aPO+QkEDIwOnPUirXiNhrhg/sn/S/J3eZt425xjrj0NOk1VPEMJ0uGBrd5uQ7tkDHPb6Ulsn/AAizMbjFz9p+75fG3b9frQBb0O/tNL06Oy1CYW9zGWLRsCSATkdPasbS9PvNO1KLUL23aG2iYs8hIIAIIzxz3FXJdKn12VtUgljhjlwAjgkjbx2+lPm1qPWYTpEUDRST/IJGbIGOeg+lMBfEUqa3FBHpR+1PCxaQKMYBGB1xU2gX1tpFh9j1KUW9wrlijAkgHp0qtbxP4XYz3BFyLgbFEfGMc96bNpsviORtSt5Ut0b93scEn5eM8UgKlnYXlpqqalcQNHaJMZWlJBAUk846960vEU8Ws28UGlt9qljfe6qMYXGM8470yTWEv4DoaQNHJIPIEhYFQRxnHpxTba1k8Mubu4ZblZh5YWPgg9c8/SmBY8O3dvo9g1pqcn2afzDJsYEnacYPGfQ1kw6feRayNUkt2WzE5mMpIxsznd69KvTWMviSQ6hbyLbKB5WxwScjvx9acdZS4hOhrAwlZfsvmlhtz93OOuOKQE3iG6h1myS20t/tUyyCQooIIXBGeceopPD1zDoto9tqj/ZZnk3qrAklcYzxnuDVe2s5PDMn2+5kS4Vx5QSPIIJ5zz9KdcWreJ2F7A4tljHlFXGST1zx9aAKUljeSas+pJbs1m0/nCXIxsznPr0rW8QXdvrFgLTTZRczlw4RQQcDqefrVf8AtdIIP7CNu7SKv2bzQw25Py5x1xUcNlN4addQuJEuI/8AVbIwQcnvz9KYEvh6aPQ4ZodWb7K8r70VhnIxjPGazruxvLvVZNRtrdpLSSYSrKCMFfX17VfngbxSy3MBFssA8siQZJJ5zxSpq0emW40eSB5HjHkmVTgEnvj8aALOu3trq2nNZ6dKLi4dlZUAIJAOT1x2qv4dddCinTVW+zNMwaMMM7gBz0z61DBp0/h511O4mjuI4vkKICCd3HepZo28UOk9sRbC3ypEnzbs89vpSAzNXikvdZN3bBXgu3/0dzIq+bhedoJBOApP4GtnUNZ0vXdHa00i+hvLi4jEkUaN8zqGGWAPbg15zeaV4V8I60bO3NzHPY3EV+LaV3a0imbIDw/883bcVK7gpDcjpVWybw21zBY39re2ct15drHDErKRHAxlaBpPujLDkqSTjBxWjqYZT5OZ+ttPzMJRxaXMor0vr8tD0nw4ToRnOrD7KJ9vl553Yznpn1FUtZs7vVNTlvrC3e4tpAAsikAHAwevPUVelYeKVCW4+zG25bfzu3emPpT4tUj0KP8AsqWFpni5LoQAd3PQ/WszcsalqNjfaVJYWlwstzKgRIwCCSMcc8djVPw+jaJPNLqg+zJMoVC3OSDk9M1AmiXOkuuryTxSxwHzDGoIYg9sn61PcTHxQFt4F+zGD5yZOc547UAVNetLrV9Re802Fri3ZAodSACQMEc4rYudTsbjSW06G4Vrp4hEseDkvjGOmOtVbfUk8Pp/Zk0TTunzl0OB83PeoDok9pINZaeNo42+0GMA7iOuM+tMBdAik0a8e41RDbROmxWbnLZzjjPYVF4itp9Yvxd6bEbmARhC68fMCcjnHqKnubo+Jttlbr9meI+aWk5BHTHH1qS2vx4cU6dcRm4cnzd8ZwOeMc/SkBZXUrEaN/Znnj7X9n8jysHO/bjb0x1rM8P282jXxu9TjNtAYzGHbkFiRgcZ9DUn9iT+Z/bYnj8vd9q8vB3Y+9tz61JcXn/CTINPgja2dT5u+Q5BA4xx9aAIvEcUutXkVxpcZuoo49jMvGGyTjnHY1oWeo2VvoyabNOqXaxGIxEHIfGMenU1Vt7v/hGQbK4Q3Ly/vQ0ZwAOmOfpUJ0ea8l/ttJo0idvtAiIO7A5xnpnimBDoVtcaNfLeanEbaAIULtgjJ6DjNT+IlbW7iGXSlN0kSFXK8bSTkDnFSXF+viWIadBGbdyRJvc5GB24+tJBL/wiwNvOv2k3B3gxnGMcd6QFzS9SsrHSo7C7nEV1EhR4yCSCc8ccdxWRolndaRqMV9qMDW9sgYNIxBAJGB0561O2kT6s7avHNHFHOfMEbAlgB2yOO1TT6kniKH+y4YmgeUhg7nIG3nt9KAGeIv8AievA2lZuhCGEm3jbnGOuPQ1c0W+s9L0yKxv5hBcR53xsCSMkkdOOhFVIGPhUlZx9pNzyPL+Xbt9c/WmS6VPrzNqsE8cCTdI3BJGOOo+lAFbSrO707U49QvoGgtY2JeQ4IGQQOnuRV3xEya4sC6UftTQsTIF42g4x1x6Us2qJrsJ0mKFoXl4Ducgbee30pkKt4UYyXGLn7T8qiPjG3nnP1oAuaJf2mk6ellqMwt7hCWZCCSATkdPasawsbuz1WPUbq3aO0SUyNKSMBTnB4571bm02XxE51OCVIEkGzY4JIxx2qWXVU1KA6KkLRyyDyRITlQR3x+FO4C+IZo9bghh0tvtUkT73VeMDGM84707Qry30axNnqcn2acuX2FSeD0PGfQ1BDC/hZjc3BFyJx5YEfBBHOeabNZSeJZDqUEiW6AeVskyTkd+PrSAsatYweHbUahp2/wA7cI/3p3DB68fhTNIhXxNFJcakW3wt5a+UdoxjPNVPD4uRqH/E4M32XYf+PvOzdxj73GetT+Ii32iMaMWEWz959k+7uz3298UwGzancWN22jwGL7PG/kruXLbT7+vNW9T0628P2h1HTw/noQg8xty4JweKlsFsDoyG7Ft9u8o7vMx5u/nGc856VkeHxeLqCf2ubg2u07vtOdmccZ3cZzQBb0kf8JOJW1LObcgJ5Xy9euevpUNxqdzpN6+k2pi+zxMFTeuWweTz+NRePNRsNJ02bVbef7PZWVtLcXklr0VEG4ltvfAOM18teNvGnxJ8QxRXyeNYvCVtcDMNlARHKAeglnzveTBGccA8AVy4nGUcNZ1Xa+x0UMNOu2o9D651HS7XQ7J9SsPMFxFjb5h3Dk4OR+NVtJY+JWkXUj/x742eV8v3uuevoK+Y/g54k+Kvh/xEsviLxG/iLQBGTLBe3huN+fulCw3KQec5x9a931jxz4dm0T+2bG7/ALOhtYnkvkUbHiAAPzBfvd8EZzWdDMcNXk4QmrlVsHWpataHQ3mo3OiXkmmWRj8iIAp5i7m5GTk/U1cvtHtNIsn1W0803EIDJvbK5Jx0/GvnqD4vePvFOmrqHhbw74f0rTJcmC+1oNdXU6gkBvLUgKPqT0rO+I/xI8Xaxonh/wALaFqeoWGtX0gGtXNqGC26IBv2MfuqScg9cYWl/amE55Q9orx3RSwFeybjoz6Q0xpPEUjw6mpVIQGTyxs5PFV9R1C40G6bTrAoIEUOPMXccnk818w2fhzVtMm+2eHvHPi7T9QxzcPqTzLIf+mkbfKwz2r07wR8cNFsPCF2PiVboviPTbtbe4itLYzPdRPjy7iNTyUPIOCcEY7gVngs3wuMbVN6rvoOvl9airtX9D16fSbSysDrMPmfao084bmyu489PTmq2l3D+I5ntNQI8uJfMXyhtOc4rmfAni3SfF12LnRdY/tCwSXFzEWYGBTnCyxtgp9GArrfESwi2iOjhFl3/P8AZcbtuO+3nGa9JNPY42mtGVNSvJ/D10bDTinklRJ+9G5snrz+FXm0i0gsP7ZXzPtSx/aOW+Xfjd09M07w8kI04vq8aed5hw10vzbeMfe7daxoxqA1dTJ9qFj5/O7d5Xl7vy24/CgRc026k8STmx1Ar5SL5o8obTkcdeeOTTdUuZfDlyLHTiPKkXzT5o3HJOOvHHFW/EP2ZbJP7H8oXHmDd9lxv24Ofu84zil8PG2Nox1jyvP3/L9qxv247bucZzQA6PSbSawGsOH+1NH9oOG+Xfjd09M1SsLuXxDcDT9QKeTtMn7obWyOnP41TuBqP9sP5X2r7F5/y7c+V5e78tuPwxWxr7Wg0/8A4lPkfat4/wCPXG/b3+7zjpTAp6pNJ4anjtdNI8uZS7+aNxyDjjpVy20u1v7BdVuBJ9pkTzW2thdw9vwpnh0wvbynWQhl3fu/tYG7GO27tmsq+W//ALXlNqbr7EJhs8vd5WzjOMcY60AWrK/n126TTL5k8mQFm8pdrZAyOam1F28NSRw6ecJOCz+b8xyOOOnrVrXTYjTn/sv7P9q3Ls+zY34zzjbz0qr4cAMU51rBbI8r7X1xg5xu/CkB5J4t1cavMuu6cZRdQ6sbTUCibhFNDkosoPy+UwUEMQR93v0l8MW51HxHe6x4jEqwCVJRIYtkMMsjsNsAXO4/dJOCQxwSa4PXdNvl+PHjS4sIdcttLa5V7ibS4BcJjylKs0XWRC27OzkZ+tbmgG51HxH4eRdWsLjT/OkMd1abyLqZcuICW+aOQEZ8pwDgHBas8RhaVKPs+Zu+v362MpYfHTqfWqavFaW/C/y3PdtWQeGvLOmHH2jIk835vu9MdPU1Np2l22t2q6pemQ3EuQ3lttX5TgcfhUPhnkz/ANtHd93yvtf4527vw6VS1wXn9pTDTPtAtONn2fPl9OcbeOua0NSW01i61W6j0u58r7PM3lvsXDYHofwq3qsCeHY0n00kPMdj+b83A54qfVBpw0iT7D9m+2bB5fk7fM3cdMc561Q8Mlxcz/2yX8vYPL+19M55xu74pgWNM02DX7b+0r9pPPZih8ptq4XgcVTtdYu7y9XSZjF9neTyDhcNtzjr60mufav7Rf8AsozfZdgx9mzs3Y5+7xmtW7TTf7Gc2wtftvk/Ls2+Zvx2xzuzSAh1W2i8PQreaeCJZG8tvNO4Y6/0pNMsYfENub/UC/nBzEPKO0bR0459TVTw75y3r/2z5hg8v5Ptedu7I6buM4zRr5m+3gaOZRbeWM/Zc7N3Ofu8Z6UANGr3n27+xsxfZfN+zfd+bZnb19cd6vapaReHbZb7Tt3nM4iPmncMHnp+AqwRpp0UkC1+3eR1+XzfM2/nuz+OayfDq3Avz/bHnfZ/LOPtROzdxj73GetMC5pdrH4khe71Et5sTeWvlHaMdff1qrJql1bXzaNEY/sqSeQNy5baTjr6807xD5n22P8AsYyCDy/n+yZ27snrt4zitG2/s86Ovn/Zvt3kndv2+b5mO+ed2ce9AFfVLC38O2n9oafv84MI/wB6dwwevH4UzSIl8TJJPqRO+BgieUdowRnnrVLw6Lo6ig1bzzbbDn7VnZu7fe4zVjxIdtxANIbZHtPmfZTgZzxnbQAy41S60y8fSrXyvs8LCNd65bB9T+NXdT0620GzbUrDf58ZCjzG3Lhjg8VPpZ09tGiN4bY3RjO8y7S+7nrnnPSsXQI7z+0Yv7U+0ta4O/7SWMeccZ3cdaALmkgeJzKdSJzb4CeV8v3uuevoKjvdRuNEuX0yyMfkRY2+Yu5uRk8/U1L4lKoYP7G4yG837J+GN238etWdEewOmR/2mbY3Z3b/ALRjzOpxnPPTFIBuo6Za6LYPqln5n2iLBXe2V5ODx+NV9JY+J2dNTIxbgMnlfLycg56+lUtFjvf7Ti/tL7SbTJ3ifPl9DjOeOuKveJykaW/9iYDZbzfsnXHGM7fx60wItRvrjQJm0+wKeTGNy+Yu48jJ5q3d6Xa6dYNrFv5n2mNBKNzZXcfb8ad4feybTV/tXyDdbm3facb8Z4zu56Vlacl6dVQ3n2k2ZkO4S7vK284znjHSkBb0qZvEsr2+okbIV8xfKG05zj3pmpXc3h64+wafs8kqJP3o3HJ68/hU3iYRJbwnRtok3nzPsn3tuO+3tmpPDzW32AnVzF9o3n/j6xv28Y+9zjrQAmqX0PiG2/s/Tw5m3CT96NowOvP403R5B4cSS31IEPMwdPK+YYAxz0pJtPXw0n9pwym5bPl7HG0c98j6UQRHxODdTubUwnywqDcD3zzQBXudOu767bV4EjNq7+aCz4baPb14q5qWpW/iC1/s6wEnnOQ481dq4HJ5qBtWksCdFWFZEjPkCUnBIPfH41JJpa+HIv7Sgma4ePCbHUAHPHagDiPjPpl5Z/BnxXppRnub61VUSE5ygdQ4/wC+Sf1r5U+KtortFO2HhL7FBH1r7T1uzm8a6Ff2xItpFt3ijC/MGZlOM59wK+S9b02XV9BuLB9kd6jKUEnG1twDD8MV8vn1V0sRRm/h1/Q+gyPlfMn5HNfCTVLuw1Y6cpkazkBdU5IjYfyB6Y9cV3mry2+sfarfTrG+1FYY3juo4ZFjjDbeY/MY4LY7DOMjOK5/TtOFr4d1iPRYZzPDC8cFyOHuJwDkoP7oPAPc5x0ycPwxpPxOOgxeF7bTf7IsJC3mX0gw6qxLOSdxOTnHAyfUda8WVGniakq3Mo2a3dvNvTX5LXuevVrcr5YrRnY+Hdft7b4WLr2l6JdR2lpG8cNkjeYwVG28n07k845rkvh/44u9V1+7fxN4mOmQOm63iSGMQ59CzKcADpnr611lp4p0b4f/AGbwXDp2sajc20Qk3W8asZDJlzgZz+AHAql4a0LwN4w8TX7zeG9U0i9hRJnsZ5fKSVWP+sCKARzwQDjnNaUqdGEas6lN8stVLRu3Tf8AP7znk5NxUXt0NvQPEw1TUtX0+wvbXVFsrdJ7eeNdnmZDZVu3DAcgdDXGy+KfEdxpdp4wuvBVu9msZKXUV0SyoTg5GCQuR3GARmvTJYvCHg+KNXbStFExCKDtRn5x/vEe54rL1rwpfwaPdW/gvWBpqTowFq6iS3O7qYjyYic9VyvPTvXNSnhlO7haMrWbutLWfw9/Rot87W5Q0/WINW0qHxd4UmNvrVngoVIEuRy9tLj7yOuRg5ByCK9RsPHmtagjz6Qw06GZB/q1zIF64LN938BXjPw++H8nh6wu7i7vxPc39uYTHbPmGPr3/iYHv25rM8OeLta0jwHb3c1++oxSq8EqyAGVJkLfuy3UggZ5546nIrpc68YTo4Gr7qat81sn8jL2NKpJSrR1sJqtn4t0HxZPf6Z8T7kNI+6Oa91CQu5znaysSrgdOmD6V9M/A/4k6z4t0O+8MeKoLQ63awRiO7suILuOQsqtt/gYFcMOnII64HyB4K0afxX4ok1K/YSun7yVmHGf4VHoB/SvqD9nLRHW58TeJVXZa2ot7W2PaVot0jj2Hzxj869/AYus8SqE5c2l3pscGZYSFKlzWs+h67pttN4euTe6iiiJ1MQ8o7jk89OPQ03VLWbxFdrfacqmKNBE3mnacg59/Wnw3sniZ/sE6LbKn70Oh3EkcYwfrSzXreGHFhCgulkHmlnO0gnjHH0r3zwS0msWkViNIYSfaVj+znC/Lvxt6+mao2NjPoN2NRvgnkhTGfKbc2T04/Cpl0RJov7cNwyuw+1eVtGM/e2564psOoyeI5P7NmiW3QjzN6HceO3P1pgJqcUniOdLnTQNkKlH847TknPHWrMGsWllZDSZxKLmNfJbauV3Hjr6c1BPO3hdxbQKLoTjzCXO3bjjtSpoqahH/bL3DRyS/vzGFBAI7Z/CkBDp2m3OiXUeo3qx+RECreW25skYHFTaqG8RvHJpoBWAFX807eT0x19KZHqsuvuulywrbrL8xdDuI289DT5XPhcrFbgXIucsxk+Xbjjt9aAPAfG9nbHx1fWtxOlvqEN6kGGuSjQliu2SMKRLlo23Bo/lJTaQTWh8DbiPWvFEHiqS4mu7SOKRpJZkAuWMZUItxgBJyvmKyS4VxyDkGt34tW1tP4r0bXINI1B7+a2nW6u7SMsIInQxquQCSeWORyB9RXN/s6+D00nxlq1teXNztuLYW9gz28sf7vd5kmQyhdwKqPcciuOWKjOsqc7XXXr5X9D6KEsNSy+Xs6rUml7r11u1KyvpfR9PTv7tqxPiQRf2aM/Z87/N+X73THX0NSabqtvoloum3yyieIkt5a7l5ORz9DUNyx8Ksot/9KFz97f8u3b6Y+tPTSE19P7Ulne3ebgooBAxx1P0rtPnSna6Vd6bdR6rcrF9mhbzGKPlsH2/GrWrSr4kjjg00EvAd7+b8oweOOtRLrMuqFdHeBIlnPleYrEkAd8fhT5oj4XCzwt9qNx8hDjbtxz2+tICXTNRt/D9r/Z1+JBOjFz5S7lweRzVK20q8s7savMsf2VH887Wy23r09easxaYniNDqc07W7v+7KIAwG3jOTTV1iS8xorQqiSH7OZAxJA6Zx+FMCbU7qLxJCtnp4bzI28xvNG0Y6e/rRpd5D4dt2sNQD+azmUeUNwweOvHpUU1r/wiwF7A/wBqaY+UVcbQB1zx9KW3sh4mU6hNKbZlPlbEG4cc5yfrQBVXSb0X39sbYvsvmfafv/Nszu6euO1X9TvYfEVuLHTw/mqwlPmjaNo468+oqv8A20+7+wjAuzd9l83cc4+7ux696fcWieFITqaTmf8A5ZsJAFUA8k5H0oAk0q4Xw5E9rqKtvlbzF8obhjGPb0rjPF+vxWWpG5tQsk803mQq46AEckVznjv4ptcXPmaZp0c/ljZ5kjEIR7DqfqcVyOm+IZ/Euq/brmJIHjAi8tCSoxzkZ9c143EWNq5fgJVqfxbLyud+XYaNeuoz2O01DWNe1fL31/NIpO4Rg7UH0UcVQj1u706YZmZcf3jlT7EGrkRHlcelc94pKpYzSkZKrnFfj2Fz3HSxKlKo3qfWzwVBwcVFHpWheI9K1LSXvpnitxCP3xZsKvvWPc/Ejwzue0tn1a5TOD5ceEP4Mefyrw7T7/UF042MryFWuXZs/wAYU5U/TD/pXU+GrM3MvkWttcXdyFDPHbQtIyg9CcD5c++K/dssm6+GjUqM+Or0owqNI9i8GeMdLF06W5cecRuimGx+P7vY9elb17p0+sX0+o2JgaJiBh3wwIABBHbpXiMwSO/XTbuK4sb18mOG7gaF5MdSm4YbH+yTXW+A9c1XSL8xXEhlBX5d5P71f7re46g11TpK3NE55R6o9Lv9ZttatH0qyWX7RNgL5i7V4OTk/hUOjo/huSSTU1AWcBU8k7uRyc9PWiHTrXTbJNfs7lrlUAdFIADbuOo6Yz+lLFKfFTmKb/RRbfMCnzbt3Hf6VgQRahplxrl2+pWKxmCQBV8xtrZAweKt3Ws2uoWLaRbCX7TIvlLuXC7h7+nFVpdVm8PSNpcMKXCRfMJGYqTu56CpTokemw/2wlw8kkQ84RlQASe2fxoAj0qOXw5M1xqSjy5l2J5J3HOc89KZqVjceILo6hYKnk7RH+9bacjrxz61LFMfFEn2WZRaiAeYGQ7ie2OaiudSl8NSHTIIluVwJd7naee3H0oAZoV3PrGoCz1KU3MGxn2NgDcMYPH1qbxC7aNdxQaW5tY5E3uqc5OcZ5z2q5r11a6rY/ZNLdZ7ncG2IMHaOp5xUPh6SPR4ZotWP2eWR9yK43ErjGeM96YFix0+yudITUbiFZLt4zI0pYglhnBxnHasrQb651fUIrLUpzcQOpZkYAAkDI6YpLzTry51OTUraJntHlEiuGABX1x+FaeuXtnqmntaaXIs9yzBlRAQSAcnk4oAp+LrqDwxALq0kFnbiNpJyvOduMdc884/GvkC/v73XfileTQ+ZbaVZs9zcFRhZZ5MkRk9wobOB3H0rv8A9qHx9deEtGHh+IKLuUpK8THOXwSgb/ZUfMR3JWsDR4pbrT7EyIouJoYiwUYXe4GcD6mvj+IcY00lFNaxT8+r+S09fQ9/KsPaLk3r+hzWrarqJkeOyc28Y4BX7x/Gsdtc8T2koaPVb1SP753KfwNdRofw/wDGmv8AxN1LQPEWoWnhvw1pcAvL6+sZFeUwHdtw5+4xCMTkDAB4PGbGgx/BnxZfajpHg+w8a2S6eoMviCW6a4giBbaslxC7H90W6kAEDn5cHBhMjqOipPl126/ia1c3owny2ZzGi6heal4wTX4EtY/EcMJURzEi3vUC7So7xSbeh5B9q7nw9Dq/iHxhbeKr3Sn0KGwhktUgkbdPdbvvbz0Eatnb3PWuOudCvtE8YW9teQiG9tL3yJ1U5UMGKtg9weoPoRVrxD4uv4PF9xpNvcXaatFcW0WlQxH/AEZ0fG/zl/iJB/DHBHNcEozqzdKCV0mvRXs16a/LU77xSUlszOv73Q/DPxH8Qx+MdLbVYbrDW0kirI6xuc8biOMHHHI28Vo/DWXXo/hxr93patKmZV0a1Z93lYByFY8kDIAHqvvXrM6QS5W4hgmXp88YYH8xXM+LdZ/sOfS9K0+20+1F6ZQktw/k28Wxd5UhR1bPHQZ5OelZ/XfrEVTjC8tL3enu9l0E6XK7tnlWrW6eDfCul+IfC/iG5VrgwC4t3lDw3LN99tjcghs5HUe1L4z8J64nig3Ph+Ivo15dw3V5bq6gRyq3zMFPOCCTx6movGL6HaXNtr/h/TIW1DV0F2rXI8wWwbliqn5Qc55x6ms3TNR126uDMdbkmkU5dUmVsfUDpXoxnUSVWL735lq+y07dGYJKT5Wei+EtAb7PbeF/D0bSate3TxyHGP4jzn+6Ewc9lBr6W8F2Z8P2Vl4VjlDWcUnlTEIB5xLfOx7/ADHJrxz9ny8bUfEM9m9qj6hNZsscgADfKQWAPbI6/wC7X0hPf2UmjNp0UyNeGDyRGBzvxjGfrXpZDh0oSrt3k20eVm9ecqvJLoReIbe30ezS50tRbTM4QshyduCcc59BSeHbeHWbSS51VRdTJJsVmOMLgHHGPU1T0C2l0a9a61WM28LIUDOdw3Eg44z6Gn69DLrN4lxpKGeFE2MyHaA2Scc47EV9AeSVptRvI9WbTUuGFoJ/JEWBjZnGPXpWrr9pbaPYfa9MjW2nDhN6nJ2nqOc+lSpf2KaP/ZzzILwQeSYypz5mMYz65rJ0K1udJvxd6pC0FuEKb3ORuPQYGaALnhyOLWoZZtVAupIn2IzHGBjOOMVnXmo3tpqsun29wyWiTCNIgBgLxxnr3q3r8b61cRTaQv2iONCrlPlwc5xzjtV+zv7G20lNPuZkS7SMxshBJD46ZoAp+NZNK8K+GbzX443t/sahmeFS74LBcBSeSc4riLb4k+GL27fTdZn1H7XLdJYW0j2w/dzOHAXrjIZOc8AlfWukt9Iu7YM2ovcWFu0ZRp43G9CemOvOe+Ky4L2wtL6OebXdXubSMytJJMYtpRF+aTGzO0t+JYDFCq0YNRnu9v6sPklKLktlueZweJdCufMmtvHPiS4gjlMTSSaRbhgy7dw5UZILrwAT8wOMAkTw65oFxpC63Z/EfxdCRNGET7BaI6l1kcNt28gCJ+RnnAGScVvaj4j06DTl1i2vvEciQWn28wtcRcuZfKittpQ8yMG5B3Bc8mqEHiOceKdbhvbDWrSx8MCObWdRm1C1MasV8yOKNFi3M5IVcEqQDk4LcueW4SnOXNTSktX5fgYwn7TDqvGbcHdJ3dtEm+vRNHX/APCw/DFtDcxeJbq81BrHfEsrQqDK8bKkm1VYHOWBwQOAxAwM1pWHic3tjbX+hPd2mm3UKzQQzQ7HUHrlWyRk5PuCCODXFXniy7k8NWWtNb6hc3OpvPc29la6hbMVtooi8s0kjw7Qyj5Op6hQRmvT/A2s6UPCGmTSXsji4t0uUa5Uea0cg3oWwMZ2kdKpypygnAqnJSimti7qunWNlpUmoWkCxXUSB0kDEkNxzg8dzVHw5J/bdxNFqj/akhUMgfjaScHpiqmnWF7Y6jDf3kDRWkb7ndmBAXnnGfcVf8Qyx61FDHo+LiSJi0gQbcA8A84qCypr15caRfvZ6bMbe3VA4RQCASOeua1LrT7GDRn1KCBUu1hEyyhjkPjOcZx1pmhXdppVgLTVJFguFdmZHGSATx0zWZb6feQammpTQstos3ms5IICZznGaQE3hyaTW7uS31WT7VFHHvVW4w2cZ4x2NJ4guZdFvRaaXIbaEoHKLyNxzk859BVvxDLFrFrHBpBFzKj73VBtIXBGecd6XQLm30i0NrqriCcuX2ONx2nGDkZ9DTAmTTrA6MNTMCG88jzzLk58zGc9cda8k+KviHU7wW2jPfOYCv2i4UkAdSFB9uCfyr0UWF6dW/tJYG+xef53mbhjy85zj0xXlnxamsdc+Ii2Mbloru6traRhwDCE8xx+OCv0Jq6ejv2KjuY9r4VutS0J9Wub7TtC0nblbzUXK+YD0YLkYB7ZOT6VzWgWzaVrM1ul7ZX1tJiSC7s5RJFKOhwR0II5HauL/bg1rWj40stGE00eiWljC0KISqF5FLM5x3JBXP8AsY9ayPhX4q1rWtZhOqWFlYxQ6bBaw/ZbUW4lEecSMo4LkHluM4FfP8SxeIy2qn0/RnpZbLkxMT6Os5d8Qwe1Y3iwZ025H+wak0q7TyVG7tVfxI+/T5tpzlMV+I0abhXXqfZS1izl7RBJBa8bigK4/DOP0rF+NfxH8T+BtK0Hwr4Oum0g3enJqN/exDE00spbA3dQoC9uST1wAK6bQgI5FBALKwdQfUGuh8c/DnTPHumWbalBKEtotlrcW2S6Rk7vLbAJGCTggHGSCDmv2rh7HKtgfZLVxd7d0fI5jQ5a3M+pjfCD4k6L48OnfD7XdW1XX2v9MMzXeowIlzp+oRqWIilQDeuFZkb7y4AJO4gdfpU095p2y5P+nWkr280ijG6WJyrNj0bGcf7VYXwn+FGjeC9Y/tfTbe+vL6GN1g88sEMjAqXkkZVAAUkBVUnknk4rs7rS00nQPs8swmupZmmuJgNvmSO5dyB2HOAPQCvcjiHRozrTjZJPRnnxp801BPc3PBF9K+oQaJdSFrK4diYieCQM49eoB+tdV4iSPQkhfSv9FaYkSFTncBjHXPrXlZM0mjieNiLmP542zzuU/wBcV6D8PNUgm05dXu2EVveRr5RbkblJDj2IPFVCopxU47NXMpwcW0+ht6HZ2eq6el7qES3Fw7MrOxwSAcDp7VjWGo3t5qcen3Nw0lrJKY2jIGCvPHT2qXWbC61XUJb3TojNbuAFZSACQMHr71qX+pafdaXJp9rMkl28flpGFIJbjjOPY1RBW8RRR6LBDNpQFrJK5R2U5yMZxznvUmhWlpq9gbzU4xcXG4pvZsHaMYHGPU1V8PI+kXUk2rIbeORNqFzuBbOccZ7VFrtncaxqJu9MiM9tsCbkO0bhnIwcetAE8GnSeHJf7TnlW5QDy9iDafm75P0p8sb+Jn+027LbLB+7KyDcSeueKisNQl8Q3f8AZ16U8naZP3Q2tkdOfxp2pu/hydbfTnASZfMfzvmOc44/CgB0etLYx/2I9s8kkX7gyqwCknvj8aSHS5fDrDUppVuEjGwogIJzx1NWbXR7S9sRq85k+0yr5zFWwu4e3pxVHTtUm127TTb0x+TICx8sbWyBkc0wPmL9ovw/ZXHj069r0qNZySPfxB3HMQAUo467VKjp1A+tW9D1G3uoIbiCRGBCvFIhyCOoI9qtftS+GJrHx4r3EEkulalYhLeQnJRgNsiA9jgg/wDAvrXA+HJptKlsdKt7Rzp8VoR9pZ+VZSAFI9xzX5/nFC85Ru7xbaT2tvp5n1GBq/u16Hqyaja3+u+K9M1K4Wzt/FunwRQTucIkyQtE8Wex+66g/eDMByCK8f0f9n3xVomtz3V94hh0/Q5yUupY7ho90GQzeZj5WXuFydxA4Fdidfto0EdzsKP8uGGQfb3q6UtJEjnigVx95QOdp9h2rfDcRujRjCrB3StddfwOStkyrVHKE7JkHiW8/wCEg8WzaqYng+1XhmRH+8sY+7n32hc+9a0F5BGFIEXmYGX2jd+fWsXVy1lo+oaxcDasEDbTj7ucDP61w1l4otnIUXiEnturxFTrYyUqyT1b289T6CjTjCKhdaHrJ1HH8QNYni/T9K8TaaLPWLYXEaMXjKuVZGIxkEe34VzEWtbkys6EezimvrkiDPzY9TVezq03zQ0ZvOg2u5xvxH1y58G6rbTaVaWjypAsVq9zCsywqgABCNlSevUH6V6d4k1DRviF8FdR1qK4sbvxDoEUUkWuWWniyZpDAsrxlQOikvGw5U7QwArB/s7w14hiE/iXTZ7+0lXYHgLboGVid2FIJB5B2nI9xmtoPow0S28HeFNMvbbQpbkXGqTyQtFujBBaNN4BZmChB1Cgkknv9pleLowwSdWSTV+a7W58ZjqFeWLaSe+hpeC11P4d+KdGvtbktrm+tJoPtjWWRGRLhGxu9FfJOB0PFfTr6LPazNrLTxtHG5uDEFIJGc4z0zXyp4u1STWNaSNdov8AVL6KGKNecM7hVVR3x/SvqNdVvZL0aLcPG8DS/ZnYLhiuduc+tY8NVJVKVRtWTldf8A1zaPLOGuti3NdjxOgsYYzbNGfN3udwIHGOPrTI7z/hFwbGaI3Rl/e7kO0Dtjn6U/VrZPDlul5ppcSu/lHzTuG08/0FJYQw67ZS6hqe4yQZT90do2gZ6evNfRnklZ9Mkeb+2jcwpHI32kREHdj723PTNXLi+HiOMadDGbdifM3udwwO3H1rD8a34s9Njt4XZY0thhc+q5rU8hNK0S01ewEi3EscYIkO4YdQTxUxkmFmtySO4/4Rc/ZJo/tRn/eBkO3GOMc1G2jz37nWkmjSOU+f5bAlgBzjPTtVjTLVfEHmTapkywHy18s7Rg81ma1r9zocV5axCN7W0VlVGHzFcdM+vPWqbSV2OMXJ2Rfm1VfEUf8AZUMLW7S/MJHYMBt56CuH+JVpbeEtCtILjSNX1+S+vIgIdOVQ0ojO4QsXIAUnB2jk4PbJHE6l4w1CC6Drqb6e2TsEL7MD0z1P41v+B7a38deMrX/hK7aXV5bOzc2lw8zjyBuUn5QQpLEj5iM8AZxXm4XMsLUxUJNO62Z7eMyDF0MJKVRrl+0r/mQ6PZaC3xFtPDNsmpzSjUm1OWR4lNslykLSpaOwOSUR/MwoIBZcnLAVlaPc+Hrn4e609zPrOl29hr0mrXur3It7g6lc7iSoRCyOVYpGq8gMqjkg49DvvD+had4l1yS202NbnU0eC6naaQuySKok2fNiMthclApJVSegq9rfw48Kab4IOlW1ncpZWzQvBH9qf900bLsKtnI24GOcV7lSpCpfnu+a1/kfPeyiqMaCXuRvZerv+ZzN74WsPENho2ta/dapdWVzpq20unC7jJmQPvaO4ljyHBbAZUIU7MHIGK7qPRpNYA1G3eK0hdQqQlPuBRtxxxjisnS20HTPCjR3UH2PS9KUCGK2JLEuxJySSWZm5yTkkkk1hQ/FAwf6NYadJFZpnaJCHfnrmvPrYqhRlyylY78NgMRiIt0YNpHcPrcerxf2Qlu8Tz/uxIzAgEc5wPpRb27eF2a4nIuRcDYBH8uMc55qtph0K40R9f0O5eWSD5vnb7j91ZT061Npcz+JJZLfUWGyFQ6eT8pyTjnrWykpK6OaUXF2aswuNKl8RStqcMyW6ONgRwWI28ZyKc+trdxf2ILZ0eT/AEcSlgQD0zj8Kiv9Sn0G7fTbMp5KKHBlG5skZPNXZ9Hs7ayGqxmQXSgTJuf5S556f0piK8Fs/hhzdzst0sw8oLGNpB655+lE9hJ4kk/tCCRbZVHlbHG45Hfj60zTnm8QXT2WpkbIV8xfKG0hs456+tN1K/m8PXh06xKeSVEn70bm3Hrzx6UgJxrUaxDQ/szl8fZfM3Dbn7u7HXFeE/FLS7xPG97BDcJbyWtxA8NyFJKSCNWUle68kEZ7mvfE0e0ax/tn979q8v7T975d+N3T0zXgPxY194PiDLcXCB1uLWHzwq4AYAgH24Fc+Kq1KUFOmr2evp1NqCjKVpHRw2Da9DbTazoFhdXUClY7s3I2oM5PbcVzztI6+nWvHfiNaQab4zhmsnDQwsd7L/EW4b+n5V29z400zTNGa4utQhtbbGTvmzk+w7n2FeTeJPE6a28t5ZafPFbn7stz8jSD1VOSB9cV85j8dHFJqjTsno5O33HrYXDum05S22R6Bo+ob4xg44q5fXZazkQnGcAfmK4jwhqKzW0eW+YcHnvWtreopbWjSSZYZAAHUnsK+HqYH97y26n0sal6dzpLGPa6yR4JU9e1dXomti1wqTGFv9iQEflXj1jZ3mpoJ7y5kMX8MQPygfSrLeGdEcbpbKFn9doB/MVVH/ZZ6VWn5L/go5ZpVVrH7z22fxPKV2vqGfdsCue1HxClxcraWc8d9cv/AAI+4L7sR0FeZW3hrTpZhFb2+9c8kksB+dei+EtJt7CJYraFU/vEDrX2eW5bicxiqlacvZ+el/RXf3nj4qvDD6QSudHEqrZR2ztwEw56ZJ6mtL4ZZu7zUPCnnpDJbSG8jDgkfNgSAe2drf8AAqzJlV4pIWOCyEZ9AeM1y/hjXrnSdd0/XpJAl9Zn7HeBhnzI+VLH3H9Aa+vUFGKUdkeG7t3fU94XWB4eX+y5bZrh4vmMiMFB3c9DUa6HLpzrrL3CSJCfOMaqQSD2z+NWtP0q0122XU7xnaaXgmJtqkDgED6VnwaxdX98mkTmL7PK5hbauG2j0OevFIgszynxRstoF+ymD94Wc7g2eMcUkepjw2DpksBum/1u9GCjntg/SnavEvhxIrjTiwedjG/m/MMAZ4p2madB4gtzqOoFzPu8v90dq4HTj8aALGupZpYZ0kQLc7xzbY37e/3ecVF4daHyJhrJj80P+7+1EbtuO27tmszwOB/bnGP9S39Ks+PNn9o2+8A/ue/+8aYFS+k1AarMtobn7F5wCCPd5ezjpjjHWtrXIbEaa50tbdbrcu022N+M84xz0q9of/IswY6eQf61yvg4r/b9vtx9x+n+7RYBmrRanP4N1uGG6+z6ubVv7OkuACyyBTjbv6EnAz2zXxxY3sk53SCRJMner/eVs8g575619t+P1DT2ZYZ+V/5iuC8YfBnSPGOlJrWkyppOuNuMkuwtDckEgeYo5B6fMOfUGvHzfL5YuClDdHbg8SqLalszwnw9bWt2twt1EkoWMlQw74ogv/7LiVp47qZFIVvs8RkKj+8VHOPoDVXWrPXfBeu29lrVqsPnllhljffFcAY3bW9RkHBAPtWktrDcMjvJdxzW+WVrSbY+ccY7HI7HivKwuVrEUlTrRtKD+9M66uKdOpzQejN61Sx8S6JcWwuo7yyuYmhlCPzhhgg91P15FeCfFTwBqvw/uoryCaXUdBum2wXLLl43/wCeUmOjeh6MPfIr6I8LXU8ys1zFqIyAN16kCufxj5P410N3aaZqWnz6fqdrFdWlwmyWKQZVl/zznsa9XB4N4V2hszlqYlyd2fGKyb1DFsenNSaSNf1XUf7O8P219fT4yywk7UH95j0Ue5wK9bvPgdv8QyLFryxaHvygEZa62/3Mn5fbd+lepeH9G0rw1oZ0jRLSO0tWO6QDlpW/vOx5Y/Wu2otNrjliWvhZwnhPRpdH8NWlrf3KvdqC07bsrvY5IHqBwM+1Um1zdas6HbywGRjgHGal8fa9AjTWthqWjrKoIKM7vN7/ACADH4muGgl1bxDrtroWjQ/aL67by4VP3QB952PZVHJNfG1snnOu29XJ3PVpY61PXoei/s56dqPi/wCI6+J5rC5W00KJ3iOwnFxJlYwcDhgm5vbI9a+wpRp/9jny/s323yONu3zfMx+e7P41k/BzStN8P+DbXw7pqDZYIoklChTO5HzSNjqxIJOfaqWoKNM8StLJh/LnEp29cE7u/evtcLQjQpKEVZHg16rqzcmaPh7zFvW/tcyeTsO37Ufl3ZHTdxnGai8VCb7T/wASjzPIeEhha52ljkc7eM4xWl43PnaLbuFODMpwf9003wJOi281nghwfMz2xwK3MTzbx1dNIlvOT8k0KH/x0Aj+ddF4d8QW50qGS4vBLiEIIXJbDAAA88dq5b4oXMdhr914du9sLS5u9NmbhZEY5eP6qxP4Fa8/TV7iwuPs84ZfQnofp61877arhqkoHrKjCtBSPoXwdqNrcWNzPlMmZ1yD2U4qt4nS2uPhnqF08cX2prF5PMZRuJGT169BXjXhHxkLO0kjkmUAzSHG7rk5robb4iaTdwR6FqUn2aCYiEzsRs2HjBP8Jwep4+ldEcVJ+69noZew5ZKUemp5H8QoGju7aZjmOSM7T2zn/CvTfAms2Xh/QdT1ia6eJLRIYHMbYY5UsEHqWPQe3tXlXiLUrvTpJfBWuWL3F1bOghlQ5Oxv9XIuM7gy8jHUcV0JtryCzxpXhmbUGeRZnOo3KxqZFTYreWMnIUkc46mvEVWpga2kHKWtu3zbPoszziljaUcPSi5yunJLTTfWT0RY8T/F3xMlv/aKXdnZIJAscC26SM2W43uwJY/TArsdZ+McFlqD/ZLOXXLO33GVpZykcoAOdoIOfYnj+deezat47gG6fRNHtgOgTTGkAH13VWk1PxDq++01Hwhp+pRNGS/2SJreUr34bIPX1pQzbMI6OG/95X+SaS/EzrUb2qTwD5Eto1It+r2b+8+j/iHJYXHg8zafHGkTRrLMsWPk+6V346Hk9fevmyXVtQ/4Sr7PFJuhMoTZjse9RNry6JDdvpKahZfaYRb3lpfRMm9A6sME8Egrwcngn1qTR7jS4GfxDfXMbS8mKBTynHU/7WO3atcVi/rsozUGna1n6mvDeMw1KFWk5NNO9pLlktO3+Vz2n4NLP/aN4zhzZ+ZGk+c+XkKx+bt3HX1r0nxHGsdtHJpsZt23YZoRs3A9OnXmuD+D+peT8O4pbgNHPqtzJeYYAbYiMRj8VRT+Nb/ivxJB/ZkUCHD+dCAQf9tRXv4ef1elCl1sfO5hUeLxNSstmzf8OiznsC+pQo06yMjSXKjccHpk1xeu6leprMVhLJMFBMiBicFckDA6YwKsXHiC1D3MFxISJJXbP1YkVz11qJ8Q+NEmt5JPLCJCiK2cBRjP4nJrizjEV6mGlTwlTkqX38vuZlQw75ryWh2n2qe5t5Y7VAk6NGSbddrbSpznHbIFa/h+G0NkTq/ktceYcfasb9vGPvc461mfDyMS6xqWoRHMMp2RkHOUQhAR/wB8sfxpPG0inXNrD7sK9fxNd+U0sRSwVOGJnzTS1fc5q3Lzvl2Gqb8aqVLXP2HzyP4vL8vd+W3H4Yrxb4tzWmo/FnVrOySJooIIYgY8YyEyenu36V9JHA8LYbp9jwf++K+O/DN5dah8V78XNhf2xlMrFp7d0Rj5mAASME/0r0kQiO88MqxebycOvIIUf1rhvF7eR+7lBX3HevpaHR1uoGCKH3LjivIfix4TeHfO6FUUEnArmr5bhcU1KUbSXVf5HXSxVWkrJ6HlPh/Xv7NuwSd0LH5vb3rd1LxHb6lqMUFrKHijO9j6muXvdNb96yRHCAZI6Yzir/hLQHuL0bUx6kCuCrw7GUuZPU6I5pUUeWx3ttrJS3WJOcDjAqSE3t7KMrM0efuopwfqauaX4VlXaskeGIymR1+ldvoOgXCWZubAl5Im2vGOHRvp0IrbA8MYPCv2lRc789vu/wAyKmYVqisnZFfwppszuqlcLj0r0CzsUiiUKOcVc0awia1jnVcNIoJGOh70+4nhtdLl1FjtgjV2LH0UkZ/Svaq1OZ2ONK+pnahbhJrcE488tDn3K5H6rXjXjrxHbaJ4vaK8kjjju7eO4KsQMk5V/wDx5TXe6L4jvPEngbVtRnURSW9xvt2UY2hSGT+VanhXTfDmvyXmoX+iafd3CShonubZJWjVssVBYHA3bjWbfJuDdkWvhB4nu/EPh14dLnv5YLMBUdI3VQCT8uejEY7HpjNevX0emf2TJ9lFr9s8v5fL2+Zu9sc561L4KjEXh63RFCoGYKqjAA3HoO1crohU+Jbc4AP2g/1rJ73MjT8OIVupTrBYxbP3f2o/Luz23d8VX8QtdDUz/ZBm+y+Wv/HrnZu5z93jPStPx/g2Nru5/enr/u1P4I/5Ah2cfvm6fQUgItdubXU7H7NpUiz3G8NtiGDtHU9vWovDzx6VBNFq5EEjvujEvJK4x796ittPl8Ny/wBpXTJNHjy9sROcnvz9Kdco/idhc2e2BYP3bCbqT14xTAoXtpqFxqst5awTPZvKHSRT8pXjnr0ra1q7s9Q097XTZY5rlyCixjDEA5P6VBFrEGnwDR5YZHmiHkl1xtJPfnnvVe10u48PSjU7qSKaKMbSsedx3cd6QE/h910lZl1c/Z2lIMfm87sZzjr6iqOsWd5qOpy3WnwSTWsgGx4zhTgYOPxzVu8RvFJSSzxALbIbzu+7pjH0qa21WHQoRpdzFJLJDks8eNpzzxn60wOX+OXhbRfiN8Nb7w5BJC2qhRPpjqMPHdIMqQfflT7Ma+L/AIc65qeo6gdE1SWW31O23IpfhpApwyOP7ykH6j6V9Z/EbxzoPwynS41C9h1HVRl4NKtWPnOSDt3npEvPVvwBr4t8Wa9f6548vvE/2eHStTuL57wwW4IjDE5IGeT79yST3rnrVFCzOzCUniIzjHXl/A+htFg1ZI8J9lcerFgfyFbSxauY/wB5LFCMf8s4v6sTXjNl8Zb+2s40t7K3hlx8/nKWIPtTv+F1a+W/fSac6D+ExEf1rSNp6pnNNOm7SR6lfXF7p4aVXkugfvJK36g9v5Vh3ni21mmFlHv+2y5VbTaTKx/2QOW/4DXLW3xihuSEv9MtmQ9WhkIP61p/Cz4mfDfw/wDFiPxDrb34ENk6W0kcHmR28khCl3x8w+TcAQD945puFtyOc3vDPwLufGGNW8ZeJdU0S1Dn7PpzxqbyRexd2HyAnoGBbHJxmvavhd8PtB+Hs6z2mhLYoU23F7OfMlk44DOcnGewwPatvRpNP8X2h8TaBrWn6hYTP5itBLvxjBKnHRvY81q3Gqx+IYP7MtoZIZJcMHlxtGOe30p8kb3sPmbVrkXiRf7XMB0f/SBFu83yeMZxjPT0NXNCurPTtNjtdSljhuEJLpIMsMnI/Sq9nnwsGN5+/wDtONvk9tvrn61Fd6XceIJG1O1liiil4CyZ3DHHb6UxFe0tby11SK9uoJUs0kLtIxyoX1q54kli1eKCLSW+0SI5ZxFwQuMZPShtYi1O2OjwwSpLKvkiR8bQRxnjnHFJZWz+GJGurxlnSYeWoi6g9e/0oAwvEfhHQvE3g+Xw/wCKWks5/OM1rOrYnt2xgSI3PuMHgjIIr5/8beBPiz4Rt5G0/T7zxPpS58q908AyFOzNCTuHH93cK+nLu1l8SS/brJ0hRR5RWXOcjnPH1qVNYiFv/YhglMyr9mMnG3d93PrisqtCnV+JXNIVZQ+Fn536vr3iG1vGM2laxDITyktnKpH4FafbeI9b1qaHQ7bTLyPULtT5PmqY1x3ckjhBgkn2r9CrezufDpF9cyieL/V7Iyc5PTrx2r5W8W6pL4n+JXizxfcSSsBcyadYox/1VpbHZtX03yB2Pqa5cTTpUKfNbXp6nZhPaYiqoXsuvoZfgLS7XwXZstjEl/fSc3N/cqS0hx0UZ+RPQdfX0HpngXWRriXKXFtHFJAw5TO0g9Ov0rhfFWs+BfBfiTTPCXiqya/1qax+26rfyatLZwacDG0iQwCNW3yEAAFhhmIycHjrfhtatZwahIkhliluSkUjLtZ404DEdic8j1zXj4vDVaSVSrK7Z7mHxGGrN06EbJfj5nbrbgfcx+FMlgJ4LMfbdT45GEdQSTMHz6GuJvQ3UG2cvr3ibQILifSrhnuGHyTReTvT6HPBrxbx3pNj4X16HxxoUb6vo4ZTqmi3DsgQD7rccmLOMgcjpnB46C1fRbew1PxR401y40jSIL82qva2wnury5bLmONT8oCphmZuBkDvXS+IdAbQksblJn1LTdRhL20txaGCQjA3wzwt91wGGR0ZWyMV6NOlWw8VXtePX0OSUcLiZuje1RbP9CjcfFnVPEMNvf316IoVGYYIVEcUQxjCqPbjJyaUfEJb+WCLzCxSVXyT12nNcD4P+EX/AAlfxIuvB0HiubQ/PtDfaMHt/OikRSfMhPzAhkyMdcqCa63Uf2afiV4fuo1i8UeG7qOQHa7GeNsDHUbD/Ou/6q6i54yvc8Z1lTlyNWsddJq19fnejrsc8uzYrb8HXKTaoND0K4LajMm69vRyljAeHlPv/Co7sR2BrN8E/s8eM7yOG413xtp8FkesWnwu8jYOMB3wF+u017L4Q0XwxoehSeGvDGnSWj3TDzbmZt8k7j+OR/vMeDjsOgAFZ0ssfNeb0KqY1ctomzqUdrc6bZ6doI81bRQuyI4KoBgZzj0q5oVxa6fYi21N0guA5YrKMtg9DVO1hk8LyNc3e24WceWoi6gjnnNJPYz+IpjqVo8cMZHl7Jc7sr9PrXsbI84qQ2F+mr/bZIJPsQnMvmE/L5ec569MVzvx91i2bRdEuLO4WWODVY2l2fwgowH612ba3BNbnRVglExX7LvONu77ufXGa53xn4O+0eFb7T7+ePbdoI4ZIgSY5QQyOc9gV59iaY0cl8NA1rqereGpZ2aYu9xaMT1RznH4Hn8a3PE2hW/iTw+1wsa+YAUmjI5R+4NeXv4kl0G+025u08nW9Ik8q9jc48yIcbwe6kd69Kl1aC4lTxB4fv1a3vAGkRWB2N3DL6HqDRipOlarFXj1OinHn0PnHxHFYadd3GitY7Yh8kk2T5mfX3xXU/DDwVftbnUHiDwDP3R2zww9RTvjRJpdhqOl6lfvGst/qkcMgwBlZMhj9Bwfwr0nwZqQsPDi2KlYbi1fzLclch+zxtjsea3eIVKManSRKpNtpdDT0bSLK72NcWyNDZoZGJHoOmazfHkZ8Nad9r0i4aKS/dGBAGUQKT3+orpdc12zuPCVxLZgQ3U6mFou6kjk+4xnmvO/iJrP2zRIE2lRa2fl/MfvMF5P6CoxGPU5qMOtvzNIUXa7Ous9Z3eArbVSQLmaIogAxulyQSB+tcn8X9Tl0rwVp/huJj9sv1WE46hRgsfz/lVDwzqdrFBpcdybi5248u1t0MkkjdQiKO5OK0vFPgfxfr/iGPU7m80qzusBRYzK7fZs9F8xchjjGSAOc4z1rOm260nLRLRCm4xikQMlroPwpFtuVZb6YKi99i43N9OMV6H8C7IaDoE9/qw+yrqZSW381fvRqDgj65z+IrJ0T4SyaRdxa34y1CDV4rdhiytlZYic/LndywB5xwD3z0r0O6z4n2LZKLb7MPmEvfd0xj6VrVmpPQwlJPYp61bXuo6nLd6bDJPauAEeM4UkDB/Wtq/vLC50qS0tZYpLp49iIowxb0qpbanF4fgGmXUTzSxEsWjxtO7nv9aqxaPd6dMusSywvDC3nMi53EHtzxnmsiB/h9JNLupJdXU28bptjMvILZz79qg1+3utT1H7VpUT3Fv5YTdEcDcM5Hb1FXLyYeJ1S2tFMDQHzGaboR0wMUttqEfhyI6bdI08hPmboumD25+lICKyvpvEdx/Zt8qRw7TJmHhsj659adeyN4ZlFtp+10nHmMZuTnpxjFWvECWtpYCXSljiuN4G62xv29+nOOlReHDDd28z6xtllV8Ibn7wXHbPbNMB8OjWuoWo1ed5VuJV85ghAXcPbHTiqdjqVx4hnXTL1Y0hkBZjECGyvI5Oar3sl/Hq0sNrLcrZiUBFjz5ezjgY4xWxrkVjbac8ulpDHcgqFa3xvxnnGOelAFTUC3hcoun/ALxbjJfzucbemMY9a8/+PHixfDPw7/4SGEs2u6nN9ltIkZQqkAlpAD12opP1Ir0Lw60dzHcNrJ83y8FPtXYc5xu/CvDfiTo6/E+f7cLmfT7Kxnb+xYk2tHs6NIwUkESYBBGCBwa8vNM2w2W04zxErJuxlXU5U5Kn8VtD518yK9u5tTvb6RJrnEyXEpZ3kl3fMSSck+uc+xqhr+ny6tZ2FwqorMxWSYP8yuBjJ9sYPPrWv4y8N6r4d1uWy1q3W2hDtJbHO6OZCRllbuM9uCO4FZw8SQWSstkgn4+4q4A+p79/8njphVp14KdN8yeqfQ+ThHEYerz021I5LVLXUrGRDevLbnB2yABo3HrgevrUljG1zL5DyWU8rNhDGeG/OupvL2C+0fzbooTcShwvlgY2jBPPJ9PQ4qdtF0TULmDULDTZVkZNrRxlhzjAYbRx9BSqYW8dND2qHEtWkrV43OeudLg066EGrJFYSkbl85Dh19VIGCKwb1HlmMsULJE7MiSfdLoOhA+pP1r0eKzMEHkG7vHQf8s5JWYD8DTbm0trhg08EMhC7RlBwPSsaFGcHebv/X9dxY/inD1qShSg1rrt/X5Gn+zN4k1XwN48097eVxpmp3EdnqCbiEdH+UMynupIIPUYPY1903ul2+hW51SzaR5oSAqyHK88Hpj1r8971PImtlt2aKMfLhT90jkN68YNfbfwo8Tf8Jn4f0bWJbuS7sby23TCU5jEqgh1OeMhwf0rug+g8qxTrqV/U6bTyfFDONQPli2xs8njO7rnOfSo7nUrjQrh9LshG8EXzK0oJbnk5xjuan8RqlksH9jDyS5bzPso64xjO38ataIlhPpscmprA90xO4z43kZ4znnpVnrkU+kWum2batbtK08S+aqswKk+4x05qtY3D+J5TaX4WNIV8xTDwc5xznPrVHTri/m1SOC7kuXs2lKusmfLKZPXtitbX47eygifR1SGZnw5th8xXHfHbNAFe8uJfDcwsbHbJG480mYZOTx2xxxVtdJtjZHWN0n2lk+0kZG3djd09M0aALa5tGk1YRyT+YQDcY3bcDHXt1rKE17/AGu0Sy3P2Lz9gQZ8vy92Mem3FAEtvqkutboNSMcVtEhnZohhhsGe+eK+VfDktvq2kSToDAl48zp3KhpGYH3PP419b+JrOy/sp002OFJJD5bm3xuKMCGHHbFfHkAs9Bvbrw5b3PmPplxJbHcNp+VyOlebmUW4xsetlc4xctNf06nQ+PNK8NeJ5F17xB4f08axFHHE98lxIVkVeATGQBnHHJP44rsfC95YC1SAzpE6Do5xn3zXA2cP9rR3FqZmPmqSFznBCnp+VP0m8F3ZpIp5HyOPRhwQfxrxsTWqVfjex7uDoUoRvBbnsCyQuv7uWNx/ssDVHUnjhiZ3lRQPVhXmwYqeOPpSyzeXG0jvhVBJZj0HrXLa51KCjqjP8QeHNK8UaNqHhPWXmtLQ6gdUsL22Te8ErpsdWT+JGAXpyCo4IJxtWen6foHgPSvCOm313qaWdzNe3d/cxshlldAgRA3zbQAOT6e/HJ6XqM7XDalGhf7TKywoxwPLAA3ew71rzXzznbwo9q71iqzpey6HnywtGFb2reqdxvhCVrf4z+Bb6AFru2vp1IwSPJe3kD59uAa+q9PX/hJxI1/mP7PhU8njO7rnOfSvmX4K2L6r+0JpStFutrCzmuJsrlcGNkAPbkuK+mPEoewkgTSA0AYEyi2GMnjGcfjXs4Dm9jZnhZkoqtePVEd5qd1ok7aXZLE8EP3TIpLcjJzgjuasXWj22j2jaravK08OHVZCCpJOOcD3qzokdhNpsUupLbvdNnzGnxvPJxnPPTFYunTXs2pRRX0ty9o8mHWXPllecZzxjpXaeeXtOmPiZ2gvwEWAB18rgknjnOajvL6bw7cHTrJY3hAEmZRlsnr0xxxUviRIrWGF9HAhkZyJDa9SMd9vap9Ajs7mw8zVViluN5Ba4xv29uvOKYDf7EtI7U6yrym4CfaduRt3Y3Yxjpmsm+8Q2VxYXM/iW+tdN0yzj8+W4L+WFIIAyTnrnGOpOMUsd1f/ANri3aW4Nn9o2bDny/L3Yx6YxXzn+138SNO1KebwN4Zt7U2thcJJqNyiDMk8bZESn0U9T3bjoDlwlT54qbsm0vvKjCUr8q2Oa+P/AMTNN8YXEeh+GbBBoVtNufUbyIC4nOB93gFIueF6seSBwK4PQvEviHQA0ehanNaxAnEJAkQfgwOPoKwdRuUW28+KMTBclFI4yM4/8dYf98mqGn6mTeSxAeY6uGYs3HPXn6555r9Bp4fDUKaopXXmeTz1JS5rnQ+MNQ1rxjd28niTUo5JEBS3VYxEkeerYHU+/wCtej/Db4nxx2sOm+KZha3kQ8tbqX/V3AHAZmH3W9c8HrXmNmTK0cQMsshOFXBdiSegAyck9hnPvgmptc0zWdOjgl1PRNRsIbjPkSXlm8Ql29du4AHH40YvK8LiaapNJdi6WJq05cyPpptSSW1cwzKfMG6MA5B+nrXjPxh8aRX0M3hixLSTy/JdzA/LEg52DH8Rx+A+teejU9citmtLXWby2tX6xRSEKPp6fhVBQ0C7Qdw6/Nyc+uetebhuHYUavPPZHVVxspxsjV8Ha1qXg3xPpfijRLqRb2zmDJvmbaykANGwPVWBIP1r71+G+t+H/iR4Wi8X6dNOk0hIurYsA1tOv3o2HtwQe4II61+d9zI7GMxcyId4Q85xzj3zXqP7N/iTVvD/AMVNEsdNu5obPXb2OxvbcOdsiNuIOPVD0PoGHQ0s2wNOrTdSCs4/iYUaslKz6n2vZ6nPr1ymmXaxpDKCzGIEN8oyOuam1Ef8IyVOn4k+0A7/ADucbemMY9an12KxttOabS0gjugyhWt8b8E84xz0qt4dIumnXWT5u0L5X2rtnOcbvwr5A7iSy0y31+2XU71pEmlJVhEQF4OB1zVWPV7nULldHnSJYJW8pigIbA9OevFRa1Jd22oSxaXJPHbADYtvnYDjnGOOta99Bp0WlST2sdut4sYKNHjzA3tjnNAFTUIF8NIlzp5LtMfLYTcgDrxjFOsLCHxDCdRviyShvLxFwuB9c881B4fc3V1Kurs0sSpmMXX3Q2e27viodee4g1AxaU8sVvsB22xOzdznpxnpSAdo9lc6De/btSQRQbDHuQhjk4xwPoak1qCTxBcx3WmKJY4k2MXOwg5z3pRqbeJmGmeT9k/5a+Zu39O2OPWpPtB8LkWmz7X537zdnZjtjHNPQCe01eysLBNLuHdLmJPLZQhIDfUfWs7SdPutFvU1HUIljt4wQzKwYgkYHA96sf2F/aZ/tj7T5RmPm+Vszt9s59qQavJ4gP8AZJthbeb83mb92NvPTj0ouBxX7RN1c6v8PLxfD2oJa3kii2V5dyFg5G5FPUEoG+YdK+Z9E8S6p8PtZn0wXSSyW9skzWkCmSFlP9/OCp5B3DnketekeNfGkWp/EHVNB0ewvtYi0YiB5bcxpGHOd332GWJB6dgK4PV9C8KeJLC18Z2tvfLd6pILZIRM0Zupd3liJ0BOclcHGMgV8hmGOVbFSw9enzUnZWsndvbrpfW33ntLKKNbCqVTSW91o18/zTujsptd0H4w+FH0WGBheMQTaMf3ts4481Wxwo/vdMcEdq8m+J3wQ8T+BLA64l9beINNiUPdXtjE6PasW6yRtzs5A3jgdwK9z0exs/hZoHiGDRLaHVvF09kL680W1vI0+ywqAN80rlSkSs2cZBJbgY5HqnhzQpofDVkR4i1DVnuLNTPPeGOWK7WRASGjChShzwOuO5r1snyalldOVOk3yyd0m78vkjwqtKMrpu/nsfA2jyhgzTi3KuQQoQEjHYHtXu3ws1LV4/hTri6HeXlhPb6xZsLi3YEhXIUoFALcjLE9MAD2rzn44/Dm5+Hnio3Fvb/Z9FvpD9mRZC6xtySik87fQHJHTJ4Jp+D/ABtr3h6zu7TSLyOO3vChuIpIElRyudpwwPIya9Vp3Pmq1F4avzSelnsdx8cw1v8AFXXEljRHeZZDsOVOUXkHAzk55x1zXCSS45BqTXte1PX9SbUtWumurplVN5UKFVRhVVVACqBwABWZLNgcUKJ4tamqlaU47NtmlpFpqOraxb2OlyW6XcpIUzybUxjkZwf5V9X/ALPtwIfhk3gGR7J9a0+Vt4tvlSRXcyBzk5B+8CTjOB618q/DKzXVPiNpSySGNLWQ3OAPvFRwPYc5/Cu/+C/xA0fw98YL+6vlezv77XZIRHLEVM0MgEaITjIIYK2Dx+teTUxVSOP9nHWKSura6u33dT9DyHARWVSnb3m27+i/4e3qfWWhlvDplOrDyhcYEez587c56dOoqtqmnXOuX8uo6fEssEgCqzsFOQMHg1aLN4rIjK/Yja/N/f3bvyx0pRqLeHFOmiD7Vs+fzN2zOecY5r2RFu51K1uNNbSomY3bR+SqFSBuAxjPTtVDSIZtAunvNUQRRSJ5alDvO7Oe3sKd/ZMloDrxuA+wfafJ2YznnbnPv1oS9PilvsLRC08v97vzvz2xjj1ouBFrVrN4guxeabGJYUQRsXIUhhk4wfqK0bfU7O30tdKmdluUi8hkCkjdjGM9KgNyfDA+xCP7WJP3u7OzHbGOfSojor3mdb+1CPzP9I8rZnHfGc+3WgCHSbG60S7W/wBRjWG2RShZWDHJ4HAr55+N/wAH/Ees+O7zxZ8ObcapBqM4mvbdpRDJbTEfMw3kBkbGeDkEngjFfRg1Q+JR/ZnkfZQ/z+Zu34284xxTh/xSnyf8ff2nn+5t2/nnrUVKcaitI3oYidCXNA+I/BHijyNRheWUROH2sxPyqR0z+oNdvp+l2NjNeXNgZCt9N57oZd6BiOdvoPzr1L4r/AfR/iDZ3PiXw/cWvhrWbkMznyibec9CZQCME4zvUZ9Q1fGvhvULfwnrV/p+sadHqywTvEWtbwMm5WIJRxwynHBHUV5OIwMld3PZw2Mc21TXy7H0EYJc7thx9Ky/E2mXOr6atlb3v2MGVWmJQtvQfw/ng/hXEQeOPAgQTPomt2snbyrk9fwNc94t8d6hdOq+Gb3VrK32nf50odmPtnOK4o4WTemh2/WqkfsM77WtZt11lrWJFht7G1SBOec55J9zgVz1/wCLCkhS32ZAzlqxfg/4T8RfELXJ7C11nTbSQsGmlvbj94+TyUjHzSH6cD1FfXXhb4AeDfCOjQXmu2dn4qvbWYzGa7ttmWbA2hdxGwYBw27v6130sC7JJ6HBPFwg3Osm5Pp5GZ+yLcXlj4S1fX9djkhttXu0Ni5jP75I02swH93JwD3wcV7lo0n2m9vL+EM1tOEEbYwSVBB47VjwIviWNYEiTT47JQEVQGBBGAABjAG2pF1P/hHQdL8j7T5fzeZv253c9Oa9SnBQioroeNXq+1qOdrXMfVmTUvEUotl3mVgi7hjJAx3+ldV4mmjh0GSKXcGkUIoxkE9f6VlyaMdPX+2hceZ5P7/ytmM98Zz700XcniciyKCz8r97vzvz2xjj1q9jIk8DRuDc3AQ+WQEBGOo5/rWX4nmS78QSJGpJwsWGGPm6f1rTW6bwwPsJjF35h83fnZjPGMc+lD6OLkf24bnbu/0nytmf9rbnPt1oAwfjz4rl8DfBq+vIT5eoywpYWh/uzSDbu/4CAzf8BFfAd2jizc5ZmJySTknnkn1r6Y/bS1q61bw34ZhS3MMQv5pCBJu3ERADt/tNXzVdSeTbK1xhGYfKn8R/DtXkY+TdRJdD1sDFKDfc1vAXw58X+M9Bv9S8OQ2c0VvcpbNHPceUzMw3FlJGMKCM85+bjPNemfET9mpvAvwim8SWs9zea7p2241CZZR5LwkgSCOPGQEyGBJycHPoMz4AfE7T/Bkc2ka5BMmj3k4mFxCgd7d8BSxX+JSAMgcjHGelfXNj4n0vx5ov2GxFtd6ZqcbRGeOXzEdCPmBGOpGQQcEZr3sPmlWrGHNK7j9552Jw3s5t2smfD/7PV0w+NfhLyYWndb8BEjk2bjsYZLegH6D3rsPiVJrLfAnwxJq+o6nfzXniHULiZ72SVnVlLxqvzjhcLuUEg8txzmvOPEelax8JvixqGlWF3La6hod+XsbkAEmIjdE+DkHKMMg5HUVJ4g8b+JPE1pFZavqCSWsUrTpbw28cEQkYYLlY1ALYGMnJxxX3FGlKvXp1425dH59f8zy5NRi4mKRUMwzxUpOBmombkk1789jnRmXcyW9wjyMFGD1PX+v4CrGi6xdwa7aapazNBNaSCS3kXgxuCCG4+n5cV7l8D/h/a+Lfgn46F3aB7rWJBb6bM/HlyWoMilfrI+0+2RXz/aI0agPGyMOGUjlSOo/A1+b5/mtRudCnpG+r7ntZfh4ykpS3P0R+E/iGy13w3p3jCIRrbPGY7lUYFoZ8YaMqOeD09iD3rqdbz4j8o6Wvm+Rnfv8AkxnGOv0NfFH7PHxAbwbqdzbajcuNCvWT+0E27vKUHCzKPVO/qpI7CvtSC7h0C1hurOSPUre/RZI5Y2AUrjIYHkEENnNeFh6yqR80aYii6UrdC3pOpWuiWS6dqDNHcRkllVSwwTkcj2rMttLvbHUI9TuIVW1jk81mDAkL64HPerI0p/EedV88W3m/L5e3djbx1yKlGrnUh/Y/2fyvN/c+bvzjHfH4VuYDdalXxBFFb6YDLJC/mOHGzAxjvUmkXsGhWhsdSLRTlzJtQbhtPTkfQ1FLH/wixFyG+1m4/d7cbMd896b9gPiUnUvNFrj91s27845znj1oAsa1Y2+h2gvtNUwz7hHuZiwwevB+lR6HCniBJbjVCZpIW2IUO3Axnt71T0CK5tNR8zVkkjtjGRuuM7N3GOvGetWPEGbq5ibSA0saphzbdAc98d8UAVrnVr2x1OTS7eZEtopBGilQSF47nnvTfiO9n4S8I3mr2AeG8AEFu+4th3+XOD6Ak/hW5YNp8elJHcm3W7EZDiTHmBueuec187/tFX/i1JdF8O6MIVuzHJf3C35bayKwjRB7sSxzx92uXG1HTw85RaTtu9jowtNVK0Ys8DM3jn4dahcw24iv4dRmMsVyYDIJJe7ADkP6qc+1d58HPD2u6xN4N0rVLjUtCS31G9vpjF+5mkTghUPVNxkYZGCBnGOKydF+I0+peELi8ghbTryzvLeG8kWH7QkMTMd8oU9gAevT1rp/AvjmC+u7LW5r2xDaVqkltNMo8tJoWUgSAMcruGDj/ZNfM0K1dVoSrUkmpJSa3vayfbr3PpsVCM8PJQfTT9T6Jm+HHw8u9Lu9Pn8G6I0F6CLoi2AlmJOSXlHzscgHJbOQD1rj9J1vU/hdrGo+FL/RtR1HwFpGlDUbTWwd76dbfMDby5x5u1lYLt+fbtyCBkd5aatE9qJi4Ee3eWJwAMZyT0x715jZw6B8S/ihdeMLfVGv9C8PWo0ZIoZD9nv7hiZZS+DtlhQOi7TlWbOcgc/Y3PkTnPjp4v8AA/xP8BJonhq9fVtS1Bmk0wfZJoVV4VMsjeZIgUEIr4AJycDvmvmPS4zFEqs2fevtH4u3Wm3fgbV9Pv8AYLVrKUBRhRHhDgrj7pHbFfGemCWaJJpBh3AZgOxPJpHjZw7QizQRDtyDUTjk1dVAsWTWdeSBUY9CM/jTPm6bcnY6L4aXM1nrd7eQqqy+T5EMjwSOoc88leg6Z/nWzf6alxcQ674wshFfacVuH1K2ZY43ZZVCJhSSw5GCQCMYr3rwZ8K/D/h/4e21jeNLPqFxGJ7m5jfawlcAkL22joAc9K8Q8b6Jd3fiWLwOtw81zeX1ukCxg/vlEqE8f7rZx6r7V8ti8NiI41VLWUmldbpfhb8UfrGU1KNPAqi94q7XS59n+IHbQzDcaafKe6J80t82cAEdenU1Jotlb67ZfbtRVpZ2coWRiowOBwKTQ2WK4uG1ZfKjbHk/aRweucZ/CqevW9xdag8ulpLJb7QA1vnZnHPTjNfUHiBb6lc3V+NIllQ2rSGAoFAOwHGM9egq5rdrFoFul3pmYZnfy2ZjuG3BOOfcCp7uWx/sRoIWg+3GAKqqB5m/HQd85qh4b823u3fV0kihMZCm5ztLZHTPfGaALGhRJr8ElxqeZpI38tSp2gDGe31qpNqtzbX76VFKgtkk8gIVBIXOMZ61J4iie8u0fSA0kSx4Y2x+UNk9cd8Yq9aPYRaLHDdNbreCHayvjzN+PfnOaAItZ0+20KwN9poaKdWCBmYsADweDUPh8HxB5zaq3n+RtEZX5cZznp9BWRp+rWmk34HiC9SBRGSYbiTLk44+TJJP4VieMfHtrjdo8Bto4lJMkg8sue2FH9fyrlr42hQ+OWvbqdNDCVq7tCJ5J+158TI4ra7+GfhrUXFvCR/arwP0zjFsWHJyxy49AFPUivmi20rTnmisp5J4JnukCoq8BGHXPb6U74hLJY+I9VlaVnWa7eYOzcvli2SfXJrvND8O2Fx4FvfEuoNepqijcoDqsanzo4ljZCu/cQXbOQBtHrXFWqTqR509D7bK8LhqbWHfxNpXtvdv/gD7f4aaWultfTX0jAKSFB4NcRq/h5oJZLnTpEnsgBiQOAMnsD36V18Gr30WjNpabPJ5Cvg7lU9QO341kThUjwUBHcYrzKdSrF3k7n2scghJNPTsY2loIY40i8y3lEgdLiJiJFcdwcjHOORzX2f+zb48v/HHh+Tw74g1L+0b/TJPJuZeA88RUtFISOc/KVJ7leeTXxzJOn7uySONTNOoDkfdGeSa7/4Da5qXhn4mabBpsF1dprBFlfwwpuYKz5R1x3Rhk46qW9a9LDV0qi6Jnyue5W6mElZXlC2q7dV+p9q65jw6Ijph8nz8+Zv+bOMY6/U1JpOn2uu2S6hqAaWd2KsyMVBAOBwKh8No1u9x/bQ2BtvlfaeQeudu78Kg1uC5n1F5NMime2IG1rfOzOOcY4617B+aken6neXl8mmXMyvbSP5LJtAJXpjI57Vpa1BFoEKXenDyZHby2LncCMZxz7ipNTuNPl0aWG0kt3vGi2osePML+gxzms3w1HNBdyNq6PHAY8Ibn7u7I6Z74zQBa0e3h8RQSXeo7pZY38tSjbRtAB7fU1QfUb2HUm0hJ1FokvkBCoJ2ZxjPXOO9WfEEMtxeK2ko7wiMBjbfd3ZPXHfGKvi505NG8h3txfCDaVOPM8zbjHruzQB5h+1d4Hs734Nahf6bG0d7o0iX8RySSi8SqM+sZY/UCviG/MctxPfSuGgDYjVWyX9B7cV+iOj2c73Pk61bzGylieOUXIJRtwxg545ya/Prxdo9loOqXejWF1HeW9rfXMUU0bblkVZCqsD34ArgxkVdS67HoYKb1iZVsHursPL91fmCjoK6/wCHnxF8R+APEX23w5dAAYM1rKN0M+P7y+vPDDkVgeS2n2HmTLtkcZx39qyrInz5JDzhSSa4oSd+ZdD0JpNcrPW/2h9ZsPiBp/h74n6cRHNNu0jVrYgB7eZQZIg2OoKl8N3AHoQPK4GwRUdlqb2+lahpzyfuNQiQ7SMjzoZQ8Z+uDIufRzUkC8DNfp3DdeVXCq/R2Pl8dTVOpZFlmBWqV7N5ULyHooyasuOKZZ2Y1DUrLTmIC3d1DASfR5FU/wA6+gxFVqDfY4oK7PvT9nPwta2vwh0LTb2FvOtrdZH2NtPmS/vnzjqcv+lfIn7Qvhu28M/GDxTplogS2+1i5hUdFWZFkx+DFq+59etS9xENFjdoYovLYWvQEdAdvfGK+Jf2p7t3+OGtxOGDQQWcT7uu4W6k5/76r8mxzdSLk973Pewb5Z/I880CRjqEadnDIffivp79jfxlFrBuvhn4jnklk04PcaMxcj9yT+8hz325DAehOOlfMvhOAy6lG/ZFLn8qtaHrt94c8cReINJYi7srgTR4OA208qfZhlT9a86jV9nVaWx6Vel7SnqfodquozaFdvp9jKsUEYDKrgMQSMnk89a0NQ060sNMk1O2R0uY0EquWJAY45weO9UfAGt6JrvhHTdaM1s8V/CLmEzYLGN+V6+nT8Kh061vINSjmvI5xaLISzSZ8sLzyc8Yr2DxCfRWfxBO8GqP50cS70CfKQc47e1Jq91LoF2LHTpBFAyCTa4DHccjOT9BVnxLLDc28KaQyyyq+XFt94Ljvjtml8PSW1vYtHqxijuPMJC3ON+3Ax97nHWkAl9qEPiOH+zrJHjlz5mZgAuB16Z55pmmyDwyr218DI07eYph5AHTnOKdcacnhtf7StpWnfPl7JMAYPfj6U20i/4SgNc3Lm2aA+WBFyCOvemBBLo9zqFy+rwvEsEzecquTuAHY8deK+Wv2xfHWo6d8UtPuNLtwsdzoKJG8y8xus8vzDBwcZ6H2r6nk1m406ZtHjhjkiibyhI5O4g9+OO9eE/te+DNLt5/DWpXVoL2JlntC0q/cOVdRkY6/P8AlXLjXBUJOpHmXY68Df28eV2Z4l8BrPULZdQ1O7+W21BVCBvvSMGJL4/unJHv9K6fxdY+GhZwaAn2TT3Ei3UKm3zAXJZAJMY4YsR1B9D2rE8NeLNM1C7ks7JzG0CjapXaGUcfKPQVualpGla7Pb3N/bebLbsGR1cqeCDg46jIBwa+CxNepHHOrXvFdl5bb7n2VKEXQ5YWZd0i00ZdP0W2umvtInsJI5VhttRma0kZGDbTE7FWQ45GAcGtHw34/XwdcatomtnSoFvryTULKXS7PyLVoyqq6lR9xwUBJYnO7qafJptrdR2k2s6St1ZSyebFHcK6R3ABwdrDBPcZU8V618Ovh18MdWlj1HTPB9hayrHuWaVpLl0IPK/vWYDB9B2FfV5Lm312Lp1Faa/Fdz5XMsD9XlzQ1i/z7HhfxP8AEN3qngKXV72C4s9Jv5Da6d5yFH1CTG5mVTyIUT5i5xuJVVzkkeVaYF8tccrX17+1Bpvhm08BNp+raJaa3f3Egg0c3IPmRXU2EBQqQQAF3Ht8ozXyjcaTNo+oXOnXhTzrWQxSeW+5dw4OCK9tp9D5XNp4aMUq0G/SSX5xZHc/OMIcADpWPqAyoQ5+ZgoP1OKsarciGJmLkKPequiypc6rp4m3TQm8h3op5ZfMXIGKLtLU83D4bC6ShOVuzivz5v67H2rJez2mkR3N5r7XsCKEaIWiRucAfxZx+lct8KvDya38Xrj4kXlr/wAS3w9B9ntweS1zKCCR2OyNh+Lj0qxB4Z13xLcppOn22twwGU+dLcWoiigAODulbG/2VVLe4616Z4NtbWy0S08H2VstvachpgxaV2zuZ2J6sSOaXLezPqoycdjc1I/8JOIk08eUbYln87jO7gYxn0p1jqcXh2D+zLyOSWVCXJiAK4bkdcUlyp8Kqj2zfaTcnaRLxjbzxj60630yPxFEdSuJXgkc7CseCMDjvVCI00qe3uV1t2jMCt9oKgndt649M81Jqk6+JI0srFWjkibzWMvAI6ds+tQx6tcXEw0RoolhZvsxkGd20cZ9M8VNcWo8NAXtvI1w8p8orJgADrnj6UANsLkeGY3tLyNpZJW80GHBAGMd8eleF/HH4k6jH4muvDXhlmtJ2VJbq8x+8j3gMqJ6HBBLe+B617tbWo8Sq15cO1u0R8oLFyCOuefrXyR+03F/YHjvxHMobMotkjfpkeUFJ/8AHCPxrz8ynUjRtTdm2l959JwtSw88fzYmPNGKcrPbQ851ibQ7C8Y6rJcCd2LNK43lz6lsk8+9dL4CuvEOrO0HhrQvEWsWG0lvLt2eNfQgnoc+h/Ctj9mvw5NcaxHr+qeBY/F0txGps7L7VCpskYttuZI5DtCMFO1m56BQckj3TxL4k8T/ANs6L4QvdIbwFb6rrEdjbG3iW7a9tthaTZcoRHavgMoGC/OVx1HNSyeMo3qybZ7OacaVKjlRoU48nTT+vkUvhF8ItOhg/wCEsnk0rVNUuVyWJ81LQd40BGA3HzMRk9BgV5X+0hLc2HxC1KCwk8vStfSHUHieJd3mA7XAbqBvjD4B6mvphfh94a8OxW1x4WsxoN1aQeTBLbSPt8vJby5ELESJuJJB5ySQQea+d/2iZLfUY/CeoqQl4VvbK9gDBhBNE8e9Ae4yxIz2Irpx0FSwrUeh5XC2Ics2g6mvNf8AzX3NHk0acVXvIiVPFay2+F96ZLb5U18osU7n7eprqaXgH4b3Xi/wJq+uadJs1TTdRHkqyk+dFHAzvEvozMyYPtjvXpPwx0Gy0zQotRsAYtTjKTxzcZVhyP8A9Vdz+zFosVr8EpddnkkTzby9uwqgcqh2D/0XXI+G5pLO2jju5ba0Jj+dJrmNGBPbBbNehmrVKnSa0bR+TLGzxGKxNKcvc5nZfh+h7tZX58baRa3FoqwzwLi4SQ8BzwQMZ4yPyIrQsdTi0CAaZeRySTISxMQBXDcjrivMvhj4jn0fVLi0hihmhvgGWTduTeoPAKnHIz+VenQaXHr8Y1OeZ4ZJPlKxgYG3jvXv4DFLFUFU69fU+LxtBUK0oRenQqW2iXGn3C6vK8LQxN5zKpO7HX8+at6hdR+Iols7FSkkZ8wmbgY6ds+tVk1ue+lXR5IY0jlbyC6k7gOmfTPFS3FoPDQF7bSG4aU+UVlGAB1zx9K7DlCyvl8No1hexvLK580GHBAB47454qs2i3M9ydaR4hA7/aQhJ3Bc7semat2liviMHULlzBIh8oLHgjA5zz9ail1ie2nOiiKIwq32cSHO7H3c+maAJNY1BPEGmT6bpyyR3MsbNG0mAAQD6HrX5uWDSvLFA8BjntndJHccowbDAD1yPwr7Z/aI074maL4csR8Kre6ubueZlvrqKSFZLeILwqByOXPGRkjb718OQapdEXG6JmvHkcyFz8/mEncWB75znPeuLGxbirI7cG0m7kvifUPNuvs6kFYhhj71nl/IsCM4efnHotNnt/saCe9YMzcpEDlmPvUERad2up2wi8t/RRXNTpqMUlsdsql2Nn+a7s4BwR8xroIYuK5ryZ57mO6mjZIpVZ4if4gGK5HtkEfgamk+0IcR3cy+mHNfovDj+rYS8o3u7nz2OaqVXZnROgHFN0+c2ms2FxHE00kN3DIsaAlnKyKcADkk4rnF+0OcSXczD0LGuj+HE76d8QfD17BI0csWowlZA2CpLAZz+NexicUp05Wj0OSMLPc/SKxu4/DgkgvEeRrhvOTyxnC9MHOOa+Tf20PB9hY+IbTx9Bfsj+JZvLNg0WTmKMBpd2eOAgK4PPOa+hdP8T2Or3djbeIbl7SZ0EMVwoGx39Hz90nsen0r5y/bT1GW9+Jmh+EI33waLZEA9y87ZJPvtRfzr8zruKg0+h7WGT9ojyjRYzYaYs+P3t3Iqr6hf/1ZNVNK09ibiaf/AF2CdvpnJ5960dVlZLizhtwC0Y+Rcd+g/SleWO1mitWkzPLkt7mvnnOVnbdnt2R9H/sc3M/iDwVqfhtZolfQboeSHJ4gn3Oo+gcSfnXvt1rNvqVq+kQRTLNMPJVnA25Hrz04r5M/Yv1e60X4geLYY0WQTaZDIQxOMpMVH6Oa+s30aHToTq8c0kkkQ84IwG0n0/WvoaD5qaZ4VdWqMr6fA3hmZrq+2yJMvlqITkg9ec4ovrCbxFP/AGjZMscYURYlODkc9s+tSQSN4mf7NchbdYB5imLkk9O9R3WoTeG5f7OtUSdCvm7peDk8Y4+laGJHoFxPqWoG21OR54PLLbJRgbhjH86k8QyHSLmKLS2NtFIm51i5BbOM9+1WPEuoWeqaS8VnOsjRsJX3AqAo6nJ+orK8Na/FpUDxy2k0iSPuLIRkDGOhqgN/TrSwudLjvbmKKS6dN7SP94t615r8RtH1Hx34PvdA+0u16U+0WDycKtxGMqCcdGG5P+Be1dQ8J1rUrnUNM8u5txP87K4yhGCQwPIOOxrf1vULPV9Oew0+UT3EhBRApGcHJ5PHQVM4qcXF7FRk4yUl0Pzu0C0lg1BHuppC9qJYUhkjCNCS+XU+4ORz05r2bwD4U1nWTG8sZsbRuTLKMMR/sr1P1OBXpPxE+E6y3r+JtLgsdN8QsQwWcfurwjrkrnZJ0+bHPf1rH0HVdX06a3s9f02/068lztE8BMbY67JRlHH0OfavEq5LCvU56zuu2x6/9ryhT5aUbPuel+HNNhi03SfDF5i+0632xhJ0VgVGcHpweeorp9VtNP0LTYv7ESGx+fafJOPlwSc+3Gc1yOn6yvlpCW/eT/usZwCCPmz7AAn8K8h+K3xE0u/trnwxo13eHTLwNBd6lajEN2qMN8Ebg5ZCflZlGDyoOM16k508PDmttppueWr1G+aVlu29EvNmF8dvElx4z1/TFiup2060kjWDU0kwkDykiORu5DsMAjBA5zzz5PrUV5pEzW+sBYZ2kYDfMpaQgnLYznnrk10NsPDVzrl9ea0t/YjSZLMCKO+823nbBMKbEXlxgDYMkdOxq1q+g+G7LTdT+LGvQS3FpqVyY9I0i8txG2o3acbzn5xbxkbm6byNvTr5WCxGIlXcHe27utL6aXvbb9Op6WZ5fgMRhouok7bNOz/4PzueaXVs2qaglrFLbiNVMkoeYKQACfu/ePAPABNegfBL4d6t4n+IOk2sFtFZxWVxDf3QuyBm3SRGJ2jJ+bgDOMk+xrzew0648ix1iTUbSO3ec3rSvExulaNsOPlBIXv2AJFfZfwD+Hl7pHhKTWJVF7retP8Aab6TaEeOI5aCNvVgrFj6E4/hFejCc6lSyei8jz/qGEw9BL2d30bf46afgem6pqN5Z6pPa2lzNFAj/IqcqAeePxJrc1e0sbLTJbuyiiiuYwCjx/eBJAOKTStRstO0uKwvZhDcxKVdNpOCTnqOO4rE0rTL3TNTh1C9tzDbRMS8m4HAIx0HPUiuwwLfh0nVZp11djcLGoMYm42kk5x0qDXLqbTdQe106aS3twoZUi5XJHNXPEbLr0cMel4umhJaQD5doI4649DU+hXlto9gLLUZPs86sXKYJ4PTkZFAElza2UejNexRxi8EHmCQff34zn65rO8PTPqN48GrSNcQrHvVZuAGyB+eCahtNOu7fVF1OW322izGYyZBwmc5x16VoeIZYddtY7XTW+0ypJ5jLjbhcEZ5+opgVdfll0u8SLSXMEDR7mWLkFskZ784xXzt+2h4SmvdF0XxbDKRJcWxs7pSesgzJGxHqR5g/AV9J6DcQaHbSWmpN9mld/MVcZyuMZ4z3Fc3418IW/i+zvbXU9N+26ReSCUkSbGCg5DqQQykdjWVaHtIWW52YDFLC11UautU15NWZxP7Meu6XdeE55bK1WCSOSG3dsDMiRW8SI30yJB9Q3vXUftB61bW/wAK76dtattHukurNrHUJ1LLbXAuYzG5CqxwMHOATjPbNeaeKPhzB8P2GsfCeTUEi+zlLiOENdTJgli7xvnzkJJJH3lJOCAa5Xwv8QZtR8V/afF2qG5l061ifT7e5SGKBZzuWa4hReSwwAN+WQMQOua1WiOSTTbaPYZ/i3cJoV1Jr3g7xR5tpKYPtlhppezvQDtE8RZgyRN975x8oPU182eKNbvNZ8Ss99Lbzqnm3R+xHzIVeeQk7W/iGxIue+M969mt9Z8Q+Ob06b4WtjdvJ8sty2TbwA9Wkfp0/hHJ6AV5Rc+ENS0uS+Npol61pHM0KTqm9ZghKCTjoCAMLgYGBXkZ1U5cNbufV8GUYTzJTqSSUU3r32MN9QsE4eVk/wB5CKgm1HTyhZZgcckgGt2L4Xa9rXw713x1NPLp9pp8TmytjalnvnTG7GSNqDkZAOSrelcIsTW+nyeedjiJiwPGODXz8svVOMZSv7x+k0M5jiqtSnSaaho3/TPo3xFeX2g/spWOmM80H2u0t4ggPGZ5fNPI9VJP414JZ2uYGZos8dcV9F/Gu5hj+DfgPw0/zyCK2eYYwFMVsMc/9tB+VfOnjjxdZ+G7mHTLe2F07LumIcAx56D6969LHVJyxUaFJXaSPG4WxFHB5bUxmIlyqc27/h+dyG1v9R0XUob3TLuaymSRWDxNjoe46Eexr7X0HxBe33hvSNQspGtorywhuCsS4UO6AtjrxnNfF1wIrzRzeEBC0ZOwsCVODjOK+9fCF5Y6L4a0/S7xltpoLaMGIIcKNgx0GK6cnqOfPfoeX4gKk3RnFau+vloW7yz0+DSnvLeKFbtIt6yKfmDY6/Ws7w/O+p3skGqObiJI9yrLwA2QM9ucE1VsdLvbPUo9RuLfZaxymVpMg4Xk5wOe9amvzQ65bR22mt9pljfzGUDGFxjPOPWvbPzcp+I7mXTL1INMka3haMMVi5BbJ5+uAK0raysZ9HS+lhja7MHmGQn59+M5+uar+HpotDtpLXVG+zyvJ5iqRuyuAM8Z7g1RuNPu5tVbU47ctaNN5wkyPuZznHXpQAuiXc+o6hHa6lK81uVLFZeFJA4r5u/a4+Ct3Drs/jn4f2Yu5L0GXUtMhTc/mDAM0QH3s9WXrn5hnJx9ReILy31rTzZabILicurBMEcDryeKi8NldCjmi1QC1aZg0YPO4Ac9M+tJxUlZlRk4u6PyvlmMd251AyrOpw6SAqwPoQea7f4ffDjxd8SL2K30qwk0/SFy0+pXUbJbQoASzZ/jbAOFXJPt1r9ANf8ADkWt6zJqy6PaXyMQYZ5beNiABjgsMjkVX+KXjHTINAOhWDpLdXcexwq4EMfc47Z6AfjXFjK9HBUZV6m0V/SOrDxq4maow3Z8JeNbTUFtbK2Hh6SCytlAs7pY9zPbBAI1YgcHguQT95z+PIWlr9s1EQyu0cCKZJmX7wUdh7k8V9UeLEuLjTTYaTam5vJlKwQpgMxCk4H4A/lXAfs9fDzVfG/jGG5axmk0fTitxdl+Fc9Ui57k8kegPrWvD3FmIzDBNSpKNtE0/wBP+CPMcrhhK1ua549rFhb21/bHTo5mhlhDNkl8Nkjr+VW7Ky1S3ube/i068YwSpKpWBv4WB9Paux13w/qXhTx/P4Vv0kRre+2KD0kQtlXHqCP6+le1pbW0mi+VgJ8uCT/OpzLjWeUKGHlS5+bq2aYPJ/rilOMrW8jSvNL1LxD4ch1TQma5V3dZ7I8GOVcAlCeCGBB2nGCSBXgHxBn1y7+MmoXHiGCaG9SGEFZUKttWBEQnPqB19c19r/BnTpvBfhu6sPERjtbm4vHmjRW3ho9qqGyM9cV87/tkaHeWXxG0vx4kLf2Rq8H2Frj+FZI8lM+m5ScZ67DSxFL9zJR7EYeqlVSZ5BqE8Fsj3sgUFFxnufauXF7NLqK3UwKksrr9M1X8VambufyY2/cp0x3960GiW48PQXQGChAz7Ecj8686nS9nBOXU7/ac02l0Pob9im2gufi/4oFwivCNFQEN0yZ1I/lX0rZ3l3catHaXNxK9o8pR42+6V54+lfNv7GmhX2pTeMNWghMny2dmDkDkB5G6/VK+qr7UrO90uTTbeXzLqSPy1j2kZbjjJ47V6+HVqUV5Hk4l3qsreJPJ0qCGXSttvI77XaLkkYzg9e9TaBDa6lYm61NY57jeVDy8HaAMD9TVTw9A2h3Ek+px/ZklTYjHByc5xxmotetJ9a1AXmnQm5gEYj3jAwRnI557itjAxPH2nSeHdEjvWuxJE9ykUgVSODkjv6gVhvq0Ztfk6kV108R8bWV1oGsPttpYS4aBdro4I2sD6gnP4V83+Ota1X4a63Jo/jCbyNg3W9yqnZdx9nQdSfVeqnr2JYHMeNfjF4i8H/GtpPCiBfsiLY38FxnytQ53bWAPG3dhXHIyexxXvPhf4ueDLC3h1TXrxtFuoUHn206M8as3y/LMoIIBPUgV8RfEDxDB4h8dX+vWAljjnkR0LqA2VRV3Y5xkrmvQzJc+JPhyIhOpvby0UliANzg5I9s4x+NePjsbVw04NW5W7M97C5fRxFNp3Ukrn1l4g+MXws1S1ink8faDbLDk8TmVmz6Koz29K4jXf2rfhn4f0ttM0eDUPFUvzL+6gNvA+eoJlGcfRTXyRY6Np+raZuR1tL23AjmRnVCWH8QzjOcfnXPQW0d1A/mgb0baHXgmu2OLjK+mxzSy1pqz3PX/ABH8Q/EPj25u7Nx/wiugTI8bpaySSbQRny3kI3EN0wMA8A8VyGgWEthEii5mlKcIzk/KueAB/CPYVk+FkvFSWOW6la33AKpbg49a6yFSIs47VrRpzu5zd77Hx3EWYRv9VpKyW/m+3ojf8KabceNvEuleFJJyiT3ImkuA5T7MiKTJNkdGVAcH6VzHxf8AE0vj3xtLdWLvHoenKLHRrYH5YbWPhSP9psbie5I9BXSeBrz+ytD+IGvK+yW28NSWds2efOupViAHvt3nj0JrhNCtvIs40YchQKpRir8pzUqssNgo67/1obHhu2n1jVtJ8OTKsovrmGy3NnIWSRQRx1HOcH0r9CVli8Kf6OIvPjmA8sJ8uxUG0D8sV8DeEJJbPxnoV9bRq0ttqNvON3QBZFJJ9AB1J4FffOkxw+J43ub1mIiO2Py/k4PJz78VKlTjU9nf3nrby7nflE3Upyk+5FJokutsdWjuUgW4+YRsu4rjjr+FTyawusj+yEt2hab5RIzAgY56fhVG91i90e7k0y0aL7PA21N65bB55OfetHUNJttHs31WzMv2iHBXzG3LycHI/Gtj1ivGh8KsZpT9rFz8oCfLtxz3+tDadJ4ic6nFKtsrfJsddx+X3FLpBfxG0iamQRAA0flfLyeuevpUOp39xoN02n2BQQqoceYu45PXmkBaOsLdxHRVgZXcfZvNLAgHpnH4UyO0bwwxv5XF0JB5WxBtIzznn6VJPpNta6e2sxGX7Ukf2gZbKbyM9PTJqvpN1L4jnaz1EqYkXzF8obTnOOv4mgBzWx8Tv9uicWqxDytrjcSeucj61JHrSWi/2K1u7vEPIMoYAE9M4/GotUnk8OzraacVEUi+Y3mjcc5x/SrMGj2t1ZDWJWl+0yJ57bWwu7GenpxQBXj0t/DrDU5ZxcpH8mxV2n5uOtZ2oeHvD/je7N1c6BpHnW5+aS6so5nYt/tEZ7Va0vUrnX7ldOvinkSKXby12tkcjmrOqq3h0xpphwbjO/zvm6dMdPWmBx/xQ+Iml/CLwhDZzWweWSX7NarbqEClgWL7B/CgOTjrwO9eV3vjrwrP4biTS9bs3KpllMm1s47q2DmsP4reIJvF3ja7u7hkmtbbNtbgL8pVeGbHuwP4AV53rvh7SpoHeSyiHH8OV/lXx+YZnRxFb2bvZPSx+n5TwtUo4NVm1zSV2n08j6D8XeLNHT4beEPBNthLjVLWOVCrgiSNEDuRj+8zcevNc5qen6ZLbxrf2VrN+8jXfLGpIy6jqeleMzXj+ND9svlMC2kUVnYCI4NtFAgRAp/AsfUsaqzw66s9tZ3PifULq0NzEDC7Z3DzFwCSelXiatOviYrmty2VjDDZNXwmBdS1+ZNvXY+5td8I2fiywdr+O3ksZv3iwSIcpjj5SCNp9xXw1+0X4ItdD+LF7BpGjXdlpUtrDJYAtJObhvLHmEOclm3hsjtjpivuu+1u9s9Ql0638oQRSeWNyZOPrn3q9qOkWmjWj6la+YZ4fuea25eflPGPQmvqZU4vVb9z4LDYuVFpPWK6N6X7nwx+z1pLeNPEcFrdxtJp1tPHdXrLjHkp0TPq7fKPbPpX3A2ktrsh1SGdYEk+URsu4jbx1FZvg3QdDuYruK00fTtLTeruum2yW4kY55baOT/iat6jqV1oVy2m2BjEEQDL5q7myeTzWdDDwo35epvmWZ1cfKMqn2VZfqWW1xL9f7GW2dGl/cCUsCAemcfhTUtm8MSfbZXF0so8oKg2kd88/SrM+kWdnYtqsHmfaY085dzZXdjPT05qppk0niOV7TUGUxxL5i+UNpznHv61ueaSSWzeJm+2xOLZY/3RRxuJI5zkfWg6utvH/YRt3Z1H2bzQwAz93dj8arapdT+HLsWOmlRE6CU+aNx3HjrxxwKvw6XbXOnLrEhl+1NH9oJDYXfjPT0zQBVj06Tw0RqU0y3KL+72Iu0/NxnJp0qHxURLCfsn2b5SHG7du57fSodOvrjxDONO1AoYGBc+UNpyOnNS6p5nhuSOLSzxcAs/mjecjgY6etMDG8eeO7f4c+Ebt7m3+1TWi+XB821ZpX5Rcdcc8+wNfGlj4w8Sabd3d8xTWDdztcTpO2xw7HLFW9PQduK9J/ad8Vt4h1eysrANc21gjzX8sf3DcZKbQD/dReoyMsa5j4N+Bj441qVblpI9NsSv2pUOJJGOcRjuvQknsBxyePq8Pk+WVcqm8wgpJ6u+67W7NkVJ4/BV4ygnB9Lq1/v3R0X7Pfia78YfFyKCXTRpsFnp9xNLNO+9Ub5VUKRgBvmPXtmvoXw34p8F+HY59G0m70bK3TGVbeaOH985JIZTg7zg1yGreLPCHgVLLwzoenpdajNNHbrZ6bbmSGzLMF826aMHy0GcnJ3kA4HeofgFLouqWviyKXVtG8QeJoNalOtX9lblVmLgeUF3jcY0VSg6gFDgnqfkKWFwuGXs8LDlh0V7nRVr1cRLnqu8jB/aph8N6LH4c1nVrfzdQu7x5LaaIHfbxBd77sffXLKMdicjuD5w/jrwvPZmKPW7RQVwQWIP5Yr1v4/fDp/FOlQ6nYyzDUtLgcW0JcmOWMnc0eOgJxkEd+Dx0+UJxYjP7uPd3+UZrtfBOB4hpxrSrOM46NaW30N8Jn9fLeanCCkmfcvwvvf+Fi+ANF8Qxy+SFtzbEsu7zTGxQuPQNtzg+tbuqXOlyae/hjV9Gt9Ut0xE6XEaPE57EowI4zXlX7L+t31n8HLCO3ZFT7deLiRM4AkGMeg5r2S00e0v7JdVuWlNxKvmsVbC7h7fhWdegsPUlRTuou1+9jjUnL3mrXPjn9qv9n/TfAekt410PU5fsl3qccL6aLceXbGXeSyvnITcAApHG7GeleNo62/huSIdFYfqa+9PiPpN18TvBGqeDLma3ikvYC9rLswIp4yJI2P+zuUA+xNfB2paXq2kXWqeH9esJbDUrKTZPbyD5kYH9QRyGHBHIry8bC9n0O/Bz3XU+v8A9jy7g8P/AAeS8azaSXVdQnumcEAlUIhUe/ER/OvXxoj6dKNZa4WRYT5xjC4Jz2z+NcR+zDoum6n8AvCU7+ZuFrJG3lvgZE8mfxzmuvttXvL+9TSZzH9nlfym2rhtv1/Cu2CSikcdT42WprgeJ8WkKm1MH7ws/wA2e2OKWLUB4bH9nSxG5Zv3u9DtHPGMH6Uarbr4ciS604sJJm8t/NO4Y6/zp+l2UPiC2OoagX84MYh5R2jA5HH4mmQS+IjbDTwdJ8r7TvH/AB6437ec/d5x0rn9S8LeH/Gvhe60Lx3p8N7bSSbo1vCVkjO3G+Njhkb3U1qaXZT+H7r7fqIVYCpjzG245OMcfhTtWjbxFMk+mgOkI2MZDtOev8qAPlrxb+yc1nqlxc+C9Vjv7PdmK21eN8Y9pohg/iv41i3Hwo+K2mtHb2fhO1vkVcKdP1S3dR9FLBsfhX2Ra6ta6fZJpdx5guIl8tgq5XP1/GqGm6XdaHdR6jfBBBECG8ttzcjA4+prmxGDpYj41c66GOrUFaDPiTUP2ffinrWozXf/AAjcGlGQ7it9ewxqWPUg7jnnngVv6F+zB4mtLJ5/FPiTR9M0+FWnuJrKN7llQDLEyMFQAAcnnGK+w9XY+IzENNUt9nyZPN+T73THr0Nc58SdRsNF+GepaVqsNxK7bEkit4Wl3B5F4wOox19s0VFDD0ZStdRV/uGsRWrVElu+x8kfDTSNFsvjtH4SvbdWtrOWZjHftG29BEzRh/4S5BRiuODxjIxXuniXwP4UuNE1Hy/DenQP9llKXEEIBjYISGBX0IzXh2p/DPwWt9dax4k8c67a3d9K08z3kdrYl2Y7idskhc8/7NVYPDHw5iV4NI+MF5aSyAqc30DIwPBBB8sEH/er4bMqccyxFPEUsRODikmowny3Tu3uvxRCyl0VKM4pttvWUb6/M4HSdetU1SG11G6kstH1S1eKS5MRZY3IwrkDlgp4IHQE12OleEru7t7iTTNW0HWYbVFeeXT9QSQRIzBQzKcOoyQORx3qrqPgLSPCcUd54w1W78ReGElae1TSfkllmcAEEElUjYKMujNyAPSmH48SabANM8I+E7Xw1o44EOn3Rjmf/aeULkt719NUxVarPnwMea+7dlHT1969vK3c4ZZPQnGNGu+VLr1NbxZoWs+GfBviSa0tXu9StgLDU4Is79PgcqzSuOC0cirsDplMFst0qX4cftO6/wCHdKFhqtg+pLGqqjrdNC7AcDcwBDEDvgE98nmrvgX4w6ffanbXFzraWuoQoUi/4SCETIFb7yC6jwwU91cBTWv4g1L4JaZ/xN9T0bwTNfsS32XR0lvZJW68R7lhX6tkexrh+vVKdVRxOHlKe6cV12tfTT8Oj7v04ZNRw1JewrRcfVp/c1f8D2P4K/H7wz49nisJ/BeuWrj5Z9TmhjntIz1zJNkbfTkelem6Q122qQi++0mzyd5n3eXjBxnPHXFfJPga8+InxqvjYeDYk8J+FbadbZ7qG3854ywyQCoVEIXk7AmMjk5r7D+22l1o8egWctzNOIkiR5xy+wDlm9SFzn1r3sLWr1XL2sVG3S92vV7fcc1RU1pB3E8UYK2/9jYzubzfsnXGBjO38etWPDptBp4Gr+QLne2ftWN+3t97nFV9Iz4caRtTAUT4CeV83Trn86i1SwuNfuWv9PCGFlCAyHacjrxXZYyIbdrs6wqzG5+w+cd28N5WzPfPG3GPatHxMkP2OP8AsZY/P8z5vsmN23B67ecZxRPqdtcaadGi8z7U0X2cAr8u/GOvpxVbSYZfDlw13qYAjkXyl8s7juznp+FAE3hzyltZf7YCCXzPk+143bcdt3bOazrmW9/teRYPtX2Lzvl2BvL2ZHTHG3H4Vc1WF/Ekq3OnAGOJfLbzTtOev9atW+p2llp66RKX+0pH5JCrld3Tr6c0WAfry2Q05jpSwfady7fs2N+M84284rhvHmq6po3gHWZI7e5udXuYxb6cki5cOwIZ13f3R83HfFdBBDJ4UR9a1gBLO3jbzDFmRuRwAoGSfYV4L44+KXirUPEtzqt78P8AWhpaDy7FXyrRxdcsApAZjyeeyjtz5eb4yWGoP2VnN7K6X5nVhsNiar5sPBScbaNpX+9o41bS8swkd/pt7ZZACmeIqrfQ9Cax/FsvlWbKD/DVDxd441jxBrkV3K40+C3Ro4bHfuUBvvF843McDnAxgY9al1ez1CbQzqGr2eoWVoyFtyeWzumPvIrEN+JB/GvjYYKVOUJVGk30v+Xc/Y6ebYmjlyqZlFQnLpF39F6/eij4NTy9Ci45bLfmTWppOj32qa3amzSGUwyLcskkwTciSLnHU9eOlWPBWgpeeHLY2es2MM7xZVL5JCM+m4AL+hqhN4W8bWOvLc21hqK6gjZjubVd6nt8rL8pXHbpjtW3PD282ppSV7X7/hp6HJXxn1zAPD4epGE+X7d1+dtPPU+6dIudJvdEt7yT7IZpot+ZNpkyc9e+axtEa+OpQrqX2n7Lg7/tAby+nGd3HWvmPQPFPj3wjqSXvinxLolnZLgyWGoOm6QZydqxDKN75+oNfVCeIdO8WaFCmjyNKb6FJoGYYVlIDg5+lfZYDGrFU07q63ttfyZ+UYrA1cI1Gq035O6+8f4j2r5H9jD+95v2T8Mbtv49at6GbE6ev9p/Z/tO47vtON+M8Z3c9KpaRnw15p1MY+0Y2eV833eufzFVdT0271y8fUbFEaCQBVMjbTkDB4ru2OQhtf7Q/teL7QLr7F53z+Zu8vZk9c8YrT8StCLaE6Ps87zP3n2TG7bjvt5xnFTT6xZ3di2lRGT7TKnkqGXC7sY6+nFVtLt38Oztd6gAI5V8tTEdxznP9KLAWPDrWps3/tbyvP8AM+X7VjftwP73OOtZV6l8dXYwfafsXnDGzd5WzPtxtx+FT6vZz+IbsX2nKrQonlEyHadwJPT8RV211a1gsF0aTzBdJH9nPy/Lvxjr6Z70AHiEWi6aTpIgFzvXH2XG/b3+7zivLviD8ULTw1o97pkLC/1+Q+Ugc7vsXGGZyfusOy9c4JwK4H9orxv4l0HWZPBPhnXYdC1AWyvd3ca7piJBkJGw5j4GSwG7kYI7/MN74P8AGMhlma+huTK26SRrplaQ+rb8bj7nJr08LgKzaqOm5R8v6Z6WCo8lSNWpTc472T39d9De+Ivia2XTW06wvBJPIwM0iNkKBztB7sSBnHQZzXqXgjRYJvB3hC7uLC8uLnxZG+l38lvetAqPcFnS5YDIZ0RJAvu2PSvniXwfrCb5r+S3hRAWZ2uUc8egUk17x8M/FN7N8ItKj0ZrWbVNF1OzSGO4nWJXZJxhCzcDejkD608wniW+aqnFPp6GubY7FY2p7WuuVPZen/DvU+u/B1hpnh3Q7TRtCtY7DT7aMJFDD8o6cscdWPUscknk1yPxt0+803Tf+E+8Fvp+neK9OeJJLi4KxwXtq0iq8N0TgNGNwcMTlSvBGaXwh420XxBDINJv4Z5bd2huLdZAZbeRSQyOo5BBB56HqOK5X4yeLdH1r7F8KYL3fqPiiUW90YDuNrZqd80hPTcVRlUepJPTnzDyC9q3xL1b+0tb0Y+ANe1bUdHijaabRlWWxnd41cLHK5UgfN02k4HQ8V89pPZ2vjDU9Ke5tWMwju4CuFw7r+8hIPSRWyCPUN6GvpmWfR/Dvh220bR7aOz06xi8q2t06Io/mT1JPJOTXxZ8VrfUfE/xQ1nU9EESwmbygRKq7io+Y475bceld2X1K1OtelFy7pHpZTjKuDxUatOPM107o+pf2evG2kaJdz+F/ECQx2t3N5trdTKCscpABRiegbAIPQEHPWvXdTN9/asy2YuvsnmDZ5Qby9vHTHGOtfnxHoPjlrRbe91qBIMY2TTO649MYwa91/Z8+Kfi3wZdWPhnxVr9vrnh64kW3V5Vk86x3fKux8YaMEj5G6D7pGMHtxuBr15urCm13udmb2xld4ilTcb6tNrfyPq3W0sRpznTVt/tOV2fZ8b8Z5xt56VwHjL4b+GviDpV1beK4WtNQWIJZakfkuIevAZvvr6qcjnsea6yw0+60W8TUb1UW3iyreW25skYHH1qfV8+JDF/Zoz9nzv835fvdMfka8JxTVmeEm07o8s+DPgXxb8OtAvfDF1rA1fT4btpdNuLFZFGxxlww6A7ucAnknmvYNQGnDSJTaC1+2CL5PK2+Zu9sc561Fp+qWmh2iabfFxPFksEXcOTkYP0NU9L0S7tdRGp3QQQxsZAFbJOf/100rA3d3E8Nu5vJf7Y8zyvL+T7WDt3Z7buM4qLxGbg6gP7J842/ljP2UHZuyc/d4z0rU8QxvrUMVvZLuaN97FztGMY6+vNQabfQ+HbY2Go71mZjKPKG4bTwOfwNAhi3sniRv7NlRbZQPN3odx47YP1oaRvDB+zRAXQm/eFn+XGOMcVLrtpDolkLzTVME5cIW3FvlOcjBz6Cm+H4o9dtpZ9VBuJIn2IclcDGccY70AJDpC6lH/bL3DRPN+9MaqCAR2z+FRxavNr7rpcsCW6TcmRGLEY56H6VVvtRvLHUpNNtZjHaxyCNUwDhT2yee9aus6daaRp0l9p8ZhuIyAj7icZODweOhoArzBvCxDQt9q+08HeNu3b9PrXIfFjwV4i+I/g8/8ACN+JB4c1GW4QmYRlx5ablKgjkE5ByPTHeus8PZ15phqxNyIQDHk7duc56Y9BUGsX1zo9/JYadIYbdAGVMA4JGTyeamUVNcsloB86eBf2b9Cj8QifWZP7beVGjYaoGYvMTw52MOBjoSSc1w2q/sv/ABCvNKubzUYvDWhXC3Tx21ssjN5ygEhgyAhEPQBufXFfa99ptlZ6Q+o20Pl3SRiVZNxOG45wTjvWf4flk1u9e31RzcxRpvVT8uGyBnjHY1zUMKqL5nJyfdv9Nl8kgep8kfsp/CT4mad8UrqDVbabTfDumuy6gJvmgu2ZGEZhBG2TkKdwxgdTzivpbXfC/hDVdS0q11TwnpV1Nol3vsLjy9hil3D59q4ByQCVOQSBmui1+5m0W9W10xzbwtGHKj5skk8859BWhDp1nLo41OSHddtB55k3H7+M5x0610qMU3JLVjuzjPHvwp8B6lC2o+IfC+j6vKWCMzWawSHJ6+ZFtb9aw/hd8FPAOheLdR8T+GdPn0u4kt1tlt2l+0Qwg4LNGHBZS20ZyT3xjNd1ot5c6xqCWWpTGeBlLFMBeQODkYNWPEGdCeJNKZrZZgWkGd24jgdc+tUIr2l3beFUm0jS9Ksooo5C7GGMQiR25ZiqjGTnrV2XSV0aP+1452meH5hGy4Bzx1/Gp9K0yy1TTIr++iMtzKCzvvIyQSOgOOgFZWl395qWpxafeztLbSkh48AZABI5HPUCgC1GW8Ut5cuLX7ONwKfNuzx3+lNl1KXw2zabFGlwqjzN7kqTu7YFSeIVGgpC+lA27TEhzndkDp1z61Nolja61Yi91OL7RcMxQvuK8DoMDAoAYulpBD/bYnYuq/afKK8Z64z6c0wTN4mYWUqi2Ef70MnzE9sYP1qjBf3k2qppck7GzabyTHgcpnGM9elaWvW8Wh2sd1patBM7+Wzbi2VwTjBz6CgCvPPL4Wb7LAq3QlHmln+Ujtjj6VJDpS30Q1uSdkeQeeYgoIBHOM/hUmgQx65bS3Gqr9oljfYpJ24XGccY7k1nXl/d22ovp1vM0dqkvlLGACAmcYz1o9AOR+Np8TeOPh9caJ4Z3Wl600M5MUh3vEjZkVT2O3keuMd6+bdb+Hnxn0Cyl1zQX102SKZIEluwt3MqkAkW+Se+QOpAzivtPWrC00Wxa902LyJ1dVD7i2AeDwc1F4dH9uGc6r/pBh2+X/DtznPTHoK5auFhVnzT1VrWsb0sVWpK0JWXY+PdP1T41adbaNe+JvAEuq2+rSrDYzNap9oLkkKrYBaMnGfnUfWteH4U/Ez4i+KETX5F8KaRNJtYG4W5uQMcYVTg9O5AGehr6e1y/vdN1GWysbhoLePG1AAcZGTyeeprWv8ATLLT9Mkv7OHy7iJA6PvJweOcHjua56eUYOnV9rGCT/rodP8AaVVJ8qSfdLWx84a9+zFL4elvL3QvHVxBbtKosILi13FRglhK6kBuRwQvTqKqj4XfHXxJNNpo8R+H7DToYVCXts2wTNkAoQiiQELk5PBwB3yPonRZn128a01RzcQohkVfu4YHGeMdiaPEEsuhXMVtpUjW8Uke91+9ls4zzntW1TAYapJTnBNj/tbFuKi53ttdJtejZ85Wv7NOnaT4rt7nUfE0mvLFIy3cN5ZDZLkYUqAx6E87s9K+kItBtfDNnHeWRGyzQRxQCMIgXG0AY6AD+VXdN02yvNKTULqDzLqWMyPJuIywzzgcdqy9Jv7vVb6Kxv5jNbyg70IAzgZHI56iumNOMXdI4JzlUk5zd2yzbO3ilmWfFr9m5Gz5t276/SnS6o+gudMjhWdYvmDscE7uegqPxCg0EwnSSbYz58zB3bsYx1z6mrWh2Nrq9il9qMZnuHYqzliMgHA4GB0qySvLoa2ER1hLhpHh/fiIqACeuM/jSQ3MniV/sU6LarEPNDIdxJ6Y5+tVLPUry71GPTriYvayS+U0eAMrnGM9a0PEEEeiW0Vzpam3lkfYzA7srjOOc9wKAEkvG8Nv9giQXIcebuc7SM8Y4+lNOkC5j/ts3LKzD7T5QTjP3sZ/CnaFaw65ayXeqBriZJPLVtxXC4BxxjuTWfPqF5BqjaXHOy2aTeQI8A/JnGM9elAHjfxy+CFj8YPEi63pk1vo+vyW+yeWYu8MwRfkyByrDoTzxjjI54rxR+yneaD4b0eDQfGlxHr7Mz380sjpalfSJFBYEHAyx5HOB0r6u1yzttGsDeabGYJw6qH3FsA9eDmq/h+NdeWd9WzcNCQIznbtB69MelUptbFqbVrHyHr/AOzh8WV03SItG13TvEcGosYr2SWJYfsPzY3lnO50xk5X5uMbeRXReC/2aLK10C80i98QS3+rX08UqEBorIGIlgjx8s4Y9W4IwMDqD9G6rfXmmalLYWM7Q20TAIgAOMgHqeepNbWp6dZadpkt/ZweVcxKGRwxOCcDoTjvV1K1Spbnk3buOdWc1aTufJnibRrDw5NLpvjPwTa2DyEgzfZAqTf7Szpjdn/ez61zj+JbfwmuhHw5qRl0DSJpG/sYQpJOxmLKzRS43sQZM7SecdTX2PoLtr5ubbV8XcKKrCNx8uSSOQOv41m6tbWmgaw0ejWNlZARqwMVrGGBOc/Ntz+tZGZ4W+hePPHejXP9kxnw/JNHss5NVQo0khIA+QZZV5PzEdegNeaeCv2Z/jLrltqdtqF/B4ZWymaGJbqRh9sfkllaMElM4+c9c8Dg19vnTrIaUdS8n/ShB5/mbj9/bnOM461T1HVL+PTxMlwVfcvIUdwc9quFSUb8rsVGco/C7HxDYfsp+P5JrtPE2qadpEqMBbEuboXI7vlTlV+oyfQV0nhL9lbxSPF+nF7qKz0izKXNxqsU25btVcHy448hlc4b74wMdTwK+vtAhj1y3ln1RftEkb7EYnbgYzjjFZ95qN5Y6nJptrMY7WOQRqmAcKccZPPc0Rm1fzHGo4p+Zdj1R9ecaZJCtusvzb1bcRjnofpSXG/wuR5GLr7SOd/y7dv0+tT65p9rpFg9/p8ZhuEdVV9xbAJweDx0qv4d/wCJ40w1XNz5IXy8/LtznPTHoKggWDSF8QL/AGrLO1u83ymNV3AbeOp+lPs9ee8uk0t7ZUVz5W8MSRjvj8KpazfXek6hJY6dKYLeMAqgAOCRk8nnrWnqGmWVlpcmp20Pl3ccYkWTcThuOcE470ICPUfN8Pyi+SQ3RmPlBHG1UHXjH0qGKxHiZf7RmlNsynytiDcOOc5P1qPQJZNcu5LbVWNxHHHvRT8uGyBnjHY03XrifRb0WemSG3gKCQqBu+Y5yec+goA//9k="
    
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
            "📋 Palpites"
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