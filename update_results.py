"""
update_results.py - Atualização automática de resultados da Copa 2026
Usa a API-Football para buscar resultados e atualiza o banco Neon.

Modos de execução:
  --mode live     : Busca jogos em andamento (durante os jogos)
  --mode post     : Busca jogos finalizados do dia (pós-jogo)
  --mode nightly  : Varredura de todos os jogos sem resultado (segurança)

Variáveis de ambiente necessárias:
  API_FOOTBALL_KEY    : Chave da API-Football
  NEON_CONNECTION_STRING : String de conexão do banco Neon
"""

import os
import sys
import json
import logging
import requests
import psycopg2
import pytz
from datetime import datetime, timedelta, timezone

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURAÇÃO
# ============================================================

API_KEY = os.environ.get('API_FOOTBALL_KEY', '').strip()
NEON_CONN = os.environ.get('NEON_CONNECTION_STRING', '').strip()
API_BASE_URL = 'https://v3.football.api-sports.io'
LEAGUE_ID = 1  # FIFA World Cup
SEASON = 2026

# Mapeamento API-Football team name → código Neon
API_NAME_TO_NEON_CODE = {
    "Algeria": "ALG",
    "Argentina": "ARG",
    "Australia": "AUS",
    "Austria": "AUT",
    "Belgium": "BEL",
    "Bosnia & Herzegovina": "BIH",
    "Brazil": "BRA",
    "Canada": "CAN",
    "Cape Verde Islands": "CPV",
    "Colombia": "COL",
    "Congo DR": "COD",
    "Croatia": "CRO",
    "Curaçao": "CUW",
    "Czech Republic": "CZE",
    "Czechia": "CZE",
    "Ecuador": "ECU",
    "Egypt": "EGY",
    "England": "ENG",
    "France": "FRA",
    "Germany": "GER",
    "Ghana": "GHA",
    "Haiti": "HAI",
    "Iran": "IRN",
    "Iraq": "IRQ",
    "Ivory Coast": "CIV",
    "Japan": "JPN",
    "Jordan": "JOR",
    "Mexico": "MEX",
    "Morocco": "MAR",
    "Netherlands": "NED",
    "New Zealand": "NZL",
    "Norway": "NOR",
    "Panama": "PAN",
    "Paraguay": "PAR",
    "Portugal": "POR",
    "Qatar": "QAT",
    "Saudi Arabia": "KSA",
    "Scotland": "SCO",
    "Senegal": "SEN",
    "South Africa": "RSA",
    "South Korea": "KOR",
    "Spain": "ESP",
    "Sweden": "SWE",
    "Switzerland": "SUI",
    "Tunisia": "TUN",
    "Türkiye": "TUR",
    "USA": "USA",
    "Uruguay": "URU",
    "Uzbekistan": "UZB",
}

# Status da API-Football que indicam jogo finalizado
FINISHED_STATUSES = {'FT', 'AET', 'PEN'}
# Status da API-Football que indicam jogo em andamento
LIVE_STATUSES = {'1H', '2H', 'HT', 'ET', 'BT', 'P', 'SUSP', 'INT', 'LIVE'}
# Status que indicam jogo não iniciado
NOT_STARTED_STATUSES = {'TBD', 'NS'}


# ============================================================
# FUNÇÕES DA API-FOOTBALL
# ============================================================

def api_request(endpoint, params=None):
    """Faz uma requisição à API-Football."""
    headers = {
        'x-apisports-key': API_KEY,
    }
    url = f'{API_BASE_URL}/{endpoint}'
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if data.get('errors'):
            logger.error(f"API errors: {data['errors']}")
            return None
        return data
    except Exception as e:
        logger.error(f"API request failed: {e}")
        return None


def get_live_fixtures():
    """Busca jogos da Copa 2026 em andamento."""
    logger.info("Buscando jogos ao vivo...")
    data = api_request('fixtures', {
        'league': LEAGUE_ID,
        'season': SEASON,
        'live': 'all'
    })
    if data and data.get('results', 0) > 0:
        logger.info(f"Encontrados {data['results']} jogos ao vivo")
        return data['response']
    logger.info("Nenhum jogo ao vivo encontrado")
    return []


def get_today_fixtures():
    """
    Busca jogos da Copa 2026 de hoje E de ontem (data UTC).
    Jogos que comecam a noite no Brasil (ex: 19h BRT = 22h UTC) podem
    terminar depois da meia-noite UTC, caindo na data UTC de ontem -- sem
    isso, o resultado final desses jogos nunca seria capturado pelo modo
    'post' assim que o dia UTC virasse.
    """
    now_utc = datetime.now(timezone.utc)
    dates = [
        (now_utc - timedelta(days=1)).strftime('%Y-%m-%d'),
        now_utc.strftime('%Y-%m-%d'),
    ]
    fixtures = []
    seen_ids = set()
    for date_str in dates:
        logger.info(f"Buscando jogos do dia {date_str}...")
        data = api_request('fixtures', {
            'league': LEAGUE_ID,
            'season': SEASON,
            'date': date_str
        })
        if data and data.get('results', 0) > 0:
            for fixture in data['response']:
                fid = fixture['fixture']['id']
                if fid not in seen_ids:
                    seen_ids.add(fid)
                    fixtures.append(fixture)
    logger.info(f"Encontrados {len(fixtures)} jogos entre as duas datas")
    return fixtures


def get_all_finished_fixtures():
    """Busca todos os jogos finalizados da Copa 2026 (para varredura noturna)."""
    logger.info("Buscando todos os jogos finalizados da Copa 2026...")
    data = api_request('fixtures', {
        'league': LEAGUE_ID,
        'season': SEASON,
    })
    if data and data.get('results', 0) > 0:
        finished = [f for f in data['response']
                    if f['fixture']['status']['short'] in FINISHED_STATUSES]
        logger.info(f"Total de jogos finalizados: {len(finished)}")
        return finished
    return []


# ============================================================
# FUNÇÕES DO BANCO NEON
# ============================================================

def get_db_connection():
    """Cria conexão com o banco Neon."""
    try:
        conn = psycopg2.connect(NEON_CONN)
        return conn
    except Exception as e:
        logger.error(f"Falha ao conectar ao banco: {e}")
        return None


def get_pending_matches(conn):
    """Busca jogos no banco que ainda não têm resultado (status != 'finished')."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, match_number, team1_code, team2_code, datetime, status,
               team1_score, team2_score, phase, "group"
        FROM matches
        WHERE status != 'finished'
        ORDER BY match_number;
    """)
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    return [dict(zip(columns, row)) for row in rows]


def update_match_result(conn, match_id, team1_score, team2_score, status='finished'):
    """Atualiza o resultado de um jogo no banco."""
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE matches
        SET team1_score = %s,
            team2_score = %s,
            status = %s,
            updated_at = NOW()
        WHERE id = %s
          AND (status != 'finished' OR status IS NULL);
    """, (team1_score, team2_score, status, match_id))
    updated = cursor.rowcount
    conn.commit()
    cursor.close()
    return updated > 0


def update_match_live(conn, match_id, team1_score, team2_score):
    """Atualiza o placar de um jogo ao vivo (sem marcar como finished)."""
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE matches
        SET team1_score = %s,
            team2_score = %s,
            status = 'live',
            updated_at = NOW()
        WHERE id = %s
          AND status != 'finished';
    """, (team1_score, team2_score, match_id))
    updated = cursor.rowcount
    conn.commit()
    cursor.close()
    return updated > 0


def score_finished_match(conn, match_id, team1_score, team2_score):
    """Calcula e salva pontos para todos os palpites de um jogo finalizado."""
    cursor = conn.cursor()

    # Busca config de pontuação do banco (com defaults caso não esteja configurado)
    cursor.execute("""
        SELECT key, value FROM config
        WHERE key IN ('pontos_placar_exato','pontos_resultado_gols',
                      'pontos_resultado','pontos_gols','pontos_nenhum')
    """)
    config = {row[0]: int(row[1]) for row in cursor.fetchall()}
    pts_exato    = config.get('pontos_placar_exato', 20)
    pts_res_gols = config.get('pontos_resultado_gols', 15)
    pts_res      = config.get('pontos_resultado', 10)
    pts_gols     = config.get('pontos_gols', 5)
    pts_nenhum   = config.get('pontos_nenhum', 0)

    # Busca todos os palpites deste jogo
    cursor.execute("""
        SELECT id, pred_team1_score, pred_team2_score
        FROM predictions
        WHERE match_id = %s
          AND pred_team1_score IS NOT NULL
          AND pred_team2_score IS NOT NULL
    """, (match_id,))
    preds = cursor.fetchall()

    if not preds:
        cursor.close()
        return 0

    real_result = 'team1' if team1_score > team2_score else ('team2' if team1_score < team2_score else 'draw')

    updated = 0
    for pred_id, p1, p2 in preds:
        pred_result = 'team1' if p1 > p2 else ('team2' if p1 < p2 else 'draw')
        acertou_resultado = pred_result == real_result
        acertou_p1 = p1 == team1_score
        acertou_p2 = p2 == team2_score

        if acertou_p1 and acertou_p2:
            pts, tipo, desc = pts_exato, 'placar_exato', 'Placar exato!'
        elif acertou_resultado and (acertou_p1 or acertou_p2):
            pts, tipo, desc = pts_res_gols, 'resultado_gols', 'Resultado + gols de um time'
        elif acertou_resultado:
            pts, tipo, desc = pts_res, 'resultado', 'Resultado correto'
        elif acertou_p1 or acertou_p2:
            pts, tipo, desc = pts_gols, 'gols', 'Gols de um time'
        else:
            pts, tipo, desc = pts_nenhum, 'nenhum', 'Nao pontuou'

        cursor.execute("""
            UPDATE predictions
            SET points_awarded = %s,
                points_type = %s,
                breakdown = %s
            WHERE id = %s
        """, (pts, tipo, desc, pred_id))
        updated += 1

    conn.commit()
    cursor.close()
    if updated > 0:
        logger.info(f"  Pontuacao calculada para {updated} palpites do jogo #{match_id}")
    return updated


def lock_missing_predictions(conn):
    """
    Regra do bolão: palpite não salvo até o início do jogo é registrado
    automaticamente como 0 x 0 (valor padrão exibido na tela de palpites).

    Idempotente: só insere onde não existe palpite, apenas para jogos que já
    começaram. Para jogos já finalizados, recalcula a pontuação dos palpites
    recém-criados via score_finished_match.
    """
    cursor = conn.cursor()

    brazil_tz = pytz.timezone('America/Sao_Paulo')
    now_naive = datetime.now(brazil_tz).replace(tzinfo=None)

    cursor.execute("""
        INSERT INTO predictions (user_id, match_id, pred_team1_score, pred_team2_score, created_at)
        SELECT u.id, m.id, 0, 0, NOW()
        FROM users u
        CROSS JOIN matches m
        WHERE u.active = TRUE
          AND u.role <> 'admin'
          AND m.datetime <= %s
          AND NOT EXISTS (
              SELECT 1 FROM predictions p
              WHERE p.user_id = u.id AND p.match_id = m.id
          )
        RETURNING match_id
    """, (now_naive,))
    rows = cursor.fetchall()
    conn.commit()

    if not rows:
        cursor.close()
        return 0

    match_ids = sorted({r[0] for r in rows})
    logger.info(f"Palpites 0x0 automaticos criados: {len(rows)} (jogos id {match_ids})")

    # Recalcula pontos dos jogos afetados que já têm placar final
    cursor.execute("""
        SELECT id, team1_score, team2_score FROM matches
        WHERE id = ANY(%s)
          AND status = 'finished'
          AND team1_score IS NOT NULL
          AND team2_score IS NOT NULL
    """, (match_ids,))
    finished = cursor.fetchall()
    cursor.close()

    for mid, s1, s2 in finished:
        score_finished_match(conn, mid, s1, s2)

    return len(rows)


# ============================================================
# PROPAGAÇÃO DE CONFRONTOS DO MATA-MATA
# ============================================================

def _calculate_group_standings_with_tiebreak(matches_rows):
    """
    Calcula a classificação de um grupo a partir das linhas de `matches`
    (team1_id, team2_id, team1_score, team2_score), aplicando pontos, saldo
    de gols, gols marcados e, em caso de empate total, confronto direto
    entre os times empatados (critério oficial da FIFA).
    """
    teams_stats = {}
    h2h_matches = []

    for team1_id, team2_id, gols1, gols2 in matches_rows:
        if team1_id is None or team2_id is None or gols1 is None or gols2 is None:
            continue

        for team_id in (team1_id, team2_id):
            if team_id not in teams_stats:
                teams_stats[team_id] = {'team_id': team_id, 'points': 0, 'goals_for': 0, 'goals_against': 0}

        teams_stats[team1_id]['goals_for'] += gols1
        teams_stats[team1_id]['goals_against'] += gols2
        teams_stats[team2_id]['goals_for'] += gols2
        teams_stats[team2_id]['goals_against'] += gols1

        if gols1 > gols2:
            teams_stats[team1_id]['points'] += 3
        elif gols2 > gols1:
            teams_stats[team2_id]['points'] += 3
        else:
            teams_stats[team1_id]['points'] += 1
            teams_stats[team2_id]['points'] += 1

        h2h_matches.append((team1_id, team2_id, gols1, gols2))

    for stats in teams_stats.values():
        stats['goal_difference'] = stats['goals_for'] - stats['goals_against']

    standings = sorted(
        teams_stats.values(),
        key=lambda x: (x['points'], x['goal_difference'], x['goals_for']),
        reverse=True
    )

    # Desempate por confronto direto entre times empatados em pontos/saldo/gols
    result = []
    i = 0
    n = len(standings)
    while i < n:
        j = i
        key_i = (standings[i]['points'], standings[i]['goal_difference'], standings[i]['goals_for'])
        while j + 1 < n and (
            standings[j + 1]['points'], standings[j + 1]['goal_difference'], standings[j + 1]['goals_for']
        ) == key_i:
            j += 1

        cluster = standings[i:j + 1]
        if len(cluster) > 1:
            cluster_ids = {item['team_id'] for item in cluster}
            mini = {item['team_id']: {'points': 0, 'goals_for': 0, 'goals_against': 0} for item in cluster}
            for t1, t2, g1, g2 in h2h_matches:
                if t1 not in cluster_ids or t2 not in cluster_ids:
                    continue
                mini[t1]['goals_for'] += g1
                mini[t1]['goals_against'] += g2
                mini[t2]['goals_for'] += g2
                mini[t2]['goals_against'] += g1
                if g1 > g2:
                    mini[t1]['points'] += 3
                elif g2 > g1:
                    mini[t2]['points'] += 3
                else:
                    mini[t1]['points'] += 1
                    mini[t2]['points'] += 1

            cluster = sorted(
                cluster,
                key=lambda item: (
                    mini[item['team_id']]['points'],
                    mini[item['team_id']]['goals_for'] - mini[item['team_id']]['goals_against'],
                    mini[item['team_id']]['goals_for'],
                ),
                reverse=True
            )
        result.extend(cluster)
        i = j + 1

    return result


def score_group_predictions(conn, group, first_id, second_id):
    """
    Calcula e salva os pontos dos palpites de classificação (group_predictions)
    de um grupo já decidido. Os palpites foram travados no início da Copa
    (auto_lock_group_predictions.py), então usa o valor já salvo em cada
    linha sem nenhuma alteração — só lê e pontua.
    """
    cursor = conn.cursor()

    cursor.execute("""
        SELECT key, value FROM config
        WHERE key IN ('grupo_ordem_correta', 'grupo_ordem_invertida', 'grupo_um_certo')
    """)
    config = {row[0]: int(row[1]) for row in cursor.fetchall()}
    pts_ordem_correta = config.get('grupo_ordem_correta', 20)
    pts_ordem_invertida = config.get('grupo_ordem_invertida', 10)
    pts_um_certo = config.get('grupo_um_certo', 5)

    cursor.execute("""
        SELECT id, first_place_team_id, second_place_team_id
        FROM group_predictions
        WHERE group_name = %s
    """, (group,))
    preds = cursor.fetchall()

    updated = 0
    for pred_id, pred_first, pred_second in preds:
        if pred_first is None or pred_second is None:
            pts, desc = 0, "Palpite incompleto"
        elif pred_first == first_id and pred_second == second_id:
            pts, desc = pts_ordem_correta, "Acertou 1º e 2º na ordem!"
        elif pred_first == second_id and pred_second == first_id:
            pts, desc = pts_ordem_invertida, "Acertou os 2 classificados (ordem invertida)"
        elif pred_first in (first_id, second_id) or pred_second in (first_id, second_id):
            pts, desc = pts_um_certo, "Acertou 1 classificado (posição errada)"
        else:
            pts, desc = 0, "Nao pontuou"

        cursor.execute("""
            UPDATE group_predictions
            SET points_awarded = %s, breakdown = %s
            WHERE id = %s
        """, (pts, desc, pred_id))
        updated += 1

    conn.commit()
    cursor.close()
    if updated > 0:
        logger.info(f"  Pontuacao de classificados calculada para {updated} palpite(s) do Grupo {group}")
    return updated


def update_completed_group_results(conn):
    """
    Para cada grupo com todos os jogos finalizados, calcula 1º e 2º lugar
    (com desempate por confronto direto), atualiza group_results — que
    alimenta propagate_group_results() — e pontua os palpites de
    classificação (group_predictions) desse grupo.
    """
    cursor = conn.cursor()
    updated = 0

    for group in list('ABCDEFGHIJKL'):
        # Verifica se todos os jogos do grupo estão finalizados
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'finished' THEN 1 ELSE 0 END) as finished
            FROM matches
            WHERE "group" = %s AND phase = 'Grupos'
        """, (group,))
        row = cursor.fetchone()
        if not row or row[0] == 0 or row[0] != row[1]:
            continue  # Grupo incompleto ou sem jogos

        # Já tinha resultado calculado antes? Evita reprocessar/repontuar sem necessidade
        cursor.execute("SELECT first_place_team_id, second_place_team_id FROM group_results WHERE group_name = %s", (group,))
        existing = cursor.fetchone()

        cursor.execute("""
            SELECT team1_id, team2_id, team1_score, team2_score
            FROM matches
            WHERE "group" = %s AND phase = 'Grupos' AND status = 'finished'
        """, (group,))
        matches_rows = cursor.fetchall()

        standings = _calculate_group_standings_with_tiebreak(matches_rows)
        if len(standings) < 2:
            continue

        first_id, second_id = standings[0]['team_id'], standings[1]['team_id']

        if existing and existing[0] == first_id and existing[1] == second_id:
            continue  # Resultado já está correto, nada a fazer

        if existing:
            cursor.execute("""
                UPDATE group_results
                SET first_place_team_id = %s, second_place_team_id = %s
                WHERE group_name = %s
            """, (first_id, second_id, group))
        else:
            cursor.execute("""
                INSERT INTO group_results (group_name, first_place_team_id, second_place_team_id)
                VALUES (%s, %s, %s)
            """, (group, first_id, second_id))

        conn.commit()
        updated += 1
        logger.info(f"✅ Grupo {group} completo — 1º: {first_id}, 2º: {second_id}")

        score_group_predictions(conn, group, first_id, second_id)

    cursor.close()
    return updated


def propagate_knockout_winners(conn):
    """
    Propaga vencedores de jogos finalizados do mata-mata para a próxima fase.
    Resolve placeholders W73, W74, L101, etc.
    Retorna o número de jogos atualizados.
    """
    cursor = conn.cursor()
    updated = 0
    
    # Busca jogos finalizados do mata-mata com ambos os times e placar
    cursor.execute("""
        SELECT m.match_number, m.team1_id, m.team2_id, m.team1_score, m.team2_score,
               m.team1_code, m.team2_code,
               t1.code as t1_code, t1.name as t1_name,
               t2.code as t2_code, t2.name as t2_name
        FROM matches m
        JOIN teams t1 ON m.team1_id = t1.id
        JOIN teams t2 ON m.team2_id = t2.id
        WHERE m.phase != 'Grupos'
          AND m.status = 'finished'
          AND m.team1_score IS NOT NULL
          AND m.team2_score IS NOT NULL
    """)
    
    finished_matches = cursor.fetchall()
    
    for row in finished_matches:
        match_num, t1_id, t2_id, t1_score, t2_score, t1_code, t2_code, t1_cd, t1_nm, t2_cd, t2_nm = row
        
        # Determina vencedor e perdedor
        if t1_score > t2_score:
            winner_id, winner_code = t1_id, t1_cd
            loser_id, loser_code = t2_id, t2_cd
        elif t2_score > t1_score:
            winner_id, winner_code = t2_id, t2_cd
            loser_id, loser_code = t1_id, t1_cd
        else:
            # Empate no mata-mata - não deveria acontecer
            logger.warning(f"Jogo #{match_num} empatado no mata-mata, não propaga")
            continue
        
        w_code = f"W{match_num}"
        l_code = f"L{match_num}"
        
        # Atualiza jogos que têm W{match_num} como team1
        cursor.execute("""
            UPDATE matches SET team1_id = %s, team1_code = %s
            WHERE team1_code = %s AND team1_id IS NULL
        """, (winner_id, winner_code, w_code))
        updated += cursor.rowcount
        
        # Atualiza jogos que têm W{match_num} como team2
        cursor.execute("""
            UPDATE matches SET team2_id = %s, team2_code = %s
            WHERE team2_code = %s AND team2_id IS NULL
        """, (winner_id, winner_code, w_code))
        updated += cursor.rowcount
        
        # Atualiza jogos que têm L{match_num} como team1 (disputa de 3º)
        cursor.execute("""
            UPDATE matches SET team1_id = %s, team1_code = %s
            WHERE team1_code = %s AND team1_id IS NULL
        """, (loser_id, loser_code, l_code))
        updated += cursor.rowcount
        
        # Atualiza jogos que têm L{match_num} como team2 (disputa de 3º)
        cursor.execute("""
            UPDATE matches SET team2_id = %s, team2_code = %s
            WHERE team2_code = %s AND team2_id IS NULL
        """, (loser_id, loser_code, l_code))
        updated += cursor.rowcount
    
    if updated > 0:
        conn.commit()
        logger.info(f"🔄 Propagados {updated} confronto(s) do mata-mata")
    
    cursor.close()
    return updated


def propagate_group_results(conn):
    """
    Propaga classificados dos grupos (1º e 2º) para jogos R32.
    Resolve placeholders 1A, 2B, etc.
    Retorna o número de jogos atualizados.
    """
    cursor = conn.cursor()
    updated = 0
    
    # Busca resultados de grupo definidos
    cursor.execute("""
        SELECT gr.group_name, gr.first_place_team_id, gr.second_place_team_id,
               t1.code as first_code, t2.code as second_code
        FROM group_results gr
        JOIN teams t1 ON gr.first_place_team_id = t1.id
        JOIN teams t2 ON gr.second_place_team_id = t2.id
    """)
    
    for row in cursor.fetchall():
        group_name, first_id, second_id, first_code, second_code = row
        
        first_placeholder = f"1{group_name}"  # Ex: "1A"
        second_placeholder = f"2{group_name}"  # Ex: "2A"
        
        # Atualiza jogos com placeholder do 1º lugar
        cursor.execute("""
            UPDATE matches SET team1_id = %s, team1_code = %s
            WHERE team1_code = %s AND team1_id IS NULL
        """, (first_id, first_code, first_placeholder))
        updated += cursor.rowcount
        
        cursor.execute("""
            UPDATE matches SET team2_id = %s, team2_code = %s
            WHERE team2_code = %s AND team2_id IS NULL
        """, (first_id, first_code, first_placeholder))
        updated += cursor.rowcount
        
        # Atualiza jogos com placeholder do 2º lugar
        cursor.execute("""
            UPDATE matches SET team1_id = %s, team1_code = %s
            WHERE team1_code = %s AND team1_id IS NULL
        """, (second_id, second_code, second_placeholder))
        updated += cursor.rowcount
        
        cursor.execute("""
            UPDATE matches SET team2_id = %s, team2_code = %s
            WHERE team2_code = %s AND team2_id IS NULL
        """, (second_id, second_code, second_placeholder))
        updated += cursor.rowcount
    
    if updated > 0:
        conn.commit()
        logger.info(f"🔄 Propagados {updated} classificado(s) de grupo para R32")
    
    cursor.close()
    return updated


# ============================================================
# LÓGICA DE MATCHING E ATUALIZAÇÃO
# ============================================================

def match_fixture_to_db(fixture, pending_matches):
    """
    Encontra o jogo correspondente no banco Neon baseado nos times.
    Retorna o match do banco ou None.
    """
    home_name = fixture['teams']['home']['name']
    away_name = fixture['teams']['away']['name']

    home_code = API_NAME_TO_NEON_CODE.get(home_name)
    away_code = API_NAME_TO_NEON_CODE.get(away_name)

    if not home_code or not away_code:
        logger.warning(f"Time não mapeado: {home_name} ou {away_name}")
        return None

    # Procurar jogo no banco onde os times batem (em qualquer ordem)
    for match in pending_matches:
        db_t1 = match['team1_code']
        db_t2 = match['team2_code']
        if (db_t1 == home_code and db_t2 == away_code) or \
           (db_t1 == away_code and db_t2 == home_code):
            # Retornar match com info de quem é home/away na API
            match['_api_home_code'] = home_code
            match['_api_away_code'] = away_code
            return match

    return None


def process_fixture(conn, fixture, pending_matches, mode='post'):
    """
    Processa um fixture da API e atualiza o banco.
    Retorna True se atualizou, False caso contrário.
    """
    fix_info = fixture['fixture']
    status_short = fix_info['status']['short']
    home_name = fixture['teams']['home']['name']
    away_name = fixture['teams']['away']['name']
    goals_home = fixture['goals']['home']
    goals_away = fixture['goals']['away']

    # Encontrar jogo correspondente no banco
    db_match = match_fixture_to_db(fixture, pending_matches)
    if not db_match:
        logger.debug(f"Jogo não encontrado no banco: {home_name} vs {away_name}")
        return False

    # Determinar scores na ordem correta do banco
    home_code = db_match['_api_home_code']
    if db_match['team1_code'] == home_code:
        team1_score = goals_home
        team2_score = goals_away
    else:
        team1_score = goals_away
        team2_score = goals_home

    if team1_score is None or team2_score is None:
        logger.debug(f"Placar não disponível: {home_name} vs {away_name}")
        return False

    match_id = db_match['id']
    match_num = db_match['match_number']

    # Jogo finalizado
    if status_short in FINISHED_STATUSES:
        if db_match['status'] == 'finished':
            logger.debug(f"Jogo #{match_num} já finalizado no banco, pulando")
            return False
        success = update_match_result(conn, match_id, team1_score, team2_score, 'finished')
        if success:
            logger.info(f"✅ Jogo #{match_num} FINALIZADO: {db_match['team1_code']} {team1_score} x {team2_score} {db_match['team2_code']}")
            score_finished_match(conn, match_id, team1_score, team2_score)
        return success

    # Jogo ao vivo (só atualiza no modo live)
    elif status_short in LIVE_STATUSES and mode == 'live':
        elapsed = fix_info['status'].get('elapsed', '?')
        success = update_match_live(conn, match_id, team1_score, team2_score)
        if success:
            logger.info(f"🔴 Jogo #{match_num} AO VIVO ({elapsed}'): {db_match['team1_code']} {team1_score} x {team2_score} {db_match['team2_code']}")
        return success

    return False


# ============================================================
# MODOS DE EXECUÇÃO
# ============================================================

def run_live():
    """Modo LIVE: atualiza jogos em andamento."""
    logger.info("=" * 50)
    logger.info("MODO LIVE - Atualizando jogos em andamento")
    logger.info("=" * 50)

    conn = get_db_connection()
    if not conn:
        return

    try:
        # Palpites não salvos viram 0x0 quando o jogo começa
        lock_missing_predictions(conn)

        pending = get_pending_matches(conn)
        if not pending:
            logger.info("Nenhum jogo pendente no banco")
            return

        fixtures = get_live_fixtures()
        if not fixtures:
            return

        updated = 0
        for fixture in fixtures:
            if process_fixture(conn, fixture, pending, mode='live'):
                updated += 1

        logger.info(f"Total de jogos atualizados: {updated}")
    finally:
        conn.close()


def run_post():
    """Modo POST: atualiza jogos finalizados do dia."""
    logger.info("=" * 50)
    logger.info("MODO POST - Atualizando jogos finalizados do dia")
    logger.info("=" * 50)

    conn = get_db_connection()
    if not conn:
        return

    try:
        # Palpites não salvos viram 0x0 quando o jogo começa
        lock_missing_predictions(conn)

        pending = get_pending_matches(conn)
        if not pending:
            logger.info("Nenhum jogo pendente no banco")
            return

        fixtures = get_today_fixtures()
        if not fixtures:
            return

        updated = 0
        for fixture in fixtures:
            if process_fixture(conn, fixture, pending, mode='post'):
                updated += 1

        logger.info(f"Total de jogos atualizados: {updated}")
        
        # Propaga confrontos do mata-mata
        if updated > 0:
            update_completed_group_results(conn)
            prop_groups = propagate_group_results(conn)
            prop_knockout = propagate_knockout_winners(conn)
            if prop_groups + prop_knockout > 0:
                logger.info(f"Propagados: {prop_groups} de grupo + {prop_knockout} de mata-mata")
    finally:
        conn.close()


def run_nightly():
    """Modo NIGHTLY: varredura de todos os jogos finalizados não registrados."""
    logger.info("=" * 50)
    logger.info("MODO NIGHTLY - Varredura completa de segurança")
    logger.info("=" * 50)

    conn = get_db_connection()
    if not conn:
        return

    try:
        pending = get_pending_matches(conn)
        if not pending:
            logger.info("Nenhum jogo pendente no banco")
            return

        logger.info(f"Jogos pendentes no banco: {len(pending)}")

        fixtures = get_all_finished_fixtures()
        if not fixtures:
            return

        updated = 0
        for fixture in fixtures:
            if process_fixture(conn, fixture, pending, mode='post'):
                updated += 1

        logger.info(f"Total de jogos atualizados na varredura: {updated}")
        
        # Propaga confrontos do mata-mata (sempre na varredura noturna)
        update_completed_group_results(conn)
        prop_groups = propagate_group_results(conn)
        prop_knockout = propagate_knockout_winners(conn)
        if prop_groups + prop_knockout > 0:
            logger.info(f"Propagados: {prop_groups} de grupo + {prop_knockout} de mata-mata")

        # Garante pontuação de todos os jogos finalizados sem pontuação
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, team1_score, team2_score FROM matches
            WHERE status = 'finished'
              AND team1_score IS NOT NULL
              AND EXISTS (
                SELECT 1 FROM predictions p
                WHERE p.match_id = matches.id
                  AND p.points_awarded IS NULL
              )
        """)
        unscored = cursor.fetchall()
        cursor.close()
        if unscored:
            logger.info(f"Pontuando {len(unscored)} jogos finalizados sem pontuação")
            for match_id, s1, s2 in unscored:
                score_finished_match(conn, match_id, s1, s2)

        # Verificar jogos que deveriam ter resultado mas não foram atualizados
        remaining = get_pending_matches(conn)
        now = datetime.now(timezone.utc)
        brazil_tz = pytz.timezone('America/Sao_Paulo')
        overdue = [m for m in remaining
                   if m['datetime'] and brazil_tz.localize(m['datetime']).astimezone(timezone.utc) < now - timedelta(hours=3)]
        if overdue:
            logger.warning(f"⚠️ {len(overdue)} jogos com mais de 3h sem resultado:")
            for m in overdue:
                logger.warning(f"  Jogo #{m['match_number']}: {m['team1_code']} vs {m['team2_code']} ({m['datetime']})")
    finally:
        conn.close()


# ============================================================
# MAIN
# ============================================================

def main():
    if not API_KEY:
        logger.error("API_FOOTBALL_KEY não configurada!")
        sys.exit(1)
    if not NEON_CONN:
        logger.error("NEON_CONNECTION_STRING não configurada!")
        sys.exit(1)

    # Verificar modo de execução
    mode = 'post'  # default
    if len(sys.argv) > 2 and sys.argv[1] == '--mode':
        mode = sys.argv[2]

    if mode == 'live':
        run_live()
    elif mode == 'post':
        run_post()
    elif mode == 'nightly':
        run_nightly()
    else:
        logger.error(f"Modo desconhecido: {mode}")
        logger.info("Modos disponíveis: live, post, nightly")
        sys.exit(1)


if __name__ == '__main__':
    main()
