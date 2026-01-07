"""
Módulo de pontuação ao vivo para visualização em tempo real
Calcula pontos temporários e variação de ranking durante os jogos
"""

from sqlalchemy import desc
from models import User, Match, Prediction
from scoring import calculate_match_points, get_scoring_config, get_ranking


def get_live_match_predictions(session, match_id: int) -> list:
    """
    Retorna todos os palpites para um jogo específico com pontuação ao vivo.
    
    Args:
        session: Sessão do banco de dados
        match_id: ID do jogo
        
    Returns:
        Lista de dicionários com informações dos palpites e pontos
    """
    match = session.query(Match).filter_by(id=match_id).first()
    
    if not match:
        return []
    
    # Pega configuração de pontos
    config = get_scoring_config(session)
    
    # Pega todos os palpites para este jogo
    predictions = session.query(Prediction).filter_by(match_id=match_id).all()
    
    results = []
    
    for pred in predictions:
        user = session.query(User).filter_by(id=pred.user_id).first()
        
        if not user or not user.active or user.role == 'admin':
            continue
        
        # Calcula pontos com o placar atual (mesmo que temporário)
        points = 0
        points_type = 'nenhum'
        breakdown = 'Aguardando resultado'
        
        if match.team1_score is not None and match.team2_score is not None:
            points, points_type, breakdown = calculate_match_points(
                pred.pred_team1_score,
                pred.pred_team2_score,
                match.team1_score,
                match.team2_score,
                config
            )
        
        results.append({
            'user_id': user.id,
            'user_name': user.name,
            'prediction': f"{pred.pred_team1_score} x {pred.pred_team2_score}",
            'pred_team1_score': pred.pred_team1_score,
            'pred_team2_score': pred.pred_team2_score,
            'points': points,
            'points_type': points_type,
            'breakdown': breakdown
        })
    
    # Ordena por pontos (maior primeiro)
    results.sort(key=lambda x: x['points'], reverse=True)
    
    return results


def calculate_live_ranking(session, match_id: int = None) -> list:
    """
    Calcula o ranking considerando o resultado atual de um jogo em andamento.
    
    Args:
        session: Sessão do banco de dados
        match_id: ID do jogo em andamento (opcional)
        
    Returns:
        Lista com ranking atualizado incluindo variação de posição
    """
    # Pega ranking atual (sem o jogo em andamento)
    current_ranking = get_ranking(session)
    
    # Se não há jogo especificado, retorna ranking atual
    if not match_id:
        for i, user_data in enumerate(current_ranking):
            user_data['posicao_atual'] = i + 1
            user_data['posicao_anterior'] = i + 1
            user_data['variacao'] = 0
        return current_ranking
    
    # Pega o jogo
    match = session.query(Match).filter_by(id=match_id).first()
    
    if not match or match.team1_score is None or match.team2_score is None:
        # Sem placar, retorna ranking atual
        for i, user_data in enumerate(current_ranking):
            user_data['posicao_atual'] = i + 1
            user_data['posicao_anterior'] = i + 1
            user_data['variacao'] = 0
        return current_ranking
    
    # Guarda posições anteriores
    posicoes_anteriores = {user_data['user_id']: i + 1 for i, user_data in enumerate(current_ranking)}
    
    # Pega configuração de pontos
    config = get_scoring_config(session)
    
    # Calcula pontos adicionais para cada usuário neste jogo
    predictions = session.query(Prediction).filter_by(match_id=match_id).all()
    
    pontos_adicionais = {}
    for pred in predictions:
        points, _, _ = calculate_match_points(
            pred.pred_team1_score,
            pred.pred_team2_score,
            match.team1_score,
            match.team2_score,
            config
        )
        pontos_adicionais[pred.user_id] = points
    
    # Atualiza pontuação total temporária
    for user_data in current_ranking:
        user_id = user_data['user_id']
        pontos_jogo = pontos_adicionais.get(user_id, 0)
        
        # Subtrai pontos já contabilizados deste jogo (se houver)
        pred_existente = session.query(Prediction).filter_by(
            user_id=user_id, 
            match_id=match_id
        ).first()
        
        if pred_existente and pred_existente.points_awarded:
            pontos_jogo -= pred_existente.points_awarded
        
        user_data['pontos_jogo_atual'] = pontos_adicionais.get(user_id, 0)
        user_data['total_pontos_temp'] = user_data['total_pontos'] + pontos_jogo
    
    # Reordena por pontuação temporária
    current_ranking.sort(key=lambda x: (
        x['total_pontos_temp'],
        x['placares_exatos'],
        x['resultado_gols'],
        x['resultado'],
        x['gols'],
        -x['zeros'],
        -x['user_id']
    ), reverse=True)
    
    # Calcula variação de posição
    for i, user_data in enumerate(current_ranking):
        user_data['posicao_atual'] = i + 1
        user_data['posicao_anterior'] = posicoes_anteriores.get(user_data['user_id'], i + 1)
        user_data['variacao'] = user_data['posicao_anterior'] - user_data['posicao_atual']
    
    return current_ranking


def get_ongoing_matches(session) -> list:
    """
    Retorna lista de jogos do dia atual (em andamento ou finalizados).
    Só mostra jogos cujo horário de início seja no dia de hoje.
    
    Returns:
        Lista de jogos com status e informações
    """
    from datetime import datetime, timedelta
    import pytz
    
    # Timezone do Brasil
    brazil_tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(brazil_tz)
    
    # Início e fim do dia atual (meia-noite a meia-noite)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    # Converte para UTC para comparar com banco
    today_start_utc = today_start.astimezone(pytz.UTC)
    today_end_utc = today_end.astimezone(pytz.UTC)
    
    # Pega apenas jogos do dia atual que já começaram
    matches = session.query(Match).filter(
        Match.datetime >= today_start_utc,
        Match.datetime < today_end_utc,
        Match.datetime <= now.astimezone(pytz.UTC)  # Já começou
    ).order_by(Match.datetime.desc()).all()
    
    result = []
    
    for match in matches:
        # Converte datetime para timezone do Brasil
        match_time_utc = match.datetime.replace(tzinfo=pytz.UTC)
        match_time_br = match_time_utc.astimezone(brazil_tz)
        
        # Determina se o jogo está em andamento
        time_since_start = now - match_time_br
        
        # Jogo em andamento: começou há menos de 2 horas e não está finalizado
        is_live = (
            time_since_start.total_seconds() > 0 and 
            time_since_start.total_seconds() < 7200 and  # 2 horas
            match.status != 'finished'
        )
        
        # Status: finalizado ou em andamento
        is_finished = match.status == 'finished'
        
        result.append({
            'id': match.id,
            'match_number': match.match_number,
            'team1': match.get_team1_display(),
            'team2': match.get_team2_display(),
            'team1_score': match.team1_score,
            'team2_score': match.team2_score,
            'datetime': match_time_br,
            'phase': match.phase,
            'group': match.group,
            'status': match.status,
            'is_live': is_live,
            'is_finished': is_finished,
            'has_started': time_since_start.total_seconds() > 0
        })
    
    return result


def get_podium_zone_info(session) -> dict:
    """
    Retorna informações sobre pódio e zona de rebaixamento.
    
    Returns:
        Dicionário com quantidade de posições no pódio e zona de rebaixamento
    """
    from db import get_config_value
    
    rebaixamento_qty = int(get_config_value(session, 'rebaixamento_quantidade', '2'))
    
    return {
        'podio_posicoes': [1, 2, 3],
        'rebaixamento_inicio': None,  # Será calculado dinamicamente
        'rebaixamento_quantidade': rebaixamento_qty
    }
