#!/usr/bin/env python3
"""
Script de Atualização Automática do Banco Neon PostgreSQL
Baixa dados de jogos internacionais do GitHub e atualiza o banco automaticamente
Fonte: https://github.com/martj42/international_results
"""

import os
import sys
import logging
from datetime import datetime
import requests
import psycopg2
from psycopg2.extras import execute_values
import csv
from io import StringIO

# Configuração de logging
LOG_FILE = '/home/ubuntu/analise-copa-2026/auto_update.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

# Configurações
GITHUB_CSV_URL = 'https://raw.githubusercontent.com/martj42/international_results/master/results.csv'
NEON_PROJECT_ID = 'restless-glitter-71170845'
NEON_CONNECTION_STRING = 'postgresql://neondb_owner:npg_J7SDEIpQ2rXB@ep-delicate-dust-ai3etwhj-pooler.c-4.us-east-1.aws.neon.tech/neondb?channel_binding=require&sslmode=require'


def get_last_update_date(conn):
    """Obtém a data do último jogo registrado no banco"""
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(date) FROM international_results;")
            result = cur.fetchone()
            last_date = result[0] if result and result[0] else None
            logging.info(f"Última data no banco: {last_date}")
            return last_date
    except Exception as e:
        logging.error(f"Erro ao obter última data: {e}")
        return None


def download_csv():
    """Baixa o CSV do GitHub"""
    try:
        logging.info(f"Baixando CSV de {GITHUB_CSV_URL}")
        response = requests.get(GITHUB_CSV_URL, timeout=30)
        response.raise_for_status()
        logging.info("CSV baixado com sucesso")
        return response.text
    except Exception as e:
        logging.error(f"Erro ao baixar CSV: {e}")
        raise


def parse_csv(csv_text, last_date=None):
    """
    Parseia o CSV e retorna apenas jogos novos
    Formato CSV: date,home_team,away_team,home_score,away_score,tournament,city,country,neutral
    """
    csv_reader = csv.DictReader(StringIO(csv_text))
    new_matches = []
    
    for row in csv_reader:
        try:
            match_date = datetime.strptime(row['date'], '%Y-%m-%d').date()
            
            # Se temos uma última data, só adiciona jogos mais recentes
            if last_date and match_date <= last_date:
                continue
            
            match_data = (
                match_date,
                row['home_team'],
                row['away_team'],
                int(row['home_score']),
                int(row['away_score']),
                row.get('tournament', ''),
                row.get('city', ''),
                row.get('country', ''),
                row.get('neutral', 'FALSE').upper() == 'TRUE'
            )
            new_matches.append(match_data)
            
        except Exception as e:
            logging.warning(f"Erro ao processar linha: {row}. Erro: {e}")
            continue
    
    logging.info(f"Total de jogos novos encontrados: {len(new_matches)}")
    return new_matches


def insert_matches(conn, matches):
    """Insere jogos novos no banco de dados"""
    if not matches:
        logging.info("Nenhum jogo novo para inserir")
        return 0
    
    try:
        with conn.cursor() as cur:
            insert_query = """
                INSERT INTO international_results 
                (date, home_team, away_team, home_score, away_score, tournament, city, country, neutral)
                VALUES %s
                ON CONFLICT DO NOTHING;
            """
            execute_values(cur, insert_query, matches)
            conn.commit()
            rows_inserted = cur.rowcount
            logging.info(f"Jogos inseridos: {rows_inserted}")
            return rows_inserted
    except Exception as e:
        conn.rollback()
        logging.error(f"Erro ao inserir jogos: {e}")
        raise


def log_update(conn, status, records_added=0, error_message=None):
    """Registra a execução do update no banco"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO update_log 
                (update_type, records_added, status, error_message, started_at, completed_at)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, (
                'international_results_auto_update',
                records_added,
                status,
                error_message,
                datetime.now(),
                datetime.now()
            ))
            conn.commit()
    except Exception as e:
        logging.warning(f"Erro ao registrar log no banco: {e}")


def main():
    """Função principal"""
    logging.info("=" * 80)
    logging.info("INICIANDO ATUALIZAÇÃO AUTOMÁTICA DO BANCO NEON")
    logging.info("=" * 80)
    
    conn = None
    records_added = 0
    
    try:
        # Conectar ao banco
        logging.info("Conectando ao banco Neon PostgreSQL...")
        conn = psycopg2.connect(NEON_CONNECTION_STRING)
        logging.info("Conexão estabelecida com sucesso")
        
        # Obter última data
        last_date = get_last_update_date(conn)
        
        # Baixar CSV
        csv_text = download_csv()
        
        # Parsear e filtrar jogos novos
        new_matches = parse_csv(csv_text, last_date)
        
        # Inserir jogos novos
        if new_matches:
            records_added = insert_matches(conn, new_matches)
            logging.info(f"✅ Atualização concluída: {records_added} jogos adicionados")
        else:
            logging.info("✅ Banco já está atualizado. Nenhum jogo novo encontrado.")
        
        # Registrar sucesso no log
        log_update(conn, 'success', records_added)
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"❌ Erro durante atualização: {error_msg}")
        if conn:
            log_update(conn, 'error', records_added, error_msg)
        sys.exit(1)
        
    finally:
        if conn:
            conn.close()
            logging.info("Conexão com banco fechada")
    
    logging.info("=" * 80)
    logging.info("ATUALIZAÇÃO FINALIZADA")
    logging.info("=" * 80)


if __name__ == "__main__":
    main()
