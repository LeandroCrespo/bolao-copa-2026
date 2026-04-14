"""
Script para deletar jogos e palpites antigos do banco Neon PostgreSQL
Isso vai forçar o app a reinicializar com os dados corretos do copa2026_data.py
"""

import os
import psycopg2

# String de conexão Neon PostgreSQL
CONN_STRING = os.environ.get('NEON_CONNECTION_STRING', '')

def main():
    print("=" * 100)
    print("🗑️  DELETAR JOGOS ANTIGOS DO BANCO")
    print("=" * 100)
    print()
    print("Este script vai:")
    print("1. DELETAR todos os palpites (predictions)")
    print("2. DELETAR todos os jogos (matches)")
    print("3. Preparar o banco para reinicialização com dados corretos")
    print()
    print("⚠️  Após executar este script, o app vai carregar os dados corretos do copa2026_data.py")
    print()
    
    confirmacao = input("Tem CERTEZA que deseja continuar? Digite 'SIM' para confirmar: ")
    
    if confirmacao.upper() != 'SIM':
        print("\n❌ Operação cancelada pelo usuário")
        return
    
    print("\n" + "=" * 100)
    
    try:
        print("🔌 Conectando ao banco Neon PostgreSQL...")
        conn = psycopg2.connect(CONN_STRING)
        cur = conn.cursor()
        print("✅ Conectado com sucesso!")
        
        # Deletar palpites primeiro (foreign key constraint)
        print("\n🗑️  Deletando palpites...")
        cur.execute("DELETE FROM predictions;")
        deleted_predictions = cur.rowcount
        print(f"✅ {deleted_predictions} palpites deletados")
        
        # Deletar jogos
        print("\n🗑️  Deletando jogos...")
        cur.execute("DELETE FROM matches;")
        deleted_matches = cur.rowcount
        print(f"✅ {deleted_matches} jogos deletados")
        
        # Commit
        conn.commit()
        
        print("\n" + "=" * 100)
        print("✅ BANCO LIMPO COM SUCESSO!")
        print("=" * 100)
        print()
        print("Próximos passos:")
        print("1. Acessar o app: https://bolao-copa-2026-familia.streamlit.app/")
        print("2. Aguardar 1-2 minutos para o app reinicializar")
        print("3. Apertar F5 para recarregar")
        print("4. O app vai carregar os 104 jogos corretos do copa2026_data.py")
        print()
        print("✅ Pronto! Sistema reinicializado com dados corretos! 🎉")
        print()
        
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        print("\nSe o erro persistir, entre em contato para suporte.")
        
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("🔌 Conexão fechada")

if __name__ == "__main__":
    main()
