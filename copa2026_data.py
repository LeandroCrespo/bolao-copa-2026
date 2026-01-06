"""
Copa do Mundo 2026 - Dados Oficiais
Fonte: FIFA (https://www.fifa.com)
Horários no fuso de Brasília (GMT-3)

Seleções da Repescagem (ainda não definidas):
- EUR_A: Itália, Irlanda do Norte, País de Gales, Bósnia
- EUR_B: Ucrânia, Suécia, Polônia, Albânia  
- EUR_C: Turquia, Romênia, Eslováquia, Kosovo
- EUR_D: República Tcheca, Irlanda, Dinamarca, Macedônia do Norte
- INT_1: Congo DR, Jamaica, Nova Caledônia
- INT_2: Bolívia, Suriname, Iraque
"""

# Formato: (match_number, group, team1_code, team2_code, date, time, venue)
# Para mata-mata: (match_number, phase, team1_code, team2_code, date, time, venue)

MATCHES_GROUP_STAGE = [
    # ========== GRUPO A ==========
    # México, África do Sul, Coreia do Sul, Europa D (repescagem)
    (1, "A", "MEX", "RSA", "2026-06-11", "16:00", "Cidade do México"),
    (2, "A", "KOR", "EUR_D", "2026-06-11", "23:00", "Guadalajara"),
    (3, "A", "EUR_D", "RSA", "2026-06-18", "13:00", "Atlanta"),
    (4, "A", "MEX", "KOR", "2026-06-18", "22:00", "Guadalajara"),
    (5, "A", "EUR_D", "MEX", "2026-06-24", "22:00", "Cidade do México"),
    (6, "A", "RSA", "KOR", "2026-06-24", "22:00", "Monterrey"),
    
    # ========== GRUPO B ==========
    # Canadá, Suíça, Qatar, Europa A (repescagem)
    (7, "B", "CAN", "EUR_A", "2026-06-12", "16:00", "Toronto"),
    (8, "B", "QAT", "SUI", "2026-06-13", "16:00", "San Francisco"),
    (9, "B", "SUI", "EUR_A", "2026-06-18", "16:00", "Los Angeles"),
    (10, "B", "CAN", "QAT", "2026-06-18", "19:00", "Vancouver"),
    (11, "B", "SUI", "CAN", "2026-06-24", "16:00", "Vancouver"),
    (12, "B", "EUR_A", "QAT", "2026-06-24", "16:00", "Seattle"),
    
    # ========== GRUPO C ==========
    # Brasil, Marrocos, Haiti, Escócia
    (13, "C", "BRA", "MAR", "2026-06-13", "19:00", "Nova York"),
    (14, "C", "HAI", "SCO", "2026-06-13", "22:00", "Boston"),
    (15, "C", "SCO", "MAR", "2026-06-19", "19:00", "Boston"),
    (16, "C", "BRA", "HAI", "2026-06-19", "22:00", "Filadélfia"),
    (17, "C", "SCO", "BRA", "2026-06-24", "19:00", "Miami"),
    (18, "C", "MAR", "HAI", "2026-06-24", "19:00", "Atlanta"),
    
    # ========== GRUPO D ==========
    # Estados Unidos, Paraguai, Austrália, Europa C (repescagem)
    (19, "D", "USA", "PAR", "2026-06-12", "22:00", "Los Angeles"),
    (20, "D", "AUS", "EUR_C", "2026-06-13", "01:00", "Vancouver"),
    (21, "D", "EUR_C", "PAR", "2026-06-19", "01:00", "San Francisco"),
    (22, "D", "USA", "AUS", "2026-06-19", "16:00", "Seattle"),
    (23, "D", "EUR_C", "USA", "2026-06-25", "23:00", "Los Angeles"),
    (24, "D", "PAR", "AUS", "2026-06-25", "23:00", "San Francisco"),
    
    # ========== GRUPO E ==========
    # Alemanha, Costa do Marfim, Equador, Curaçao
    (25, "E", "GER", "CUR", "2026-06-14", "14:00", "Houston"),
    (26, "E", "CIV", "ECU", "2026-06-14", "20:00", "Filadélfia"),
    (27, "E", "GER", "CIV", "2026-06-20", "17:00", "Toronto"),
    (28, "E", "ECU", "CUR", "2026-06-20", "21:00", "Kansas City"),
    (29, "E", "ECU", "GER", "2026-06-25", "17:00", "Nova York"),
    (30, "E", "CUR", "CIV", "2026-06-25", "17:00", "Filadélfia"),
    
    # ========== GRUPO F ==========
    # Holanda, Japão, Tunísia, Europa B (repescagem)
    (31, "F", "NED", "JPN", "2026-06-14", "17:00", "Dallas"),
    (32, "F", "EUR_B", "TUN", "2026-06-14", "23:00", "Monterrey"),
    (33, "F", "NED", "EUR_B", "2026-06-20", "14:00", "Houston"),
    (34, "F", "TUN", "JPN", "2026-06-21", "01:00", "Monterrey"),
    (35, "F", "TUN", "NED", "2026-06-25", "20:00", "Kansas City"),
    (36, "F", "JPN", "EUR_B", "2026-06-25", "20:00", "Dallas"),
    
    # ========== GRUPO G ==========
    # Bélgica, Egito, Irã, Nova Zelândia
    (37, "G", "BEL", "EGY", "2026-06-15", "16:00", "Seattle"),
    (38, "G", "IRN", "NZL", "2026-06-15", "22:00", "Los Angeles"),
    (39, "G", "BEL", "IRN", "2026-06-21", "16:00", "Los Angeles"),
    (40, "G", "NZL", "EGY", "2026-06-21", "22:00", "Vancouver"),
    (41, "G", "EGY", "IRN", "2026-06-27", "00:00", "Seattle"),
    (42, "G", "NZL", "BEL", "2026-06-27", "00:00", "Vancouver"),
    
    # ========== GRUPO H ==========
    # Espanha, Uruguai, Arábia Saudita, Cabo Verde
    (43, "H", "ESP", "CPV", "2026-06-15", "13:00", "Atlanta"),
    (44, "H", "KSA", "URU", "2026-06-15", "19:00", "Miami"),
    (45, "H", "ESP", "KSA", "2026-06-21", "13:00", "Atlanta"),
    (46, "H", "URU", "CPV", "2026-06-21", "19:00", "Miami"),
    (47, "H", "URU", "ESP", "2026-06-26", "21:00", "Guadalajara"),
    (48, "H", "CPV", "KSA", "2026-06-26", "21:00", "Houston"),
    
    # ========== GRUPO I ==========
    # França, Senegal, Noruega, Intercontinental 2 (repescagem)
    (49, "I", "FRA", "SEN", "2026-06-16", "16:00", "Nova York"),
    (50, "I", "INT_2", "NOR", "2026-06-16", "19:00", "Boston"),
    (51, "I", "FRA", "INT_2", "2026-06-22", "18:00", "Filadélfia"),
    (52, "I", "NOR", "SEN", "2026-06-22", "21:00", "Nova York"),
    (53, "I", "NOR", "FRA", "2026-06-26", "16:00", "Boston"),
    (54, "I", "SEN", "INT_2", "2026-06-26", "16:00", "Toronto"),
    
    # ========== GRUPO J ==========
    # Argentina, Argélia, Áustria, Jordânia
    (55, "J", "ARG", "ALG", "2026-06-16", "22:00", "Kansas City"),
    (56, "J", "AUT", "JOR", "2026-06-17", "01:00", "San Francisco"),
    (57, "J", "ARG", "AUT", "2026-06-22", "14:00", "Dallas"),
    (58, "J", "JOR", "ALG", "2026-06-23", "00:00", "San Francisco"),
    (59, "J", "JOR", "ARG", "2026-06-27", "23:00", "Dallas"),
    (60, "J", "ALG", "AUT", "2026-06-27", "23:00", "Kansas City"),
    
    # ========== GRUPO K ==========
    # Portugal, Colômbia, Uzbequistão, Intercontinental 1 (repescagem)
    (61, "K", "POR", "INT_1", "2026-06-17", "14:00", "Houston"),
    (62, "K", "UZB", "COL", "2026-06-17", "23:00", "Cidade do México"),
    (63, "K", "POR", "UZB", "2026-06-23", "14:00", "Houston"),
    (64, "K", "COL", "INT_1", "2026-06-23", "23:00", "Guadalajara"),
    (65, "K", "COL", "POR", "2026-06-27", "20:30", "Miami"),
    (66, "K", "INT_1", "UZB", "2026-06-27", "20:30", "Atlanta"),
    
    # ========== GRUPO L ==========
    # Inglaterra, Croácia, Gana, Panamá
    (67, "L", "ENG", "CRO", "2026-06-17", "17:00", "Dallas"),
    (68, "L", "GHA", "PAN", "2026-06-17", "20:00", "Toronto"),
    (69, "L", "ENG", "GHA", "2026-06-23", "17:00", "Boston"),
    (70, "L", "PAN", "CRO", "2026-06-23", "20:00", "Toronto"),
    (71, "L", "PAN", "ENG", "2026-06-27", "18:00", "Nova York"),
    (72, "L", "CRO", "GHA", "2026-06-27", "18:00", "Filadélfia"),
]

MATCHES_KNOCKOUT = [
    # ========== FASE DE 32 (Round of 32) ==========
    (73, "R32", "1A", "3CDF", "2026-06-28", "16:00", "Los Angeles"),
    (74, "R32", "2C", "2D", "2026-06-29", "17:30", "Boston"),
    (75, "R32", "1B", "3AEF", "2026-06-29", "22:00", "Monterrey"),
    (76, "R32", "2A", "2B", "2026-06-29", "14:00", "Houston"),
    (77, "R32", "1D", "3BEF", "2026-06-30", "18:00", "Nova York"),
    (78, "R32", "1C", "3ABD", "2026-06-30", "14:00", "Dallas"),
    (79, "R32", "2E", "2F", "2026-06-30", "22:00", "Cidade do México"),
    (80, "R32", "1F", "3ABC", "2026-07-01", "13:00", "Atlanta"),
    (81, "R32", "1E", "3DEF", "2026-07-01", "21:00", "San Francisco"),
    (82, "R32", "2G", "2H", "2026-07-01", "17:00", "Seattle"),
    (83, "R32", "1H", "3GIJ", "2026-07-02", "20:00", "Toronto"),
    (84, "R32", "1G", "3HIK", "2026-07-02", "16:00", "Los Angeles"),
    (85, "R32", "2I", "2J", "2026-07-03", "00:00", "Vancouver"),
    (86, "R32", "1J", "3GHK", "2026-07-03", "19:00", "Miami"),
    (87, "R32", "1I", "3JKL", "2026-07-03", "22:30", "Kansas City"),
    (88, "R32", "2K", "2L", "2026-07-03", "15:00", "Dallas"),
    
    # ========== OITAVAS DE FINAL (Round of 16) ==========
    (89, "R16", "W73", "W74", "2026-07-04", "18:00", "Filadélfia"),
    (90, "R16", "W75", "W76", "2026-07-04", "14:00", "Houston"),
    (91, "R16", "W77", "W78", "2026-07-05", "17:00", "Nova York"),
    (92, "R16", "W79", "W80", "2026-07-05", "21:00", "Cidade do México"),
    (93, "R16", "W81", "W82", "2026-07-06", "16:00", "Dallas"),
    (94, "R16", "W83", "W84", "2026-07-06", "21:00", "Seattle"),
    (95, "R16", "W85", "W86", "2026-07-07", "13:00", "Atlanta"),
    (96, "R16", "W87", "W88", "2026-07-07", "17:00", "Vancouver"),
    
    # ========== QUARTAS DE FINAL ==========
    (97, "QF", "W89", "W90", "2026-07-09", "17:00", "Boston"),
    (98, "QF", "W91", "W92", "2026-07-10", "16:00", "Los Angeles"),
    (99, "QF", "W93", "W94", "2026-07-11", "18:00", "Miami"),
    (100, "QF", "W95", "W96", "2026-07-11", "22:00", "Kansas City"),
    
    # ========== SEMIFINAIS ==========
    (101, "SF", "W97", "W98", "2026-07-14", "16:00", "Dallas"),
    (102, "SF", "W99", "W100", "2026-07-15", "16:00", "Atlanta"),
    
    # ========== DISPUTA DE 3º LUGAR ==========
    (103, "3RD", "L101", "L102", "2026-07-18", "18:00", "Miami"),
    
    # ========== FINAL ==========
    (104, "FINAL", "W101", "W102", "2026-07-19", "16:00", "Nova York"),
]

# Todos os jogos
ALL_MATCHES = MATCHES_GROUP_STAGE + MATCHES_KNOCKOUT

# Seleções classificadas com seus códigos FIFA
TEAMS = {
    # Grupo A
    "MEX": {"name": "México", "flag": "🇲🇽", "fifa_rank": 15},
    "RSA": {"name": "África do Sul", "flag": "🇿🇦", "fifa_rank": 61},
    "KOR": {"name": "Coreia do Sul", "flag": "🇰🇷", "fifa_rank": 22},
    
    # Grupo B
    "CAN": {"name": "Canadá", "flag": "🇨🇦", "fifa_rank": 27},
    "SUI": {"name": "Suíça", "flag": "🇨🇭", "fifa_rank": 17},
    "QAT": {"name": "Qatar", "flag": "🇶🇦", "fifa_rank": 54},
    
    # Grupo C
    "BRA": {"name": "Brasil", "flag": "🇧🇷", "fifa_rank": 5},
    "MAR": {"name": "Marrocos", "flag": "🇲🇦", "fifa_rank": 11},
    "HAI": {"name": "Haiti", "flag": "🇭🇹", "fifa_rank": 84},
    "SCO": {"name": "Escócia", "flag": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "fifa_rank": 36},
    
    # Grupo D
    "USA": {"name": "Estados Unidos", "flag": "🇺🇸", "fifa_rank": 14},
    "PAR": {"name": "Paraguai", "flag": "🇵🇾", "fifa_rank": 39},
    "AUS": {"name": "Austrália", "flag": "🇦🇺", "fifa_rank": 26},
    
    # Grupo E
    "GER": {"name": "Alemanha", "flag": "🇩🇪", "fifa_rank": 9},
    "CIV": {"name": "Costa do Marfim", "flag": "🇨🇮", "fifa_rank": 42},
    "ECU": {"name": "Equador", "flag": "🇪🇨", "fifa_rank": 23},
    "CUR": {"name": "Curaçao", "flag": "🇨🇼", "fifa_rank": 82},
    
    # Grupo F
    "NED": {"name": "Holanda", "flag": "🇳🇱", "fifa_rank": 7},
    "JPN": {"name": "Japão", "flag": "🇯🇵", "fifa_rank": 18},
    "TUN": {"name": "Tunísia", "flag": "🇹🇳", "fifa_rank": 41},
    
    # Grupo G
    "BEL": {"name": "Bélgica", "flag": "🇧🇪", "fifa_rank": 8},
    "EGY": {"name": "Egito", "flag": "🇪🇬", "fifa_rank": 35},
    "IRN": {"name": "Irã", "flag": "🇮🇷", "fifa_rank": 20},
    "NZL": {"name": "Nova Zelândia", "flag": "🇳🇿", "fifa_rank": 87},
    
    # Grupo H
    "ESP": {"name": "Espanha", "flag": "🇪🇸", "fifa_rank": 1},
    "URU": {"name": "Uruguai", "flag": "🇺🇾", "fifa_rank": 16},
    "KSA": {"name": "Arábia Saudita", "flag": "🇸🇦", "fifa_rank": 60},
    "CPV": {"name": "Cabo Verde", "flag": "🇨🇻", "fifa_rank": 67},
    
    # Grupo I
    "FRA": {"name": "França", "flag": "🇫🇷", "fifa_rank": 3},
    "SEN": {"name": "Senegal", "flag": "🇸🇳", "fifa_rank": 19},
    "NOR": {"name": "Noruega", "flag": "🇳🇴", "fifa_rank": 29},
    
    # Grupo J
    "ARG": {"name": "Argentina", "flag": "🇦🇷", "fifa_rank": 2},
    "ALG": {"name": "Argélia", "flag": "🇩🇿", "fifa_rank": 34},
    "AUT": {"name": "Áustria", "flag": "🇦🇹", "fifa_rank": 24},
    "JOR": {"name": "Jordânia", "flag": "🇯🇴", "fifa_rank": 64},
    
    # Grupo K
    "POR": {"name": "Portugal", "flag": "🇵🇹", "fifa_rank": 6},
    "COL": {"name": "Colômbia", "flag": "🇨🇴", "fifa_rank": 13},
    "UZB": {"name": "Uzbequistão", "flag": "🇺🇿", "fifa_rank": 50},
    
    # Grupo L
    "ENG": {"name": "Inglaterra", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "fifa_rank": 4},
    "CRO": {"name": "Croácia", "flag": "🇭🇷", "fifa_rank": 10},
    "GHA": {"name": "Gana", "flag": "🇬🇭", "fifa_rank": 72},
    "PAN": {"name": "Panamá", "flag": "🇵🇦", "fifa_rank": 30},
    
    # Repescagem Europa
    "EUR_A": {"name": "Europa A", "flag": "🇪🇺", "fifa_rank": None, "playoff": ["Itália", "Irlanda do Norte", "País de Gales", "Bósnia"]},
    "EUR_B": {"name": "Europa B", "flag": "🇪🇺", "fifa_rank": None, "playoff": ["Ucrânia", "Suécia", "Polônia", "Albânia"]},
    "EUR_C": {"name": "Europa C", "flag": "🇪🇺", "fifa_rank": None, "playoff": ["Turquia", "Romênia", "Eslováquia", "Kosovo"]},
    "EUR_D": {"name": "Europa D", "flag": "🇪🇺", "fifa_rank": None, "playoff": ["Rep. Tcheca", "Irlanda", "Dinamarca", "Macedônia do Norte"]},
    
    # Repescagem Intercontinental
    "INT_1": {"name": "Intercon. 1", "flag": "🌍", "fifa_rank": None, "playoff": ["Congo DR", "Jamaica", "Nova Caledônia"]},
    "INT_2": {"name": "Intercon. 2", "flag": "🌍", "fifa_rank": None, "playoff": ["Bolívia", "Suriname", "Iraque"]},
}

# Funções auxiliares
def get_all_matches():
    """Retorna todos os 104 jogos da Copa do Mundo 2026"""
    return ALL_MATCHES

def get_group_stage_matches():
    """Retorna apenas os 72 jogos da fase de grupos"""
    return MATCHES_GROUP_STAGE

def get_knockout_matches():
    """Retorna apenas os 32 jogos do mata-mata"""
    return MATCHES_KNOCKOUT

def get_matches_by_group(group_letter):
    """Retorna os 6 jogos de um grupo específico"""
    return [m for m in MATCHES_GROUP_STAGE if m[1] == group_letter]

def get_team_info(code):
    """Retorna informações de uma seleção pelo código"""
    return TEAMS.get(code, {"name": code, "flag": "🏳️", "fifa_rank": None})

# Verificação de integridade
if __name__ == "__main__":
    print(f"Total de jogos: {len(ALL_MATCHES)}")
    print(f"Jogos fase de grupos: {len(MATCHES_GROUP_STAGE)}")
    print(f"Jogos mata-mata: {len(MATCHES_KNOCKOUT)}")
    print(f"Seleções cadastradas: {len(TEAMS)}")
    
    print(f"\nVerificação por grupo:")
    for group in 'ABCDEFGHIJKL':
        matches = get_matches_by_group(group)
        print(f"Grupo {group}: {len(matches)} jogos", "✅" if len(matches) == 6 else "❌")
    
    # Verificar tamanho dos códigos
    max_len = 0
    for match in ALL_MATCHES:
        code1 = match[2]
        code2 = match[3]
        max_len = max(max_len, len(code1), len(code2))
    print(f"\nMaior código: {max_len} caracteres (limite: 10)")
    print("✅ Todos os códigos estão dentro do limite!" if max_len <= 10 else "❌ ERRO!")
