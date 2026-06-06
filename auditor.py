"""
VAR — Verificação e Auditoria do Resultado
Agente de auditoria do Bolão Copa 2026.

Lê o banco, verifica integridade dos palpites, alerta usuários via Telegram.
Nunca altera palpites — somente leitura (exceto contador de controle na config).

Uso:
  python auditor.py          # modo normal (envia Telegram só se houver alertas ou jogo próximo)
  python auditor.py --full   # força relatório completo mesmo sem alertas (primeiro uso)
"""

import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta

import psycopg2
import pytz

BRAZIL_TZ = pytz.timezone("America/Sao_Paulo")
WINDOW_HOURS = 2.5   # alerta para jogos que começam em até X horas


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

def send_telegram(token: str, chat_id: str, text: str):
    """Envia mensagem via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "HTML"}).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"  Telegram: falha ao enviar ({e})")


# ---------------------------------------------------------------------------
# Conexão
# ---------------------------------------------------------------------------

def get_connection():
    conn_str = os.environ.get("NEON_CONNECTION_STRING") or os.environ.get("DATABASE_URL")
    if not conn_str:
        raise RuntimeError("NEON_CONNECTION_STRING não configurada")
    return psycopg2.connect(conn_str.strip())


def now_brazil():
    return datetime.now(BRAZIL_TZ).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Verificações
# ---------------------------------------------------------------------------

def check_db_health(cur) -> list[str]:
    """Verifica conectividade e contagens básicas."""
    alerts = []
    cur.execute("SELECT COUNT(*) FROM predictions")
    pred_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM group_predictions")
    group_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM podium_predictions")
    podium_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM users WHERE active = true AND role != 'admin'")
    user_count = cur.fetchone()[0]

    if pred_count == 0 and user_count > 0:
        alerts.append("⚠️ Nenhum palpite de jogo encontrado no banco!")
    return alerts, pred_count, group_count, podium_count, user_count


def check_upcoming_no_prediction(cur) -> list[str]:
    """Jogos iniciando nas próximas WINDOW_HOURS sem palpite de algum usuário ativo."""
    alerts = []
    now = now_brazil()
    limite = now + timedelta(hours=WINDOW_HOURS)

    # Jogos futuros dentro da janela
    cur.execute("""
        SELECT m.id, m.match_number, m.datetime,
               COALESCE(t1.flag || ' ' || t1.name, m.team1_code) AS team1,
               COALESCE(t2.flag || ' ' || t2.name, m.team2_code) AS team2
        FROM matches m
        LEFT JOIN teams t1 ON m.team1_id = t1.id
        LEFT JOIN teams t2 ON m.team2_id = t2.id
        WHERE m.status = 'scheduled'
          AND m.datetime > %s
          AND m.datetime <= %s
        ORDER BY m.datetime
    """, (now, limite))
    upcoming = cur.fetchall()

    if not upcoming:
        return alerts

    # Usuários ativos (não admin)
    cur.execute("""
        SELECT id, name FROM users
        WHERE active = true AND role != 'admin'
        ORDER BY name
    """)
    users = cur.fetchall()
    if not users:
        return alerts

    user_ids = {u[0]: u[1] for u in users}

    for match_id, match_num, match_dt, team1, team2 in upcoming:
        # Quem já palpitou para este jogo
        cur.execute("""
            SELECT user_id FROM predictions
            WHERE match_id = %s
              AND pred_team1_score IS NOT NULL
              AND pred_team2_score IS NOT NULL
        """, (match_id,))
        palpitaram = {r[0] for r in cur.fetchall()}

        faltam = [name for uid, name in user_ids.items() if uid not in palpitaram]
        if faltam:
            hora_jogo = match_dt.strftime("%H:%M")
            minutos = int((match_dt - now).total_seconds() / 60)
            faltam_str = ", ".join(faltam)
            alerts.append(
                f"⏰ <b>Jogo #{match_num} em {minutos}min ({hora_jogo} Brasília)</b>\n"
                f"   {team1} x {team2}\n"
                f"   Sem palpite: {faltam_str}"
            )
    return alerts


def check_invalid_predictions(cur) -> list[str]:
    """Palpites com valores NULL onde não deveria ter."""
    alerts = []
    cur.execute("""
        SELECT p.id, u.name, m.match_number
        FROM predictions p
        JOIN users u ON p.user_id = u.id
        JOIN matches m ON p.match_id = m.id
        WHERE p.pred_team1_score IS NULL OR p.pred_team2_score IS NULL
        ORDER BY p.id
    """)
    rows = cur.fetchall()
    if rows:
        detalhe = ", ".join(f"{r[1]} (jogo #{r[2]})" for r in rows[:5])
        extras = f" e mais {len(rows)-5}" if len(rows) > 5 else ""
        alerts.append(f"🚨 {len(rows)} palpite(s) com placar NULL: {detalhe}{extras}")
    return alerts


def check_duplicate_predictions(cur) -> list[str]:
    """Palpites duplicados (mesmo user_id + match_id)."""
    alerts = []
    cur.execute("""
        SELECT user_id, match_id, COUNT(*) AS cnt
        FROM predictions
        GROUP BY user_id, match_id
        HAVING COUNT(*) > 1
    """)
    rows = cur.fetchall()
    if rows:
        alerts.append(f"🚨 {len(rows)} combinação(ões) user+jogo com palpites DUPLICADOS")
    return alerts


def check_invalid_group_predictions(cur) -> list[str]:
    """GroupPrediction com 1º == 2º lugar."""
    alerts = []
    cur.execute("""
        SELECT gp.id, u.name, gp.group_name
        FROM group_predictions gp
        JOIN users u ON gp.user_id = u.id
        WHERE gp.first_place_team_id IS NOT NULL
          AND gp.first_place_team_id = gp.second_place_team_id
    """)
    rows = cur.fetchall()
    if rows:
        detalhe = ", ".join(f"{r[1]} Grupo {r[2]}" for r in rows)
        alerts.append(f"🚨 Palpites de grupo inválidos (1º = 2º): {detalhe}")
    return alerts


def check_invalid_podium_predictions(cur) -> list[str]:
    """PodiumPrediction com times duplicados nas 3 posições."""
    alerts = []
    cur.execute("""
        SELECT pp.id, u.name
        FROM podium_predictions pp
        JOIN users u ON pp.user_id = u.id
        WHERE pp.champion_team_id IS NOT NULL
          AND (
            pp.champion_team_id = pp.runner_up_team_id OR
            pp.champion_team_id = pp.third_place_team_id OR
            pp.runner_up_team_id = pp.third_place_team_id
          )
    """)
    rows = cur.fetchall()
    if rows:
        detalhe = ", ".join(r[1] for r in rows)
        alerts.append(f"🚨 Palpites de pódio com times repetidos: {detalhe}")
    return alerts


def check_unscored_finished(cur) -> list[str]:
    """Jogos finalizados com palpites que ainda não foram pontuados."""
    alerts = []
    cur.execute("""
        SELECT m.match_number,
               COALESCE(t1.flag || ' ' || t1.name, m.team1_code) AS team1,
               COALESCE(t2.flag || ' ' || t2.name, m.team2_code) AS team2,
               COUNT(p.id) AS sem_pontos
        FROM matches m
        JOIN predictions p ON p.match_id = m.id
        LEFT JOIN teams t1 ON m.team1_id = t1.id
        LEFT JOIN teams t2 ON m.team2_id = t2.id
        WHERE m.status = 'finished'
          AND p.points_awarded IS NULL
        GROUP BY m.id, m.match_number, team1, team2
        ORDER BY m.match_number
    """)
    rows = cur.fetchall()
    if rows:
        for match_num, team1, team2, cnt in rows:
            alerts.append(
                f"⚠️ Jogo #{match_num} ({team1} x {team2}) finalizado "
                f"sem pontuação para {cnt} palpite(s)"
            )
    return alerts


def check_prediction_count_drop(cur) -> list[str]:
    """Verifica se a contagem total de palpites caiu (possível deleção acidental)."""
    alerts = []
    cur.execute("SELECT COUNT(*) FROM predictions")
    current = cur.fetchone()[0]

    cur.execute("SELECT value FROM config WHERE key = 'var_pred_count_last'")
    row = cur.fetchone()
    previous = int(row[0]) if row else None

    if previous is not None and current < previous:
        diff = previous - current
        alerts.append(
            f"🚨 ALERTA: contagem de palpites caiu {diff} unidade(s)! "
            f"Era {previous}, agora é {current}. Verificar deleção acidental."
        )

    # Atualiza contador (única escrita permitida ao auditor)
    if previous is None:
        cur.execute(
            "INSERT INTO config (key, value, description, category) VALUES (%s, %s, %s, %s)",
            ("var_pred_count_last", str(current), "Última contagem de palpites pelo VAR", "sistema")
        )
    else:
        cur.execute(
            "UPDATE config SET value = %s WHERE key = 'var_pred_count_last'",
            (str(current),)
        )

    return alerts


def check_pre_copa_missing_predictions(cur) -> list[str]:
    """Quando a Copa começa em até 8 dias, lista quem não salvou pódio/grupos."""
    alerts = []
    now = now_brazil()

    cur.execute("SELECT value FROM config WHERE key = 'data_inicio_copa'")
    row = cur.fetchone()

    raw = row[0].strip() if row else ""
    copa_start = None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%d"):
        try:
            copa_start = datetime.strptime(raw, fmt)
            break
        except ValueError:
            continue
    if not copa_start:
        # Default: 11/06/2026 13:00 (início da Copa 2026)
        copa_start = datetime(2026, 6, 11, 13, 0)

    dias_ate_copa = (copa_start - now).days
    if dias_ate_copa > 8 or dias_ate_copa < 0:
        return alerts

    cur.execute(
        "SELECT id, name FROM users WHERE active = true AND role != 'admin' ORDER BY name"
    )
    users = cur.fetchall()

    sem_podio = []
    grupos_incompletos = []

    for user_id, name in users:
        cur.execute("""
            SELECT id FROM podium_predictions
            WHERE user_id = %s
              AND champion_team_id IS NOT NULL
              AND runner_up_team_id IS NOT NULL
              AND third_place_team_id IS NOT NULL
        """, (user_id,))
        if not cur.fetchone():
            sem_podio.append(name)

        cur.execute("""
            SELECT COUNT(DISTINCT group_name) FROM group_predictions
            WHERE user_id = %s
              AND first_place_team_id IS NOT NULL
              AND second_place_team_id IS NOT NULL
        """, (user_id,))
        feitos = cur.fetchone()[0]
        if feitos < 12:
            grupos_incompletos.append((name, feitos))

    if sem_podio:
        nomes = ", ".join(sem_podio)
        alerts.append(
            f"🏆 <b>Palpite de Pódio não salvo</b> ({len(sem_podio)}/{len(users)}):\n"
            f"   {nomes}"
        )
    if grupos_incompletos:
        detalhe = ", ".join(f"{n} ({f}/12)" for n, f in grupos_incompletos)
        alerts.append(
            f"📋 <b>Palpites de Grupos incompletos</b>:\n"
            f"   {detalhe}"
        )
    if sem_podio or grupos_incompletos:
        alerts.append(
            f"⏰ Prazo: {copa_start.strftime('%d/%m/%Y às %H:%M')} — "
            f"faltam {dias_ate_copa} dia(s)!"
        )
    return alerts


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    force_full = "--full" in sys.argv

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não configurados — alertas desabilitados")

    print("=== VAR — Auditoria do Bolão Copa 2026 ===")
    now = now_brazil()
    print(f"Horário: {now.strftime('%d/%m/%Y %H:%M')} (Brasília)")

    conn = get_connection()
    cur = conn.cursor()

    # --- Saúde do banco ---
    health_alerts, pred_count, group_count, podium_count, user_count = check_db_health(cur)

    # --- Todas as verificações ---
    pre_copa_alerts   = check_pre_copa_missing_predictions(cur)
    upcoming_alerts   = check_upcoming_no_prediction(cur)
    invalid_preds     = check_invalid_predictions(cur)
    duplicate_preds   = check_duplicate_predictions(cur)
    invalid_groups    = check_invalid_group_predictions(cur)
    invalid_podium    = check_invalid_podium_predictions(cur)
    unscored          = check_unscored_finished(cur)
    count_drop        = check_prediction_count_drop(cur)
    conn.commit()

    all_alerts = (
        health_alerts + pre_copa_alerts + upcoming_alerts + invalid_preds +
        duplicate_preds + invalid_groups + invalid_podium +
        unscored + count_drop
    )

    # Log no console sempre
    summary = (
        f"DB: {pred_count} preds | {group_count} group_preds | "
        f"{podium_count} podium_preds | {user_count} usuários ativos"
    )
    print(summary)
    if all_alerts:
        for a in all_alerts:
            print(" •", a.replace("<b>", "").replace("</b>", ""))
    else:
        print("Nenhum alerta — sistema saudável.")

    cur.close()
    conn.close()

    # --- Telegram ---
    # Envia sempre se houver alertas, ou se --full foi passado
    has_upcoming = bool(upcoming_alerts)
    has_critical  = bool(
        pre_copa_alerts + invalid_preds + duplicate_preds + invalid_groups +
        invalid_podium + unscored + count_drop + health_alerts
    )

    if not (all_alerts or force_full):
        print("Sem alertas e sem --full — Telegram não enviado (anti-spam).")
        return

    ts = now.strftime("%d/%m/%Y %H:%M")
    linhas = [f"⚽ <b>VAR — Bolão Copa 2026</b> | {ts}\n"]
    linhas.append(f"📊 {summary}\n")

    if not all_alerts:
        linhas.append("✅ Sistema saudável — 0 alertas.")
    else:
        if pre_copa_alerts:
            linhas.append("─── ⚠️ Atenção: Copa em breve! ───")
            linhas.extend(pre_copa_alerts)
            linhas.append("")
        if has_upcoming:
            linhas.append("─── Palpites pendentes ───")
            linhas.extend(upcoming_alerts)
        if has_critical:
            linhas.append("\n─── Integridade ───")
            for a in (invalid_preds + duplicate_preds + invalid_groups +
                      invalid_podium + unscored + count_drop + health_alerts):
                linhas.append(a)

    msg = "\n".join(linhas)

    # Telegram tem limite de 4096 chars por mensagem
    if len(msg) > 4000:
        msg = msg[:3990] + "\n[...mensagem truncada]"

    if token and chat_id:
        send_telegram(token, chat_id, msg)
        print("Mensagem enviada ao Telegram.")
    else:
        print("(Telegram não configurado — mensagem não enviada)")
        print("--- Mensagem que seria enviada ---")
        print(msg)


if __name__ == "__main__":
    main()
