"""
Gerenciamento de conexão com o banco de dados
Suporta SQLite (desenvolvimento) e PostgreSQL (produção)
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from models import Base, Config
from config import (
    DATABASE_NAME, ADMIN_DEFAULT, 
    DEFAULT_SCORING, DEFAULT_GROUP_SCORING, 
    DEFAULT_PODIUM_SCORING, DEFAULT_PREMIACAO
)


def get_database_url():
    """
    Retorna a URL de conexão com o banco de dados.
    Usa variável de ambiente DATABASE_URL se disponível (Postgres),
    caso contrário usa SQLite local.
    """
    database_url = os.environ.get("DATABASE_URL")
    
    if database_url:
        # Corrige URL do Heroku/Railway se necessário
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        return database_url
    
    # SQLite local para desenvolvimento
    return f"sqlite:///{DATABASE_NAME}"


def get_engine():
    """Cria e retorna o engine do SQLAlchemy"""
    database_url = get_database_url()
    
    if database_url.startswith("sqlite"):
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            echo=False
        )
    else:
        engine = create_engine(database_url, echo=False)
    
    return engine


def create_tables(engine):
    """Cria todas as tabelas no banco de dados"""
    Base.metadata.create_all(engine)


def get_session(engine):
    """Cria e retorna uma sessão do banco de dados"""
    Session = sessionmaker(bind=engine)
    return Session()


@contextmanager
def session_scope(engine):
    """
    Context manager para gerenciar sessões de forma segura.
    Uso: with session_scope(engine) as session:
    """
    session = get_session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database():
    """
    Inicializa o banco de dados:
    - Cria as tabelas se não existirem
    - Cria o usuário admin padrão se não existir
    - Inicializa todas as configurações padrão
    """
    from auth import hash_password
    from models import User, Config
    
    engine = get_engine()
    create_tables(engine)
    
    with session_scope(engine) as session:
        # Verifica se já existe algum usuário admin
        admin_exists = session.query(User).filter_by(role='admin').first()
        
        if not admin_exists:
            # Cria usuário admin padrão
            admin = User(
                name=ADMIN_DEFAULT["name"],
                username=ADMIN_DEFAULT["username"],
                password_hash=hash_password(ADMIN_DEFAULT["password"]),
                role='admin',
                active=True
            )
            session.add(admin)
            # Usuário admin criado
        
        # Inicializa configurações de pontuação por jogo
        for key, value in DEFAULT_SCORING.items():
            config_key = f"pontos_{key}"
            if not session.query(Config).filter_by(key=config_key).first():
                session.add(Config(
                    key=config_key, 
                    value=str(value), 
                    description=f"Pontuação: {key.replace('_', ' ').title()}",
                    category='pontuacao'
                ))
        
        # Inicializa configurações de pontuação de grupos
        for key, value in DEFAULT_GROUP_SCORING.items():
            config_key = f"grupo_{key}"
            if not session.query(Config).filter_by(key=config_key).first():
                session.add(Config(
                    key=config_key, 
                    value=str(value), 
                    description=f"Grupo: {key.replace('_', ' ').title()}",
                    category='grupo'
                ))
        
        # Inicializa configurações de pontuação do pódio
        for key, value in DEFAULT_PODIUM_SCORING.items():
            config_key = f"podio_{key}"
            if not session.query(Config).filter_by(key=config_key).first():
                session.add(Config(
                    key=config_key, 
                    value=str(value), 
                    description=f"Pódio: {key.replace('_', ' ').title()}",
                    category='podio'
                ))
        
        # Inicializa configurações de premiação
        for key, value in DEFAULT_PREMIACAO.items():
            config_key = f"premiacao_{key}"
            if not session.query(Config).filter_by(key=config_key).first():
                session.add(Config(
                    key=config_key, 
                    value=str(value), 
                    description=f"Premiação: {key.replace('_', ' ').title()}",
                    category='premiacao'
                ))
        
        # Configuração de data de início da Copa
        if not session.query(Config).filter_by(key='data_inicio_copa').first():
            session.add(Config(
                key='data_inicio_copa',
                value='',
                description='Data e hora de início da Copa (para bloquear palpites de pódio)',
                category='sistema'
            ))
    
    return engine


def get_config_value(session, key, default=None):
    """Obtém um valor de configuração do banco"""
    config = session.query(Config).filter_by(key=key).first()
    if config and config.value:
        return config.value
    return default


def set_config_value(session, key, value, description=None, category=None):
    """Define um valor de configuração no banco"""
    from models import Config
    config = session.query(Config).filter_by(key=key).first()
    if config:
        config.value = str(value)
        if description:
            config.description = description
        if category:
            config.category = category
    else:
        session.add(Config(
            key=key,
            value=str(value),
            description=description,
            category=category
        ))
    session.commit()


def populate_copa2026_data(session):
    """
    Popula o banco de dados com os 104 jogos da Copa do Mundo 2026
    """
    from copa2026_data import ALL_MATCHES
    from models import Match
    
    print("🏆 Carregando dados da Copa do Mundo 2026...")
    
    # Verificar se já existem jogos no banco
    existing_matches = session.query(Match).count()
    if existing_matches > 0:
        print(f"⚠️  Banco já contém {existing_matches} jogos. Pulando inicialização.")
        return
    
    # Inserir todos os 104 jogos
    matches_added = 0
    
    for match_data in ALL_MATCHES:
        # Formato da tupla: (match_number, group, team1, team2, date, time, venue)
        match_number, group, team1, team2, date, time, venue = match_data
        
        # Criar objeto Match
        match = Match(
            match_number=match_number,
            group_name=group,
            team1=team1,
            team2=team2,
            match_date=date,
            match_time=time,
            venue=venue,
            team1_score=None,
            team2_score=None
        )
        
        session.add(match)
        matches_added += 1
    
    # Commit
    session.commit()
    
    print(f"✅ {matches_added} jogos carregados com sucesso!")
    print(f"   - Fase de grupos: 72 jogos")
    print(f"   - Mata-mata: 32 jogos")
    print(f"   - Total: {matches_added} jogos")


def init_database_with_copa2026():
    """
    Inicializa o banco de dados completo com dados da Copa 2026.
    """
    engine = init_database()
    
    with session_scope(engine) as session:
        populate_copa2026_data(session)
    
    return engine
