"""
Função para recalcular reservas após substituição manual.
"""

import pandas as pd
from typing import Dict, List, Any

POSICAO_MAP = {1: 'GOL', 2: 'LAT', 3: 'ZAG', 4: 'MEI', 5: 'ATA', 6: 'TEC'}


def recalcular_reservas(
    escalacao: Dict,
    df_ranqueado: pd.DataFrame,
    estrategia: Any = None
) -> Dict:
    """
    Recalcula os reservas e reserva de luxo após uma substituição manual.
    
    Args:
        escalacao: Dicionário com a escalação atual (titulares, capitão, etc.)
        df_ranqueado: DataFrame com todos os jogadores ranqueados por score
        estrategia: Instância da EstrategiaV7 (opcional, para formatação)
    
    Returns:
        Escalação atualizada com novos reservas e reserva de luxo
    """
    if df_ranqueado is None or df_ranqueado.empty:
        return escalacao
    
    titulares = escalacao.get('titulares', [])
    capitao = escalacao.get('capitao')
    
    if not titulares:
        return escalacao
    
    # IDs dos titulares (não podem ser reservas)
    ids_titulares = set(str(t['atleta_id']) for t in titulares)
    
    # Posição do capitão
    pos_capitao = capitao.get('pos_id') if capitao else None
    
    # Preços máximos por posição (reserva deve ser mais barato)
    precos_max = {}
    for t in titulares:
        pos_id = t['pos_id']
        if pos_id not in precos_max:
            precos_max[pos_id] = t['preco']
        else:
            precos_max[pos_id] = min(precos_max[pos_id], t['preco'])
    
    # Garantir que df_ranqueado tem as colunas necessárias
    df = df_ranqueado.copy()
    if 'atleta_id' not in df.columns:
        return escalacao
    
    df['atleta_id_str'] = df['atleta_id'].astype(str)
    
    # Filtrar jogadores que não são titulares
    df_disponiveis = df[~df['atleta_id_str'].isin(ids_titulares)].copy()
    
    # Selecionar reserva de luxo (melhor jogador mais barato que o capitão)
    reserva_luxo = None
    if pos_capitao and capitao:
        preco_capitao = capitao.get('preco', 100)
        
        # Candidatos para reserva de luxo: mesma posição, mais barato que capitão
        luxo_candidatos = df_disponiveis[
            (df_disponiveis['posicao_id'] == pos_capitao) &
            (df_disponiveis['preco'] < preco_capitao)
        ].sort_values('score', ascending=False)
        
        if not luxo_candidatos.empty:
            luxo = luxo_candidatos.iloc[0]
            reserva_luxo = {
                'atleta_id': str(luxo['atleta_id']),
                'apelido': luxo['apelido'],
                'pos_id': int(luxo['posicao_id']),
                'posicao': POSICAO_MAP.get(int(luxo['posicao_id']), ''),
                'preco': float(luxo.get('preco', 0)),
                'media': float(luxo.get('media', luxo.get('media_num', 0))),
                'score': float(luxo.get('score', 0)),
                'clube': luxo.get('clube_nome', ''),
                'clube_id': int(luxo.get('clube_id', 0)),
                'pontos_reais': 0,
                'valorizacao_prevista': round(float(luxo.get('score', 0)) * 0.1, 2),
                'explicacao': {
                    'resumo': '⭐ Reserva de Luxo',
                    'significado': f"Score de {float(luxo.get('score', 0)):.2f} pontos previstos.",
                    'motivo': 'Melhor jogador da posição do capitão com preço menor.',
                    'fatores': [
                        f"📊 Score: {float(luxo.get('score', 0)):.2f}",
                        f"💰 Preço: C$ {float(luxo.get('preco', 0)):.1f}"
                    ]
                }
            }
    
    # IDs a excluir para reservas normais
    ids_excluir = ids_titulares.copy()
    if reserva_luxo:
        ids_excluir.add(reserva_luxo['atleta_id'])
    
    # Selecionar reservas por posição
    reservas = {}
    posicoes_titulares = set(t['pos_id'] for t in titulares)
    
    for pos_id in posicoes_titulares:
        preco_max = precos_max.get(pos_id, 100)
        
        # Se é a posição do capitão e temos reserva de luxo, usar ela
        if pos_id == pos_capitao and reserva_luxo:
            reservas[pos_id] = reserva_luxo.copy()
            reservas[pos_id]['is_reserva_luxo'] = True
            continue
        
        # Candidatos: mesma posição, mais barato que o titular mais barato
        candidatos = df_disponiveis[
            (df_disponiveis['posicao_id'] == pos_id) &
            (df_disponiveis['preco'] < preco_max) &
            (~df_disponiveis['atleta_id_str'].isin(ids_excluir))
        ].sort_values('preco', ascending=True)  # Mais barato primeiro
        
        if not candidatos.empty:
            res = candidatos.iloc[0]
            reservas[pos_id] = {
                'atleta_id': str(res['atleta_id']),
                'apelido': res['apelido'],
                'pos_id': int(res['posicao_id']),
                'posicao': POSICAO_MAP.get(int(res['posicao_id']), ''),
                'preco': float(res.get('preco', 0)),
                'media': float(res.get('media', res.get('media_num', 0))),
                'score': float(res.get('score', 0)),
                'clube': res.get('clube_nome', ''),
                'clube_id': int(res.get('clube_id', 0)),
                'pontos_reais': 0,
                'valorizacao_prevista': round(float(res.get('score', 0)) * 0.1, 2),
                'explicacao': {
                    'resumo': '🔄 Reserva',
                    'significado': f"Score de {float(res.get('score', 0)):.2f} pontos previstos.",
                    'motivo': 'Jogador mais barato disponível na posição.',
                    'fatores': [
                        f"📊 Score: {float(res.get('score', 0)):.2f}",
                        f"💰 Preço: C$ {float(res.get('preco', 0)):.1f}"
                    ]
                }
            }
            # Adicionar à lista de excluídos
            ids_excluir.add(str(res['atleta_id']))
    
    # Atualizar escalação
    escalacao['reservas'] = reservas
    escalacao['reserva_luxo'] = reserva_luxo
    
    return escalacao
