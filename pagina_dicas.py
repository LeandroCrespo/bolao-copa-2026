"""
NOVA PÁGINA: Dicas - Power Ranking FIFA
Adiciona uma página de dicas para ajudar os participantes nos palpites

INSTRUÇÕES:
1. Adicione esta função no arquivo app.py
2. Adicione "Dicas" no menu de navegação
3. Chame a função page_dicas(session) quando o menu "Dicas" for selecionado
"""

def page_dicas(session):
    """Página de Dicas com Power Ranking FIFA"""
    st.header("💡 Dicas para seus Palpites")
    
    # Texto explicativo sobre o ranking
    st.markdown("""
    ### 📊 Sobre o Ranking FIFA
    
    O **Ranking FIFA/Coca-Cola** é a classificação oficial das seleções masculinas de futebol, 
    atualizado mensalmente pela FIFA. Ele considera os resultados das partidas internacionais, 
    a importância dos jogos e a força dos adversários enfrentados.
    
    > **⚠️ Importante:** Este ranking serve como uma **referência** para auxiliar nos seus palpites, 
    > mas **não deve ser seguido à risca**! O futebol é imprevisível e grandes surpresas acontecem 
    > em toda Copa do Mundo. Seleções bem posicionadas podem tropeçar, enquanto equipes menos 
    > cotadas frequentemente surpreendem. Use estas informações como um **guia**, mas confie 
    > também na sua **intuição** e **conhecimento do futebol**!
    
    ---
    """)
    
    # Power Ranking das seleções da Copa 2026
    st.subheader("🏆 Power Ranking - Copa do Mundo 2026")
    
    # Dados do ranking FIFA (dezembro 2025)
    ranking_data = [
        # Tier 1 - Favoritas (Top 5)
        {"tier": "⭐ FAVORITAS", "teams": [
            {"pos": 1, "code": "ESP", "name": "Espanha", "flag": "🇪🇸", "rank": 1, "points": 1877, "group": "H"},
            {"pos": 2, "code": "ARG", "name": "Argentina", "flag": "🇦🇷", "rank": 2, "points": 1873, "group": "J"},
            {"pos": 3, "code": "FRA", "name": "França", "flag": "🇫🇷", "rank": 3, "points": 1870, "group": "I"},
            {"pos": 4, "code": "ENG", "name": "Inglaterra", "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "rank": 4, "points": 1834, "group": "L"},
            {"pos": 5, "code": "BRA", "name": "Brasil", "flag": "🇧🇷", "rank": 5, "points": 1760, "group": "C"},
        ]},
        # Tier 2 - Fortes candidatas (6-10)
        {"tier": "🥇 FORTES CANDIDATAS", "teams": [
            {"pos": 6, "code": "POR", "name": "Portugal", "flag": "🇵🇹", "rank": 6, "points": 1760, "group": "K"},
            {"pos": 7, "code": "NED", "name": "Holanda", "flag": "🇳🇱", "rank": 7, "points": 1756, "group": "F"},
            {"pos": 8, "code": "BEL", "name": "Bélgica", "flag": "🇧🇪", "rank": 8, "points": 1731, "group": "G"},
            {"pos": 9, "code": "GER", "name": "Alemanha", "flag": "🇩🇪", "rank": 9, "points": 1724, "group": "E"},
            {"pos": 10, "code": "CRO", "name": "Croácia", "flag": "🇭🇷", "rank": 10, "points": 1717, "group": "L"},
        ]},
        # Tier 3 - Competitivas (11-20)
        {"tier": "🥈 COMPETITIVAS", "teams": [
            {"pos": 11, "code": "MAR", "name": "Marrocos", "flag": "🇲🇦", "rank": 11, "points": 1716, "group": "C"},
            {"pos": 12, "code": "COL", "name": "Colômbia", "flag": "🇨🇴", "rank": 13, "points": 1701, "group": "K"},
            {"pos": 13, "code": "USA", "name": "Estados Unidos", "flag": "🇺🇸", "rank": 14, "points": 1682, "group": "D"},
            {"pos": 14, "code": "MEX", "name": "México", "flag": "🇲🇽", "rank": 15, "points": 1676, "group": "A"},
            {"pos": 15, "code": "URU", "name": "Uruguai", "flag": "🇺🇾", "rank": 16, "points": 1673, "group": "H"},
            {"pos": 16, "code": "SUI", "name": "Suíça", "flag": "🇨🇭", "rank": 17, "points": 1655, "group": "B"},
            {"pos": 17, "code": "JPN", "name": "Japão", "flag": "🇯🇵", "rank": 18, "points": 1650, "group": "F"},
            {"pos": 18, "code": "SEN", "name": "Senegal", "flag": "🇸🇳", "rank": 19, "points": 1648, "group": "I"},
            {"pos": 19, "code": "IRN", "name": "Irã", "flag": "🇮🇷", "rank": 20, "points": 1617, "group": "G"},
            {"pos": 20, "code": "KOR", "name": "Coreia do Sul", "flag": "🇰🇷", "rank": 22, "points": 1599, "group": "A"},
        ]},
        # Tier 4 - Médias (21-35)
        {"tier": "🥉 MÉDIAS", "teams": [
            {"pos": 21, "code": "ECU", "name": "Equador", "flag": "🇪🇨", "rank": 23, "points": 1592, "group": "E"},
            {"pos": 22, "code": "AUT", "name": "Áustria", "flag": "🇦🇹", "rank": 24, "points": 1586, "group": "J"},
            {"pos": 23, "code": "AUS", "name": "Austrália", "flag": "🇦🇺", "rank": 26, "points": 1574, "group": "D"},
            {"pos": 24, "code": "CAN", "name": "Canadá", "flag": "🇨🇦", "rank": 27, "points": 1559, "group": "B"},
            {"pos": 25, "code": "NOR", "name": "Noruega", "flag": "🇳🇴", "rank": 29, "points": 1553, "group": "I"},
            {"pos": 26, "code": "PAN", "name": "Panamá", "flag": "🇵🇦", "rank": 30, "points": 1540, "group": "L"},
            {"pos": 27, "code": "ALG", "name": "Argélia", "flag": "🇩🇿", "rank": 34, "points": 1518, "group": "J"},
            {"pos": 28, "code": "EGY", "name": "Egito", "flag": "🇪🇬", "rank": 35, "points": 1515, "group": "G"},
            {"pos": 29, "code": "SCO", "name": "Escócia", "flag": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "rank": 36, "points": 1507, "group": "C"},
            {"pos": 30, "code": "PAR", "name": "Paraguai", "flag": "🇵🇾", "rank": 39, "points": 1502, "group": "D"},
        ]},
        # Tier 5 - Zebras potenciais (36-48)
        {"tier": "🦓 ZEBRAS POTENCIAIS", "teams": [
            {"pos": 31, "code": "TUN", "name": "Tunísia", "flag": "🇹🇳", "rank": 41, "points": 1495, "group": "F"},
            {"pos": 32, "code": "CIV", "name": "Costa do Marfim", "flag": "🇨🇮", "rank": 42, "points": 1490, "group": "E"},
            {"pos": 33, "code": "UZB", "name": "Uzbequistão", "flag": "🇺🇿", "rank": 50, "points": 1462, "group": "K"},
            {"pos": 34, "code": "QAT", "name": "Qatar", "flag": "🇶🇦", "rank": 54, "points": 1455, "group": "B"},
            {"pos": 35, "code": "KSA", "name": "Arábia Saudita", "flag": "🇸🇦", "rank": 60, "points": 1429, "group": "H"},
            {"pos": 36, "code": "RSA", "name": "África do Sul", "flag": "🇿🇦", "rank": 61, "points": 1427, "group": "A"},
            {"pos": 37, "code": "JOR", "name": "Jordânia", "flag": "🇯🇴", "rank": 64, "points": 1389, "group": "J"},
            {"pos": 38, "code": "CPV", "name": "Cabo Verde", "flag": "🇨🇻", "rank": 67, "points": 1370, "group": "H"},
            {"pos": 39, "code": "GHA", "name": "Gana", "flag": "🇬🇭", "rank": 72, "points": 1351, "group": "L"},
            {"pos": 40, "code": "CUR", "name": "Curaçao", "flag": "🇨🇼", "rank": 82, "points": 1303, "group": "E"},
            {"pos": 41, "code": "HAI", "name": "Haiti", "flag": "🇭🇹", "rank": 84, "points": 1294, "group": "C"},
            {"pos": 42, "code": "NZL", "name": "Nova Zelândia", "flag": "🇳🇿", "rank": 87, "points": 1279, "group": "G"},
        ]},
    ]
    
    # Exibir cada tier
    for tier_data in ranking_data:
        st.markdown(f"### {tier_data['tier']}")
        
        # Criar tabela
        table_data = []
        for team in tier_data['teams']:
            table_data.append({
                "#": team['pos'],
                "Seleção": f"{team['flag']} {team['name']}",
                "Ranking FIFA": f"#{team['rank']}",
                "Pontos": team['points'],
                "Grupo": team['group']
            })
        
        import pandas as pd
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown("---")
    
    # Seleções da Repescagem
    st.subheader("🎯 Seleções da Repescagem (A Definir)")
    
    st.markdown("""
    Estas seleções ainda disputarão a repescagem para definir as últimas vagas:
    
    **🇪🇺 Repescagem Europa:**
    | Chave | Seleções |
    |-------|----------|
    | Europa A | 🇮🇹 Itália, 🇮🇪 Irlanda do Norte, 🏴󠁧󠁢󠁷󠁬󠁳󠁿 País de Gales, 🇧🇦 Bósnia |
    | Europa B | 🇺🇦 Ucrânia, 🇸🇪 Suécia, 🇵🇱 Polônia, 🇦🇱 Albânia |
    | Europa C | 🇹🇷 Turquia, 🇷🇴 Romênia, 🇸🇰 Eslováquia, 🇽🇰 Kosovo |
    | Europa D | 🇨🇿 Rep. Tcheca, 🇮🇪 Irlanda, 🇩🇰 Dinamarca, 🇲🇰 Macedônia do Norte |
    
    **🌍 Repescagem Intercontinental:**
    | Chave | Seleções |
    |-------|----------|
    | Intercon. 1 | 🇨🇩 Congo DR, 🇯🇲 Jamaica, 🇳🇨 Nova Caledônia |
    | Intercon. 2 | 🇧🇴 Bolívia, 🇸🇷 Suriname, 🇮🇶 Iraque |
    """)
    
    # Dicas extras
    st.subheader("📝 Dicas Extras")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🏠 Fator Casa:**
        - 🇺🇸 EUA, 🇨🇦 Canadá e 🇲🇽 México jogam em casa
        - Seleções anfitriãs costumam ter desempenho acima do esperado
        - Torcida e clima familiar fazem diferença!
        """)
        
        st.markdown("""
        **📈 Seleções em Alta:**
        - 🇲🇦 Marrocos: Semifinalista em 2022
        - 🇯🇵 Japão: Eliminando potências europeias
        - 🇦🇺 Austrália: Crescimento consistente
        """)
    
    with col2:
        st.markdown("""
        **⚠️ Atenção aos Grupos:**
        - **Grupo C** (Brasil, Marrocos, Escócia, Haiti): Grupo da morte!
        - **Grupo L** (Inglaterra, Croácia, Gana, Panamá): Muito equilibrado
        - **Grupo J** (Argentina, Argélia, Áustria, Jordânia): Argentina favorita
        """)
        
        st.markdown("""
        **🎲 Zebras Históricas:**
        - Coreia do Sul 2002 (4º lugar)
        - Croácia 2018 (Vice-campeã)
        - Marrocos 2022 (4º lugar)
        """)
    
    # Rodapé
    st.markdown("---")
    st.caption("📅 Ranking FIFA atualizado em Dezembro/2025 | Fonte: FIFA.com")


# ============================================
# COMO ADICIONAR NO app.py:
# ============================================
# 
# 1. Cole esta função no arquivo app.py (após as outras funções de página)
#
# 2. No menu de navegação, adicione a opção "Dicas":
#    
#    Exemplo (localize o menu de navegação e adicione):
#    
#    if st.session_state.user:
#        menu_options = ["🏠 Início", "⚽ Jogos", "📊 Ranking", "💡 Dicas", ...]
#        ...
#        if menu == "💡 Dicas":
#            page_dicas(session)
#
# 3. Salve e faça commit
#
# ============================================
