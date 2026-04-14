"""
Módulo de pontuação do Bolão Copa do Mundo 2026
Calcula pontos dos palpites e gera ranking com critérios de desempate completos
"""

import json
from datetime import datetime
from sqlalchemy import func, desc, case
from models import (
    User, Match, Prediction, GroupPrediction, PodiumPrediction, 
    Team, Config, TournamentResult, GroupResult
)
from db import get_config_value


def get_scoring_config(session):
    """
    Obtém todas as configurações de pontuação do banco de dados.
    """
    config = {}
    
    # Pontuação de jogos
    config['placar_exato'] = int(get_config_value(session, 'pontos_placar_exato', '20'))
    config['resultado_gols'] = int(get_config_value(session, 'pontos_resultado_gols', '15'))
    config['resultado'] = int(get_config_value(session, 'pontos_resultado', '10'))
    config['gols'] = int(get_config_value(session, 'pontos_gols', '5'))
    config['nenhum'] = int(get_config_value(session, 'pontos_nenhum', '0'))
    
    # Pontuação de grupos
    config['grupo_ordem_correta'] = int(get_config_value(session, 'grupo_ordem_correta', '20'))
    config['grupo_ordem_invertida'] = int(get_config_value(session, 'grupo_ordem_invertida', '10'))
    config['grupo_um_certo'] = int(get_config_value(session, 'grupo_um_certo', '5'))
    
    # Pontuação do pódio
    config['podio_completo'] = int(get_config_value(session, 'podio_completo', '150'))
    config['podio_campeao'] = int(get_config_value(session, 'podio_campeao', '100'))
    config['podio_vice'] = int(get_config_value(session, 'podio_vice', '50'))
    config['podio_terceiro'] = int(get_config_value(session, 'podio_terceiro', '30'))
    config['podio_fora_ordem'] = int(get_config_value(session, 'podio_fora_ordem', '20'))
    
    return config


def calculate_match_points(pred_team1: int, pred_team2: int, 
                           real_team1: int, real_team2: int,
                           config: dict) -> tuple:
    """
    Calcula os pontos de um palpite para uma partida.
    
    Regras:
    - 20 pts: acertar resultado e placar exato
    - 15 pts: acertar vencedor/empate + gols de uma das equipes
    - 10 pts: acertar vencedor/empate, sem acertar gols
    - 5 pts: acertar apenas os gols de uma das equipes
    - 0 pts: errar tudo
    """
    # Determina resultado previsto e real
    if pred_team1 > pred_team2:
        pred_result = 'team1'
    elif pred_team1 < pred_team2:
        pred_result = 'team2'
    else:
        pred_result = 'draw'
    
    if real_team1 > real_team2:
        real_result = 'team1'
    elif real_team1 < real_team2:
        real_result = 'team2'
    else:
        real_result = 'draw'
    
    # Verifica acertos
    acertou_resultado = pred_result == real_result
    acertou_gols_team1 = pred_team1 == real_team1
    acertou_gols_team2 = pred_team2 == real_team2
    acertou_placar = acertou_gols_team1 and acertou_gols_team2
    
    # Calcula pontuação
    if acertou_placar:
        return config['placar_exato'], 'placar_exato', "Placar exato! 🎯"
    
    elif acertou_resultado and (acertou_gols_team1 or acertou_gols_team2):
        return config['resultado_gols'], 'resultado_gols', "Resultado + gols de um time ✓"
    
    elif acertou_resultado:
        return config['resultado'], 'resultado', "Resultado correto ✓"
    
    elif acertou_gols_team1 or acertou_gols_team2:
        return config['gols'], 'gols', "Gols de um time ✓"
    
    else:
        return config['nenhum'], 'nenhum', "Não pontuou"


def calculate_group_points(pred_first_id: int, pred_second_id: int,
                           real_first_id: int, real_second_id: int,
                           config: dict) -> tuple:
    """
    Calcula os pontos de um palpite de classificação de grupo.
    
    Regras:
    - 20 pts: acertou os 2 classificados na ordem correta
    - 10 pts: acertou os 2 classificados em ordem invertida
    - 5 pts: acertou apenas 1 classificado na posição errada
    """
    if pred_first_id is None or pred_second_id is None:
        return 0, "Palpite incompleto"
    
    if real_first_id is None or real_second_id is None:
        return 0, "Resultado ainda não definido"
    
    # Acertou os dois na ordem correta
    if pred_first_id == real_first_id and pred_second_id == real_second_id:
        return config['grupo_ordem_correta'], "Acertou 1º e 2º na ordem! 🎯"
    
    # Acertou os dois, mas invertidos
    if pred_first_id == real_second_id and pred_second_id == real_first_id:
        return config['grupo_ordem_invertida'], "Acertou os 2 classificados (ordem invertida) ✓"
    
    # Acertou apenas um na posição errada
    if pred_first_id in [real_first_id, real_second_id] or pred_second_id in [real_first_id, real_second_id]:
        return config['grupo_um_certo'], "Acertou 1 classificado (posição errada) ✓"
    
    return 0, "Não pontuou"


def calculate_podium_points(pred_champion: int, pred_runner: int, pred_third: int,
                            real_champion: int, real_runner: int, real_third: int,
                            config: dict) -> tuple:
    """
    Calcula os pontos do palpite de pódio.
    
    Regras:
    - 150 pts: acertou Campeão, Vice e 3º na ordem correta
    - 100 pts: acertou o Campeão
    - 50 pts: acertou o Vice-Campeão
    - 30 pts: acertou o 3º Lugar
    - 20 pts: acertou posição fora de ordem (ex: indicou campeão como vice)
    """
    total_points = 0
    breakdown = []
    
    if real_champion is None:
        return 0, "Resultado ainda não definido"
    
    # Verifica pódio completo na ordem
    if (pred_champion == real_champion and 
        pred_runner == real_runner and 
        pred_third == real_third):
        return config['podio_completo'], "Pódio completo na ordem exata! 🏆🥈🥉"
    
    # Verifica acertos individuais
    real_podium = {real_champion, real_runner, real_third}
    
    # Campeão correto
    if pred_champion == real_champion:
        total_points += config['podio_campeao']
        breakdown.append(f"Campeão correto (+{config['podio_campeao']})")
    elif pred_champion in real_podium:
        total_points += config['podio_fora_ordem']
        breakdown.append(f"Campeão no pódio (+{config['podio_fora_ordem']})")
    
    # Vice correto
    if pred_runner == real_runner:
        total_points += config['podio_vice']
        breakdown.append(f"Vice correto (+{config['podio_vice']})")
    elif pred_runner in real_podium:
        total_points += config['podio_fora_ordem']
        breakdown.append(f"Vice no pódio (+{config['podio_fora_ordem']})")
    
    # Terceiro correto
    if pred_third == real_third:
        total_points += config['podio_terceiro']
        breakdown.append(f"3º lugar correto (+{config['podio_terceiro']})")
    elif pred_third in real_podium:
        total_points += config['podio_fora_ordem']
        breakdown.append(f"3º lugar no pódio (+{config['podio_fora_ordem']})")
    
    if not breakdown:
        breakdown.append("Não pontuou no pódio")
    
    return total_points, "; ".join(breakdown)


def process_match_predictions(session, match_id: int):
    """
    Processa todos os palpites de uma partida e atribui pontos.
    - Se o jogo tem placar (em andamento ou finalizado): calcula pontos
    - Se o jogo não tem placar (resultado apagado): zera pontos
    """
    match = session.query(Match).filter_by(id=match_id).first()
    
    if not match:
        return
    
    predictions = session.query(Prediction).filter_by(match_id=match_id).all()
    
    # Se o jogo não tem placar, zera os pontos
    if match.team1_score is None or match.team2_score is None:
        for pred in predictions:
            pred.points_awarded = 0
            pred.points_type = None
            pred.breakdown = None
        session.commit()
        return
    
    # Jogo tem placar (em andamento ou finalizado) - calcula pontos
    config = get_scoring_config(session)
    
    for pred in predictions:
        points, points_type, breakdown = calculate_match_points(
            pred.pred_team1_score, pred.pred_team2_score,
            match.team1_score, match.team2_score,
            config
        )
        
        pred.points_awarded = points
        pred.points_type = points_type
        pred.breakdown = breakdown
    
    session.commit()


def process_group_predictions(session, group_name: str):
    """
    Processa todos os palpites de classificação de um grupo.
    """
    result = session.query(GroupResult).filter_by(group_name=group_name).first()
    
    if not result or not result.first_place_team_id or not result.second_place_team_id:
        return
    
    config = get_scoring_config(session)
    predictions = session.query(GroupPrediction).filter_by(group_name=group_name).all()
    
    for pred in predictions:
        points, breakdown = calculate_group_points(
            pred.first_place_team_id, pred.second_place_team_id,
            result.first_place_team_id, result.second_place_team_id,
            config
        )
        
        pred.points_awarded = points
        pred.breakdown = breakdown
    
    session.commit()


def process_podium_predictions(session):
    """
    Processa todos os palpites de pódio após definição dos resultados.
    """
    champion = session.query(TournamentResult).filter_by(result_type='champion').first()
    runner = session.query(TournamentResult).filter_by(result_type='runner_up').first()
    third = session.query(TournamentResult).filter_by(result_type='third_place').first()
    
    if not champion:
        return
    
    config = get_scoring_config(session)
    predictions = session.query(PodiumPrediction).all()
    
    for pred in predictions:
        points, breakdown = calculate_podium_points(
            pred.champion_team_id, pred.runner_up_team_id, pred.third_place_team_id,
            champion.team_id if champion else None,
            runner.team_id if runner else None,
            third.team_id if third else None,
            config
        )
        
        pred.points_awarded = points
        pred.breakdown = breakdown
    
    session.commit()


def get_user_stats(session, user_id: int) -> dict:
    """
    Obtém estatísticas detalhadas de um usuário.
    SÓ considera jogos que têm placar registrado (não usa 0x0 implícito).
    """
    from datetime import datetime
    import pytz
    
    # Pega horário atual (Brasília, naive para comparar com banco)
    brazil_tz = pytz.timezone('America/Sao_Paulo')
    now_br = datetime.now(brazil_tz)
    now_naive = now_br.replace(tzinfo=None)
    
    # Pega jogos que já começaram E TÊM PLACAR REGISTRADO
    matches_with_score = session.query(Match).filter(
        Match.datetime <= now_naive,
        Match.team1_score.isnot(None),
        Match.team2_score.isnot(None)
    ).all()
    matches_with_score_ids = {m.id for m in matches_with_score}
    
    # Mapa de placares
    match_scores = {}
    for m in matches_with_score:
        match_scores[m.id] = {
            'team1_score': m.team1_score,
            'team2_score': m.team2_score
        }
    
    # Pega todos os palpites do usuário
    all_predictions = session.query(Prediction).filter_by(user_id=user_id).all()
    
    # Filtra apenas palpites de jogos que têm placar registrado
    predictions = [p for p in all_predictions if p.match_id in matches_with_score_ids]
    
    config = get_scoring_config(session)
    
    stats = {
        'total_palpites': len(all_predictions),  # Total de palpites feitos
        'placares_exatos': 0,
        'resultados_corretos': 0,
        'gols_corretos': 0,
        'palpites_zerados': 0,
        'pontos_jogos': 0,
        'pontos_grupos': 0,
        'pontos_podio': 0,
        'total_pontos': 0
    }
    
    for pred in predictions:
        # Pega placar registrado
        scores = match_scores.get(pred.match_id)
        if not scores:
            continue
        
        # Calcula pontos
        points, points_type, _ = calculate_match_points(
            pred.pred_team1_score, pred.pred_team2_score,
            scores['team1_score'], scores['team2_score'],
            config
        )
        
        stats['pontos_jogos'] += points
        
        if points_type == 'placar_exato':
            stats['placares_exatos'] += 1
            stats['resultados_corretos'] += 1
            stats['gols_corretos'] += 1
        elif points_type == 'resultado_gols':
            stats['resultados_corretos'] += 1
            stats['gols_corretos'] += 1
        elif points_type == 'resultado':
            stats['resultados_corretos'] += 1
        elif points_type == 'gols':
            stats['gols_corretos'] += 1
        elif points_type == 'nenhum':
            stats['palpites_zerados'] += 1
    
    # Pontos de grupos - busca todos os resultados de grupo de uma vez
    all_group_results = {gr.group_name: gr for gr in session.query(GroupResult).all()}
    group_preds = session.query(GroupPrediction).filter_by(user_id=user_id).all()
    for gp in group_preds:
        # Verifica se o grupo tem resultado salvo (sem query individual)
        group_result = all_group_results.get(gp.group_name)
        if group_result and group_result.first_place_team_id and group_result.second_place_team_id:
            stats['pontos_grupos'] += gp.points_awarded or 0
    
    # Pontos de pódio - só conta se o pódio foi definido
    podium_pred = session.query(PodiumPrediction).filter_by(user_id=user_id).first()
    if podium_pred:
        # Verifica se o pódio foi definido (1 query em vez de N)
        all_tournament_results = {tr.result_type: tr for tr in session.query(TournamentResult).all()}
        campeao = all_tournament_results.get('champion')
        if campeao and campeao.team_id:
            stats['pontos_podio'] = podium_pred.points_awarded or 0
    
    stats['total_pontos'] = stats['pontos_jogos'] + stats['pontos_grupos'] + stats['pontos_podio']
    
    return stats


def get_ranking(session) -> list:
    """
    Gera o ranking completo dos participantes com critérios de desempate.
    
    Critérios de desempate (em ordem):
    1. Maior pontuação total
    2. Maior número de placares exatos (20 pts)
    3. Maior número de acerto de Vencedores com gols corretos (15 pts)
    4. Maior número de acerto de Vencedores (10 pts)
    5. Maior número de acerto de classificados no grupo
    6. Maior número de acerto de pódio
    7. Maior número de acerto de gols de um time (5 pts)
    8. Menos palpites zerados
    9. Ordem de inscrição (quem se inscreveu primeiro)
    
    IMPORTANTE: Só considera jogos que TÊM PLACAR REGISTRADO (não usa 0x0 implícito)
    """
    from datetime import datetime
    import pytz
    
    users = session.query(User).filter_by(active=True).filter(User.role != 'admin').all()
    
    # Pega horário atual (Brasília, naive para comparar com banco)
    brazil_tz = pytz.timezone('America/Sao_Paulo')
    now_br = datetime.now(brazil_tz)
    now_naive = now_br.replace(tzinfo=None)
    
    # Pega jogos que já começaram E TÊM PLACAR REGISTRADO
    matches_with_score = session.query(Match).filter(
        Match.datetime <= now_naive,
        Match.team1_score.isnot(None),
        Match.team2_score.isnot(None)
    ).all()
    matches_with_score_ids = {m.id for m in matches_with_score}
    
    # Mapa de placares
    match_scores = {}
    for m in matches_with_score:
        match_scores[m.id] = {
            'team1_score': m.team1_score,
            'team2_score': m.team2_score
        }
    
    ranking = []
    
    config = get_scoring_config(session)
    
    # =====================================================================
    # QUERIES EM BATCH (antes do loop) para eliminar problema N+1
    # =====================================================================
    from collections import defaultdict
    
    # Todos os palpites de jogos com placar
    all_predictions = session.query(Prediction).filter(
        Prediction.match_id.in_(matches_with_score_ids)
    ).all() if matches_with_score_ids else []
    
    # Agrupar por user_id
    preds_by_user = defaultdict(list)
    for pred in all_predictions:
        preds_by_user[pred.user_id].append(pred)
    
    # Todos os palpites de grupo
    all_group_preds = session.query(GroupPrediction).all()
    group_preds_by_user = defaultdict(list)
    for gp in all_group_preds:
        group_preds_by_user[gp.user_id].append(gp)
    
    # Todos os resultados de grupo (de uma vez)
    all_group_results = {gr.group_name: gr for gr in session.query(GroupResult).all()}
    
    # Todos os palpites de pódio
    all_podium_preds = {pp.user_id: pp for pp in session.query(PodiumPrediction).all()}
    
    # Resultados do torneio (de uma vez)
    all_tournament_results = {tr.result_type: tr for tr in session.query(TournamentResult).all()}
    
    # Contagem total de palpites por usuário (incluindo jogos sem placar)
    all_user_predictions = session.query(Prediction).all()
    total_preds_by_user = defaultdict(int)
    for pred in all_user_predictions:
        total_preds_by_user[pred.user_id] += 1
    
    # =====================================================================
    # LOOP DE USUÁRIOS (sem queries individuais)
    # =====================================================================
    for user in users:
        scored_predictions = preds_by_user.get(user.id, [])
        
        # Calcula pontos
        placares_exatos = 0
        resultado_gols = 0
        resultado = 0
        gols = 0
        zeros = 0
        pontos_jogos = 0
        
        for pred in scored_predictions:
            # Pega placar registrado
            scores = match_scores.get(pred.match_id)
            if not scores:
                continue
            
            # Calcula pontos
            points, points_type, _ = calculate_match_points(
                pred.pred_team1_score, pred.pred_team2_score,
                scores['team1_score'], scores['team2_score'],
                config
            )
            
            pontos_jogos += points
            
            if points_type == 'placar_exato':
                placares_exatos += 1
            elif points_type == 'resultado_gols':
                resultado_gols += 1
            elif points_type == 'resultado':
                resultado += 1
            elif points_type == 'gols':
                gols += 1
            elif points_type == 'nenhum':
                zeros += 1
        
        # Pontos de grupos - só conta se o grupo tem resultado salvo
        group_preds = group_preds_by_user.get(user.id, [])
        pontos_grupos = 0
        grupos_corretos = 0  # Conta quantos classificados acertou
        for gp in group_preds:
            # Verifica se o grupo tem resultado salvo
            group_result = all_group_results.get(gp.group_name)
            if group_result and group_result.first_place_team_id and group_result.second_place_team_id:
                pontos_grupos += gp.points_awarded or 0
                # Conta acertos de classificados
                if gp.first_place_team_id == group_result.first_place_team_id:
                    grupos_corretos += 1
                if gp.second_place_team_id == group_result.second_place_team_id:
                    grupos_corretos += 1
        
        # Pontos de pódio - só conta se o pódio foi definido
        podium_pred = all_podium_preds.get(user.id)
        pontos_podio = 0
        podio_corretos = 0  # Conta quantos acertos de pódio
        if podium_pred:
            # Verifica se o pódio foi definido
            campeao = all_tournament_results.get('champion')
            vice = all_tournament_results.get('runner_up')
            terceiro = all_tournament_results.get('third_place')
            
            if campeao and campeao.team_id:
                pontos_podio = podium_pred.points_awarded or 0
                
                # Conta acertos de pódio
                if podium_pred.champion_team_id == campeao.team_id:
                    podio_corretos += 1
                if vice and podium_pred.runner_up_team_id == vice.team_id:
                    podio_corretos += 1
                if terceiro and podium_pred.third_place_team_id == terceiro.team_id:
                    podio_corretos += 1
        
        total_pontos = pontos_jogos + pontos_grupos + pontos_podio
        
        ranking.append({
            'user_id': user.id,
            'nome': user.name,
            'total_pontos': total_pontos,
            'placares_exatos': placares_exatos,
            'resultado_gols': resultado_gols,
            'resultado': resultado,
            'gols': gols,
            'zeros': zeros,
            'grupos_corretos': grupos_corretos,
            'podio_corretos': podio_corretos,
            'resultados_corretos': placares_exatos + resultado_gols + resultado,
            'created_at': user.created_at
        })
    
    # Ordena pelo critério de desempate completo
    # Ordem definida pelo usuário:
    # 1. Maior pontuação total
    # 2. Maior número de placares exatos (20 pts)
    # 3. Maior número de acerto de Vencedores com gols corretos (15 pts)
    # 4. Maior número de acerto de Vencedores (10 pts)
    # 5. Maior número de acerto de classificados no grupo
    # 6. Maior número de acerto de pódio
    # 7. Maior número de acerto de gols de um time (5 pts)
    # 8. Menos palpites zerados
    # 9. Ordem de inscrição (quem se inscreveu primeiro)
    ranking.sort(key=lambda x: (
        -x['total_pontos'],        # 1. Maior pontuação total
        -x['placares_exatos'],     # 2. Mais placares exatos (20 pts)
        -x['resultado_gols'],      # 3. Mais resultado + gols (15 pts)
        -x['resultado'],           # 4. Mais resultado sem gols (10 pts)
        -x['grupos_corretos'],     # 5. Mais acertos de classificados no grupo
        -x['podio_corretos'],      # 6. Mais acertos de pódio
        -x['gols'],                # 7. Mais gols de um time (5 pts)
        x['zeros'],                # 8. Menos zeros
        x['user_id']               # 9. Ordem de inscrição
    ))
    
    # Adiciona posição
    for i, r in enumerate(ranking, 1):
        r['posicao'] = i
    
    return ranking
