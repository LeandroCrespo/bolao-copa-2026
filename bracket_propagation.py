"""
bracket_propagation.py - Propagação automática de confrontos no mata-mata

Resolve placeholders dos jogos do mata-mata:
  - "1A", "2B" etc. → times classificados dos grupos (1º e 2º)
  - "3CDF" etc. → melhores 3ºs colocados (resolvido via admin ou API)
  - "W73", "W74" etc. → vencedor do jogo indicado
  - "L101", "L102" etc. → perdedor do jogo indicado (para disputa de 3º)
"""

import re
import logging
from sqlalchemy.orm import Session
from models import Match, Team, GroupResult

logger = logging.getLogger(__name__)


# ============================================================
# RESOLUÇÃO DE PLACEHOLDERS DE GRUPOS (1º e 2º)
# ============================================================

def resolve_group_placeholders(session: Session):
    """
    Resolve placeholders do tipo "1A", "2B" etc. nos jogos R32.
    Usa os GroupResults definidos para encontrar os times classificados.
    
    Retorna o número de jogos atualizados.
    """
    updated = 0
    
    # Busca todos os resultados de grupo definidos
    group_results = {}
    for gr in session.query(GroupResult).all():
        group_results[gr.group_name] = gr
    
    if not group_results:
        logger.info("Nenhum resultado de grupo definido ainda")
        return 0
    
    # Busca jogos R32 que ainda têm placeholders (team1_id ou team2_id é NULL)
    r32_matches = session.query(Match).filter(
        Match.phase == 'R32'
    ).all()
    
    for match in r32_matches:
        changed = False
        
        # Resolver team1
        if match.team1_id is None and match.team1_code:
            team = _resolve_position_code(session, match.team1_code, group_results)
            if team:
                match.team1_id = team.id
                match.team1_code = team.code
                changed = True
                logger.info(f"Jogo #{match.match_number} team1: {match.team1_code} -> {team.flag} {team.name}")
        
        # Resolver team2
        if match.team2_id is None and match.team2_code:
            team = _resolve_position_code(session, match.team2_code, group_results)
            if team:
                match.team2_id = team.id
                match.team2_code = team.code
                changed = True
                logger.info(f"Jogo #{match.match_number} team2: {match.team2_code} -> {team.flag} {team.name}")
        
        if changed:
            updated += 1
    
    if updated > 0:
        session.commit()
        logger.info(f"Resolvidos placeholders de grupo em {updated} jogos R32")
    
    return updated


def _resolve_position_code(session, code, group_results):
    """
    Resolve um código de posição como "1A" (1º do grupo A) ou "2B" (2º do grupo B).
    Retorna o Team ou None se não puder resolver.
    
    Não resolve códigos de 3ºs colocados (ex: "3CDF") - esses são tratados
    separadamente pelo admin ou pela API-Football.
    """
    # Padrão: "1X" ou "2X" onde X é a letra do grupo
    match = re.match(r'^([12])([A-L])$', code)
    if not match:
        return None
    
    position = int(match.group(1))
    group_letter = match.group(2)
    
    gr = group_results.get(group_letter)
    if not gr:
        return None
    
    if position == 1 and gr.first_place_team_id:
        return session.query(Team).get(gr.first_place_team_id)
    elif position == 2 and gr.second_place_team_id:
        return session.query(Team).get(gr.second_place_team_id)
    
    return None


# ============================================================
# RESOLUÇÃO DE VENCEDORES/PERDEDORES DO MATA-MATA
# ============================================================

def resolve_knockout_winners(session: Session):
    """
    Resolve placeholders do tipo "W73" (vencedor do jogo 73) e "L101" (perdedor do jogo 101)
    nos jogos do mata-mata.
    
    Chamada após cada resultado de jogo do mata-mata ser finalizado.
    Retorna o número de jogos atualizados.
    """
    updated = 0
    
    # Busca todos os jogos finalizados do mata-mata que têm ambos os times definidos
    finished_knockout = session.query(Match).filter(
        Match.phase != 'Grupos',
        Match.status == 'finished',
        Match.team1_id.isnot(None),
        Match.team2_id.isnot(None),
        Match.team1_score.isnot(None),
        Match.team2_score.isnot(None)
    ).all()
    
    # Mapeia match_number -> (winner_team, loser_team)
    results = {}
    for m in finished_knockout:
        winner, loser = _determine_winner_loser(session, m)
        if winner and loser:
            results[m.match_number] = {
                'winner': winner,
                'loser': loser,
                'match': m
            }
    
    if not results:
        return 0
    
    # Busca todos os jogos que ainda têm placeholders W/L
    all_knockout = session.query(Match).filter(
        Match.phase != 'Grupos'
    ).all()
    
    for match in all_knockout:
        changed = False
        
        # Resolver team1
        if match.team1_id is None and match.team1_code:
            team = _resolve_wl_code(match.team1_code, results)
            if team:
                match.team1_id = team.id
                match.team1_code = team.code
                changed = True
                logger.info(f"Jogo #{match.match_number} team1: W/L -> {team.flag} {team.name}")
        
        # Resolver team2
        if match.team2_id is None and match.team2_code:
            team = _resolve_wl_code(match.team2_code, results)
            if team:
                match.team2_id = team.id
                match.team2_code = team.code
                changed = True
                logger.info(f"Jogo #{match.match_number} team2: W/L -> {team.flag} {team.name}")
        
        if changed:
            updated += 1
    
    if updated > 0:
        session.commit()
        logger.info(f"Resolvidos {updated} confrontos do mata-mata com vencedores/perdedores")
    
    return updated


def _determine_winner_loser(session, match):
    """
    Determina o vencedor e perdedor de um jogo finalizado.
    Para jogos decididos nos pênaltis, usa o placar final (que já inclui pênaltis).
    
    Retorna (winner_team, loser_team) ou (None, None).
    """
    if match.team1_score is None or match.team2_score is None:
        return None, None
    
    team1 = session.query(Team).get(match.team1_id) if match.team1_id else None
    team2 = session.query(Team).get(match.team2_id) if match.team2_id else None
    
    if not team1 or not team2:
        return None, None
    
    # No mata-mata, não pode haver empate no resultado final
    # O placar armazenado deve refletir o resultado final (incluindo prorrogação/pênaltis)
    if match.team1_score > match.team2_score:
        return team1, team2
    elif match.team2_score > match.team1_score:
        return team2, team1
    else:
        # Empate no placar - isso não deveria acontecer no mata-mata
        # Se acontecer, não podemos determinar o vencedor automaticamente
        logger.warning(
            f"Jogo #{match.match_number} terminou empatado ({match.team1_score}x{match.team2_score}). "
            f"No mata-mata, o resultado deve incluir prorrogação/pênaltis. "
            f"O admin precisa definir o vencedor manualmente."
        )
        return None, None


def _resolve_wl_code(code, results):
    """
    Resolve um código "W73" (vencedor do jogo 73) ou "L101" (perdedor do jogo 101).
    Retorna o Team ou None.
    """
    # Padrão: "W" ou "L" seguido do número do jogo
    wl_match = re.match(r'^([WL])(\d+)$', code)
    if not wl_match:
        return None
    
    wl_type = wl_match.group(1)
    match_number = int(wl_match.group(2))
    
    result = results.get(match_number)
    if not result:
        return None
    
    if wl_type == 'W':
        return result['winner']
    elif wl_type == 'L':
        return result['loser']
    
    return None


# ============================================================
# FUNÇÃO PRINCIPAL DE PROPAGAÇÃO
# ============================================================

def propagate_all(session: Session):
    """
    Executa toda a propagação de confrontos:
    1. Resolve placeholders de grupos (1º e 2º) para jogos R32
    2. Resolve vencedores/perdedores do mata-mata para próximas fases
    
    Retorna o total de jogos atualizados.
    """
    total = 0
    total += resolve_group_placeholders(session)
    total += resolve_knockout_winners(session)
    
    if total > 0:
        logger.info(f"Propagação total: {total} jogos atualizados")
    else:
        logger.info("Propagação: nenhum jogo atualizado")
    
    return total


def propagate_after_group_result(session: Session, group_name: str):
    """
    Chamada após definir os classificados de um grupo.
    Resolve os placeholders do tipo "1X" e "2X" para o grupo específico.
    """
    logger.info(f"Propagando classificados do Grupo {group_name}...")
    updated = resolve_group_placeholders(session)
    return updated


def propagate_after_match_result(session: Session, match_id: int):
    """
    Chamada após finalizar um jogo do mata-mata.
    Resolve o vencedor/perdedor para os jogos da próxima fase.
    """
    match = session.query(Match).get(match_id)
    if not match or match.phase == 'Grupos':
        return 0
    
    logger.info(f"Propagando resultado do Jogo #{match.match_number}...")
    updated = resolve_knockout_winners(session)
    return updated
