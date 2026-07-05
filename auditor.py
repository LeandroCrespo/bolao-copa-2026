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


def check_upcoming_no_prediction(cur):
    """Jogos iniciando nas próximas WINDOW_HOURS — sempre reporta status de palpites."""
    alerts = []        # jogos com palpites faltando
    ok_alerts = []     # jogos em que todos palpitaram
    now = now_brazil()
    limite = now + timedelta(hours=WINDOW_HOURS)

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
        return alerts, ok_alerts

    cur.execute("""
        SELECT id, name FROM users
        WHERE active = true AND role != 'admin'
        ORDER BY name
    """)
    users = cur.fetchall()
    if not users:
        return alerts, ok_alerts

    user_ids = {u[0]: u[1] for u in users}

    for match_id, match_num, match_dt, team1, team2 in upcoming:
        cur.execute("""
            SELECT user_id FROM predictions
            WHERE match_id = %s
              AND pred_team1_score IS NOT NULL
              AND pred_team2_score IS NOT NULL
              AND (
                pred_team1_score != 0 OR pred_team2_score != 0
                OR manually_confirmed = TRUE
              )
        """, (match_id,))
        palpitaram = {r[0] for r in cur.fetchall()}

        faltam = [name for uid, name in user_ids.items() if uid not in palpitaram]
        hora_jogo = match_dt.strftime("%H:%M")
        minutos = int((match_dt - now).total_seconds() / 60)

        if faltam:
            faltam_str = ", ".join(faltam)
            alerts.append(
                f"⏰ <b>Jogo #{match_num} em {minutos}min ({hora_jogo} Brasília)</b>\n"
                f"   {team1} x {team2}\n"
                f"   Sem palpite: {faltam_str}"
            )
        else:
            ok_alerts.append(
                f"✅ <b>Jogo #{match_num} em {minutos}min ({hora_jogo} Brasília)</b>\n"
                f"   {team1} x {team2}\n"
                f"   Todos os {len(user_ids)} participantes palpitaram!"
            )

    return alerts, ok_alerts


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
            SELECT DISTINCT group_name FROM group_predictions
            WHERE user_id = %s
              AND first_place_team_id IS NOT NULL
              AND second_place_team_id IS NOT NULL
        """, (user_id,))
        feitos = {r[0] for r in cur.fetchall()}
        faltando = sorted(set("ABCDEFGHIJKL") - feitos)
        if faltando:
            grupos_incompletos.append((name, len(feitos), faltando))

    if sem_podio or grupos_incompletos:
        prazo_str = copa_start.strftime('%d/%m/%Y às %H:%M')
        alerts.append(
            f"⏰ <b>Copa começa em {dias_ate_copa} dia(s) — {prazo_str}!</b>\n"
            f"Após esse horário, os palpites de Grupos e Pódio serão bloqueados automaticamente."
        )

    if sem_podio:
        nomes = "\n   • ".join(sem_podio)
        alerts.append(
            f"🏆 <b>Palpite de Pódio pendente ({len(sem_podio)}/{len(users)} participantes):</b>\n"
            f"   • {nomes}"
        )

    if grupos_incompletos:
        linhas_grupos = []
        for n, feitos, faltando in grupos_incompletos:
            if feitos == 0:
                linhas_grupos.append(f"{n} — nenhum salvo (A–L)")
            else:
                linhas_grupos.append(f"{n} — falta(m): {', '.join(faltando)}")
        detalhe = "\n   • ".join(linhas_grupos)
        alerts.append(
            f"📋 <b>Palpites de Classificação dos Grupos pendentes:</b>\n"
            f"   • {detalhe}"
        )

    if sem_podio or grupos_incompletos:
        alerts.append(
            "ℹ️ <b>Como salvar:</b>\n"
            "   1. Acesse o sistema do Bolão\n"
            "   2. No menu lateral, clique em <b>Palpites Grupos</b> e/ou <b>Palpites Pódio</b>\n"
            "   3. Escolha suas seleções\n"
            "   4. Em <b>Palpites Grupos</b>: selecione o 1º e 2º de cada grupo e clique no botão verde ✅ <b>Salvar Todos os Grupos</b> no final da página — salva os 12 grupos de uma vez!\n"
            "   5. Em <b>Palpites Pódio</b>: escolha Campeão, Vice e 3º Lugar e clique em 💾 <b>Salvar Palpite de Pódio</b>\n\n"
            "Se você está aguardando para palpitar mais próximo do início da Copa, tudo bem! "
            "Este é apenas um lembrete. Mas se esqueceu, acesse agora para não perder o prazo. 😊"
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
    pre_copa_alerts          = check_pre_copa_missing_predictions(cur)
    upcoming_alerts, upcoming_ok = check_upcoming_no_prediction(cur)
    invalid_preds            = check_invalid_predictions(cur)
    duplicate_preds          = check_duplicate_predictions(cur)
    invalid_groups           = check_invalid_group_predictions(cur)
    invalid_podium           = check_invalid_podium_predictions(cur)
    unscored                 = check_unscored_finished(cur)
    count_drop               = check_prediction_count_drop(cur)
    conn.commit()

    all_alerts = (
        health_alerts + pre_copa_alerts + upcoming_alerts + invalid_preds +
        duplicate_preds + invalid_groups + invalid_podium +
        unscored + count_drop
    )
    has_upcoming_any = bool(upcoming_alerts or upcoming_ok)

    # Log no console sempre
    summary = (
        f"DB: {pred_count} preds | {group_count} group_preds | "
        f"{podium_count} podium_preds | {user_count} usuários ativos"
    )
    print(summary)
    if all_alerts:
        for a in all_alerts:
            print(" •", a.replace("<b>", "").replace("</b>", ""))
    if upcoming_ok:
        for a in upcoming_ok:
            print(" •", a.replace("<b>", "").replace("</b>", ""))
    if not all_alerts and not upcoming_ok:
        print("Nenhum alerta — sistema saudável.")

    cur.close()
    conn.close()

    # --- Telegram ---
    # Envia se houver alertas, jogos próximos (mesmo com todos palpitados) ou --full
    if not (all_alerts or has_upcoming_any or force_full):
        print("Sem alertas e sem jogos próximos — Telegram não enviado (anti-spam).")
        return

    ts = now.strftime("%d/%m/%Y %H:%M")
    linhas = [f"⚽ <b>VAR — Bolão Copa 2026</b> | {ts}\n"]
    linhas.append(f"📊 {summary}\n")

    if not all_alerts and not has_upcoming_any:
        linhas.append("✅ Sistema saudável — 0 alertas.")
    else:
        if pre_copa_alerts:
            linhas.append("─── ⚠️ Atenção: Copa em breve! ───")
            linhas.extend(pre_copa_alerts)
            linhas.append("")
        if upcoming_alerts:
            linhas.append("─── ⏰ Palpites pendentes ───")
            linhas.extend(upcoming_alerts)
        if upcoming_ok:
            linhas.append("─── ✅ Jogos próximos OK ───")
            linhas.extend(upcoming_ok)
        if any([invalid_preds, duplicate_preds, invalid_groups,
                invalid_podium, unscored, count_drop, health_alerts]):
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
