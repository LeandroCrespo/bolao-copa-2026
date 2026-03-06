"""
Generate ML predictions using the Python RandomForest model and save to Neon DB.
This bridges the gap between the Python ML model and the TypeScript web app.

Run from /tmp/cartola-fc-automacao directory:
  cd /tmp/cartola-fc-automacao && NEON_DATABASE_URL="..." python3 /home/ubuntu/cartola-web/scripts/generate-predictions.py
"""
import sys
import os
import json

sys.path.insert(0, '/tmp/cartola-fc-automacao')

import requests
import pandas as pd
import psycopg2

def main():
    # 1. Load the model
    from estrategia_v7 import EstrategiaV7
    e = EstrategiaV7(modo_simulacao=False)
    print(f'Model loaded: {e.modelo is not None}')
    
    # 2. Get market data
    resp = requests.get('https://api.cartola.globo.com/atletas/mercado', timeout=30)
    data = resp.json()
    atletas = data.get('atletas', [])
    clubes = {int(c['id']): c['nome'] for c in data.get('clubes', {}).values()}
    print(f'Atletas no mercado: {len(atletas)}')
    
    # 3. Create DataFrame like the Streamlit app does
    df = pd.DataFrame(atletas)
    df['atleta_id'] = df['atleta_id'].astype(str)
    df['posicao_id'] = df['posicao_id'].astype(int)
    df['preco_num'] = pd.to_numeric(df['preco_num'], errors='coerce').fillna(0)
    df['media_num'] = pd.to_numeric(df['media_num'], errors='coerce').fillna(0)
    df['pontos_num'] = pd.to_numeric(df.get('pontos_num', 0), errors='coerce').fillna(0)
    df['clube_nome'] = df['clube_id'].map(clubes)
    
    # 4. Prepare features (this populates score_geral_v9 and other features)
    df_features = e.preparar_features_v9(df.copy(), modo_simulacao=False)
    
    # 5. Apply model predictions (same as inside escalar_time)
    if e.modelo:
        try:
            df_features['pred'] = e.modelo.predict(df_features[e.features])
            print(f'ML predictions generated for {len(df_features)} jogadores')
        except Exception as ex:
            print(f'Model prediction failed: {ex}')
            df_features['pred'] = df_features['score_geral_v9']
    else:
        df_features['pred'] = df_features['score_geral_v9']
    
    # 6. Extract predictions
    predictions = []
    for _, row in df_features.iterrows():
        predictions.append({
            'atleta_id': str(row['atleta_id']),
            'apelido': str(row.get('apelido', '')),
            'pred': float(row.get('pred', 0)),
            'score_geral_v9': float(row.get('score_geral_v9', 0)),
            'media': float(row.get('media', 0)),
            'preco': float(row.get('preco', 0)),
            'posicao_id': int(row.get('posicao_id', 0)),
            'status_id': int(row.get('status_id', 0)),
            'clube_id': int(row.get('clube_id', 0)),
            'clube_nome': str(row.get('clube_nome', '')),
            'media_ultimas_3': float(row.get('media_ultimas_3', 0)),
            'media_ultimas_5': float(row.get('media_ultimas_5', 0)),
            'media_ultimas_10': float(row.get('media_ultimas_10', 0)),
            'pontos_ultima': float(row.get('pontos_ultima', 0)),
            'media_historica': float(row.get('media_historica', 0)),
            'tendencia': float(row.get('tendencia', 0)),
            'momentum': float(row.get('momentum', 0)),
            'padrao_evolucao': float(row.get('padrao_evolucao', 0)),
            'oportunidade_regressao': float(row.get('oportunidade_regressao', 0)),
            'distancia_media': float(row.get('distancia_media', 0)),
        })
    
    # Show top 10
    predictions.sort(key=lambda x: x['pred'], reverse=True)
    print('\nTop 10 by ML prediction:')
    for p in predictions[:10]:
        print(f"  {p['apelido']:<20} pred: {p['pred']:>6.2f} score_v9: {p['score_geral_v9']:>6.2f} media: {p['media']:>6.2f} preco: {p['preco']:>7.2f} pos: {p['posicao_id']}")
    
    # 7. Save to Neon DB
    db_url = os.environ.get('NEON_DATABASE_URL')
    if not db_url:
        print('ERROR: No NEON_DATABASE_URL found!')
        return
    
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    
    # Create table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ml_predictions (
            atleta_id VARCHAR(20) PRIMARY KEY,
            apelido VARCHAR(100),
            pred DOUBLE PRECISION,
            score_geral_v9 DOUBLE PRECISION,
            media DOUBLE PRECISION,
            preco DOUBLE PRECISION,
            posicao_id INTEGER,
            status_id INTEGER,
            clube_id INTEGER,
            clube_nome VARCHAR(100),
            features JSONB,
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    # Clear old predictions
    cur.execute("DELETE FROM ml_predictions")
    
    # Insert new predictions
    for p in predictions:
        features = {k: p[k] for k in ['media_ultimas_3', 'media_ultimas_5', 'media_ultimas_10',
                                        'pontos_ultima', 'media_historica', 'tendencia',
                                        'momentum', 'padrao_evolucao', 'oportunidade_regressao',
                                        'distancia_media']}
        cur.execute("""
            INSERT INTO ml_predictions (atleta_id, apelido, pred, score_geral_v9, media, preco, posicao_id, status_id, clube_id, clube_nome, features, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            p['atleta_id'], p['apelido'], p['pred'], p['score_geral_v9'],
            p['media'], p['preco'], p['posicao_id'], p['status_id'],
            p['clube_id'], p['clube_nome'], json.dumps(features)
        ))
    
    conn.commit()
    cur.close()
    conn.close()
    
    print(f'\nSaved {len(predictions)} ML predictions to Neon DB (ml_predictions table)')

if __name__ == '__main__':
    main()
