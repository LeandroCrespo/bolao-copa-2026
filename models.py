"""
Modelos do banco de dados para o Bolão Copa do Mundo 2026
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """Tabela de usuários (participantes e admin)"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='player')  # 'admin' ou 'player'
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    predictions = relationship("Prediction", back_populates="user")
    group_predictions = relationship("GroupPrediction", back_populates="user")
    podium_prediction = relationship("PodiumPrediction", back_populates="user", uselist=False)


class Team(Base):
    """Tabela de seleções"""
    __tablename__ = 'teams'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10), unique=True)  # Ex: BRA, ARG, GER
    group = Column(String(5))  # A, B, C... L
    flag = Column(String(20))  # Emoji da bandeira
    
    # Resultado real após fase de grupos
    final_position = Column(Integer)  # 1, 2, 3, 4 (posição final no grupo)
    qualified = Column(Boolean, default=False)  # Se classificou para mata-mata


class Match(Base):
    """Tabela de partidas"""
    __tablename__ = 'matches'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    match_number = Column(Integer, unique=True)  # Número do jogo (1-128)
    
    # Times
    team1_id = Column(Integer, ForeignKey('teams.id'))
    team2_id = Column(Integer, ForeignKey('teams.id'))
    team1_code = Column(String(10))  # Código do time ou placeholder (ex: "1A", "W97")
    team2_code = Column(String(10))
    
    # Data e local
    datetime = Column(DateTime, nullable=False)
    city = Column(String(100))
    
    # Fase e grupo
    phase = Column(String(50), nullable=False)  # Grupos, Oitavas32, Oitavas16, Quartas, Semifinal, Terceiro, Final
    group = Column(String(5))  # Apenas para fase de grupos
    
    # Resultado
    status = Column(String(20), default='scheduled')  # scheduled, finished, cancelled
    team1_score = Column(Integer)
    team2_score = Column(Integer)
    
    # Controle
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, onupdate=lambda: datetime.utcnow())
    
    team1 = relationship("Team", foreign_keys=[team1_id])
    team2 = relationship("Team", foreign_keys=[team2_id])
    predictions = relationship("Prediction", back_populates="match")
    
    def get_team1_display(self):
        """Retorna nome do time 1 para exibição"""
        if self.team1:
            return f"{self.team1.flag} {self.team1.name}"
        return self.team1_code or "A definir"
    
    def get_team2_display(self):
        """Retorna nome do time 2 para exibição"""
        if self.team2:
            return f"{self.team2.flag} {self.team2.name}"
        return self.team2_code or "A definir"


class Prediction(Base):
    """Tabela de palpites dos usuários para partidas"""
    __tablename__ = 'predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    match_id = Column(Integer, ForeignKey('matches.id'), nullable=False)
    pred_team1_score = Column(Integer, nullable=False)
    pred_team2_score = Column(Integer, nullable=False)
    points_awarded = Column(Integer, default=0)
    points_type = Column(String(50))  # Tipo de acerto: 'placar_exato', 'resultado_gols', etc.
    breakdown = Column(Text)  # Descrição do acerto
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, onupdate=lambda: datetime.utcnow())
    locked_at = Column(DateTime)  # Quando foi travado
    
    user = relationship("User", back_populates="predictions")
    match = relationship("Match", back_populates="predictions")


class GroupPrediction(Base):
    """Tabela de palpites de classificação dos grupos"""
    __tablename__ = 'group_predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    group_name = Column(String(5), nullable=False)  # A, B, C... L
    first_place_team_id = Column(Integer, ForeignKey('teams.id'))  # Palpite 1º lugar
    second_place_team_id = Column(Integer, ForeignKey('teams.id'))  # Palpite 2º lugar
    points_awarded = Column(Integer, default=0)
    breakdown = Column(Text)  # Descrição do acerto
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, onupdate=lambda: datetime.utcnow())
    
    user = relationship("User", back_populates="group_predictions")
    first_place_team = relationship("Team", foreign_keys=[first_place_team_id])
    second_place_team = relationship("Team", foreign_keys=[second_place_team_id])


class PodiumPrediction(Base):
    """Tabela de palpites do pódio (campeão, vice, 3º lugar)"""
    __tablename__ = 'podium_predictions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    # Palpites
    champion_team_id = Column(Integer, ForeignKey('teams.id'))
    runner_up_team_id = Column(Integer, ForeignKey('teams.id'))
    third_place_team_id = Column(Integer, ForeignKey('teams.id'))
    
    # Pontuação
    points_awarded = Column(Integer, default=0)
    breakdown = Column(Text)
    
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, onupdate=lambda: datetime.utcnow())
    locked = Column(Boolean, default=False)  # Travado após início da Copa
    
    user = relationship("User", back_populates="podium_prediction")
    champion_team = relationship("Team", foreign_keys=[champion_team_id])
    runner_up_team = relationship("Team", foreign_keys=[runner_up_team_id])
    third_place_team = relationship("Team", foreign_keys=[third_place_team_id])


class TournamentResult(Base):
    """Tabela com resultados oficiais do torneio (pódio real)"""
    __tablename__ = 'tournament_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    result_type = Column(String(50), nullable=False)  # 'champion', 'runner_up', 'third_place'
    team_id = Column(Integer, ForeignKey('teams.id'))
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    team = relationship("Team")


class GroupResult(Base):
    """Tabela com resultados oficiais dos grupos"""
    __tablename__ = 'group_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    group_name = Column(String(5), nullable=False)  # A, B, C... L
    first_place_team_id = Column(Integer, ForeignKey('teams.id'))
    second_place_team_id = Column(Integer, ForeignKey('teams.id'))
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    
    first_place_team = relationship("Team", foreign_keys=[first_place_team_id])
    second_place_team = relationship("Team", foreign_keys=[second_place_team_id])


class Config(Base):
    """Tabela de configurações do sistema"""
    __tablename__ = 'config'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(String(500))
    description = Column(String(255))
    category = Column(String(50))  # 'pontuacao', 'bonus', 'grupo', 'podio', 'premiacao'


class AuditLog(Base):
    """Tabela de auditoria de ações"""
    __tablename__ = 'audit_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100), nullable=False)
    target_user_id = Column(Integer)  # ID do usuário afetado (se aplicável)
    details = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
