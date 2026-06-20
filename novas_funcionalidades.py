"""
Novas funcionalidades do Bolão Copa do Mundo 2026
- Timer regressivo
- Gráfico de evolução do ranking
- Sistema de medalhas/conquistas
- Melhor palpite da rodada
- Comparativo entre participantes
- Página de regras e pontuação
- Estatísticas gerais
- Exportar ranking em PDF
- Backup do banco
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pytz
import json
import os
import shutil
from sqlalchemy import func, desc

from models import (
    User, Match, Prediction, Team, Config,
    GroupPrediction, PodiumPrediction, TournamentResult, GroupResult
)
from scoring import get_ranking, get_user_stats, get_scoring_config, calculate_match_points


# =============================================================================
# 1. TIMER REGRESSIVO
# =============================================================================
def render_countdown_timer():
    """
    Renderiza timer regressivo para o início da Copa do Mundo 2026.
    Data de abertura: 11 de junho de 2026, 16:00 (Brasília)
    """
    st.markdown("""
    <style>
        .countdown-container {
            background: linear-gradient(135deg, #1E3A5F 0%, #2A398D 100%);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            margin: 15px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .countdown-title {
            color: #FFD700 !important;
            font-size: 1.1rem !important;
            font-weight: 700 !important;
            margin-bottom: 10px !important;
            letter-spacing: 2px !important;
        }
        .countdown-boxes {
            display: flex;
            justify-content: center;
            gap: 10px;
            flex-wrap: wrap;
        }
        .countdown-box {
            background: rgba(255,255,255,0.15);
            border-radius: 10px;
            padding: 10px 15px;
            min-width: 65px;
        }
        .countdown-number {
            font-size: 1.8rem !important;
            font-weight: 800 !important;
            color: #ffffff !important;
            display: block !important;
        }
        .countdown-label {
            font-size: 0.7rem !important;
            color: #FFD700 !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
        }
        .countdown-started {
            color: #2ECC71 !important;
            font-size: 1.3rem !important;
            font-weight: 700 !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Data de início da Copa: 11/06/2026 16:00 (Brasília)
    tz_brazil = pytz.timezone('America/Sao_Paulo')
    copa_start = tz_brazil.localize(datetime(2026, 6, 11, 16, 0, 0))
    now = datetime.now(tz_brazil)
    
    diff = copa_start - now
    
    if diff.total_seconds() <= 0:
        st.markdown("""
        <div class="countdown-container">
            <div class="countdown-started">🏆 A COPA DO MUNDO 2026 COMEÇOU! ⚽</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        days = diff.days
        hours, remainder = divmod(diff.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        st.markdown(f"""
        <div class="countdown-container">
            <div class="countdown-title">⏳ FALTAM PARA A COPA DO MUNDO 2026</div>
            <div class="countdown-boxes">
                <div class="countdown-box">
                    <span class="countdown-number">{days}</span>
                    <span class="countdown-label">Dias</span>
                </div>
                <div class="countdown-box">
                    <span class="countdown-number">{hours:02d}</span>
                    <span class="countdown-label">Horas</span>
                </div>
                <div class="countdown-box">
                    <span class="countdown-number">{minutes:02d}</span>
                    <span class="countdown-label">Min</span>
                </div>
                <div class="countdown-box">
                    <span class="countdown-number">{seconds:02d}</span>
                    <span class="countdown-label">Seg</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_next_match_countdown(session):
    """
    Renderiza timer regressivo para o próximo jogo com palpites abertos.
    """
    tz_brazil = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(tz_brazil).replace(tzinfo=None)
    
    next_match = session.query(Match).filter(
        Match.status == 'scheduled',
        Match.datetime > now
    ).order_by(Match.datetime).first()
    
    if not next_match:
        return
    
    diff = next_match.datetime - now
    
    if diff.total_seconds() <= 0:
        return
    
    days = diff.days
    hours, remainder = divmod(diff.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    
    team1_name = next_match.team1.name if next_match.team1 else next_match.team1_code
    team2_name = next_match.team2.name if next_match.team2 else next_match.team2_code
    team1_flag = next_match.team1.flag if next_match.team1 else "🏳️"
    team2_flag = next_match.team2.flag if next_match.team2 else "🏳️"
    
    time_str = ""
    if days > 0:
        time_str = f"{days}d {hours:02d}h {minutes:02d}m"
    else:
        time_str = f"{hours:02d}h {minutes:02d}m"
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #2ECC71 0%, #27AE60 100%);
        border-radius: 10px;
        padding: 12px 15px;
        text-align: center;
        margin: 10px 0;
    ">
        <div style="color: #fff; font-size: 0.8rem; font-weight: 600; margin-bottom: 5px;">
            ⏰ PRÓXIMO JOGO EM {time_str}
        </div>
        <div style="color: #fff; font-size: 1rem; font-weight: 700;">
            {team1_flag} {team1_name} vs {team2_name} {team2_flag}
        </div>
        <div style="color: rgba(255,255,255,0.8); font-size: 0.75rem;">
            {next_match.datetime.strftime('%d/%m/%Y às %H:%M')} | 📍 {next_match.city}
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# 2. GRÁFICO DE EVOLUÇÃO DO RANKING
# =============================================================================
def render_ranking_evolution_chart(session):
    """
    Gráfico mostrando a evolução de posição de cada participante ao longo da competição.
    Agrupa por rodada (data) e mostra a posição de cada um.
    """
    st.subheader("📈 Evolução no Ranking")
    
    tz_brazil = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(tz_brazil).replace(tzinfo=None)
    
    # Busca jogos finalizados com placar, ordenados por data
    matches_finished = session.query(Match).filter(
        Match.datetime <= now,
        Match.team1_score.isnot(None),
        Match.team2_score.isnot(None)
    ).order_by(Match.datetime).all()
    
    if not matches_finished:
        st.info("📊 Ainda não há jogos finalizados para mostrar a evolução.")
        return
    
    # Agrupa jogos por data
    matches_by_date = {}
    for m in matches_finished:
        date_key = m.datetime.strftime('%d/%m')
        if date_key not in matches_by_date:
            matches_by_date[date_key] = []
        matches_by_date[date_key].append(m)
    
    # Busca todos os participantes ativos
    users = session.query(User).filter_by(active=True).filter(User.role != 'admin').all()
    
    if not users:
        st.info("Nenhum participante encontrado.")
        return
    
    config = get_scoring_config(session)
    
    # Para cada data, calcula o ranking acumulado até aquele ponto
    dates = list(matches_by_date.keys())
    user_positions = {u.id: {'name': u.name, 'positions': []} for u in users}
    
    cumulative_points = {u.id: 0 for u in users}
    
    for date_key in dates:
        # Soma pontos dos jogos desta data
        for match in matches_by_date[date_key]:
            for user in users:
                pred = session.query(Prediction).filter_by(
                    user_id=user.id,
                    match_id=match.id
                ).first()
                
                if pred and match.team1_score is not None and match.team2_score is not None:
                    points, _, _ = calculate_match_points(
                        pred.pred_team1_score, pred.pred_team2_score,
                        match.team1_score, match.team2_score,
                        config
                    )
                    cumulative_points[user.id] += points
        
        # Calcula ranking nesta data
        sorted_users = sorted(cumulative_points.items(), key=lambda x: -x[1])
        for pos, (uid, pts) in enumerate(sorted_users, 1):
            user_positions[uid]['positions'].append(pos)
    
    if not dates or len(dates) < 1:
        st.info("📊 Dados insuficientes para o gráfico de evolução.")
        return
    
    # Gráfico de linhas com:
    # - a linha do usuário logado sempre em destaque (grossa e colorida)
    # - demais linhas em cinza-claro ao fundo (sem poluição visual)
    # - nome de cada participante escrito na ponta direita da sua linha
    #   (posições finais são únicas, então os nomes não se sobrepõem)
    # - seletor para destacar outros participantes para comparação
    n_users = len(users)
    _session_user = st.session_state.get('user') or {}
    try:
        current_user_id = int(_session_user.get('id'))
    except (TypeError, ValueError):
        current_user_id = None

    all_names = [user_positions[u.id]['name'] for u in users]
    highlighted = st.multiselect(
        "🔦 Destacar participantes para comparar",
        all_names,
        key="rank_evo_highlight",
        help="Sua linha já aparece destacada automaticamente"
    )

    if current_user_id not in user_positions:
        st.caption(
            "💡 Conta logada não participa do ranking (ex.: admin) — "
            "use o seletor acima para destacar participantes."
        )

    fig = go.Figure()

    colors = px.colors.qualitative.Dark24
    DIM_COLOR = 'rgba(170,170,170,0.45)'
    USER_COLOR = '#E61D25'  # vermelho da identidade visual da Copa

    for i, (uid, data) in enumerate(user_positions.items()):
        is_current_user = (uid == current_user_id)
        is_highlighted = is_current_user or data['name'] in highlighted

        if is_current_user:
            color = USER_COLOR
        elif is_highlighted:
            color = colors[i % len(colors)]
        else:
            color = DIM_COLOR

        fig.add_trace(go.Scatter(
            x=dates,
            y=data['positions'],
            mode='lines+markers' if is_highlighted else 'lines',
            name=data['name'],
            line=dict(width=4 if is_highlighted else 1.5, color=color),
            marker=dict(size=8, color=color),
            showlegend=False,
            hovertemplate=f"<b>{data['name']}</b><br>%{{x}} — %{{y}}º lugar<extra></extra>"
        ))

        # Nome na ponta direita da linha
        label = data['name'] if is_highlighted else data['name'].split()[0]
        fig.add_annotation(
            x=dates[-1],
            y=data['positions'][-1],
            text=f"<b>{label} (você)</b>" if is_current_user else (f"<b>{label}</b>" if is_highlighted else label),
            xanchor='left',
            xshift=8,
            showarrow=False,
            font=dict(
                size=12 if is_highlighted else 10,
                color=color if is_highlighted else '#555555'
            )
        )

    fig.update_layout(
        yaxis=dict(
            autorange=False,
            range=[n_users + 0.5, 0.5],  # 1º lugar no topo
            tickmode='array',
            tickvals=list(range(1, n_users + 1)),
            ticktext=[f"{p}º" for p in range(1, n_users + 1)],
            title=None,
            fixedrange=True,
            tickfont=dict(size=11, color='#1a1a2e')
        ),
        xaxis=dict(title=None, fixedrange=True, tickfont=dict(size=11, color='#1a1a2e')),
        hovermode='closest',
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=max(480, 26 * n_users + 60),
        margin=dict(l=10, r=110, t=10, b=10)
    )

    fig.update_xaxes(showgrid=True, gridcolor='rgba(200,200,200,0.3)')
    fig.update_yaxes(showgrid=True, gridcolor='rgba(200,200,200,0.3)')

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={'displayModeBar': False}
    )


# =============================================================================
# 3. SISTEMA DE MEDALHAS E CONQUISTAS
# =============================================================================
def get_user_achievements(session, user_id):
    """
    Retorna o catálogo COMPLETO de conquistas, cada uma com:
    - icon, title, color
    - criteria: o que é preciso fazer para conquistar
    - unlocked: se o participante já conquistou
    - progress: progresso atual rumo à meta (ex.: "2/3")
    """
    tz_brazil = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(tz_brazil).replace(tzinfo=None)

    # Busca palpites do usuário em jogos com resultado
    matches_with_score = session.query(Match).filter(
        Match.datetime <= now,
        Match.team1_score.isnot(None),
        Match.team2_score.isnot(None)
    ).all()
    match_by_id = {m.id: m for m in matches_with_score}
    match_ids = set(match_by_id.keys())

    predictions = session.query(Prediction).filter(
        Prediction.user_id == user_id,
        Prediction.match_id.in_(match_ids) if match_ids else False
    ).all()

    config = get_scoring_config(session)

    # Contadores
    placares_exatos = 0
    resultados_corretos = 0
    sequencia_atual = 0
    maior_sequencia = 0
    total_pontos_jogos = 0

    # Ordena palpites pela data do jogo (para calcular sequência)
    pred_with_match = [(p, match_by_id[p.match_id]) for p in predictions if p.match_id in match_by_id]
    pred_with_match.sort(key=lambda x: x[1].datetime)

    for pred, match in pred_with_match:
        points, points_type, _ = calculate_match_points(
            pred.pred_team1_score, pred.pred_team2_score,
            match.team1_score, match.team2_score,
            config
        )
        total_pontos_jogos += points

        if points_type == 'placar_exato':
            placares_exatos += 1
            resultados_corretos += 1
            sequencia_atual += 1
        elif points_type in ('resultado_gols', 'resultado'):
            resultados_corretos += 1
            sequencia_atual += 1
        else:
            sequencia_atual = 0

        maior_sequencia = max(maior_sequencia, sequencia_atual)

    # Palpites feitos em todos os jogos já iniciados
    total_matches = session.query(Match).filter(Match.datetime <= now).count()
    total_preds = session.query(Prediction).filter_by(user_id=user_id).count()

    # Catálogo completo: (atual, meta) definem progresso e desbloqueio
    catalogo = [
        ('🎯', 'Sniper', 'Acerte 1 placar exato', '#E74C3C', placares_exatos, 1),
        ('🔥', 'Em Chamas', 'Acerte 3 placares exatos', '#E67E22', placares_exatos, 3),
        ('💎', 'Diamante', 'Acerte 5 placares exatos', '#3498DB', placares_exatos, 5),
        ('👑', 'Rei dos Placares', 'Acerte 10 placares exatos', '#FFD700', placares_exatos, 10),
        ('⚡', 'Sequência de Fogo', 'Acerte 3 jogos seguidos', '#F39C12', maior_sequencia, 3),
        ('🌟', 'Imbatível', 'Acerte 5 jogos seguidos', '#9B59B6', maior_sequencia, 5),
        ('🏅', 'Consistente', 'Acerte o resultado de 10 jogos', '#2ECC71', resultados_corretos, 10),
        ('⭐', 'Meio Centenário', 'Some 50 pontos em jogos', '#1ABC9C', total_pontos_jogos, 50),
        ('💯', 'Centenário', 'Some 100 pontos em jogos', '#E74C3C', total_pontos_jogos, 100),
        ('📝', 'Dedicado', 'Faça palpite em todos os jogos já realizados', '#2980B9',
         total_preds if total_matches > 0 else 0, max(total_matches, 1)),
    ]

    achievements = []
    for icon, title, criteria, color, atual, meta in catalogo:
        unlocked = atual >= meta
        achievements.append({
            'icon': icon,
            'title': title,
            'criteria': criteria,
            'color': color,
            'unlocked': unlocked,
            'progress': f'{min(atual, meta)}/{meta}',
        })

    return achievements


def render_achievements(session, user_id):
    """Renderiza a galeria de conquistas: as obtidas em destaque e as
    ainda bloqueadas em cinza, sempre mostrando o critério de cada uma."""
    achievements = get_user_achievements(session, user_id)

    conquistadas = sum(1 for a in achievements if a['unlocked'])
    st.caption(
        f"🏅 Você desbloqueou **{conquistadas} de {len(achievements)}** conquistas. "
        "As cinzas mostram o que falta para conquistá-las."
    )

    st.markdown("""
    <style>
        .achievement-card {
            display: flex;
            align-items: center;
            gap: 12px;
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 12px;
            padding: 12px 16px;
            margin: 6px 0;
            border-left: 5px solid;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .achievement-card.locked { background: #fbfcfd; opacity: 0.7; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
        .achievement-card.locked .achievement-icon { filter: grayscale(100%); opacity: 0.45; }
        .achievement-icon { font-size: 1.9rem; line-height: 1; }
        .achievement-info { display: flex; flex-direction: column; }
        .achievement-title { font-weight: 700; font-size: 0.92rem; color: #1a1a2e; }
        .achievement-card.locked .achievement-title { color: #6b7280; }
        .achievement-criteria { font-size: 0.78rem; color: #555; }
        .achievement-status { font-size: 0.72rem; font-weight: 600; }
        .achievement-status.done { color: #2e7d32; }
        .achievement-status.todo { color: #8a8f98; }
    </style>
    """, unsafe_allow_html=True)

    # Conquistadas primeiro, mantendo a ordem do catálogo dentro de cada grupo
    achievements = sorted(achievements, key=lambda a: not a['unlocked'])

    for ach in achievements:
        if ach['unlocked']:
            card_class = "achievement-card"
            border = ach['color']
            status = '<span class="achievement-status done">✅ Conquistada</span>'
        else:
            card_class = "achievement-card locked"
            border = "#c9ccd1"
            status = f'<span class="achievement-status todo">🔒 Progresso: {ach["progress"]}</span>'

        # HTML em uma única linha: evita que o Streamlit interprete a
        # indentação como bloco de código (markdown).
        html = (
            f'<div class="{card_class}" style="border-left-color: {border};">'
            f'<span class="achievement-icon">{ach["icon"]}</span>'
            f'<div class="achievement-info">'
            f'<span class="achievement-title">{ach["title"]}</span>'
            f'<span class="achievement-criteria">{ach["criteria"]}</span>'
            f'{status}'
            f'</div></div>'
        )
        st.markdown(html, unsafe_allow_html=True)


# =============================================================================
# 4. MELHOR PALPITE DA RODADA
# =============================================================================
def get_best_predictions_by_round(session):
    """
    Retorna, para cada rodada (data de jogos finalizados), os melhores E os
    piores palpites. Em caso de empate, todos os empatados são incluídos.

    Cada item: {date, num_matches, best: {points, users:[{name, exatos}]},
                worst: {points, users:[{name, exatos}]} ou None}.
    """
    tz_brazil = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(tz_brazil).replace(tzinfo=None)

    # Busca jogos finalizados
    matches = session.query(Match).filter(
        Match.datetime <= now,
        Match.team1_score.isnot(None),
        Match.team2_score.isnot(None)
    ).order_by(Match.datetime).all()

    if not matches:
        return []

    # Agrupa por data
    matches_by_date = {}
    for m in matches:
        date_key = m.datetime.strftime('%d/%m/%Y')
        matches_by_date.setdefault(date_key, []).append(m)

    config = get_scoring_config(session)
    users = session.query(User).filter_by(active=True).filter(User.role != 'admin').all()

    results = []

    for date_key, date_matches in matches_by_date.items():
        match_ids = [m.id for m in date_matches]
        match_by_id = {m.id: m for m in date_matches}

        # Busca todos os palpites desses jogos de uma vez (evita N+1)
        preds = session.query(Prediction).filter(
            Prediction.match_id.in_(match_ids)
        ).all()
        preds_by_user = {}
        for p in preds:
            preds_by_user.setdefault(p.user_id, []).append(p)

        # Calcula pontos/exatos de cada participante que palpitou na rodada
        scored = []
        for user in users:
            user_preds = preds_by_user.get(user.id, [])
            if not user_preds:
                continue
            user_points = 0
            user_exatos = 0
            for p in user_preds:
                m = match_by_id[p.match_id]
                points, ptype, _ = calculate_match_points(
                    p.pred_team1_score, p.pred_team2_score,
                    m.team1_score, m.team2_score, config
                )
                user_points += points
                if ptype == 'placar_exato':
                    user_exatos += 1
            scored.append({'name': user.name, 'points': user_points, 'exatos': user_exatos})

        if not scored:
            continue

        best_points = max(s['points'] for s in scored)
        worst_points = min(s['points'] for s in scored)

        # Só destaca melhor se alguém efetivamente pontuou
        if best_points <= 0:
            continue

        best_users = [
            {'name': s['name'], 'exatos': s['exatos']}
            for s in scored if s['points'] == best_points
        ]

        # Pior só faz sentido se não for o mesmo grupo dos melhores
        worst = None
        if worst_points < best_points:
            worst = {
                'points': worst_points,
                'users': [
                    {'name': s['name'], 'exatos': s['exatos']}
                    for s in scored if s['points'] == worst_points
                ],
            }

        results.append({
            'date': date_key,
            'num_matches': len(date_matches),
            'best': {'points': best_points, 'users': best_users},
            'worst': worst,
        })

    return results


def _render_prediction_cards(users, points, accent, bg_gradient, icon):
    """Renderiza cards de participantes lado a lado (flex), um por pessoa.
    HTML em uma linha por elemento para evitar interpretação como código."""
    cards = []
    for u in users:
        exatos = (
            f'<span style="margin-left:6px;font-size:0.72rem;color:#555;">🎯 {u["exatos"]} exato(s)</span>'
            if u.get('exatos') else ''
        )
        cards.append(
            f'<div style="flex:1 1 160px;min-width:150px;background:{bg_gradient};'
            f'border-left:4px solid {accent};border-radius:10px;padding:10px 14px;">'
            f'<div style="font-weight:700;color:#1a1a2e;font-size:0.95rem;">{icon} {u["name"]}</div>'
            f'<div style="margin-top:4px;"><span style="background:{accent};color:#1a1a2e;'
            f'padding:2px 10px;border-radius:14px;font-weight:700;font-size:0.8rem;">{points} pts</span>'
            f'{exatos}</div></div>'
        )
    html = f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin:4px 0 12px 0;">{"".join(cards)}</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_best_predictions(session):
    """Renderiza os melhores e piores palpites da rodada escolhida."""
    st.subheader("🌟 Destaques da Rodada")

    results = get_best_predictions_by_round(session)

    if not results:
        st.info("Ainda não há rodadas finalizadas.")
        return

    results_desc = list(reversed(results))  # mais recente primeiro
    date_options = [r['date'] for r in results_desc]

    selected_date = st.selectbox(
        "Escolha o dia",
        date_options,
        index=0,
        key="destaques_rodada_data",
    )

    r = next(r for r in results_desc if r['date'] == selected_date)

    st.markdown(
        f'<div style="font-weight:700;color:#1a1a2e;margin-top:6px;">📅 {r["date"]} '
        f'<span style="color:#666;font-size:0.8rem;font-weight:400;">({r["num_matches"]} jogos)</span></div>',
        unsafe_allow_html=True,
    )

    plural_melhor = "Melhores palpites" if len(r['best']['users']) > 1 else "Melhor palpite"
    st.markdown(
        f'<div style="font-size:0.82rem;color:#856404;font-weight:600;margin:2px 0;">🏆 {plural_melhor}</div>',
        unsafe_allow_html=True,
    )
    _render_prediction_cards(
        r['best']['users'], r['best']['points'],
        accent='#FFD700', bg_gradient='linear-gradient(135deg,#fffef5 0%,#fff3cd 100%)', icon='🏆'
    )

    if r['worst']:
        plural_pior = "Piores palpites" if len(r['worst']['users']) > 1 else "Pior palpite"
        st.markdown(
            f'<div style="font-size:0.82rem;color:#721c24;font-weight:600;margin:2px 0;">🥶 {plural_pior}</div>',
            unsafe_allow_html=True,
        )
        _render_prediction_cards(
            r['worst']['users'], r['worst']['points'],
            accent='#E68A8A', bg_gradient='linear-gradient(135deg,#fff8f8 0%,#ffe3e3 100%)', icon='🥶'
        )


# =============================================================================
# 5. COMPARATIVO ENTRE PARTICIPANTES
# =============================================================================
def render_comparison(session):
    """Permite selecionar 2 participantes e comparar palpites lado a lado."""
    st.subheader("🔄 Comparar Participantes")
    
    users = session.query(User).filter_by(active=True).filter(User.role != 'admin').order_by(User.name).all()
    
    if len(users) < 2:
        st.info("É necessário pelo menos 2 participantes para comparar.")
        return
    
    user_options = {u.id: u.name for u in users}

    col1, col2 = st.columns(2)

    with col1:
        user1_id = st.selectbox(
            "Participante 1",
            list(user_options.keys()),
            format_func=lambda uid: user_options[uid],
            key="comp_user1"
        )

    with col2:
        user2_ids = [uid for uid in user_options if uid != user1_id]
        user2_id = st.selectbox(
            "Participante 2",
            user2_ids,
            format_func=lambda uid: user_options[uid],
            key="comp_user2"
        )

    if st.button("🔍 Comparar", key="btn_compare"):
        st.session_state["comp_show"] = True
        st.session_state["comp_user1_sel"] = user1_id
        st.session_state["comp_user2_sel"] = user2_id

    # Usa session_state em vez do retorno do botão, que so e True no instante
    # do clique -- sem isso, qualquer interacao depois (ex: o checkbox "ver
    # todos os jogos") recarrega a pagina e o bloco inteiro desaparece.
    if st.session_state.get("comp_show"):
        user1_id = st.session_state.get("comp_user1_sel", user1_id)
        user2_id = st.session_state.get("comp_user2_sel", user2_id)

        stats1 = get_user_stats(session, user1_id)
        stats2 = get_user_stats(session, user2_id)

        ranking = get_ranking(session)
        pos1 = next((r['posicao'] for r in ranking if r['user_id'] == user1_id), '-')
        pos2 = next((r['posicao'] for r in ranking if r['user_id'] == user2_id), '-')
        
        # Tabela comparativa
        st.markdown(f"""
        <style>
            .comp-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }}
            .comp-table th {{
                background: #1E3A5F;
                color: white !important;
                padding: 10px;
                text-align: center;
                font-size: 0.9rem;
            }}
            .comp-table td {{
                padding: 8px 12px;
                text-align: center;
                border-bottom: 1px solid #eee;
                font-size: 0.85rem;
            }}
            .comp-table tr:hover {{
                background: #f8f9fa;
            }}
            .comp-winner {{
                font-weight: 700;
                color: #2ECC71;
            }}
        </style>
        <table class="comp-table">
            <tr>
                <th>{user_options[user1_id]}</th>
                <th>Estatística</th>
                <th>{user_options[user2_id]}</th>
            </tr>
            <tr>
                <td class="{'comp-winner' if isinstance(pos1, int) and isinstance(pos2, int) and pos1 < pos2 else ''}">{pos1}º</td>
                <td><strong>Posição no Ranking</strong></td>
                <td class="{'comp-winner' if isinstance(pos1, int) and isinstance(pos2, int) and pos2 < pos1 else ''}">{pos2}º</td>
            </tr>
            <tr>
                <td class="{'comp-winner' if stats1['total_pontos'] > stats2['total_pontos'] else ''}">{stats1['total_pontos']}</td>
                <td><strong>Total de Pontos</strong></td>
                <td class="{'comp-winner' if stats2['total_pontos'] > stats1['total_pontos'] else ''}">{stats2['total_pontos']}</td>
            </tr>
            <tr>
                <td class="{'comp-winner' if stats1['placares_exatos'] > stats2['placares_exatos'] else ''}">{stats1['placares_exatos']}</td>
                <td><strong>Placares Exatos</strong></td>
                <td class="{'comp-winner' if stats2['placares_exatos'] > stats1['placares_exatos'] else ''}">{stats2['placares_exatos']}</td>
            </tr>
            <tr>
                <td class="{'comp-winner' if stats1['resultados_corretos'] > stats2['resultados_corretos'] else ''}">{stats1['resultados_corretos']}</td>
                <td><strong>Resultados Corretos (total)</strong></td>
                <td class="{'comp-winner' if stats2['resultados_corretos'] > stats1['resultados_corretos'] else ''}">{stats2['resultados_corretos']}</td>
            </tr>
            <tr>
                <td class="{'comp-winner' if stats1['resultado_puro'] > stats2['resultado_puro'] else ''}">{stats1['resultado_puro']}</td>
                <td><strong>↳ Resultado Correto (sem gols)</strong></td>
                <td class="{'comp-winner' if stats2['resultado_puro'] > stats1['resultado_puro'] else ''}">{stats2['resultado_puro']}</td>
            </tr>
            <tr>
                <td class="{'comp-winner' if stats1['resultado_gols'] > stats2['resultado_gols'] else ''}">{stats1['resultado_gols']}</td>
                <td><strong>↳ Resultado + Gols de um Time</strong></td>
                <td class="{'comp-winner' if stats2['resultado_gols'] > stats1['resultado_gols'] else ''}">{stats2['resultado_gols']}</td>
            </tr>
            <tr>
                <td class="{'comp-winner' if stats1['pontos_grupos'] > stats2['pontos_grupos'] else ''}">{stats1['pontos_grupos']}</td>
                <td><strong>Pontos de Grupos</strong></td>
                <td class="{'comp-winner' if stats2['pontos_grupos'] > stats1['pontos_grupos'] else ''}">{stats2['pontos_grupos']}</td>
            </tr>
            <tr>
                <td class="{'comp-winner' if stats1['pontos_podio'] > stats2['pontos_podio'] else ''}">{stats1['pontos_podio']}</td>
                <td><strong>Pontos de Pódio</strong></td>
                <td class="{'comp-winner' if stats2['pontos_podio'] > stats1['pontos_podio'] else ''}">{stats2['pontos_podio']}</td>
            </tr>
            <tr>
                <td>{stats1['total_palpites']}</td>
                <td><strong>Total de Palpites</strong></td>
                <td>{stats2['total_palpites']}</td>
            </tr>
        </table>
        """, unsafe_allow_html=True)
        
        # Comparação jogo a jogo
        st.markdown("#### Palpites Jogo a Jogo")

        tz_brazil = pytz.timezone('America/Sao_Paulo')
        now = datetime.now(tz_brazil).replace(tzinfo=None)

        total_jogos_realizados = session.query(Match).filter(
            Match.datetime <= now,
            Match.team1_score.isnot(None),
            Match.team2_score.isnot(None)
        ).count()

        ver_todos = False
        if total_jogos_realizados > 20:
            st.caption(f"Mostrando os 20 jogos mais recentes de {total_jogos_realizados} já realizados.")
            ver_todos = st.checkbox("Ver todos os jogos", key="comp_ver_todos")

        matches_query = session.query(Match).filter(
            Match.datetime <= now,
            Match.team1_score.isnot(None),
            Match.team2_score.isnot(None)
        ).order_by(desc(Match.datetime))
        matches = matches_query.all() if ver_todos else matches_query.limit(20).all()

        for match in matches:
            pred1 = session.query(Prediction).filter_by(user_id=user1_id, match_id=match.id).first()
            pred2 = session.query(Prediction).filter_by(user_id=user2_id, match_id=match.id).first()
            
            t1 = match.team1.flag + " " + match.team1.name if match.team1 else match.team1_code
            t2 = match.team2.flag + " " + match.team2.name if match.team2 else match.team2_code
            
            p1_text = f"{pred1.pred_team1_score}x{pred1.pred_team2_score}" if pred1 else "—"
            p2_text = f"{pred2.pred_team1_score}x{pred2.pred_team2_score}" if pred2 else "—"
            
            pts1 = pred1.points_awarded if pred1 else 0
            pts2 = pred2.points_awarded if pred2 else 0
            
            result_text = f"{match.team1_score}x{match.team2_score}"
            
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 12px;
                margin: 4px 0;
                background: #f8f9fa;
                border-radius: 8px;
                font-size: 0.85rem;
                flex-wrap: wrap;
                gap: 5px;
            ">
                <span style="{'font-weight:700; color:#2ECC71;' if pts1 > pts2 else ''}">{p1_text} ({pts1}pts)</span>
                <span style="font-weight: 600; color: #1E3A5F;">{t1} <strong>{result_text}</strong> {t2}</span>
                <span style="{'font-weight:700; color:#2ECC71;' if pts2 > pts1 else ''}">{p2_text} ({pts2}pts)</span>
            </div>
            """, unsafe_allow_html=True)


# =============================================================================
# 6. PÁGINA DE REGRAS E PONTUAÇÃO
# =============================================================================
def page_regras(get_session_func, engine):
    """Página dedicada explicando o sistema de pontuação."""
    st.header("📋 Regras e Sistema de Pontuação")
    
    session = get_session_func(engine)
    try:
        config = get_scoring_config(session)
    finally:
        session.close()
    
    # Pontuação de Jogos
    st.subheader("⚽ Pontuação por Jogo")
    
    st.markdown(f"""
    A cada jogo da Copa do Mundo, você pode ganhar pontos conforme a precisão do seu palpite.
    Os pontos são cumulativos e quanto mais preciso o palpite, maior a pontuação.
    
    | Tipo de Acerto | Pontos | Exemplo |
    |---|---|---|
    | **Placar Exato** | **{config['placar_exato']} pts** | Palpite: 2x1, Resultado: 2x1 |
    | **Resultado + Gols de um time** | **{config['resultado_gols']} pts** | Palpite: 2x1, Resultado: 2x0 (acertou gols do time 1 + vitória) |
    | **Resultado Correto** | **{config['resultado']} pts** | Palpite: 2x1, Resultado: 3x0 (acertou vitória do time 1) |
    | **Gols de um time** | **{config['gols']} pts** | Palpite: 2x1, Resultado: 2x3 (acertou gols do time 1, mas errou resultado) |
    | **Nenhum acerto** | **{config['nenhum']} pts** | Errou tudo |
    """)
    
    st.divider()
    
    # Pontuação de Grupos
    st.subheader("🏅 Pontuação por Classificação de Grupo")
    
    st.markdown(f"""
    Antes do início da Copa, você deve palpitar quem será o 1º e o 2º colocado de cada grupo.
    
    | Tipo de Acerto | Pontos |
    |---|---|
    | **Acertou 1º e 2º na ordem correta** | **{config['grupo_ordem_correta']} pts** |
    | **Acertou os 2 classificados (ordem invertida)** | **{config['grupo_ordem_invertida']} pts** |
    | **Acertou apenas 1 classificado** | **{config['grupo_um_certo']} pts** |
    """)
    
    st.divider()
    
    # Pontuação do Pódio
    st.subheader("🏆 Pontuação do Pódio")
    
    st.markdown(f"""
    Antes do início da Copa, você deve palpitar o Campeão, Vice-Campeão e 3º Lugar.
    
    | Tipo de Acerto | Pontos |
    |---|---|
    | **Pódio completo na ordem exata** | **{config['podio_completo']} pts** |
    | **Acertou o Campeão** | **{config['podio_campeao']} pts** |
    | **Acertou o Vice-Campeão** | **{config['podio_vice']} pts** |
    | **Acertou o 3º Lugar** | **{config['podio_terceiro']} pts** |
    | **Acertou seleção no pódio (posição errada)** | **{config['podio_fora_ordem']} pts** |
    
    > **Nota:** Os pontos do pódio são cumulativos. Por exemplo, se você acertar o Campeão e o Vice, 
    > ganha os pontos de ambos.
    """)
    
    st.divider()
    
    # Critérios de Desempate
    st.subheader("⚖️ Critérios de Desempate")
    
    st.markdown("""
    Em caso de empate na pontuação total, os seguintes critérios são aplicados em ordem:
    
    | Prioridade | Critério |
    |---|---|
    | 1º | Maior pontuação total |
    | 2º | Maior número de placares exatos (20 pts) |
    | 3º | Maior número de acertos de resultado + gols (15 pts) |
    | 4º | Maior número de acertos de resultado (10 pts) |
    | 5º | Maior número de acertos de classificados no grupo |
    | 6º | Maior número de acertos de pódio |
    | 7º | Maior número de acertos de gols de um time (5 pts) |
    | 8º | Menos palpites zerados |
    | 9º | Ordem de inscrição (quem se inscreveu primeiro) |
    """)
    
    st.divider()
    
    # Regras Gerais
    st.subheader("📌 Regras Gerais")
    
    st.markdown("""
    **Prazos para palpites:**
    - Os palpites de cada jogo são bloqueados automaticamente no horário de início da partida.
    - Os palpites de classificação dos grupos e do pódio são bloqueados antes do início da Copa.
    - Você pode alterar seus palpites quantas vezes quiser antes do prazo.
    
    **Importante:**
    - Todos os horários são no fuso horário de Brasília (GMT-3).
    - Palpite não salvo até o início do jogo é registrado automaticamente como **0 x 0** (o valor padrão da tela de palpites).
    - Em caso de jogo decidido nos pênaltis, o resultado considerado é o do tempo regulamentar/prorrogação.
    """)


# =============================================================================
# 7. ESTATÍSTICAS GERAIS
# =============================================================================
def render_general_stats(session):
    """Página com estatísticas gerais do bolão."""
    st.header("📊 Estatísticas Gerais do Bolão")
    
    tz_brazil = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(tz_brazil).replace(tzinfo=None)
    
    # Seleção mais apostada como campeã
    st.subheader("🏆 Seleção Mais Apostada como Campeã")
    
    champion_counts = session.query(
        Team.name, Team.flag,
        func.count(PodiumPrediction.id).label('count')
    ).join(
        PodiumPrediction, PodiumPrediction.champion_team_id == Team.id
    ).group_by(Team.name, Team.flag).order_by(desc('count')).all()
    
    if champion_counts:
        total_preds = sum(c.count for c in champion_counts)
        
        for i, c in enumerate(champion_counts[:10]):
            pct = (c.count / total_preds * 100) if total_preds > 0 else 0
            bar_width = pct
            
            medal = ""
            if i == 0:
                medal = "🥇 "
            elif i == 1:
                medal = "🥈 "
            elif i == 2:
                medal = "🥉 "
            
            st.markdown(f"""
            <div style="margin: 6px 0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                    <span style="font-weight: 600; font-size: 0.9rem;">{medal}{c.flag} {c.name}</span>
                    <span style="font-weight: 700; color: #1E3A5F;">{c.count} ({pct:.0f}%)</span>
                </div>
                <div style="background: #e9ecef; border-radius: 5px; height: 8px; overflow: hidden;">
                    <div style="background: linear-gradient(90deg, #FFD700, #FFA500); width: {bar_width}%; height: 100%; border-radius: 5px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhum palpite de campeão registrado.")
    
    st.divider()
    
    # Placar mais repetido nos palpites
    st.subheader("📝 Placares Mais Apostados")
    
    placar_counts = session.query(
        Prediction.pred_team1_score,
        Prediction.pred_team2_score,
        func.count(Prediction.id).label('count')
    ).group_by(
        Prediction.pred_team1_score,
        Prediction.pred_team2_score
    ).order_by(desc('count')).limit(10).all()
    
    if placar_counts:
        for i, p in enumerate(placar_counts):
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 12px;
                margin: 4px 0;
                background: {'#fff3cd' if i == 0 else '#f8f9fa'};
                border-radius: 8px;
                border-left: 3px solid {'#FFD700' if i == 0 else '#dee2e6'};
            ">
                <span style="font-weight: 700; font-size: 1.1rem; color: #1E3A5F;">
                    {p.pred_team1_score} x {p.pred_team2_score}
                </span>
                <span style="color: #666; font-size: 0.85rem;">
                    {p.count} palpites
                </span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhum palpite registrado.")
    
    st.divider()
    
    # Média de acertos
    st.subheader("📈 Médias Gerais")
    
    users = session.query(User).filter_by(active=True).filter(User.role != 'admin').all()
    
    if users:
        total_pontos = 0
        total_exatos = 0
        total_resultados = 0
        
        for user in users:
            stats = get_user_stats(session, user.id)
            total_pontos += stats['total_pontos']
            total_exatos += stats['placares_exatos']
            total_resultados += stats['resultados_corretos']
        
        n = len(users)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Média de Pontos", f"{total_pontos / n:.1f}")
        with col2:
            st.metric("Média de Placares Exatos", f"{total_exatos / n:.1f}")
        with col3:
            st.metric("Média de Resultados Corretos", f"{total_resultados / n:.1f}")
    
    st.divider()
    
    # Jogos com mais acertos
    st.subheader("🎯 Jogos com Mais Placares Exatos")
    
    matches_with_exatos = session.query(
        Match,
        func.count(Prediction.id).label('exatos')
    ).join(
        Prediction, Prediction.match_id == Match.id
    ).filter(
        Prediction.points_type == 'placar_exato',
        Match.team1_score.isnot(None)
    ).group_by(Match.id).order_by(desc('exatos')).limit(5).all()
    
    if matches_with_exatos:
        for match, exatos in matches_with_exatos:
            t1 = f"{match.team1.flag} {match.team1.name}" if match.team1 else match.team1_code
            t2 = f"{match.team2.flag} {match.team2.name}" if match.team2 else match.team2_code
            
            st.markdown(f"""
            <div style="
                padding: 8px 12px;
                margin: 4px 0;
                background: #f8f9fa;
                border-radius: 8px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
            ">
                <span style="font-weight: 600;">{t1} {match.team1_score}x{match.team2_score} {t2}</span>
                <span style="color: #2ECC71; font-weight: 700;">🎯 {exatos} placar(es) exato(s)</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Nenhum placar exato registrado ainda.")


# =============================================================================
# 8. EXPORTAR RANKING EM PDF
# =============================================================================
def export_ranking_pdf(session):
    """Gera PDF do ranking atual."""
    from fpdf import FPDF
    
    ranking = get_ranking(session)
    
    if not ranking:
        st.warning("Nenhum dado no ranking para exportar.")
        return None
    
    pdf = FPDF()
    pdf.add_page()
    
    # Título
    pdf.set_font('Helvetica', 'B', 18)
    pdf.cell(0, 15, 'Ranking - Bolao Copa do Mundo 2026', ln=True, align='C')
    
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 8, f'Atualizado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}', ln=True, align='C')
    pdf.ln(10)
    
    # Cabeçalho da tabela
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_fill_color(30, 58, 95)  # #1E3A5F
    pdf.set_text_color(255, 255, 255)
    
    col_widths = [15, 60, 30, 25, 25, 25]
    headers = ['#', 'Participante', 'Pontos', 'Exatos', 'Result.', 'Gols']
    
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, border=1, fill=True, align='C')
    pdf.ln()
    
    # Dados
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(0, 0, 0)
    
    for r in ranking:
        # Cor de fundo alternada
        if r['posicao'] % 2 == 0:
            pdf.set_fill_color(245, 245, 245)
        else:
            pdf.set_fill_color(255, 255, 255)
        
        # Medalha
        pos_text = str(r['posicao'])
        if r['posicao'] == 1:
            pos_text = "1o"
        elif r['posicao'] == 2:
            pos_text = "2o"
        elif r['posicao'] == 3:
            pos_text = "3o"
        
        row_data = [
            pos_text,
            r['nome'],
            str(r['total_pontos']),
            str(r['placares_exatos']),
            str(r['resultados_corretos']),
            str(r['gols'])
        ]
        
        for i, data in enumerate(row_data):
            align = 'C' if i != 1 else 'L'
            pdf.cell(col_widths[i], 7, data, border=1, fill=True, align=align)
        pdf.ln()
    
    # Rodapé
    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.cell(0, 5, 'Bolao Copa do Mundo 2026 - FIFA World Cup 2026', ln=True, align='C')
    
    # Salva em arquivo temporário
    pdf_path = '/tmp/ranking_bolao_copa2026.pdf'
    pdf.output(pdf_path)
    
    return pdf_path


# =============================================================================
# 9. BACKUP DO BANCO DE DADOS
# =============================================================================
def admin_backup_database(session):
    """Interface de backup do banco de dados para admin."""
    st.subheader("💾 Backup do Banco de Dados")
    
    st.markdown("""
    Faça backup dos dados do bolão para garantir a segurança das informações.
    O backup inclui todos os participantes, palpites, resultados e configurações.
    """)
    
    if st.button("📥 Gerar Backup Agora", key="btn_backup"):
        try:
            backup_data = generate_backup(session)
            
            # Salva como JSON
            backup_filename = f"backup_bolao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_path = f"/tmp/{backup_filename}"
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2, default=str)
            
            with open(backup_path, 'rb') as f:
                st.download_button(
                    label="⬇️ Baixar Backup",
                    data=f,
                    file_name=backup_filename,
                    mime="application/json"
                )
            
            st.success(f"✅ Backup gerado com sucesso! ({backup_filename})")
            
            # Estatísticas do backup
            st.markdown(f"""
            **Resumo do Backup:**
            - Participantes: {len(backup_data.get('users', []))}
            - Palpites de jogos: {len(backup_data.get('predictions', []))}
            - Palpites de grupos: {len(backup_data.get('group_predictions', []))}
            - Palpites de pódio: {len(backup_data.get('podium_predictions', []))}
            - Jogos: {len(backup_data.get('matches', []))}
            - Configurações: {len(backup_data.get('configs', []))}
            """)
            
        except Exception as e:
            st.error(f"Erro ao gerar backup: {str(e)}")


def generate_backup(session):
    """Gera dados de backup em formato JSON."""
    from models import User, Match, Prediction, Team, Config, GroupPrediction, PodiumPrediction
    
    backup = {
        'generated_at': datetime.now().isoformat(),
        'version': '1.0',
        'users': [],
        'teams': [],
        'matches': [],
        'predictions': [],
        'group_predictions': [],
        'podium_predictions': [],
        'configs': []
    }
    
    # Usuários
    for u in session.query(User).all():
        backup['users'].append({
            'id': u.id, 'name': u.name, 'username': u.username,
            'role': u.role, 'active': u.active, 'created_at': str(u.created_at)
        })
    
    # Times
    for t in session.query(Team).all():
        backup['teams'].append({
            'id': t.id, 'name': t.name, 'code': t.code,
            'group': t.group, 'flag': t.flag
        })
    
    # Jogos
    for m in session.query(Match).all():
        backup['matches'].append({
            'id': m.id, 'match_number': m.match_number,
            'team1_code': m.team1_code, 'team2_code': m.team2_code,
            'datetime': str(m.datetime), 'city': m.city,
            'phase': m.phase, 'group': m.group,
            'status': m.status,
            'team1_score': m.team1_score, 'team2_score': m.team2_score
        })
    
    # Palpites
    for p in session.query(Prediction).all():
        backup['predictions'].append({
            'id': p.id, 'user_id': p.user_id, 'match_id': p.match_id,
            'pred_team1_score': p.pred_team1_score,
            'pred_team2_score': p.pred_team2_score,
            'points_awarded': p.points_awarded,
            'points_type': p.points_type
        })
    
    # Palpites de grupos
    for gp in session.query(GroupPrediction).all():
        backup['group_predictions'].append({
            'id': gp.id, 'user_id': gp.user_id,
            'group_name': gp.group_name,
            'first_place_team_id': gp.first_place_team_id,
            'second_place_team_id': gp.second_place_team_id,
            'points_awarded': gp.points_awarded
        })
    
    # Palpites de pódio
    for pp in session.query(PodiumPrediction).all():
        backup['podium_predictions'].append({
            'id': pp.id, 'user_id': pp.user_id,
            'champion_team_id': pp.champion_team_id,
            'runner_up_team_id': pp.runner_up_team_id,
            'third_place_team_id': pp.third_place_team_id,
            'points_awarded': pp.points_awarded
        })
    
    # Configurações
    for c in session.query(Config).all():
        backup['configs'].append({
            'id': c.id, 'key': c.key, 'value': c.value,
            'description': c.description, 'category': c.category
        })
    
    return backup
