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
    """Página com ranking completo"""
    st.markdown("## 📊 Ranking do Bolão")
    
    session = get_session(engine)
    
    try:
        ranking = get_ranking(session)
        
        if not ranking:
            st.info("Nenhum participante no ranking ainda.")
            return
        
        # Tabela de ranking
        for r in ranking:
            medal = ""
            bg_class = ""
            if r['posicao'] == 1:
                medal = "🥇"
                bg_class = "ranking-gold"
            elif r['posicao'] == 2:
                medal = "🥈"
                bg_class = "ranking-silver"
            elif r['posicao'] == 3:
                medal = "🥉"
                bg_class = "ranking-bronze"
            
            is_current_user = r['user_id'] == st.session_state.user['id']
            highlight = "**" if is_current_user else ""
            
            col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 2])
            
            with col1:
                st.markdown(f"{medal} {highlight}{r['posicao']}º{highlight}")
            with col2:
                st.markdown(f"{highlight}{r['nome']}{highlight}")
            with col3:
                st.markdown(f"{highlight}{r['total_pontos']} pts{highlight}")
            with col4:
                st.markdown(f"🎯 {r['placares_exatos']}")
            with col5:
                st.markdown(f"✅ {r['resultados_corretos']}")
    
    finally:
        session.close()

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