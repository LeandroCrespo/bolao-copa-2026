"""
FUNÇÃO ATUALIZADA: admin_participantes
Adiciona opção de EXCLUIR participante (além de desativar e resetar senha)

INSTRUÇÕES:
1. Abra o arquivo app.py
2. Localize a função admin_participantes (linha ~829)
3. Substitua a função inteira por esta versão
4. Salve e faça commit
"""

def admin_participantes(session):
    """Gerenciamento de participantes"""
    st.subheader("👥 Gerenciar Participantes")
    
    # Formulário para novo participante
    with st.expander("➕ Adicionar Participante"):
        with st.form("new_participant"):
            name = st.text_input("Nome completo")
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            
            if st.form_submit_button("Criar Participante"):
                if name and username and password:
                    user = create_user(session, name, username, password, 'player')
                    if user:
                        st.success(f"Participante '{name}' criado com sucesso!")
                        log_action(session, st.session_state.user['id'], 'participante_criado', user.id)
                        st.rerun()
                    else:
                        st.error("Usuário já existe!")
                else:
                    st.warning("Preencha todos os campos!")
    
    # Lista de participantes
    users = session.query(User).filter(User.role == 'player').order_by(User.name).all()
    
    for user in users:
        status = "✅ Ativo" if user.active else "❌ Inativo"
        
        with st.expander(f"{user.name} (@{user.username}) - {status}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if user.active:
                    if st.button(f"🚫 Desativar", key=f"deactivate_{user.id}"):
                        user.active = False
                        session.commit()
                        log_action(session, st.session_state.user['id'], 'participante_desativado', user.id)
                        st.rerun()
                else:
                    if st.button(f"✅ Ativar", key=f"activate_{user.id}"):
                        user.active = True
                        session.commit()
                        log_action(session, st.session_state.user['id'], 'participante_ativado', user.id)
                        st.rerun()
            
            with col2:
                if st.button(f"🔑 Resetar Senha", key=f"reset_{user.id}"):
                    user.password_hash = hash_password("123456")
                    session.commit()
                    st.success(f"Senha resetada para '123456'")
                    log_action(session, st.session_state.user['id'], 'senha_resetada', user.id)
            
            with col3:
                # Botão de excluir com confirmação
                if st.button(f"🗑️ Excluir", key=f"delete_{user.id}", type="secondary"):
                    st.session_state[f'confirm_delete_{user.id}'] = True
                
                # Confirmação de exclusão
                if st.session_state.get(f'confirm_delete_{user.id}', False):
                    st.warning(f"⚠️ Tem certeza que deseja EXCLUIR '{user.name}'?")
                    st.caption("Esta ação é irreversível! Todos os palpites serão perdidos.")
                    
                    confirm_col1, confirm_col2 = st.columns(2)
                    with confirm_col1:
                        if st.button("✅ Sim, excluir", key=f"confirm_yes_{user.id}", type="primary"):
                            # Deletar palpites do usuário
                            session.query(Prediction).filter(Prediction.user_id == user.id).delete()
                            session.query(GroupPrediction).filter(GroupPrediction.user_id == user.id).delete()
                            session.query(PodiumPrediction).filter(PodiumPrediction.user_id == user.id).delete()
                            
                            # Registrar ação antes de deletar
                            log_action(session, st.session_state.user['id'], 'participante_excluido', user.id, 
                                      f"Excluído: {user.name} (@{user.username})")
                            
                            # Deletar usuário
                            session.delete(user)
                            session.commit()
                            
                            st.success(f"Participante '{user.name}' excluído com sucesso!")
                            st.session_state[f'confirm_delete_{user.id}'] = False
                            st.rerun()
                    
                    with confirm_col2:
                        if st.button("❌ Cancelar", key=f"confirm_no_{user.id}"):
                            st.session_state[f'confirm_delete_{user.id}'] = False
                            st.rerun()
