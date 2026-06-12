"""
Módulo de resumo diário do Bolão Copa do Mundo 2026
Gera resumos automáticos com resultados, pontuadores e variações de ranking
"""

from datetime import datetime, timedelta
import pytz
from sqlalchemy import and_
from models import Match, Prediction, User
from scoring import get_ranking, get_scoring_config, calculate_match_points


def get_brazil_time():
    """Retorna o horário atual no Brasil"""
    brazil_tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(brazil_tz)


def get_matches_by_date(session, target_date=None):
    """
    Retorna jogos de uma data específica.
    
    Args:
        session: Sessão do banco de dados
        target_date: Data alvo (datetime). Se None, usa hoje.
        
    Returns:
        Lista de jogos da data
    """
    if target_date is None:
        target_date = get_brazil_time()
    
    # Define início e fim do dia
    brazil_tz = pytz.timezone('America/Sao_Paulo')
    start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Converte para UTC para comparar com banco
    start_utc = start_of_day.astimezone(pytz.UTC)
    end_utc = end_of_day.astimezone(pytz.UTC)
    
    matches = session.query(Match).filter(
        and_(
            Match.datetime >= start_utc,
            Match.datetime <= end_utc
        )
    ).order_by(Match.datetime).all()
    
    return matches


def get_daily_scorers(session, target_date=None):
    """
    Retorna os maiores e menores pontuadores do dia.
    
    Args:
        session: Sessão do banco de dados
        target_date: Data alvo (datetime). Se None, usa hoje.
        
    Returns:
        Dicionário com top e bottom scorers
    """
    matches = get_matches_by_date(session, target_date)
    
    if not matches:
        return {'top': [], 'bottom': []}
    
    # Filtra apenas jogos finalizados
    finished_matches = [m for m in matches if m.status == 'finished' and m.team1_score is not None]
    
    if not finished_matches:
        return {'top': [], 'bottom': []}
    
    match_ids = [m.id for m in finished_matches]
    
    # Calcula pontos de cada usuário nos jogos do dia
    users = session.query(User).filter_by(active=True).filter(User.role != 'admin').all()
    
    user_points = []
    
    for user in users:
        predictions = session.query(Prediction).filter(
            and_(
                Prediction.user_id == user.id,
                Prediction.match_id.in_(match_ids)
            )
        ).all()
        
        total_points = sum(p.points_awarded or 0 for p in predictions)
        
        user_points.append({
            'user_id': user.id,
            'user_name': user.name,
            'points': total_points,
            'predictions_count': len(predictions)
        })
    
    # Ordena por pontos
    user_points.sort(key=lambda x: x['points'], reverse=True)
    
    # Top 3 e Bottom 3
    top_scorers = user_points[:3]
    bottom_scorers = user_points[-3:] if len(user_points) > 3 else []
    bottom_scorers.reverse()  # Inverte para mostrar do pior para o menos pior
    
    return {
        'top': top_scorers,
        'bottom': bottom_scorers
    }


def calculate_ranking_changes(session, target_date=None):
    """
    Calcula as maiores variações de ranking do dia selecionado.

    Compara duas "fotos" reais do ranking acumulado:
    - posição ao FIM do dia anterior (jogos até a meia-noite do dia selecionado)
    - posição ao FIM do dia selecionado
    Assim a variação se mantém consistente de um dia para o outro, mesmo
    consultando datas passadas.

    Args:
        session: Sessão do banco de dados
        target_date: Data alvo (datetime). Se None, usa hoje.

    Returns:
        Lista com maiores subidas e quedas
    """
    if target_date is None:
        target_date = get_brazil_time()

    # Normaliza para naive em horário de Brasília (padrão do banco)
    brazil_tz = pytz.timezone('America/Sao_Paulo')
    if target_date.tzinfo is not None:
        target_date = target_date.astimezone(brazil_tz).replace(tzinfo=None)

    day_start = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    # Pontos do dia de TODOS os participantes (não só top/bottom 3)
    matches = get_matches_by_date(session, target_date)
    finished_matches = [m for m in matches if m.status == 'finished' and m.team1_score is not None]

    if not finished_matches:
        return {'gains': [], 'losses': []}

    from collections import defaultdict
    match_ids = [m.id for m in finished_matches]
    daily_points_map = defaultdict(int)
    for pred in session.query(Prediction).filter(Prediction.match_id.in_(match_ids)).all():
        daily_points_map[pred.user_id] += pred.points_awarded or 0

    # Fotos reais do ranking (mesmos critérios oficiais de desempate)
    previous_ranking = get_ranking(session, cutoff_datetime=day_start)
    current_ranking = get_ranking(session, cutoff_datetime=day_end)

    previous_positions = {r['user_id']: r['posicao'] for r in previous_ranking}
    current_positions = {r['user_id']: r['posicao'] for r in current_ranking}

    # Calcula variações
    changes = []
    for user_data in current_ranking:
        user_id = user_data['user_id']
        prev_pos = previous_positions.get(user_id)
        curr_pos = current_positions.get(user_id)
        if prev_pos is None or curr_pos is None:
            continue
        variation = prev_pos - curr_pos

        if variation != 0:
            changes.append({
                'user_id': user_id,
                'user_name': user_data['nome'],
                'previous_position': prev_pos,
                'current_position': curr_pos,
                'variation': variation,
                'daily_points': daily_points_map.get(user_id, 0)
            })
    
    # Separa em ganhos e perdas
    gains = [c for c in changes if c['variation'] > 0]
    losses = [c for c in changes if c['variation'] < 0]
    
    # Ordena por magnitude da variação
    gains.sort(key=lambda x: x['variation'], reverse=True)
    losses.sort(key=lambda x: abs(x['variation']), reverse=True)
    
    return {
        'gains': gains[:5],  # Top 5 maiores subidas
        'losses': losses[:5]  # Top 5 maiores quedas
    }


def generate_daily_summary(session, target_date=None, format_type='rich'):
    """
    Gera resumo diário completo.
    
    Args:
        session: Sessão do banco de dados
        target_date: Data alvo (datetime). Se None, usa hoje.
        format_type: 'rich' (com emojis e formatação) ou 'plain' (texto simples)
        
    Returns:
        String com o resumo formatado
    """
    if target_date is None:
        target_date = get_brazil_time()
    
    # Pega dados
    matches = get_matches_by_date(session, target_date)
    scorers = get_daily_scorers(session, target_date)
    changes = calculate_ranking_changes(session, target_date)
    
    # Filtra jogos finalizados
    finished_matches = [m for m in matches if m.status == 'finished' and m.team1_score is not None]
    
    # Formata data
    date_str = target_date.strftime('%d/%m/%Y')
    
    # Monta resumo
    if format_type == 'rich':
        summary = f"📅 *RESUMO DO DIA - {date_str}*\n"
        summary += "=" * 40 + "\n\n"
    else:
        summary = f"RESUMO DO DIA - {date_str}\n"
        summary += "=" * 40 + "\n\n"
    
    # Resultados dos jogos
    if finished_matches:
        if format_type == 'rich':
            summary += "⚽ *RESULTADOS DOS JOGOS*\n\n"
        else:
            summary += "RESULTADOS DOS JOGOS\n\n"
        
        for match in finished_matches:
            team1 = match.get_team1_display()
            team2 = match.get_team2_display()
            score = f"{match.team1_score} x {match.team2_score}"
            
            if format_type == 'rich':
                summary += f"🏟️ {team1} *{score}* {team2}\n"
            else:
                summary += f"   {team1} {score} {team2}\n"
        
        summary += "\n"
    else:
        summary += "Nenhum jogo finalizado hoje.\n\n"
    
    # Maiores pontuadores
    if scorers['top']:
        if format_type == 'rich':
            summary += "🏆 *MAIORES PONTUADORES DO DIA*\n\n"
        else:
            summary += "MAIORES PONTUADORES DO DIA\n\n"
        
        medals = ['🥇', '🥈', '🥉']
        for i, scorer in enumerate(scorers['top']):
            medal = medals[i] if i < 3 and format_type == 'rich' else f"{i+1}."
            if format_type == 'rich':
                summary += f"{medal} *{scorer['user_name']}* - {scorer['points']} pontos\n"
            else:
                summary += f"{medal} {scorer['user_name']} - {scorer['points']} pontos\n"
        
        summary += "\n"
    
    # Menores pontuadores
    if scorers['bottom']:
        if format_type == 'rich':
            summary += "📉 *MENORES PONTUADORES DO DIA*\n\n"
        else:
            summary += "MENORES PONTUADORES DO DIA\n\n"
        
        for scorer in scorers['bottom']:
            if format_type == 'rich':
                summary += f"• {scorer['user_name']} - {scorer['points']} pontos\n"
            else:
                summary += f"  {scorer['user_name']} - {scorer['points']} pontos\n"
        
        summary += "\n"
    
    # Variações no ranking
    if changes['gains']:
        if format_type == 'rich':
            summary += "📈 *MAIORES SUBIDAS NO RANKING*\n\n"
        else:
            summary += "MAIORES SUBIDAS NO RANKING\n\n"
        
        for change in changes['gains']:
            if format_type == 'rich':
                summary += f"⬆️ *{change['user_name']}* subiu {change['variation']} posições "
                summary += f"({change['previous_position']}º → {change['current_position']}º) "
                summary += f"com {change['daily_points']} pontos\n"
            else:
                summary += f"  {change['user_name']} subiu {change['variation']} posições "
                summary += f"({change['previous_position']}º -> {change['current_position']}º)\n"
        
        summary += "\n"
    
    if changes['losses']:
        if format_type == 'rich':
            summary += "📉 *MAIORES QUEDAS NO RANKING*\n\n"
        else:
            summary += "MAIORES QUEDAS NO RANKING\n\n"
        
        for change in changes['losses']:
            if format_type == 'rich':
                summary += f"⬇️ *{change['user_name']}* caiu {abs(change['variation'])} posições "
                summary += f"({change['previous_position']}º → {change['current_position']}º) "
                summary += f"com {change['daily_points']} pontos\n"
            else:
                summary += f"  {change['user_name']} caiu {abs(change['variation'])} posições "
                summary += f"({change['previous_position']}º -> {change['current_position']}º)\n"
        
        summary += "\n"
    
    # Rodapé
    if format_type == 'rich':
        summary += "=" * 40 + "\n"
        summary += "🏆 *Bolão Copa do Mundo 2026*\n"
        summary += f"Gerado em {get_brazil_time().strftime('%d/%m/%Y às %H:%M')}"
    else:
        summary += "=" * 40 + "\n"
        summary += "Bolão Copa do Mundo 2026\n"
        summary += f"Gerado em {get_brazil_time().strftime('%d/%m/%Y às %H:%M')}"
    
    return summary


def generate_ranking_text(session, format_type='rich'):
    """
    Gera a classificação atual completa do bolão, formatada para WhatsApp.

    Args:
        session: Sessão do banco de dados
        format_type: 'rich' (com emojis e formatação) ou 'plain' (texto simples)

    Returns:
        String com a classificação formatada
    """
    ranking = get_ranking(session)
    date_str = get_brazil_time().strftime('%d/%m/%Y')

    if format_type == 'rich':
        text = f"🏆 *CLASSIFICAÇÃO ATUAL - {date_str}*\n"
    else:
        text = f"CLASSIFICACAO ATUAL - {date_str}\n"
    text += "=" * 40 + "\n\n"

    if not ranking:
        text += "Nenhum participante pontuou ainda.\n\n"
    else:
        medals = ['🥇', '🥈', '🥉']
        for r in ranking:
            pos = r['posicao']
            if format_type == 'rich':
                marker = medals[pos - 1] if pos <= 3 else f"*{pos}º*"
                text += f"{marker} *{r['nome']}* — {r['total_pontos']} pts"
                if r['placares_exatos'] > 0:
                    text += f" ({r['placares_exatos']} exato{'s' if r['placares_exatos'] > 1 else ''})"
                text += "\n"
            else:
                text += f"{pos}. {r['nome']} - {r['total_pontos']} pts\n"

    text += "\n"
    if format_type == 'rich':
        text += "=" * 40 + "\n"
        text += "🏆 *Bolão Copa do Mundo 2026*\n"
        text += f"Gerado em {get_brazil_time().strftime('%d/%m/%Y às %H:%M')}"
    else:
        text += "=" * 40 + "\n"
        text += "Bolão Copa do Mundo 2026\n"
        text += f"Gerado em {get_brazil_time().strftime('%d/%m/%Y às %H:%M')}"

    return text


def format_for_whatsapp(summary_text):
    """
    Formata o resumo para WhatsApp (mantém formatação rica).
    
    Args:
        summary_text: Texto do resumo
        
    Returns:
        Texto formatado para WhatsApp
    """
    # WhatsApp suporta *negrito*, _itálico_, ~riscado~
    # O texto já está formatado, apenas retorna
    return summary_text
