"""
Trava automaticamente os palpites de classificados de grupo (1º e 2º colocado)
assim que a Copa começa, para usuários que não salvaram manualmente.

Regra de negócio:
- Se o usuário não salvou seu palpite de classificados de um grupo, no momento em
  que a Copa começa o sistema grava automaticamente a classificação sugerida
  (calculada a partir dos palpites de placar do usuário) como palpite final.
- Uma vez gravado (manual ou automaticamente), o registro nunca é sobrescrito —
  scoring.py apenas lê GroupPrediction para pontuar, nunca recalcula.

Idempotente: pode rodar repetidamente (ex: a cada 5 min via GitHub Actions) sem
efeitos colaterais — só age sobre grupos sem palpite ainda salvo, e só depois que
a Copa começou.
"""

from datetime import datetime

import pytz

from db import get_engine, session_scope, get_config_value
from models import User, GroupPrediction
from group_standings import get_predicted_group_standings

GRUPOS = "ABCDEFGHIJKL"


def get_brazil_time():
    """Retorna a hora atual no fuso horário de Brasília"""
    tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(tz)


def _parse_data_inicio(raw: str) -> datetime | None:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw.strip(), fmt)
        except ValueError:
            continue
    return None


def run():
    engine = get_engine()

    with session_scope(engine) as session:
        raw = get_config_value(session, "data_inicio_copa")
        if not raw:
            print("data_inicio_copa não configurado — nada a fazer.")
            return

        dt_inicio = _parse_data_inicio(raw)
        if dt_inicio is None:
            print(f"data_inicio_copa inválido ('{raw}') — nada a fazer.")
            return

        now = get_brazil_time().replace(tzinfo=None)
        if now < dt_inicio:
            print(f"Copa ainda não começou ({now} < {dt_inicio}) — nada a fazer.")
            return

        users = (
            session.query(User)
            .filter(User.active == True, User.role != "admin")
            .all()
        )

        travados = 0
        ja_travados = 0
        sem_classificacao = 0

        for user in users:
            for grupo in GRUPOS:
                existing = (
                    session.query(GroupPrediction)
                    .filter_by(user_id=user.id, group_name=grupo)
                    .first()
                )
                if existing and existing.first_place_team_id and existing.second_place_team_id:
                    ja_travados += 1
                    continue

                standings = get_predicted_group_standings(session, user.id, grupo)
                if len(standings) < 2:
                    sem_classificacao += 1
                    continue

                first_team = standings[0]["team"]
                second_team = standings[1]["team"]

                # PlaceholderTeam tem id string ("placeholder_xxx") — não é FK válido.
                if not isinstance(first_team.id, int) or not isinstance(second_team.id, int):
                    sem_classificacao += 1
                    continue

                if existing:
                    existing.first_place_team_id = first_team.id
                    existing.second_place_team_id = second_team.id
                else:
                    session.add(GroupPrediction(
                        user_id=user.id,
                        group_name=grupo,
                        first_place_team_id=first_team.id,
                        second_place_team_id=second_team.id,
                    ))

                travados += 1
                print(f"  Auto-travado: {user.name} — Grupo {grupo} -> "
                      f"1º {first_team.name}, 2º {second_team.name}")

        print(f"\nResumo: {travados} grupo(s) auto-travado(s), "
              f"{ja_travados} já travado(s), {sem_classificacao} sem classificação possível.")


if __name__ == "__main__":
    run()
