"""
Funções para calcular classificação dos grupos
Versão corrigida para incluir times da repescagem (placeholders)
"""
from sqlalchemy.orm import Session
from models import Match, Team, Prediction


class PlaceholderTeam:
    """Classe para representar times placeholder (repescagem)"""
    def __init__(self, code):
        self.id = f"placeholder_{code}"
        self.code = code
        self.name = code  # Nome é o próprio código (EUR_A, EUR_B, etc.)
        self.flag = "🏳️"  # Bandeira genérica


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
        # Determina time 1 (pode ser real ou placeholder)
        if match.team1_id:
            team1_key = match.team1_id
            team1_obj = match.team1
        elif match.team1_code:
            team1_key = f"placeholder_{match.team1_code}"
            team1_obj = PlaceholderTeam(match.team1_code)
        else:
            continue  # Sem time definido
        
        # Determina time 2 (pode ser real ou placeholder)
        if match.team2_id:
            team2_key = match.team2_id
            team2_obj = match.team2
        elif match.team2_code:
            team2_key = f"placeholder_{match.team2_code}"
            team2_obj = PlaceholderTeam(match.team2_code)
        else:
            continue  # Sem time definido
            
        # Inicializa times se necessário
        if team1_key not in teams_stats:
            teams_stats[team1_key] = {
                'team': team1_obj,
                'points': 0,
                'played': 0,
                'wins': 0,
                'draws': 0,
                'losses': 0,
                'goals_for': 0,
                'goals_against': 0,
                'goal_difference': 0
            }
        
        if team2_key not in teams_stats:
            teams_stats[team2_key] = {
                'team': team2_obj,
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
        teams_stats[team1_key]['played'] += 1
        teams_stats[team2_key]['played'] += 1
        teams_stats[team1_key]['goals_for'] += gols1
        teams_stats[team1_key]['goals_against'] += gols2
        teams_stats[team2_key]['goals_for'] += gols2
        teams_stats[team2_key]['goals_against'] += gols1
        
        if gols1 > gols2:
            # Time 1 venceu
            teams_stats[team1_key]['points'] += 3
            teams_stats[team1_key]['wins'] += 1
            teams_stats[team2_key]['losses'] += 1
        elif gols2 > gols1:
            # Time 2 venceu
            teams_stats[team2_key]['points'] += 3
            teams_stats[team2_key]['wins'] += 1
            teams_stats[team1_key]['losses'] += 1
        else:
            # Empate
            teams_stats[team1_key]['points'] += 1
            teams_stats[team1_key]['draws'] += 1
            teams_stats[team2_key]['points'] += 1
            teams_stats[team2_key]['draws'] += 1
    
    # Calcula saldo de gols
    for team_key in teams_stats:
        teams_stats[team_key]['goal_difference'] = teams_stats[team_key]['goals_for'] - teams_stats[team_key]['goals_against']
    
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
