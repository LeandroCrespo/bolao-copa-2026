"""
Funções para calcular classificação dos grupos
"""
from sqlalchemy.orm import Session
from models import Match, Team, Prediction

def calculate_group_standings(session: Session, group: str, matches_results: dict = None, is_prediction: bool = False):
    """
    Calcula a classificação de um grupo baseado nos resultados dos jogos
    
    Args:
        session: Sessão do banco de dados
        group: Letra do grupo (A-L)
        matches_results: Dicionário com resultados {match_id: (gols1, gols2)} - usado para palpites
        is_prediction: Se True, usa matches_results; se False, usa resultados oficiais
    
    Returns:
        Lista de dicionários com a classificação ordenada
    """
    # Busca todos os jogos do grupo
    matches = session.query(Match).filter(
        Match.group == group,
        Match.phase == 'Grupos'
    ).all()
    
    if not matches:
        return []
    
    # Inicializa estatísticas dos times
    teams_stats = {}
    
    for match in matches:
        if not match.team1_id or not match.team2_id:
            continue
            
        # Inicializa times se necessário
        if match.team1_id not in teams_stats:
            teams_stats[match.team1_id] = {
                'team': match.team1,
                'points': 0,
                'played': 0,
                'wins': 0,
                'draws': 0,
                'losses': 0,
                'goals_for': 0,
                'goals_against': 0,
                'goal_difference': 0
            }
        
        if match.team2_id not in teams_stats:
            teams_stats[match.team2_id] = {
                'team': match.team2,
                'points': 0,
                'played': 0,
                'wins': 0,
                'draws': 0,
                'losses': 0,
                'goals_for': 0,
                'goals_against': 0,
                'goal_difference': 0
            }
        
        # Determina os gols
        if is_prediction and matches_results and match.id in matches_results:
            gols1, gols2 = matches_results[match.id]
        elif not is_prediction and match.status == 'finished':
            gols1, gols2 = match.team1_score, match.team2_score
        else:
            continue  # Jogo sem resultado ainda
        
        # Atualiza estatísticas
        teams_stats[match.team1_id]['played'] += 1
        teams_stats[match.team2_id]['played'] += 1
        teams_stats[match.team1_id]['goals_for'] += gols1
        teams_stats[match.team1_id]['goals_against'] += gols2
        teams_stats[match.team2_id]['goals_for'] += gols2
        teams_stats[match.team2_id]['goals_against'] += gols1
        
        if gols1 > gols2:
            # Time 1 venceu
            teams_stats[match.team1_id]['points'] += 3
            teams_stats[match.team1_id]['wins'] += 1
            teams_stats[match.team2_id]['losses'] += 1
        elif gols2 > gols1:
            # Time 2 venceu
            teams_stats[match.team2_id]['points'] += 3
            teams_stats[match.team2_id]['wins'] += 1
            teams_stats[match.team1_id]['losses'] += 1
        else:
            # Empate
            teams_stats[match.team1_id]['points'] += 1
            teams_stats[match.team1_id]['draws'] += 1
            teams_stats[match.team2_id]['points'] += 1
            teams_stats[match.team2_id]['draws'] += 1
    
    # Calcula saldo de gols
    for team_id in teams_stats:
        teams_stats[team_id]['goal_difference'] = teams_stats[team_id]['goals_for'] - teams_stats[team_id]['goals_against']
    
    # Ordena por: pontos, saldo de gols, gols marcados
    standings = sorted(
        teams_stats.values(),
        key=lambda x: (x['points'], x['goal_difference'], x['goals_for']),
        reverse=True
    )
    
    return standings


def get_predicted_group_standings(session: Session, user_id: int, group: str):
    """
    Calcula a classificação de um grupo baseado nos palpites de um usuário
    
    Args:
        session: Sessão do banco de dados
        user_id: ID do usuário
        group: Letra do grupo (A-L)
    
    Returns:
        Lista de dicionários com a classificação ordenada baseada nos palpites
    """
    # Busca todos os jogos do grupo
    matches = session.query(Match).filter(
        Match.group == group,
        Match.phase == 'Grupos'
    ).all()
    
    if not matches:
        return []
    
    # Busca os palpites do usuário para esses jogos
    match_ids = [m.id for m in matches]
    predictions = session.query(Prediction).filter(
        Prediction.user_id == user_id,
        Prediction.match_id.in_(match_ids)
    ).all()
    
    # Cria dicionário de resultados dos palpites
    matches_results = {}
    for pred in predictions:
        matches_results[pred.match_id] = (pred.pred_team1_score, pred.pred_team2_score)
    
    # Calcula classificação baseada nos palpites
    return calculate_group_standings(session, group, matches_results, is_prediction=True)


def get_official_group_standings(session: Session, group: str):
    """
    Calcula a classificação oficial de um grupo baseado nos resultados lançados
    
    Args:
        session: Sessão do banco de dados
        group: Letra do grupo (A-L)
    
    Returns:
        Lista de dicionários com a classificação oficial
    """
    return calculate_group_standings(session, group, is_prediction=False)
