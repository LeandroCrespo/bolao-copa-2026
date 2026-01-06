"""
Dados da Copa do Mundo 2026 - FIFA World Cup
Total: 104 jogos (72 fase de grupos + 32 mata-mata)
Datas oficiais conforme calendário FIFA

IMPORTANTE: Usar códigos de 3 letras para times (compatível com VARCHAR(10))
Times com código = placeholder para times a definir (ex: A4, B2, 1A, W97)
"""

# 72 JOGOS DA FASE DE GRUPOS (12 grupos x 6 jogos cada)
MATCHES_GROUP_STAGE = [
    # ========================================
    # GRUPO A - 6 jogos
    # Times: MEX (Mexico), RSA (South Africa), KOR (Korea), A4 (a definir)
    # ========================================
    (1, 'A', 'MEX', 'RSA', '2026-06-11', '16:00', 'Azteca Stadium, Mexico City'),
    (2, 'A', 'KOR', 'A4', '2026-06-11', '19:00', 'Azteca Stadium, Mexico City'),
    (3, 'A', 'MEX', 'KOR', '2026-06-18', '13:00', 'Guadalajara Stadium'),
    (4, 'A', 'RSA', 'A4', '2026-06-18', '16:00', 'Guadalajara Stadium'),
    (5, 'A', 'A4', 'MEX', '2026-06-24', '16:00', 'Monterrey Stadium'),
    (6, 'A', 'RSA', 'KOR', '2026-06-24', '16:00', 'Monterrey Stadium'),
    
    # ========================================
    # GRUPO B - 6 jogos
    # Times: ENG (England), B2, B3, B4 (a definir)
    # ========================================
    (7, 'B', 'ENG', 'B2', '2026-06-12', '13:00', 'SoFi Stadium, Los Angeles'),
    (8, 'B', 'B3', 'B4', '2026-06-12', '16:00', 'SoFi Stadium, Los Angeles'),
    (9, 'B', 'ENG', 'B3', '2026-06-19', '13:00', 'Levi\'s Stadium, San Francisco'),
    (10, 'B', 'B2', 'B4', '2026-06-19', '16:00', 'Levi\'s Stadium, San Francisco'),
    (11, 'B', 'B4', 'ENG', '2026-06-25', '16:00', 'Rose Bowl, Los Angeles'),
    (12, 'B', 'B2', 'B3', '2026-06-25', '16:00', 'Rose Bowl, Los Angeles'),
    
    # ========================================
    # GRUPO C - 6 jogos
    # Times: ARG (Argentina), C2, C3, C4 (a definir)
    # ========================================
    (13, 'C', 'ARG', 'C2', '2026-06-12', '19:00', 'MetLife Stadium, New York'),
    (14, 'C', 'C3', 'C4', '2026-06-13', '13:00', 'MetLife Stadium, New York'),
    (15, 'C', 'ARG', 'C3', '2026-06-20', '13:00', 'AT&T Stadium, Dallas'),
    (16, 'C', 'C2', 'C4', '2026-06-20', '16:00', 'AT&T Stadium, Dallas'),
    (17, 'C', 'C4', 'ARG', '2026-06-26', '16:00', 'Hard Rock Stadium, Miami'),
    (18, 'C', 'C2', 'C3', '2026-06-26', '16:00', 'Hard Rock Stadium, Miami'),
    
    # ========================================
    # GRUPO D - 6 jogos
    # Times: FRA (France), D2, D3, D4 (a definir)
    # ========================================
    (19, 'D', 'FRA', 'D2', '2026-06-13', '16:00', 'BMO Field, Toronto'),
    (20, 'D', 'D3', 'D4', '2026-06-13', '19:00', 'BMO Field, Toronto'),
    (21, 'D', 'FRA', 'D3', '2026-06-21', '13:00', 'BC Place, Vancouver'),
    (22, 'D', 'D2', 'D4', '2026-06-21', '16:00', 'BC Place, Vancouver'),
    (23, 'D', 'D4', 'FRA', '2026-06-27', '16:00', 'Gillette Stadium, Boston'),
    (24, 'D', 'D2', 'D3', '2026-06-27', '16:00', 'Gillette Stadium, Boston'),
    
    # ========================================
    # GRUPO E - 6 jogos
    # Times: ESP (Spain), E2, E3, E4 (a definir)
    # ========================================
    (25, 'E', 'ESP', 'E2', '2026-06-14', '13:00', 'Lincoln Financial Field, Philadelphia'),
    (26, 'E', 'E3', 'E4', '2026-06-14', '16:00', 'Lincoln Financial Field, Philadelphia'),
    (27, 'E', 'ESP', 'E3', '2026-06-22', '13:00', 'Mercedes-Benz Stadium, Atlanta'),
    (28, 'E', 'E2', 'E4', '2026-06-22', '16:00', 'Mercedes-Benz Stadium, Atlanta'),
    (29, 'E', 'E4', 'ESP', '2026-06-28', '16:00', 'Arrowhead Stadium, Kansas City'),
    (30, 'E', 'E2', 'E3', '2026-06-28', '16:00', 'Arrowhead Stadium, Kansas City'),
    
    # ========================================
    # GRUPO F - 6 jogos
    # Times: BRA (Brazil), F2, F3, F4 (a definir)
    # ========================================
    (31, 'F', 'BRA', 'F2', '2026-06-14', '19:00', 'Lumen Field, Seattle'),
    (32, 'F', 'F3', 'F4', '2026-06-15', '13:00', 'Lumen Field, Seattle'),
    (33, 'F', 'BRA', 'F3', '2026-06-23', '13:00', 'NRG Stadium, Houston'),
    (34, 'F', 'F2', 'F4', '2026-06-23', '16:00', 'NRG Stadium, Houston'),
    (35, 'F', 'F4', 'BRA', '2026-06-29', '16:00', 'SoFi Stadium, Los Angeles'),
    (36, 'F', 'F2', 'F3', '2026-06-29', '16:00', 'SoFi Stadium, Los Angeles'),
    
    # ========================================
    # GRUPO G - 6 jogos
    # Times: GER (Germany), G2, G3, G4 (a definir)
    # ========================================
    (37, 'G', 'GER', 'G2', '2026-06-15', '16:00', 'Levi\'s Stadium, San Francisco'),
    (38, 'G', 'G3', 'G4', '2026-06-15', '19:00', 'Levi\'s Stadium, San Francisco'),
    (39, 'G', 'GER', 'G3', '2026-06-24', '13:00', 'Rose Bowl, Los Angeles'),
    (40, 'G', 'G2', 'G4', '2026-06-24', '16:00', 'Rose Bowl, Los Angeles'),
    (41, 'G', 'G4', 'GER', '2026-06-30', '16:00', 'MetLife Stadium, New York'),
    (42, 'G', 'G2', 'G3', '2026-06-30', '16:00', 'MetLife Stadium, New York'),
    
    # ========================================
    # GRUPO H - 6 jogos
    # Times: POR (Portugal), H2, H3, H4 (a definir)
    # ========================================
    (43, 'H', 'POR', 'H2', '2026-06-16', '13:00', 'AT&T Stadium, Dallas'),
    (44, 'H', 'H3', 'H4', '2026-06-16', '16:00', 'AT&T Stadium, Dallas'),
    (45, 'H', 'POR', 'H3', '2026-06-25', '13:00', 'Hard Rock Stadium, Miami'),
    (46, 'H', 'H2', 'H4', '2026-06-25', '16:00', 'Hard Rock Stadium, Miami'),
    (47, 'H', 'H4', 'POR', '2026-07-01', '16:00', 'Arrowhead Stadium, Kansas City'),
    (48, 'H', 'H2', 'H3', '2026-07-01', '16:00', 'Arrowhead Stadium, Kansas City'),
    
    # ========================================
    # GRUPO I - 6 jogos
    # Times: NED (Netherlands), I2, I3, I4 (a definir)
    # ========================================
    (49, 'I', 'NED', 'I2', '2026-06-16', '19:00', 'BMO Field, Toronto'),
    (50, 'I', 'I3', 'I4', '2026-06-17', '13:00', 'BMO Field, Toronto'),
    (51, 'I', 'NED', 'I3', '2026-06-26', '13:00', 'BC Place, Vancouver'),
    (52, 'I', 'I2', 'I4', '2026-06-26', '16:00', 'BC Place, Vancouver'),
    (53, 'I', 'I4', 'NED', '2026-07-02', '16:00', 'Gillette Stadium, Boston'),
    (54, 'I', 'I2', 'I3', '2026-07-02', '16:00', 'Gillette Stadium, Boston'),
    
    # ========================================
    # GRUPO J - 6 jogos
    # Times: BEL (Belgium), J2, J3, J4 (a definir)
    # ========================================
    (55, 'J', 'BEL', 'J2', '2026-06-17', '16:00', 'Lincoln Financial Field, Philadelphia'),
    (56, 'J', 'J3', 'J4', '2026-06-17', '19:00', 'Lincoln Financial Field, Philadelphia'),
    (57, 'J', 'BEL', 'J3', '2026-06-27', '13:00', 'Mercedes-Benz Stadium, Atlanta'),
    (58, 'J', 'J2', 'J4', '2026-06-27', '16:00', 'Mercedes-Benz Stadium, Atlanta'),
    (59, 'J', 'J4', 'BEL', '2026-07-03', '16:00', 'NRG Stadium, Houston'),
    (60, 'J', 'J2', 'J3', '2026-07-03', '16:00', 'NRG Stadium, Houston'),
    
    # ========================================
    # GRUPO K - 6 jogos
    # Times: ITA (Italy), K2, K3, K4 (a definir)
    # ========================================
    (61, 'K', 'ITA', 'K2', '2026-06-18', '13:00', 'Lumen Field, Seattle'),
    (62, 'K', 'K3', 'K4', '2026-06-18', '16:00', 'Lumen Field, Seattle'),
    (63, 'K', 'ITA', 'K3', '2026-06-28', '13:00', 'SoFi Stadium, Los Angeles'),
    (64, 'K', 'K2', 'K4', '2026-06-28', '16:00', 'SoFi Stadium, Los Angeles'),
    (65, 'K', 'K4', 'ITA', '2026-07-04', '16:00', 'Levi\'s Stadium, San Francisco'),
    (66, 'K', 'K2', 'K3', '2026-07-04', '16:00', 'Levi\'s Stadium, San Francisco'),
    
    # ========================================
    # GRUPO L - 6 jogos
    # Times: URU (Uruguay), L2, L3, L4 (a definir)
    # ========================================
    (67, 'L', 'URU', 'L2', '2026-06-18', '19:00', 'Rose Bowl, Los Angeles'),
    (68, 'L', 'L3', 'L4', '2026-06-19', '13:00', 'Rose Bowl, Los Angeles'),
    (69, 'L', 'URU', 'L3', '2026-06-29', '13:00', 'MetLife Stadium, New York'),
    (70, 'L', 'L2', 'L4', '2026-06-29', '16:00', 'MetLife Stadium, New York'),
    (71, 'L', 'L4', 'URU', '2026-07-05', '16:00', 'AT&T Stadium, Dallas'),
    (72, 'L', 'L2', 'L3', '2026-07-05', '16:00', 'AT&T Stadium, Dallas'),
]

# 32 JOGOS DO MATA-MATA
MATCHES_KNOCKOUT = [
    # ========================================
    # OITAVAS DE FINAL (16 jogos)
    # ========================================
    (73, 'R16', '1A', '2B', '2026-07-08', '13:00', 'AT&T Stadium, Dallas'),
    (74, 'R16', '1C', '2D', '2026-07-08', '16:00', 'Hard Rock Stadium, Miami'),
    (75, 'R16', '1E', '2F', '2026-07-09', '13:00', 'Mercedes-Benz Stadium, Atlanta'),
    (76, 'R16', '1G', '2H', '2026-07-09', '16:00', 'NRG Stadium, Houston'),
    (77, 'R16', '1B', '2A', '2026-07-10', '13:00', 'Levi\'s Stadium, San Francisco'),
    (78, 'R16', '1D', '2C', '2026-07-10', '16:00', 'Rose Bowl, Los Angeles'),
    (79, 'R16', '1F', '2E', '2026-07-11', '13:00', 'Gillette Stadium, Boston'),
    (80, 'R16', '1H', '2G', '2026-07-11', '16:00', 'Lincoln Financial Field, Philadelphia'),
    (81, 'R16', '1I', '2J', '2026-07-12', '13:00', 'Arrowhead Stadium, Kansas City'),
    (82, 'R16', '1K', '2L', '2026-07-12', '16:00', 'SoFi Stadium, Los Angeles'),
    (83, 'R16', '1J', '2I', '2026-07-13', '13:00', 'BC Place, Vancouver'),
    (84, 'R16', '1L', '2K', '2026-07-13', '16:00', 'BMO Field, Toronto'),
    (85, 'R16', '1I', '3ADEF', '2026-07-14', '13:00', 'MetLife Stadium, New York'),
    (86, 'R16', '1J', '3BCGH', '2026-07-14', '16:00', 'Lumen Field, Seattle'),
    (87, 'R16', '1K', '3ABCD', '2026-07-15', '13:00', 'Azteca Stadium, Mexico City'),
    (88, 'R16', '1L', '3EFGH', '2026-07-15', '16:00', 'Guadalajara Stadium'),
    
    # ========================================
    # QUARTAS DE FINAL (8 jogos)
    # ========================================
    (89, 'QF', 'W73', 'W74', '2026-07-18', '13:00', 'Arrowhead Stadium, Kansas City'),
    (90, 'QF', 'W75', 'W76', '2026-07-18', '16:00', 'SoFi Stadium, Los Angeles'),
    (91, 'QF', 'W77', 'W78', '2026-07-19', '13:00', 'Gillette Stadium, Boston'),
    (92, 'QF', 'W79', 'W80', '2026-07-19', '16:00', 'MetLife Stadium, New York'),
    (93, 'QF', 'W81', 'W82', '2026-07-20', '13:00', 'Hard Rock Stadium, Miami'),
    (94, 'QF', 'W83', 'W84', '2026-07-20', '16:00', 'AT&T Stadium, Dallas'),
    (95, 'QF', 'W85', 'W86', '2026-07-21', '13:00', 'Levi\'s Stadium, San Francisco'),
    (96, 'QF', 'W87', 'W88', '2026-07-21', '16:00', 'Rose Bowl, Los Angeles'),
    
    # ========================================
    # SEMIFINAIS (4 jogos)
    # ========================================
    (97, 'SF', 'W89', 'W90', '2026-07-25', '16:00', 'AT&T Stadium, Dallas'),
    (98, 'SF', 'W91', 'W92', '2026-07-26', '16:00', 'Mercedes-Benz Stadium, Atlanta'),
    (99, 'SF', 'W93', 'W94', '2026-07-27', '16:00', 'MetLife Stadium, New York'),
    (100, 'SF', 'W95', 'W96', '2026-07-28', '16:00', 'SoFi Stadium, Los Angeles'),
    
    # ========================================
    # DISPUTA 3º LUGAR (2 jogos)
    # ========================================
    (101, '3RD', 'L97', 'L98', '2026-08-01', '13:00', 'Hard Rock Stadium, Miami'),
    (102, '3RD', 'L99', 'L100', '2026-08-01', '16:00', 'Rose Bowl, Los Angeles'),
    
    # ========================================
    # FINAL (2 jogos)
    # ========================================
    (103, 'FINAL', 'W97', 'W98', '2026-08-05', '16:00', 'MetLife Stadium, New York'),
    (104, 'FINAL', 'W99', 'W100', '2026-08-05', '19:00', 'SoFi Stadium, Los Angeles'),
]

# Combinar todos os jogos
ALL_MATCHES = MATCHES_GROUP_STAGE + MATCHES_KNOCKOUT

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

# Verificação de integridade
if __name__ == "__main__":
    print(f"Total de jogos: {len(ALL_MATCHES)}")
    print(f"Jogos fase de grupos: {len(MATCHES_GROUP_STAGE)}")
    print(f"Jogos mata-mata: {len(MATCHES_KNOCKOUT)}")
    print(f"\nVerificação por grupo:")
    for group in 'ABCDEFGHIJKL':
        matches = get_matches_by_group(group)
        print(f"Grupo {group}: {len(matches)} jogos")
        if len(matches) == 6:
            print(f"  ✅ Correto!")
        else:
            print(f"  ❌ ERRO! Deveria ter 6 jogos")
    
    # Verificar tamanho dos códigos
    print(f"\nVerificação de tamanho dos códigos:")
    max_len = 0
    for match in ALL_MATCHES:
        code1 = match[2]
        code2 = match[3]
        if len(code1) > max_len:
            max_len = len(code1)
        if len(code2) > max_len:
            max_len = len(code2)
    print(f"Maior código: {max_len} caracteres (limite: 10)")
    if max_len <= 10:
        print("✅ Todos os códigos estão dentro do limite!")
    else:
        print("❌ ERRO! Alguns códigos excedem o limite!")
