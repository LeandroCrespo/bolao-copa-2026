"""
Módulo de autenticação do Bolão Copa do Mundo 2026
Gerencia hash de senhas e verificação de credenciais
"""

import bcrypt
from models import User


def hash_password(password: str) -> str:
    """
    Gera hash seguro da senha usando bcrypt.
    
    Args:
        password: Senha em texto plano
        
    Returns:
        Hash da senha
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifica se a senha corresponde ao hash armazenado.
    
    Args:
        password: Senha em texto plano
        password_hash: Hash armazenado no banco
        
    Returns:
        True se a senha estiver correta, False caso contrário
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception:
        return False


def authenticate_user(session, username: str, password: str):
    """
    Autentica um usuário pelo username e senha.
    
    Args:
        session: Sessão do banco de dados
        username: Nome de usuário
        password: Senha em texto plano
        
    Returns:
        Objeto User se autenticado, None caso contrário
    """
    user = session.query(User).filter_by(username=username, active=True).first()
    
    if user and verify_password(password, user.password_hash):
        return user
    
    return None


def create_user(session, name: str, username: str, password: str, role: str = 'player'):
    """
    Cria um novo usuário no sistema.
    
    Args:
        session: Sessão do banco de dados
        name: Nome completo do usuário
        username: Nome de usuário (único)
        password: Senha em texto plano
        role: 'admin' ou 'player'
        
    Returns:
        Objeto User criado ou None se username já existir
    """
    # Verifica se username já existe
    existing = session.query(User).filter_by(username=username).first()
    if existing:
        return None
    
    user = User(
        name=name,
        username=username,
        password_hash=hash_password(password),
        role=role,
        active=True
    )
    
    session.add(user)
    session.commit()
    
    return user


def change_password(session, user_id: int, new_password: str) -> bool:
    """
    Altera a senha de um usuário.
    
    Args:
        session: Sessão do banco de dados
        user_id: ID do usuário
        new_password: Nova senha em texto plano
        
    Returns:
        True se alterado com sucesso, False caso contrário
    """
    user = session.query(User).filter_by(id=user_id).first()
    
    if user:
        user.password_hash = hash_password(new_password)
        session.commit()
        return True
    
    return False


def deactivate_user(session, user_id: int) -> bool:
    """
    Desativa um usuário (não exclui, apenas marca como inativo).
    
    Args:
        session: Sessão do banco de dados
        user_id: ID do usuário
        
    Returns:
        True se desativado com sucesso, False caso contrário
    """
    user = session.query(User).filter_by(id=user_id).first()
    
    if user:
        user.active = False
        session.commit()
        return True
    
    return False


def activate_user(session, user_id: int) -> bool:
    """
    Reativa um usuário desativado.
    
    Args:
        session: Sessão do banco de dados
        user_id: ID do usuário
        
    Returns:
        True se ativado com sucesso, False caso contrário
    """
    user = session.query(User).filter_by(id=user_id).first()
    
    if user:
        user.active = True
        session.commit()
        return True
    
    return False
