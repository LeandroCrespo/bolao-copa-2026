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
# CSS PERSONALIZADO
# =============================================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .match-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 0.5rem;
        border-left: 4px solid #1E3A5F;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .team-name {
        font-size: 1.1rem;
        font-weight: 600;
    }
    .match-info {
        color: #666;
        font-size: 0.9rem;
    }
    .stButton>button {
        width: 100%;
    }
    .ranking-gold { background-color: #FFD700 !important; }
    .ranking-silver { background-color: #C0C0C0 !important; }
    .ranking-bronze { background-color: #CD7F32 !important; }
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
        return f"{team.flag} {team.name}"
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
    st.markdown('<h1 class="main-header">⚽ Bolão Copa do Mundo 2026</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Faça login para acessar o sistema</p>', unsafe_allow_html=True)
    
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
                
                with st.form(f"grupo_{grupo}"):
                    primeiro = st.selectbox(
                        "1º Lugar",
                        options=team_ids,
                        format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                        index=team_ids.index(pred.first_place_team_id) if pred and pred.first_place_team_id in team_ids else 0,
                        key=f"g{grupo}_1"
                    )
                    
                    segundo = st.selectbox(
                        "2º Lugar",
                        options=team_ids,
                        format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                        index=team_ids.index(pred.second_place_team_id) if pred and pred.second_place_team_id in team_ids else 0,
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
            col1, col2 = st.columns(2)
            
            with col1:
                if user.active:
                    if st.button(f"Desativar", key=f"deactivate_{user.id}"):
                        user.active = False
                        session.commit()
                        log_action(session, st.session_state.user['id'], 'participante_desativado', user.id)
                        st.rerun()
                else:
                    if st.button(f"Ativar", key=f"activate_{user.id}"):
                        user.active = True
                        session.commit()
                        log_action(session, st.session_state.user['id'], 'participante_ativado', user.id)
                        st.rerun()
            
            with col2:
                if st.button(f"Resetar Senha", key=f"reset_{user.id}"):
                    user.password_hash = hash_password("123456")
                    session.commit()
                    st.success(f"Senha resetada para '123456'")
                    log_action(session, st.session_state.user['id'], 'senha_resetada', user.id)


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
    
    # Todos os jogos pendentes de resultado
    jogos_pendentes = session.query(Match).filter(
        Match.status == 'scheduled'
    ).order_by(Match.datetime).all()
    
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
                    
                    if st.form_submit_button("✏️ Atualizar Resultado"):
                        match.team1_score = gols1_edit
                        match.team2_score = gols2_edit
                        session.commit()
                        
                        # Reprocessa pontuação dos palpites
                        process_match_predictions(session, match.id)
                        
                        st.success(f"Resultado atualizado: {gols1_edit} x {gols2_edit}")
                        log_action(session, st.session_state.user['id'], 'resultado_editado', details=f"Jogo #{match.match_number}: {gols1_edit}x{gols2_edit}")
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
        
        with st.expander(f"Grupo {grupo}"):
            with st.form(f"group_result_{grupo}"):
                primeiro = st.selectbox(
                    "1º Lugar",
                    options=team_ids,
                    format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                    index=team_ids.index(result.first_place_team_id) if result and result.first_place_team_id in team_ids else 0,
                    key=f"gr_{grupo}_1"
                )
                
                segundo = st.selectbox(
                    "2º Lugar",
                    options=team_ids,
                    format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                    index=team_ids.index(result.second_place_team_id) if result and result.second_place_team_id in team_ids else 0,
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
            "estatisticas": page_estatisticas,
            "configuracoes": page_configuracoes,
            "admin": page_admin,
        }
        
        page_func = pages.get(st.session_state.page, page_home)
        page_func()


if __name__ == "__main__":
    main()
