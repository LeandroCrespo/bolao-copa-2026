"""
FUNÇÃO CORRIGIDA para db.py
Substitua a função populate_copa2026_data() no seu arquivo db.py por esta versão

Esta versão usa as novas variáveis do copa2026_data.py:
- ALL_MATCHES (todos os 104 jogos)
- MATCHES_GROUP_STAGE (72 jogos fase de grupos)
- MATCHES_KNOCKOUT (32 jogos mata-mata)
"""

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


# ============================================
# INSTRUÇÕES DE USO:
# ============================================
# 
# 1. Abrir o arquivo db.py no seu projeto
# 
# 2. Localizar a função populate_copa2026_data()
#    (deve estar por volta da linha 200)
# 
# 3. DELETAR a função antiga inteira
# 
# 4. COPIAR e COLAR esta nova função no lugar
# 
# 5. Salvar o arquivo
# 
# 6. Fazer commit e push no GitHub:
#    git add db.py
#    git commit -m "Corrigir função populate_copa2026_data"
#    git push
# 
# 7. Aguardar Streamlit Cloud atualizar (1-2 min)
# 
# 8. Executar o script deletar_jogos_antigos.py
# 
# 9. Recarregar o app (F5)
# 
# ✅ Pronto! Sistema funcionando!
# ============================================
