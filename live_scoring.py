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
    Calcula o ranking considerando o resultado de um jogo, mostrando para qual
    posição cada participante está indo COM o resultado desse jogo.

    - posicao_atual: posição no ranking JÁ considerando os pontos deste jogo
      (é a posição real do ranking, pois o jogo já tem placar registrado).
    - posicao_anterior: posição que o participante tinha SEM os pontos deste jogo.
    - variacao: posicao_anterior - posicao_atual (positivo = subiu).

    Args:
        session: Sessão do banco de dados
        match_id: ID do jogo de referência (opcional)

    Returns:
        Lista (ordenada pela posição atual) com variação de posição
    """
    # Ranking real, já incluindo este jogo (o jogo tem placar registrado)
    current_ranking = get_ranking(session)

    match = session.query(Match).filter_by(id=match_id).first() if match_id else None

    # Sem jogo válido ou sem placar: não há variação a calcular
    if not match or match.team1_score is None or match.team2_score is None:
        for i, user_data in enumerate(current_ranking):
            user_data['posicao_atual'] = i + 1
            user_data['posicao_anterior'] = i + 1
            user_data['variacao'] = 0
        return current_ranking

    # Ranking "antes" deste jogo: recalculado excluindo os pontos do jogo,
    # com os mesmos critérios oficiais de desempate
    ranking_anterior = get_ranking(session, exclude_match_id=match_id)
    posicoes_anteriores = {u['user_id']: u['posicao'] for u in ranking_anterior}

    for i, user_data in enumerate(current_ranking):
        user_data['posicao_atual'] = user_data.get('posicao', i + 1)
        user_data['posicao_anterior'] = posicoes_anteriores.get(
            user_data['user_id'], user_data['posicao_atual']
        )
        user_data['variacao'] = user_data['posicao_anterior'] - user_data['posicao_atual']

    return current_ranking


def get_ongoing_matches(session, today_only=True) -> list:
    """
    Retorna lista de jogos em andamento ou finalizados.
    Por padrão, só mostra jogos cujo horário de início seja no dia de hoje.
    Com today_only=False, inclui todos os jogos já realizados da Copa.

    Returns:
        Lista de jogos com status e informações
    """
    from datetime import datetime, timedelta
    import pytz

    # Timezone do Brasil
    brazil_tz = pytz.timezone('America/Sao_Paulo')
    now_br = datetime.now(brazil_tz)
    now_naive = now_br.replace(tzinfo=None)  # Para comparar com banco (naive)

    # Início e fim do dia atual (meia-noite a meia-noite) - naive
    today_start = now_naive.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    # Pega jogos que já começaram (comparação naive)
    query = session.query(Match).filter(
        Match.datetime <= now_naive  # Já começou
    )
    if today_only:
        query = query.filter(
            Match.datetime >= today_start,
            Match.datetime < today_end
        )
    matches = query.order_by(Match.datetime.desc()).all()
    
    result = []
    
    for match in matches:
        # Datetime do jogo (naive, assume horário de Brasília)
        match_time = match.datetime
        
        # Calcula tempo desde o início
        time_since_start = now_naive - match_time
        
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
            'datetime': match_time,
            'phase': match.phase,
            'group': match.group,
            'status': match.status,
            'is_live': is_live,
            'is_finished': is_finished,
            'has_started': time_since_start.total_seconds() > 0,
            'is_today': today_start <= match_time < today_end
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
