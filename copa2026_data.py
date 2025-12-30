"""
Dados oficiais da Copa do Mundo FIFA 2026
Baseado no Match Schedule oficial da FIFA
Horários convertidos para Brasília (BRT)
Total: 72 jogos na fase de grupos + 32 jogos no mata-mata = 104 jogos
"""

# Seleções confirmadas e suas bandeiras
SELECOES = [
    {'nome': 'México', 'codigo': 'MEX', 'bandeira': '🇲🇽', 'grupo': 'A'},
    {'nome': 'África do Sul', 'codigo': 'RSA', 'bandeira': '🇿🇦', 'grupo': 'A'},
    {'nome': 'Coreia do Sul', 'codigo': 'KOR', 'bandeira': '🇰🇷', 'grupo': 'A'},
    {'nome': 'A4 (A definir)', 'codigo': 'A4', 'bandeira': '🏳️', 'grupo': 'A'},
    {'nome': 'Canadá', 'codigo': 'CAN', 'bandeira': '🇨🇦', 'grupo': 'B'},
    {'nome': 'B2 (A definir)', 'codigo': 'B2', 'bandeira': '🏳️', 'grupo': 'B'},
    {'nome': 'Catar', 'codigo': 'QAT', 'bandeira': '🇶🇦', 'grupo': 'B'},
    {'nome': 'Suíça', 'codigo': 'SUI', 'bandeira': '🇨🇭', 'grupo': 'B'},
    {'nome': 'Brasil', 'codigo': 'BRA', 'bandeira': '🇧🇷', 'grupo': 'C'},
    {'nome': 'Marrocos', 'codigo': 'MAR', 'bandeira': '🇲🇦', 'grupo': 'C'},
    {'nome': 'Haiti', 'codigo': 'HAI', 'bandeira': '🇭🇹', 'grupo': 'C'},
    {'nome': 'Escócia', 'codigo': 'SCO', 'bandeira': '🏴\U000e0067\U000e0062\U000e0073\U000e0063\U000e0074\U000e007f', 'grupo': 'C'},
    {'nome': 'Estados Unidos', 'codigo': 'USA', 'bandeira': '🇺🇸', 'grupo': 'D'},
    {'nome': 'Paraguai', 'codigo': 'PAR', 'bandeira': '🇵🇾', 'grupo': 'D'},
    {'nome': 'Austrália', 'codigo': 'AUS', 'bandeira': '🇦🇺', 'grupo': 'D'},
    {'nome': 'D4 (A definir)', 'codigo': 'D4', 'bandeira': '🏳️', 'grupo': 'D'},
    {'nome': 'Alemanha', 'codigo': 'GER', 'bandeira': '🇩🇪', 'grupo': 'E'},
    {'nome': 'E2 (A definir)', 'codigo': 'E2', 'bandeira': '🏳️', 'grupo': 'E'},
    {'nome': 'Costa do Marfim', 'codigo': 'CIV', 'bandeira': '🇨🇮', 'grupo': 'E'},
    {'nome': 'Equador', 'codigo': 'ECU', 'bandeira': '🇪🇨', 'grupo': 'E'},
    {'nome': 'Holanda', 'codigo': 'NED', 'bandeira': '🇳🇱', 'grupo': 'F'},
    {'nome': 'Japão', 'codigo': 'JPN', 'bandeira': '🇯🇵', 'grupo': 'F'},
    {'nome': 'F3 (A definir)', 'codigo': 'F3', 'bandeira': '🏳️', 'grupo': 'F'},
    {'nome': 'Tunísia', 'codigo': 'TUN', 'bandeira': '🇹🇳', 'grupo': 'F'},
    {'nome': 'Bélgica', 'codigo': 'BEL', 'bandeira': '🇧🇪', 'grupo': 'G'},
    {'nome': 'Egito', 'codigo': 'EGY', 'bandeira': '🇪🇬', 'grupo': 'G'},
    {'nome': 'Irã', 'codigo': 'IRN', 'bandeira': '🇮🇷', 'grupo': 'G'},
    {'nome': 'Nova Zelândia', 'codigo': 'NZL', 'bandeira': '🇳🇿', 'grupo': 'G'},
    {'nome': 'Espanha', 'codigo': 'ESP', 'bandeira': '🇪🇸', 'grupo': 'H'},
    {'nome': 'Cabo Verde', 'codigo': 'CPV', 'bandeira': '🇨🇻', 'grupo': 'H'},
    {'nome': 'Arábia Saudita', 'codigo': 'KSA', 'bandeira': '🇸🇦', 'grupo': 'H'},
    {'nome': 'Uruguai', 'codigo': 'URU', 'bandeira': '🇺🇾', 'grupo': 'H'},
    {'nome': 'França', 'codigo': 'FRA', 'bandeira': '🇫🇷', 'grupo': 'I'},
    {'nome': 'Senegal', 'codigo': 'SEN', 'bandeira': '🇸🇳', 'grupo': 'I'},
    {'nome': 'I3 (A definir)', 'codigo': 'I3', 'bandeira': '🏳️', 'grupo': 'I'},
    {'nome': 'Noruega', 'codigo': 'NOR', 'bandeira': '🇳🇴', 'grupo': 'I'},
    {'nome': 'Argentina', 'codigo': 'ARG', 'bandeira': '🇦🇷', 'grupo': 'J'},
    {'nome': 'Argélia', 'codigo': 'ALG', 'bandeira': '🇩🇿', 'grupo': 'J'},
    {'nome': 'Áustria', 'codigo': 'AUT', 'bandeira': '🇦🇹', 'grupo': 'J'},
    {'nome': 'Jordânia', 'codigo': 'JOR', 'bandeira': '🇯🇴', 'grupo': 'J'},
    {'nome': 'Portugal', 'codigo': 'POR', 'bandeira': '🇵🇹', 'grupo': 'K'},
    {'nome': 'Colômbia', 'codigo': 'COL', 'bandeira': '🇨🇴', 'grupo': 'K'},
    {'nome': 'Uzbequistão', 'codigo': 'UZB', 'bandeira': '🇺🇿', 'grupo': 'K'},
    {'nome': 'K4 (A definir)', 'codigo': 'K4', 'bandeira': '🏳️', 'grupo': 'K'},
    {'nome': 'Inglaterra', 'codigo': 'ENG', 'bandeira': '🏴\U000e0067\U000e0062\U000e0065\U000e006e\U000e0067\U000e007f', 'grupo': 'L'},
    {'nome': 'Croácia', 'codigo': 'CRO', 'bandeira': '🇭🇷', 'grupo': 'L'},
    {'nome': 'Gana', 'codigo': 'GHA', 'bandeira': '🇬🇭', 'grupo': 'L'},
    {'nome': 'Panamá', 'codigo': 'PAN', 'bandeira': '🇵🇦', 'grupo': 'L'},
]

# Cidades-sede
CIDADES = {
    "Vancouver": "🇨🇦",
    "Seattle": "🇺🇸",
    "San Francisco": "🇺🇸",
    "Los Angeles": "🇺🇸",
    "Guadalajara": "🇲🇽",
    "Mexico City": "🇲🇽",
    "Monterrey": "🇲🇽",
    "Houston": "🇺🇸",
    "Dallas": "🇺🇸",
    "Kansas City": "🇺🇸",
    "Atlanta": "🇺🇸",
    "Miami": "🇺🇸",
    "Toronto": "🇨🇦",
    "Boston": "🇺🇸",
    "Philadelphia": "🇺🇸",
    "New York": "🇺🇸",
}

# Jogos da Fase de Grupos
# Formato: (numero_jogo, time1_codigo, time2_codigo, data, hora_brasilia, cidade, fase, grupo)
# Horários já convertidos para Brasília (BRT = ET + 1h no verão)
# Total: 72 jogos (12 grupos × 6 jogos por grupo)
JOGOS_FASE_GRUPOS = [
    # 11 de Junho
    (1, "MEX", "RSA", "2026-06-11", "13:00", "Mexico City", "Grupos", "A"),

    # 12 de Junho
    (2, "AUS", "D4", "2026-06-12", "07:00", "Vancouver", "Grupos", "D"),
    (3, "BEL", "EGY", "2026-06-12", "13:00", "Seattle", "Grupos", "G"),
    (4, "QAT", "SUI", "2026-06-12", "16:00", "San Francisco", "Grupos", "B"),
    (5, "USA", "PAR", "2026-06-12", "16:00", "Los Angeles", "Grupos", "D"),
    (6, "KOR", "A4", "2026-06-12", "22:00", "Guadalajara", "Grupos", "A"),
    (7, "CAN", "B2", "2026-06-12", "14:00", "Toronto", "Grupos", "B"),
    (8, "HAI", "SCO", "2026-06-12", "14:00", "Boston", "Grupos", "C"),
    (9, "CIV", "ECU", "2026-06-12", "22:00", "Philadelphia", "Grupos", "E"),
    (10, "BRA", "MAR", "2026-06-12", "22:00", "New York", "Grupos", "C"),

    # 13 de Junho
    (12, "AUT", "JOR", "2026-06-13", "10:00", "San Francisco", "Grupos", "J"),
    (13, "IRN", "NZL", "2026-06-13", "13:00", "Los Angeles", "Grupos", "G"),
    (14, "MEX", "KOR", "2026-06-13", "22:00", "Guadalajara", "Grupos", "A"),
    (15, "TUN", "F3", "2026-06-13", "22:00", "Monterrey", "Grupos", "F"),
    (16, "NED", "JPN", "2026-06-13", "16:00", "Dallas", "Grupos", "F"),
    (17, "ARG", "ALG", "2026-06-13", "16:00", "Kansas City", "Grupos", "J"),
    (18, "ESP", "CPV", "2026-06-13", "19:00", "Atlanta", "Grupos", "H"),
    (19, "KSA", "URU", "2026-06-13", "19:00", "Miami", "Grupos", "H"),

    # 14 de Junho
    (20, "CAN", "QAT", "2026-06-14", "07:00", "Vancouver", "Grupos", "B"),
    (21, "USA", "AUS", "2026-06-14", "13:00", "Seattle", "Grupos", "D"),
    (22, "SUI", "B2", "2026-06-14", "10:00", "San Francisco", "Grupos", "B"),
    (24, "UZB", "COL", "2026-06-14", "22:00", "Mexico City", "Grupos", "K"),
    (25, "GER", "E2", "2026-06-14", "16:00", "Houston", "Grupos", "E"),
    (26, "ENG", "CRO", "2026-06-14", "19:00", "Dallas", "Grupos", "L"),

    # 15 de Junho
    (28, "GHA", "PAN", "2026-06-15", "16:00", "Toronto", "Grupos", "L"),
    (29, "NOR", "I3", "2026-06-15", "19:00", "Boston", "Grupos", "I"),
    (30, "BRA", "HAI", "2026-06-15", "22:00", "Philadelphia", "Grupos", "C"),
    (31, "FRA", "SEN", "2026-06-15", "22:00", "New York", "Grupos", "I"),

    # 16 de Junho
    (32, "NZL", "EGY", "2026-06-16", "07:00", "Vancouver", "Grupos", "G"),
    (33, "JOR", "ALG", "2026-06-16", "10:00", "San Francisco", "Grupos", "J"),
    (34, "BEL", "IRN", "2026-06-16", "13:00", "Los Angeles", "Grupos", "G"),
    (35, "RSA", "KOR", "2026-06-16", "22:00", "Guadalajara", "Grupos", "A"),

    # 17 de Junho
    (36, "AUT", "ARG", "2026-06-17", "10:00", "San Francisco", "Grupos", "J"),
    (37, "TUN", "JPN", "2026-06-17", "22:00", "Monterrey", "Grupos", "F"),
    (38, "ECU", "E2", "2026-06-17", "16:00", "Kansas City", "Grupos", "E"),

    # 18 de Junho
    (41, "USA", "D4", "2026-06-18", "13:00", "Seattle", "Grupos", "D"),
    (42, "PAR", "AUS", "2026-06-18", "10:00", "San Francisco", "Grupos", "D"),
    (43, "CIV", "E2", "2026-06-18", "22:00", "Philadelphia", "Grupos", "E"),
    (44, "COL", "K4", "2026-06-18", "22:00", "Guadalajara", "Grupos", "K"),
    (46, "ECU", "GER", "2026-06-18", "16:00", "Dallas", "Grupos", "E"),
    (47, "URU", "CPV", "2026-06-18", "19:00", "Miami", "Grupos", "H"),
    (49, "SCO", "MAR", "2026-06-18", "19:00", "Boston", "Grupos", "C"),
    (50, "FRA", "I3", "2026-06-18", "22:00", "New York", "Grupos", "I"),

    # 19 de Junho
    (53, "JOR", "ARG", "2026-06-19", "10:00", "San Francisco", "Grupos", "J"),
    (54, "PAR", "D4", "2026-06-19", "10:00", "San Francisco", "Grupos", "D"),
    (55, "EGY", "IRN", "2026-06-19", "13:00", "Los Angeles", "Grupos", "G"),
    (57, "RSA", "A4", "2026-06-19", "22:00", "Mexico City", "Grupos", "A"),
    (58, "POR", "UZB", "2026-06-19", "16:00", "Houston", "Grupos", "K"),
    (61, "ESP", "KSA", "2026-06-19", "19:00", "Atlanta", "Grupos", "H"),
    (62, "SCO", "BRA", "2026-06-19", "19:00", "Miami", "Grupos", "C"),
    (63, "CIV", "GER", "2026-06-19", "16:00", "Toronto", "Grupos", "E"),
    (64, "ENG", "GHA", "2026-06-19", "19:00", "Boston", "Grupos", "L"),
    (65, "FRA", "NOR", "2026-06-19", "22:00", "Philadelphia", "Grupos", "I"),
    (66, "SEN", "I3", "2026-06-19", "22:00", "New York", "Grupos", "I"),

    # 20 de Junho
    (67, "NZL", "BEL", "2026-06-20", "16:00", "Vancouver", "Grupos", "G"),
    (69, "CAN", "SUI", "2026-06-20", "16:00", "Vancouver", "Grupos", "B"),
    (70, "QAT", "B2", "2026-06-20", "16:00", "Seattle", "Grupos", "B"),

    # 21 de Junho
    (73, "MEX", "A4", "2026-06-21", "22:00", "Mexico City", "Grupos", "A"),

    # 22 de Junho
    (75, "COL", "POR", "2026-06-22", "22:00", "Guadalajara", "Grupos", "K"),
    (76, "UZB", "K4", "2026-06-22", "22:00", "Guadalajara", "Grupos", "K"),
    (77, "CPV", "KSA", "2026-06-22", "19:00", "Houston", "Grupos", "H"),
    (78, "JPN", "F3", "2026-06-22", "19:00", "Dallas", "Grupos", "F"),
    (80, "ALG", "AUT", "2026-06-22", "19:00", "Kansas City", "Grupos", "J"),
    (81, "MAR", "HAI", "2026-06-22", "22:00", "Atlanta", "Grupos", "C"),
    (82, "URU", "ESP", "2026-06-22", "22:00", "Atlanta", "Grupos", "H"),

    # 23 de Junho
    (83, "POR", "K4", "2026-06-23", "19:00", "Houston", "Grupos", "K"),
    (84, "NED", "F3", "2026-06-23", "19:00", "Houston", "Grupos", "F"),
    (85, "TUN", "NED", "2026-06-23", "19:00", "Kansas City", "Grupos", "F"),
    (89, "ENG", "PAN", "2026-06-23", "22:00", "New York", "Grupos", "L"),

    # 24 de Junho
    (90, "SEN", "NOR", "2026-06-24", "19:00", "Toronto", "Grupos", "I"),
    (91, "PAN", "CRO", "2026-06-24", "19:00", "Toronto", "Grupos", "L"),
    (94, "CRO", "GHA", "2026-06-24", "22:00", "Miami", "Grupos", "L"),
]

# Jogos do Mata-Mata (Round of 32, Round of 16, Quartas, Semis, Final)
# Horários já convertidos para Brasília (BRT = ET + 1h no verão)
# Total: 32 jogos (16 + 8 + 4 + 2 + 1 + 1)
JOGOS_MATA_MATA = [
    # 28 de Junho
    (97, "1B", "3AFJ", "2026-06-28", "13:00", "Vancouver", "Oitavas32", None),
    (98, "1G", "3BHJ", "2026-06-28", "16:00", "Seattle", "Oitavas32", None),
    (99, "1D", "3BFJ", "2026-06-28", "19:00", "San Francisco", "Oitavas32", None),
    (100, "1H", "2J", "2026-06-28", "22:00", "Los Angeles", "Oitavas32", None),

    # 29 de Junho
    (101, "2A", "2B", "2026-06-29", "13:00", "Guadalajara", "Oitavas32", None),
    (102, "1A", "3CEF", "2026-06-29", "16:00", "Mexico City", "Oitavas32", None),
    (103, "1F", "2C", "2026-06-29", "19:00", "Monterrey", "Oitavas32", None),
    (104, "1C", "2F", "2026-06-29", "22:00", "Houston", "Oitavas32", None),

    # 30 de Junho
    (105, "2E", "2D", "2026-06-30", "13:00", "Dallas", "Oitavas32", None),
    (106, "2G", "2I", "2026-06-30", "16:00", "Kansas City", "Oitavas32", None),
    (107, "1K", "3ADGF", "2026-06-30", "19:00", "Atlanta", "Oitavas32", None),
    (108, "1L", "3EFIK", "2026-06-30", "22:00", "Miami", "Oitavas32", None),

    # 1 de Julho
    (109, "2K", "2L", "2026-07-01", "13:00", "Toronto", "Oitavas32", None),
    (110, "1E", "3ADGF", "2026-07-01", "16:00", "Boston", "Oitavas32", None),
    (111, "1I", "2H", "2026-07-01", "19:00", "Philadelphia", "Oitavas32", None),
    (112, "1J", "2G", "2026-07-01", "22:00", "New York", "Oitavas32", None),

    # 4 de Julho
    (113, "W97", "W98", "2026-07-04", "16:00", "Vancouver", "Oitavas16", None),
    (114, "W99", "W100", "2026-07-04", "19:00", "Houston", "Oitavas16", None),

    # 5 de Julho
    (115, "W101", "W102", "2026-07-05", "16:00", "Dallas", "Oitavas16", None),
    (116, "W103", "W104", "2026-07-05", "19:00", "Los Angeles", "Oitavas16", None),

    # 6 de Julho
    (117, "W105", "W106", "2026-07-06", "16:00", "Mexico City", "Oitavas16", None),
    (118, "W107", "W108", "2026-07-06", "19:00", "Kansas City", "Oitavas16", None),
    (119, "W109", "W110", "2026-07-06", "16:00", "Boston", "Oitavas16", None),
    (120, "W111", "W112", "2026-07-06", "19:00", "Philadelphia", "Oitavas16", None),

    # 11 de Julho
    (121, "W113", "W114", "2026-07-11", "19:00", "Atlanta", "Quartas", None),
    (122, "W115", "W116", "2026-07-11", "22:00", "Miami", "Quartas", None),

    # 12 de Julho
    (123, "W117", "W118", "2026-07-12", "19:00", "Dallas", "Quartas", None),
    (124, "W119", "W120", "2026-07-12", "22:00", "New York", "Quartas", None),

    # 15 de Julho
    (125, "W121", "W122", "2026-07-15", "22:00", "Atlanta", "Semifinal", None),

    # 16 de Julho
    (126, "W123", "W124", "2026-07-16", "22:00", "New York", "Semifinal", None),

    # 18 de Julho
    (127, "L125", "L126", "2026-07-18", "19:00", "Miami", "Terceiro", None),

    # 19 de Julho
    (128, "W125", "W126", "2026-07-19", "16:00", "New York", "Final", None),
]
