"""
Configurações do Bolão Copa do Mundo 2026
Valores padrão de pontuação (podem ser alterados pelo admin no sistema)
"""

# =============================================================================
# PONTUAÇÃO POR JOGO (Ajustável pelo Admin)
# =============================================================================
DEFAULT_SCORING = {
    "placar_exato": 20,        # Acertou resultado + placar exato
    "resultado_gols": 15,      # Acertou resultado + gols de um time
    "resultado": 10,           # Acertou apenas o resultado (vencedor/empate)
    "gols_um_time": 5,         # Acertou apenas gols de um time
    "errou_tudo": 0            # Errou tudo
}

# =============================================================================
# PONTUAÇÃO DE CLASSIFICAÇÃO DOS GRUPOS (Ajustável pelo Admin)
# =============================================================================
DEFAULT_GROUP_SCORING = {
    "dois_corretos_ordem": 20,    # Acertou 1º e 2º na ordem correta
    "dois_corretos_invertido": 10, # Acertou os 2 classificados, mas ordem invertida
    "um_correto_errado": 5         # Acertou apenas 1 classificado na posição errada
}

# =============================================================================
# PONTUAÇÃO DO PÓDIO - Campeão, Vice, 3º (Ajustável pelo Admin)
# =============================================================================
DEFAULT_PODIUM_SCORING = {
    "podio_completo_ordem": 150,   # Acertou campeão, vice e 3º na ordem exata
    "campeao_correto": 100,        # Acertou o campeão
    "vice_correto": 50,            # Acertou o vice-campeão
    "terceiro_correto": 30,        # Acertou o 3º lugar
    "podio_fora_ordem": 20         # Acertou uma seleção do pódio mas na posição errada
}

# =============================================================================
# CONFIGURAÇÕES DE PREMIAÇÃO (Definido pelo Admin posteriormente)
# =============================================================================
DEFAULT_PREMIACAO = {
    "valor_participacao": 0,       # Valor de participação (R$)
    "taxa_admin": 0,               # Taxa do administrador (%)
    "premio_1_lugar": 60,          # % do prêmio para 1º lugar
    "premio_2_lugar": 30,          # % do prêmio para 2º lugar
    "premio_3_lugar": 10           # % do prêmio para 3º lugar
}

# =============================================================================
# CONFIGURAÇÕES DO ADMIN PADRÃO
# =============================================================================
ADMIN_DEFAULT = {
    "username": "admin",
    "password": "admin",
    "name": "Administrador"
}

# =============================================================================
# FASES DO TORNEIO - COPA 2026 (48 seleções)
# =============================================================================
FASES = [
    "Fase de Grupos",
    "Oitavas de Final",
    "Quartas de Final", 
    "Semifinal",
    "Disputa 3º Lugar",
    "Final"
]

# =============================================================================
# GRUPOS DA COPA 2026 (12 grupos de 4 seleções)
# =============================================================================
GRUPOS = [f"Grupo {chr(65+i)}" for i in range(12)]  # Grupo A até Grupo L

# =============================================================================
# CONFIGURAÇÕES DO BANCO DE DADOS
# =============================================================================
DATABASE_NAME = "bolao2026.db"

# =============================================================================
# CRITÉRIOS DE DESEMPATE (em ordem de prioridade)
# =============================================================================
CRITERIOS_DESEMPATE = [
    ("total_pontos", "Maior pontuação total"),
    ("placares_exatos", "Mais acertos de placares exatos"),
    ("resultado_gols", "Mais acertos de resultado + gols de uma equipe"),
    ("resultado", "Mais acertos de resultado sem gols"),
    ("gols_um_time", "Mais acertos de gols de uma equipe"),
    ("menos_zeros", "Menos palpites zerados"),
    ("ordem_inscricao", "Ordem de inscrição")
]

# =============================================================================
# DATA DE INÍCIO DA COPA (para bloquear palpites de pódio)
# Será configurável pelo admin
# =============================================================================
DATA_INICIO_COPA = None  # Será definido pelo admin
