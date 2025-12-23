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
        return code
    return "A definir"

def can_predict_match(match):
    """Verifica se ainda é possível fazer palpite para uma partida"""
    if match.status == 'finished':
        return False
    now = get_brazil_time().replace(tzinfo=None)
    kickoff = match.datetime
    return now < kickoff

def can_predict_podium(session):
    """Verifica se ainda é possível fazer palpite de pódio (antes do início da Copa)"""
    data_inicio = get_config_value(session, 'data_inicio_copa', '')
    if not data_inicio:
        return True
    try:
        inicio = datetime.strptime(data_inicio, "%Y-%m-%d %H:%M")
        now = get_brazil_time().replace(tzinfo=None)
        return now < inicio
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
    """Página de login do sistema"""
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
                    
                    pred = session.query(Prediction).filter_by(
                        user_id=st.session_state.user['id'],
                        match_id=match.id
                    ).first()
                    
                    status_icon = "✅" if pred else "⚠️"
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="match-card">
                            <div class="team-name">{status_icon} {team1_display} vs {team2_display}</div>
                            <div class="match-info">📍 {match.city} | 🕐 {format_datetime(match.datetime)}</div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("Nenhum jogo programado no momento.")
        
        with col2:
            st.subheader("🏅 Top 5 Ranking")
            
            if ranking:
                for r in ranking[:5]:
                    medal = "🥇" if r['posicao'] == 1 else "🥈" if r['posicao'] == 2 else "🥉" if r['posicao'] == 3 else "🏅"
                    st.markdown(f"{medal} **{r['nome']}** - {r['pontos']} pts")
            else:
                st.info("Ranking ainda não disponível.")
    
    finally:
        session.close()

# =============================================================================
# PÁGINA DE PALPITES DE JOGOS
# =============================================================================
def page_palpites_jogos():
    """Página para fazer palpites nos jogos"""
    st.markdown("## 📝 Palpites dos Jogos")
    
    session = get_session(engine)
    
    try:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            fase_selecionada = st.selectbox(
                "Fase",
                options=["Todas"] + list(FASES.keys()),
                format_func=lambda x: FASES.get(x, x) if x != "Todas" else "Todas as Fases"
            )
        with col2:
            grupo_selecionado = st.selectbox(
                "Grupo",
                options=["Todos"] + GRUPOS,
                format_func=lambda x: f"Grupo {x}" if x != "Todos" else "Todos os Grupos"
            )
        
        # Busca jogos
        query = session.query(Match).order_by(Match.datetime)
        
        if fase_selecionada != "Todas":
            query = query.filter(Match.phase == fase_selecionada)
        
        if grupo_selecionado != "Todos":
            query = query.filter(Match.group == grupo_selecionado)
        
        jogos = query.all()
        
        if not jogos:
            st.info("Nenhum jogo encontrado com os filtros selecionados.")
            return
        
        # Agrupa jogos por data
        jogos_por_data = {}
        for jogo in jogos:
            data = jogo.datetime.strftime("%d/%m/%Y (%A)")
            if data not in jogos_por_data:
                jogos_por_data[data] = []
            jogos_por_data[data].append(jogo)
        
        # Exibe jogos
        for data, jogos_data in jogos_por_data.items():
            st.subheader(f"📅 {data}")
            
            for match in jogos_data:
                team1_display = get_team_display(match.team1, match.team1_code)
                team2_display = get_team_display(match.team2, match.team2_code)
                
                # Busca palpite existente
                pred = session.query(Prediction).filter_by(
                    user_id=st.session_state.user['id'],
                    match_id=match.id
                ).first()
                
                can_predict = can_predict_match(match)
                
                with st.expander(f"🕐 {format_time(match.datetime)} - {team1_display} vs {team2_display}", expanded=can_predict and not pred):
                    col1, col2, col3 = st.columns([2, 1, 2])
                    
                    with col1:
                        st.markdown(f"### {team1_display}")
                    with col2:
                        st.markdown("### VS")
                    with col3:
                        st.markdown(f"### {team2_display}")
                    
                    st.caption(f"📍 {match.city} | {FASES.get(match.phase, match.phase)}" + (f" - Grupo {match.group}" if match.group else ""))
                    
                    if match.status == 'finished':
                        st.success(f"**Resultado Final:** {match.team1_score} x {match.team2_score}")
                        if pred:
                            st.info(f"Seu palpite: {pred.pred_team1_score} x {pred.pred_team2_score} | Pontos: {pred.points_awarded}")
                    
                    elif can_predict:
                        with st.form(f"pred_form_{match.id}"):
                            c1, c2 = st.columns(2)
                            with c1:
                                gols1 = st.number_input(
                                    f"Gols {team1_display}",
                                    min_value=0, max_value=20,
                                    value=pred.pred_team1_score if pred else 0,
                                    key=f"gols1_{match.id}"
                                )
                            with c2:
                                gols2 = st.number_input(
                                    f"Gols {team2_display}",
                                    min_value=0, max_value=20,
                                    value=pred.pred_team2_score if pred else 0,
                                    key=f"gols2_{match.id}"
                                )
                            
                            if st.form_submit_button("💾 Salvar Palpite", use_container_width=True):
                                if pred:
                                    pred.pred_team1_score = gols1
                                    pred.pred_team2_score = gols2
                                    pred.updated_at = datetime.utcnow()
                                else:
                                    pred = Prediction(
                                        user_id=st.session_state.user['id'],
                                        match_id=match.id,
                                        pred_team1_score=gols1,
                                        pred_team2_score=gols2
                                    )
                                    session.add(pred)
                                
                                session.commit()
                                st.success("Palpite salvo com sucesso!")
                                st.rerun()
                    else:
                        st.warning("⏰ Prazo encerrado para este jogo!")
                        if pred:
                            st.info(f"Seu palpite: {pred.pred_team1_score} x {pred.pred_team2_score}")
    
    finally:
        session.close()

# =============================================================================
# PÁGINA DE PALPITES DE GRUPOS
# =============================================================================
def page_palpites_grupos():
    """Página para fazer palpites de classificação dos grupos"""
    st.markdown("## 🏅 Palpites de Classificação dos Grupos")
    st.info("Escolha quem será o 1º e 2º colocado de cada grupo")
    
    session = get_session(engine)
    
    try:
        # Organiza times por grupo
        teams = session.query(Team).order_by(Team.group, Team.name).all()
        teams_by_group = {}
        for team in teams:
            if team.group:
                if team.group not in teams_by_group:
                    teams_by_group[team.group] = []
                teams_by_group[team.group].append(team)
        
        # Exibe grupos em colunas
        cols = st.columns(3)
        
        for idx, grupo in enumerate(GRUPOS):
            col = cols[idx % 3]
            
            with col:
                st.subheader(f"Grupo {grupo}")
                
                grupo_teams = teams_by_group.get(grupo, [])
                
                if not grupo_teams:
                    st.warning("Nenhuma seleção cadastrada neste grupo")
                    continue
                
                # Busca palpite existente
                pred = session.query(GroupPrediction).filter_by(
                    user_id=st.session_state.user['id'],
                    group_name=grupo
                ).first()
                
                team_options = [(t.id, f"{t.flag} {t.name}") for t in grupo_teams]
                team_ids = [t[0] for t in team_options]
                team_names = {t[0]: t[1] for t in team_options}
                
                with st.form(f"group_pred_{grupo}"):
                    primeiro = st.selectbox(
                        "1º Lugar",
                        options=team_ids,
                        format_func=lambda x: team_names.get(x, "Selecione"),
                        index=team_ids.index(pred.first_place_team_id) if pred and pred.first_place_team_id in team_ids else 0,
                        key=f"primeiro_{grupo}"
                    )
                    
                    segundo = st.selectbox(
                        "2º Lugar",
                        options=team_ids,
                        format_func=lambda x: team_names.get(x, "Selecione"),
                        index=team_ids.index(pred.second_place_team_id) if pred and pred.second_place_team_id in team_ids else 0,
                        key=f"segundo_{grupo}"
                    )
                    
                    if st.form_submit_button("💾 Salvar", use_container_width=True):
                        if primeiro == segundo:
                            st.error("1º e 2º lugar devem ser diferentes!")
                        else:
                            if pred:
                                pred.first_place_team_id = primeiro
                                pred.second_place_team_id = segundo
                                pred.updated_at = datetime.utcnow()
                            else:
                                pred = GroupPrediction(
                                    user_id=st.session_state.user['id'],
                                    group_name=grupo,
                                    first_place_team_id=primeiro,
                                    second_place_team_id=segundo
                                )
                                session.add(pred)
                            
                            session.commit()
                            st.success("Salvo!")
                            st.rerun()
    
    finally:
        session.close()

# =============================================================================
# PÁGINA DE PALPITES DE PÓDIO
# =============================================================================
def page_palpites_podio():
    """Página para fazer palpites do pódio"""
    st.markdown("## 🏆 Palpites do Pódio")
    
    session = get_session(engine)
    
    try:
        can_predict = can_predict_podium(session)
        
        if not can_predict:
            st.warning("⏰ O prazo para palpites de pódio já encerrou (início da Copa).")
        
        # Busca todas as seleções
        teams = session.query(Team).order_by(Team.name).all()
        team_options = [(t.id, f"{t.flag} {t.name}") for t in teams]
        team_ids = [t[0] for t in team_options]
        team_names = {t[0]: t[1] for t in team_options}
        
        # Busca palpite existente
        pred = session.query(PodiumPrediction).filter_by(
            user_id=st.session_state.user['id']
        ).first()
        
        st.info("Escolha quem será o Campeão, Vice-Campeão e 3º Lugar da Copa do Mundo 2026")
        
        with st.form("podium_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 🥇 Campeão")
                campeao = st.selectbox(
                    "Selecione o Campeão",
                    options=team_ids,
                    format_func=lambda x: team_names.get(x, "Selecione"),
                    index=team_ids.index(pred.champion_team_id) if pred and pred.champion_team_id in team_ids else 0,
                    disabled=not can_predict
                )
            
            with col2:
                st.markdown("### 🥈 Vice-Campeão")
                vice = st.selectbox(
                    "Selecione o Vice",
                    options=team_ids,
                    format_func=lambda x: team_names.get(x, "Selecione"),
                    index=team_ids.index(pred.runner_up_team_id) if pred and pred.runner_up_team_id in team_ids else 0,
                    disabled=not can_predict
                )
            
            with col3:
                st.markdown("### 🥉 3º Lugar")
                terceiro = st.selectbox(
                    "Selecione o 3º Lugar",
                    options=team_ids,
                    format_func=lambda x: team_names.get(x, "Selecione"),
                    index=team_ids.index(pred.third_place_team_id) if pred and pred.third_place_team_id in team_ids else 0,
                    disabled=not can_predict
                )
            
            if can_predict:
                if st.form_submit_button("💾 Salvar Palpite de Pódio", use_container_width=True):
                    if len(set([campeao, vice, terceiro])) != 3:
                        st.error("Campeão, Vice e 3º Lugar devem ser seleções diferentes!")
                    else:
                        if pred:
                            pred.champion_team_id = campeao
                            pred.runner_up_team_id = vice
                            pred.third_place_team_id = terceiro
                            pred.updated_at = datetime.utcnow()
                        else:
                            pred = PodiumPrediction(
                                user_id=st.session_state.user['id'],
                                champion_team_id=campeao,
                                runner_up_team_id=vice,
                                third_place_team_id=terceiro
                            )
                            session.add(pred)
                        
                        session.commit()
                        st.success("Palpite de pódio salvo com sucesso!")
                        st.rerun()
        
        if pred:
            st.divider()
            st.subheader("Seu Palpite Atual")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"🥇 **Campeão:** {team_names.get(pred.champion_team_id, 'N/A')}")
            with col2:
                st.markdown(f"🥈 **Vice:** {team_names.get(pred.runner_up_team_id, 'N/A')}")
            with col3:
                st.markdown(f"🥉 **3º Lugar:** {team_names.get(pred.third_place_team_id, 'N/A')}")
    
    finally:
        session.close()

# =============================================================================
# PÁGINA DE RANKING
# =============================================================================
def page_ranking():
    """Página com ranking completo"""
    st.markdown("## 📊 Ranking Geral")
    
    session = get_session(engine)
    
    try:
        ranking = get_ranking(session)
        
        if not ranking:
            st.info("Ranking ainda não disponível. Aguarde os primeiros resultados.")
            return
        
        # Tabela de ranking
        for r in ranking:
            pos = r['posicao']
            if pos == 1:
                medal = "🥇"
                bg_color = "#FFD700"
            elif pos == 2:
                medal = "🥈"
                bg_color = "#C0C0C0"
            elif pos == 3:
                medal = "🥉"
                bg_color = "#CD7F32"
            else:
                medal = f"{pos}º"
                bg_color = "#f8f9fa"
            
            is_current_user = r['user_id'] == st.session_state.user['id']
            border = "3px solid #1E3A5F" if is_current_user else "none"
            
            st.markdown(f"""
            <div style="background-color: {bg_color}; padding: 10px; border-radius: 8px; margin-bottom: 5px; border: {border};">
                <strong>{medal} {r['nome']}</strong> - {r['pontos']} pts
                <span style="float: right; color: #666;">
                    🎯 {r.get('placares_exatos', 0)} | ✅ {r.get('resultados', 0)}
                </span>
            </div>
            """, unsafe_allow_html=True)
    
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
            st.metric("Total de Pontos", stats.get('total_pontos', 0))
            st.metric("Palpites Feitos", stats.get('total_palpites', 0))
        
        with col2:
            st.metric("Placares Exatos", stats.get('placares_exatos', 0))
            st.metric("Resultados Corretos", stats.get('resultados_corretos', 0))
        
        with col3:
            st.metric("Gols Corretos", stats.get('gols_corretos', 0))
            st.metric("Palpites Zerados", stats.get('palpites_zerados', 0))
        
        st.divider()
        
        # Pontuação por categoria
        st.subheader("Pontuação por Categoria")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Pontos em Jogos", stats.get('pontos_jogos', 0))
        with col2:
            st.metric("Pontos em Grupos", stats.get('pontos_grupos', 0))
        with col3:
            st.metric("Pontos em Pódio", stats.get('pontos_podio', 0))
    
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
        st.subheader("Alterar Senha")
        
        with st.form("change_password_form"):
            current_password = st.text_input("Senha Atual", type="password")
            new_password = st.text_input("Nova Senha", type="password")
            confirm_password = st.text_input("Confirmar Nova Senha", type="password")
            
            if st.form_submit_button("Alterar Senha"):
                if not all([current_password, new_password, confirm_password]):
                    st.warning("Preencha todos os campos!")
                elif new_password != confirm_password:
                    st.error("As senhas não coincidem!")
                elif len(new_password) < 4:
                    st.error("A nova senha deve ter pelo menos 4 caracteres!")
                else:
                    user = session.query(User).get(st.session_state.user['id'])
                    if change_password(session, user, current_password, new_password):
                        st.success("Senha alterada com sucesso!")
                    else:
                        st.error("Senha atual incorreta!")
    
    finally:
        session.close()


# =============================================================================
# PAINEL ADMINISTRATIVO
# =============================================================================
def page_admin():
    """Painel administrativo"""
    st.markdown("## 🔧 Painel Administrativo")
    
    if st.session_state.user['role'] != 'admin':
        st.error("Acesso negado. Apenas administradores podem acessar esta página.")
        return
    
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
        
        # Tab: Participantes
        with tabs[0]:
            admin_participantes(session)
        
        # Tab: Seleções
        with tabs[1]:
            admin_selecoes(session)
        
        # Tab: Jogos
        with tabs[2]:
            admin_jogos(session)
        
        # Tab: Resultados
        with tabs[3]:
            admin_resultados(session)
        
        # Tab: Grupos
        with tabs[4]:
            admin_grupos(session)
        
        # Tab: Pódio
        with tabs[5]:
            admin_podio(session)
        
        # Tab: Pontuação
        with tabs[6]:
            admin_pontuacao(session)
        
        # Tab: Premiação
        with tabs[7]:
            admin_premiacao(session)
        
        # Tab: Palpites
        with tabs[8]:
            admin_palpites(session)
    
    finally:
        session.close()


def admin_participantes(session):
    """Gerenciamento de participantes"""
    st.subheader("👥 Gerenciar Participantes")
    
    # Lista de participantes
    users = session.query(User).order_by(User.name).all()
    
    st.markdown(f"**Total de participantes:** {len(users)}")
    
    for user in users:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        with col1:
            role_icon = "👑" if user.role == 'admin' else "👤"
            status_icon = "✅" if user.active else "❌"
            st.markdown(f"{role_icon} {status_icon} **{user.name}** (@{user.username})")
        
        with col2:
            if user.role != 'admin':
                if st.button("🔑 Reset Senha", key=f"reset_{user.id}"):
                    user.password_hash = hash_password("123456")
                    session.commit()
                    st.success(f"Senha de {user.username} resetada para '123456'")
        
        with col3:
            if user.role != 'admin':
                new_status = not user.active
                btn_label = "Ativar" if new_status else "Desativar"
                if st.button(btn_label, key=f"status_{user.id}"):
                    user.active = new_status
                    session.commit()
                    st.rerun()
        
        with col4:
            if user.role != 'admin' and user.id != st.session_state.user['id']:
                if st.button("🗑️", key=f"del_{user.id}"):
                    session.delete(user)
                    session.commit()
                    st.rerun()
    
    st.divider()
    
    # Adicionar novo participante
    st.subheader("➕ Adicionar Participante")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Nome completo")
            new_username = st.text_input("Usuário")
        with col2:
            new_password = st.text_input("Senha", value="123456")
            new_role = st.selectbox("Tipo", options=["player", "admin"], format_func=lambda x: "Participante" if x == "player" else "Administrador")
        
        if st.form_submit_button("Adicionar"):
            if new_name and new_username:
                user = create_user(session, new_name, new_username, new_password, new_role)
                if user:
                    st.success(f"Participante {new_name} adicionado!")
                    st.rerun()
                else:
                    st.error("Usuário já existe!")
            else:
                st.warning("Preencha nome e usuário!")


def admin_selecoes(session):
    """Gerenciamento de seleções"""
    st.subheader("🏳️ Gerenciar Seleções")
    
    teams = session.query(Team).order_by(Team.group, Team.name).all()
    
    # Agrupa por grupo
    teams_by_group = {}
    for team in teams:
        grupo = team.group or "Sem Grupo"
        if grupo not in teams_by_group:
            teams_by_group[grupo] = []
        teams_by_group[grupo].append(team)
    
    # Exibe por grupo
    for grupo in sorted(teams_by_group.keys()):
        with st.expander(f"Grupo {grupo} ({len(teams_by_group[grupo])} seleções)"):
            for team in teams_by_group[grupo]:
                col1, col2, col3, col4, col5 = st.columns([1, 3, 1, 1, 1])
                
                with col1:
                    st.markdown(f"### {team.flag}")
                with col2:
                    st.markdown(f"**{team.name}** ({team.code})")
                with col3:
                    new_name = st.text_input("Nome", value=team.name, key=f"team_name_{team.id}", label_visibility="collapsed")
                with col4:
                    new_flag = st.text_input("Bandeira", value=team.flag, key=f"team_flag_{team.id}", label_visibility="collapsed")
                with col5:
                    if st.button("💾", key=f"save_team_{team.id}"):
                        team.name = new_name
                        team.flag = new_flag
                        session.commit()
                        st.success("Salvo!")
                        st.rerun()
    
    st.divider()
    
    # Adicionar nova seleção
    st.subheader("➕ Adicionar Seleção")
    
    with st.form("add_team_form"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            new_name = st.text_input("Nome da Seleção")
        with col2:
            new_code = st.text_input("Código (3 letras)")
        with col3:
            new_group = st.selectbox("Grupo", options=GRUPOS)
        with col4:
            new_flag = st.text_input("Emoji Bandeira", value="🏳️")
        
        if st.form_submit_button("Adicionar"):
            if new_name and new_code:
                team = Team(name=new_name, code=new_code.upper(), group=new_group, flag=new_flag)
                session.add(team)
                session.commit()
                st.success(f"Seleção {new_name} adicionada!")
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
            format_func=lambda x: FASES.get(x, x) if x != "Todas" else "Todas"
        )
    with col2:
        grupo_filter = st.selectbox(
            "Filtrar por Grupo",
            options=["Todos"] + GRUPOS
        )
    
    # Busca jogos
    query = session.query(Match).order_by(Match.match_number)
    if fase_filter != "Todas":
        query = query.filter(Match.phase == fase_filter)
    if grupo_filter != "Todos":
        query = query.filter(Match.group == grupo_filter)
    
    matches = query.all()
    teams = session.query(Team).order_by(Team.name).all()
    team_options = {t.id: f"{t.flag} {t.name}" for t in teams}
    team_ids = [None] + [t.id for t in teams]
    
    st.markdown(f"**Total de jogos:** {len(matches)}")
    
    for match in matches:
        team1_display = get_team_display(match.team1, match.team1_code)
        team2_display = get_team_display(match.team2, match.team2_code)
        
        with st.expander(f"#{match.match_number} - {team1_display} vs {team2_display} | {format_datetime(match.datetime)}"):
            with st.form(f"edit_match_{match.id}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    # Time 1
                    current_team1_idx = team_ids.index(match.team1_id) if match.team1_id in team_ids else 0
                    new_team1 = st.selectbox(
                        "Time 1",
                        options=team_ids,
                        format_func=lambda x: team_options.get(x, "A definir") if x else "A definir",
                        index=current_team1_idx
                    )
                    
                    # Data
                    new_date = st.date_input("Data", value=match.datetime.date())
                
                with col2:
                    # Time 2
                    current_team2_idx = team_ids.index(match.team2_id) if match.team2_id in team_ids else 0
                    new_team2 = st.selectbox(
                        "Time 2",
                        options=team_ids,
                        format_func=lambda x: team_options.get(x, "A definir") if x else "A definir",
                        index=current_team2_idx
                    )
                    
                    # Hora
                    new_time = st.time_input("Horário", value=match.datetime.time())
                
                # Cidade
                new_city = st.text_input("Cidade", value=match.city or "")
                
                if st.form_submit_button("💾 Salvar Alterações"):
                    match.team1_id = new_team1
                    match.team2_id = new_team2
                    match.datetime = datetime.combine(new_date, new_time)
                    match.city = new_city
                    
                    # Atualiza códigos
                    if new_team1:
                        team1 = session.query(Team).get(new_team1)
                        match.team1_code = team1.code if team1 else None
                    if new_team2:
                        team2 = session.query(Team).get(new_team2)
                        match.team2_code = team2.code if team2 else None
                    
                    session.commit()
                    st.success("Jogo atualizado!")
                    st.rerun()


def admin_resultados(session):
    """Lançamento de resultados"""
    st.subheader("📝 Lançar Resultados")
    
    # Jogos pendentes de resultado
    jogos_pendentes = session.query(Match).filter(
        Match.status == 'scheduled',
        Match.team1_id.isnot(None),
        Match.team2_id.isnot(None)
    ).order_by(Match.datetime).all()
    
    if not jogos_pendentes:
        st.info("Nenhum jogo pendente de resultado.")
    else:
        st.markdown(f"**Jogos pendentes:** {len(jogos_pendentes)}")
        
        for match in jogos_pendentes:
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
    
    st.divider()
    
    # Jogos já finalizados (para correção)
    st.subheader("📋 Jogos Finalizados")
    
    jogos_finalizados = session.query(Match).filter(
        Match.status == 'finished'
    ).order_by(Match.datetime.desc()).limit(10).all()
    
    for match in jogos_finalizados:
        team1_display = get_team_display(match.team1, match.team1_code)
        team2_display = get_team_display(match.team2, match.team2_code)
        
        st.markdown(f"#{match.match_number} - {team1_display} **{match.team1_score}** x **{match.team2_score}** {team2_display}")


def admin_grupos(session):
    """Definir classificados dos grupos"""
    st.subheader("🏅 Classificados dos Grupos")
    st.info("Defina os classificados de cada grupo após o término da fase de grupos")
    
    teams = session.query(Team).order_by(Team.name).all()
    
    for grupo in GRUPOS:
        grupo_teams = [t for t in teams if t.group == grupo]
        
        if not grupo_teams:
            continue
        
        # Busca resultado existente
        result = session.query(GroupResult).filter_by(group_name=grupo).first()
        
        with st.expander(f"Grupo {grupo}"):
            team_options = {t.id: f"{t.flag} {t.name}" for t in grupo_teams}
            team_ids = [None] + [t.id for t in grupo_teams]
            
            with st.form(f"group_result_{grupo}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    primeiro = st.selectbox(
                        "1º Lugar",
                        options=team_ids,
                        format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                        index=team_ids.index(result.first_place_team_id) if result and result.first_place_team_id in team_ids else 0,
                        key=f"gr_primeiro_{grupo}"
                    )
                
                with col2:
                    segundo = st.selectbox(
                        "2º Lugar",
                        options=team_ids,
                        format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                        index=team_ids.index(result.second_place_team_id) if result and result.second_place_team_id in team_ids else 0,
                        key=f"gr_segundo_{grupo}"
                    )
                
                if st.form_submit_button("💾 Salvar e Calcular Pontos"):
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
                        st.rerun()
                    else:
                        st.error("Selecione dois times diferentes!")


def admin_podio(session):
    """Definir pódio oficial"""
    st.subheader("🏆 Pódio Oficial")
    st.info("Defina o pódio oficial após o término da Copa")
    
    teams = session.query(Team).order_by(Team.name).all()
    team_options = {t.id: f"{t.flag} {t.name}" for t in teams}
    team_ids = [None] + [t.id for t in teams]
    
    # Busca resultados existentes
    campeao = session.query(TournamentResult).filter_by(result_type='champion').first()
    vice = session.query(TournamentResult).filter_by(result_type='runner_up').first()
    terceiro = session.query(TournamentResult).filter_by(result_type='third_place').first()
    
    with st.form("podium_result_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("### 🥇 Campeão")
            new_campeao = st.selectbox(
                "Selecione o Campeão",
                options=team_ids,
                format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                index=team_ids.index(campeao.team_id) if campeao and campeao.team_id in team_ids else 0
            )
        
        with col2:
            st.markdown("### 🥈 Vice-Campeão")
            new_vice = st.selectbox(
                "Selecione o Vice",
                options=team_ids,
                format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                index=team_ids.index(vice.team_id) if vice and vice.team_id in team_ids else 0
            )
        
        with col3:
            st.markdown("### 🥉 3º Lugar")
            new_terceiro = st.selectbox(
                "Selecione o 3º Lugar",
                options=team_ids,
                format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                index=team_ids.index(terceiro.team_id) if terceiro and terceiro.team_id in team_ids else 0
            )
        
        if st.form_submit_button("💾 Salvar Pódio e Calcular Pontos"):
            if new_campeao and new_vice and new_terceiro:
                if len(set([new_campeao, new_vice, new_terceiro])) != 3:
                    st.error("Selecione três times diferentes!")
                else:
                    # Salva ou atualiza resultados
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
                    
                    st.success("Pódio oficial salvo e pontuação calculada!")
                    st.rerun()
            else:
                st.warning("Selecione todos os três lugares!")


def admin_pontuacao(session):
    """Configuração de pontuação"""
    st.subheader("⭐ Configuração de Pontuação")
    
    # Pontuação por jogo
    st.markdown("### Pontuação por Jogo")
    
    scoring_configs = [
        ("pontos_placar_exato", "Placar Exato (acertou tudo)", 20),
        ("pontos_resultado_gols", "Resultado + Gols de um time", 15),
        ("pontos_resultado", "Apenas Resultado (vitória/empate)", 10),
        ("pontos_gols", "Apenas Gols de um time", 5),
        ("pontos_nenhum", "Nenhum acerto", 0),
    ]
    
    with st.form("scoring_form"):
        for key, label, default in scoring_configs:
            current = get_config_value(session, key, str(default))
            st.number_input(label, min_value=0, max_value=100, value=int(current), key=f"cfg_{key}")
        
        if st.form_submit_button("💾 Salvar Pontuação de Jogos"):
            for key, label, default in scoring_configs:
                value = st.session_state[f"cfg_{key}"]
                set_config_value(session, key, value, label, 'pontuacao')
            st.success("Pontuação salva!")
    
    st.divider()
    
    # Pontuação de grupos
    st.markdown("### Pontuação de Classificação dos Grupos")
    
    group_configs = [
        ("grupo_ordem_correta", "Acertou os 2 na ordem correta", 20),
        ("grupo_ordem_invertida", "Acertou os 2 em ordem invertida", 10),
        ("grupo_um_certo", "Acertou apenas 1 na posição errada", 5),
    ]
    
    with st.form("group_scoring_form"):
        for key, label, default in group_configs:
            current = get_config_value(session, key, str(default))
            st.number_input(label, min_value=0, max_value=100, value=int(current), key=f"cfg_{key}")
        
        if st.form_submit_button("💾 Salvar Pontuação de Grupos"):
            for key, label, default in group_configs:
                value = st.session_state[f"cfg_{key}"]
                set_config_value(session, key, value, label, 'grupo')
            st.success("Pontuação de grupos salva!")
    
    st.divider()
    
    # Pontuação de pódio
    st.markdown("### Pontuação de Pódio")
    
    podium_configs = [
        ("podio_completo", "Acertou Campeão, Vice e 3º na ordem", 150),
        ("podio_campeao", "Acertou o Campeão", 100),
        ("podio_vice", "Acertou o Vice-Campeão", 50),
        ("podio_terceiro", "Acertou o 3º Lugar", 30),
        ("podio_fora_ordem", "Acertou posição fora de ordem", 20),
    ]
    
    with st.form("podium_scoring_form"):
        for key, label, default in podium_configs:
            current = get_config_value(session, key, str(default))
            st.number_input(label, min_value=0, max_value=500, value=int(current), key=f"cfg_{key}")
        
        if st.form_submit_button("💾 Salvar Pontuação de Pódio"):
            for key, label, default in podium_configs:
                value = st.session_state[f"cfg_{key}"]
                set_config_value(session, key, value, label, 'podio')
            st.success("Pontuação de pódio salva!")
    
    st.divider()
    
    # Data de início da Copa
    st.markdown("### Data de Início da Copa")
    st.info("Os palpites de pódio serão bloqueados após esta data/hora")
    
    current_date = get_config_value(session, 'data_inicio_copa', '')
    
    with st.form("copa_start_form"):
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Data", value=datetime.strptime(current_date.split()[0], "%Y-%m-%d").date() if current_date else datetime(2026, 6, 11).date())
        with col2:
            start_time = st.time_input("Hora", value=datetime.strptime(current_date.split()[1], "%H:%M").time() if current_date and len(current_date.split()) > 1 else datetime.strptime("13:00", "%H:%M").time())
        
        if st.form_submit_button("💾 Salvar Data de Início"):
            date_str = f"{start_date.strftime('%Y-%m-%d')} {start_time.strftime('%H:%M')}"
            set_config_value(session, 'data_inicio_copa', date_str, 'Data de início da Copa', 'sistema')
            st.success(f"Data de início salva: {date_str}")


def admin_premiacao(session):
    """Configuração de premiação"""
    st.subheader("💰 Configuração de Premiação")
    
    premiacao_configs = [
        ("premiacao_valor_inscricao", "Valor da Inscrição (R$)", "0"),
        ("premiacao_primeiro", "Prêmio 1º Lugar", "A definir"),
        ("premiacao_segundo", "Prêmio 2º Lugar", "A definir"),
        ("premiacao_terceiro", "Prêmio 3º Lugar", "A definir"),
        ("premiacao_observacoes", "Observações", ""),
    ]
    
    with st.form("premiacao_form"):
        for key, label, default in premiacao_configs:
            current = get_config_value(session, key, default)
            if key == "premiacao_observacoes":
                st.text_area(label, value=current, key=f"cfg_{key}")
            else:
                st.text_input(label, value=current, key=f"cfg_{key}")
        
        if st.form_submit_button("💾 Salvar Premiação"):
            for key, label, default in premiacao_configs:
                value = st.session_state[f"cfg_{key}"]
                set_config_value(session, key, value, label, 'premiacao')
            st.success("Premiação salva!")


def admin_palpites(session):
    """Gerenciamento de palpites de todos os usuários"""
    st.subheader("📋 Gerenciar Palpites")
    st.warning("⚠️ Use com cuidado! Aqui você pode editar os palpites de qualquer participante.")
    
    # Seleciona usuário
    users = session.query(User).filter(User.role == 'player').order_by(User.name).all()
    
    if not users:
        st.info("Nenhum participante cadastrado.")
        return
    
    user_options = {u.id: u.name for u in users}
    selected_user_id = st.selectbox(
        "Selecione o Participante",
        options=list(user_options.keys()),
        format_func=lambda x: user_options.get(x)
    )
    
    if selected_user_id:
        st.divider()
        
        # Tabs para diferentes tipos de palpites
        tabs = st.tabs(["⚽ Jogos", "🏅 Grupos", "🏆 Pódio"])
        
        # Tab: Palpites de Jogos
        with tabs[0]:
            st.markdown(f"### Palpites de Jogos - {user_options[selected_user_id]}")
            
            matches = session.query(Match).order_by(Match.datetime).all()
            
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
        
        # Tab: Palpites de Grupos
        with tabs[1]:
            st.markdown(f"### Palpites de Grupos - {user_options[selected_user_id]}")
            
            teams = session.query(Team).order_by(Team.name).all()
            
            for grupo in GRUPOS:
                grupo_teams = [t for t in teams if t.group == grupo]
                if not grupo_teams:
                    continue
                
                pred = session.query(GroupPrediction).filter_by(
                    user_id=selected_user_id,
                    group_name=grupo
                ).first()
                
                with st.expander(f"Grupo {grupo}"):
                    team_options = {t.id: f"{t.flag} {t.name}" for t in grupo_teams}
                    team_ids = [None] + [t.id for t in grupo_teams]
                    
                    with st.form(f"admin_group_{grupo}_{selected_user_id}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            primeiro = st.selectbox(
                                "1º Lugar",
                                options=team_ids,
                                format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                                index=team_ids.index(pred.first_place_team_id) if pred and pred.first_place_team_id in team_ids else 0,
                                key=f"admin_gp1_{grupo}_{selected_user_id}"
                            )
                        
                        with col2:
                            segundo = st.selectbox(
                                "2º Lugar",
                                options=team_ids,
                                format_func=lambda x: team_options.get(x, "Selecione") if x else "Selecione",
                                index=team_ids.index(pred.second_place_team_id) if pred and pred.second_place_team_id in team_ids else 0,
                                key=f"admin_gp2_{grupo}_{selected_user_id}"
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
                                st.success("Salvo!")
        
        # Tab: Palpites de Pódio
        with tabs[2]:
            st.markdown(f"### Palpite de Pódio - {user_options[selected_user_id]}")
            
            teams = session.query(Team).order_by(Team.name).all()
            team_options = {t.id: f"{t.flag} {t.name}" for t in teams}
            team_ids = [None] + [t.id for t in teams]
            
            pred = session.query(PodiumPrediction).filter_by(user_id=selected_user_id).first()
            
            with st.form(f"admin_podium_{selected_user_id}"):
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
                        "🥈 Vice",
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
            
            # Menu de navegação
            menu_options = {
                "🏠 Início": "home",
                "📝 Palpites - Jogos": "palpites_jogos",
                "🏅 Palpites - Grupos": "palpites_grupos",
                "🏆 Palpites - Pódio": "palpites_podio",
                "📊 Ranking": "ranking",
                "📈 Estatísticas": "estatisticas",
                "⚙️ Configurações": "configuracoes",
            }
            
            if st.session_state.user['role'] == 'admin':
                menu_options["🔧 Admin"] = "admin"
            
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
