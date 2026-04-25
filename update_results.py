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

API_KEY = os.environ.get('API_FOOTBALL_KEY', '')
NEON_CONN = os.environ.get('NEON_CONNECTION_STRING', '')
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
    """Busca todos os jogos da Copa 2026 de hoje."""
    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    logger.info(f"Buscando jogos do dia {today}...")
    data = api_request('fixtures', {
        'league': LEAGUE_ID,
        'season': SEASON,
        'date': today
    })
    if data and data.get('results', 0) > 0:
        logger.info(f"Encontrados {data['results']} jogos hoje")
        return data['response']
    logger.info("Nenhum jogo encontrado para hoje")
    return []


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


# ============================================================
# PROPAGAÇÃO DE CONFRONTOS DO MATA-MATA
# ============================================================

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
        prop_groups = propagate_group_results(conn)
        prop_knockout = propagate_knockout_winners(conn)
        if prop_groups + prop_knockout > 0:
            logger.info(f"Propagados: {prop_groups} de grupo + {prop_knockout} de mata-mata")

        # Verificar jogos que deveriam ter resultado mas não foram atualizados
        remaining = get_pending_matches(conn)
        now = datetime.now(timezone.utc)
        overdue = [m for m in remaining
                   if m['datetime'] and m['datetime'].replace(tzinfo=timezone.utc) < now - timedelta(hours=3)]
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
