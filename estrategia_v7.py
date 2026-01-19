"""\nEstratégia v9 CORRIGIDA - Escalação Automática do Cartola FC\n============================================================\nCorreções implementadas:\n1. Usar previsão do modelo (pred) como score - NÃO sobrescrever com score_geral_v9\n2. Filtrar por status: excluir apenas Suspenso (3) e Contundido (5)\n3. Filtro de sequência: excluir apenas quem NUNCA jogou no campeonato\n4. Modo simulação: para histórico, verifica quem realmente jogou\n5. CORREÇÃO DATA LEAKAGE: Em modo_simulacao, calcular média do histórico ao invés de usar media_num\n"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
import os
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
import joblib

# Importar otimizador global
try:
    from otimizador_escalacao import otimizar_escalacao_ilp, otimizar_com_downgrade
    OTIMIZADOR_DISPONIVEL = True
except ImportError:
    OTIMIZADOR_DISPONIVEL = False

# Mapeamento de posições
POSICAO_MAP = {
    1: 'GOL',
    2: 'LAT',
    3: 'ZAG',
    4: 'MEI',
    5: 'ATA',
    6: 'TEC'
}

# Formações disponíveis
FORMACOES = {
    '3-4-3': {1: 1, 2: 0, 3: 3, 4: 4, 5: 3, 6: 1},
    '3-5-2': {1: 1, 2: 0, 3: 3, 4: 5, 5: 2, 6: 1},
    '4-3-3': {1: 1, 2: 2, 3: 2, 4: 3, 5: 3, 6: 1},
    '4-4-2': {1: 1, 2: 2, 3: 2, 4: 4, 5: 2, 6: 1},
    '4-5-1': {1: 1, 2: 2, 3: 2, 4: 5, 5: 1, 6: 1},
    '5-3-2': {1: 1, 2: 2, 3: 3, 4: 3, 5: 2, 6: 1},
    '5-4-1': {1: 1, 2: 2, 3: 3, 4: 4, 5: 1, 6: 1},
}

# Modelos disponíveis:
# - modelo_v9.joblib: Treinado com 2022-2024 (para simulação histórica de 2025)
# - modelo_v9_2026.joblib: Treinado com 2022-2025 (para escalação real de 2026)
MODEL_FILE = 'modelo_v9.joblib'  # Modelo padrão (simulação histórica)
MODEL_FILE_2026 = 'modelo_v9_2026.joblib'  # Modelo para escalação real 2026
STATE_FILE = 'estrategia_v9_state.json'

class EstrategiaV7:
    """Estratégia v9 CORRIGIDA com ML e filtros corretos.
    
    Suporta dois modelos:
    - modo_simulacao=True: Usa modelo_v9.joblib (2022-2024) para simulação histórica
    - modo_simulacao=False: Usa modelo_v9_2026.joblib (2022-2025) para escalação real
    """
    
    def __init__(self, orcamento: float = 100.0, modo_simulacao: bool = False):
        self.orcamento = orcamento
        self.historico = {}
        self.rodada_atual = 1
        self.modelo = None
        self.resultados = []
        self.stats_ano_anterior = {}
        self.modo_simulacao = modo_simulacao
        self.features = [
            'media', 'preco', 'media_ultimas_3', 'media_ultimas_5', 'media_ultimas_10',
            'std_ultimas_5', 'max_ultimas_5', 'pontos_ultima', 'media_historica',
            'sequencia_jogos', 'custo_beneficio', 'tendencia', 'momentum',
            'variacao_acum_3', 'seq_valorizacao', 'padrao_evolucao',
            'distancia_media', 'abaixo_media', 'oportunidade_regressao',
            'score_oportunidade', 'score_recuperacao', 'risco_regressao', 'score_geral_v9'
        ]
        self._carregar_modelo()
        self._carregar_estado()
    
    def _carregar_modelo(self):
        """Carrega o modelo pré-treinado v9.
        
        - modo_simulacao=True: Usa modelo_v9.joblib (2022-2024)
        - modo_simulacao=False: Usa modelo_v9_2026.joblib (2022-2025) se disponível
        """
        # Determinar qual modelo usar
        if self.modo_simulacao:
            # Simulação histórica: usar modelo sem dados do ano simulado
            model_file = MODEL_FILE
        else:
            # Escalação real: usar modelo com todos os dados disponíveis
            model_file = MODEL_FILE_2026 if os.path.exists(MODEL_FILE_2026) else MODEL_FILE
        
        if os.path.exists(model_file):
            try:
                self.modelo = joblib.load(model_file)
                # print(f"[DEBUG] Modelo carregado: {model_file}")
            except:
                self.modelo = None
        else:
            # Fallback para modelo padrão
            if os.path.exists(MODEL_FILE):
                try:
                    self.modelo = joblib.load(MODEL_FILE)
                except:
                    self.modelo = None
    
    def _carregar_estado(self):
        """Carrega estado persistente."""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, 'r') as f:
                    estado = json.load(f)
                    self.historico = estado.get('historico', {})
                    self.rodada_atual = estado.get('rodada_atual', 1)
            except:
                pass

    def carregar_stats_ano_anterior(self, df_rodada: pd.DataFrame):
        """Carrega estatísticas do ano anterior para usar na rodada 1."""
        for _, row in df_rodada.iterrows():
            aid = str(row.get('atleta_id', row.get('atletas.atleta_id', '')))
            if not aid: continue
            
            pontos = float(row.get('pontos_num', row.get('atletas.pontos_num', 0)))
            entrou = int(row.get('entrou_em_campo', row.get('atletas.entrou_em_campo', 1)))
            
            if aid not in self.stats_ano_anterior:
                self.stats_ano_anterior[aid] = {'pts': [], 'entrou': []}
            
            self.stats_ano_anterior[aid]['pts'].append(pontos)
            self.stats_ano_anterior[aid]['entrou'].append(entrou)

    def atualizar_historico(self, df_rodada: pd.DataFrame):
        """Atualiza o histórico com dados da rodada anterior."""
        for _, row in df_rodada.iterrows():
            aid = str(row.get('atleta_id', row.get('atletas.atleta_id', '')))
            if not aid: continue
            
            if aid not in self.historico:
                self.historico[aid] = {'pts': [], 'entrou': [], 'variacao': [], 'total_jogos': 0}
            
            pontos = float(row.get('pontos_num', row.get('atletas.pontos_num', 0)))
            entrou = int(row.get('entrou_em_campo', row.get('atletas.entrou_em_campo', 1)))
            variacao = float(row.get('variacao_num', row.get('atletas.variacao_num', 0)))
            
            self.historico[aid]['pts'].append(pontos)
            self.historico[aid]['entrou'].append(entrou)
            self.historico[aid]['variacao'].append(variacao)
            
            # Contar total de jogos no campeonato
            if entrou:
                self.historico[aid]['total_jogos'] = self.historico[aid].get('total_jogos', 0) + 1
            
            # Limitar histórico
            for k in ['pts', 'entrou', 'variacao']:
                if len(self.historico[aid][k]) > 15:
                    self.historico[aid][k] = self.historico[aid][k][-15:]

    def identificar_armadilhas(self, df: pd.DataFrame) -> set:
        """
        Identifica jogadores 'armadilha' que têm média histórica alta mas não estão pontuando.
        
        Critério: média > 5 E (entrou em campo < 30% OU ratio pts_real/média < 0.2)
        
        Returns:
            Set de atleta_ids que são considerados armadilhas
        """
        armadilhas = set()
        
        for aid, hist in self.historico.items():
            pts_list = hist.get('pts', [])
            entrou_list = hist.get('entrou', [])
            
            # Precisa de mínimo de 5 rodadas de histórico
            if len(pts_list) < 5:
                continue
            
            # Calcular métricas
            total_rodadas = len(entrou_list)
            total_entrou = sum(entrou_list) if entrou_list else 0
            pct_entrou = total_entrou / total_rodadas if total_rodadas > 0 else 1
            
            pts_real_media = sum(pts_list) / len(pts_list) if pts_list else 0
            
            # Buscar média histórica do jogador no DataFrame
            jogador_df = df[df['atleta_id'].astype(str) == str(aid)]
            if len(jogador_df) == 0:
                continue
            
            media_hist = jogador_df['media_num'].iloc[0] if 'media_num' in jogador_df.columns else 0
            
            # Calcular ratio
            ratio = pts_real_media / media_hist if media_hist > 0 else 1
            
            # Critério de armadilha: média > 5 E (entrou < 30% OU ratio < 0.2)
            if media_hist > 5 and (pct_entrou < 0.30 or ratio < 0.2):
                armadilhas.add(aid)
        
        return armadilhas

    def preparar_features_v9(self, df: pd.DataFrame, modo_simulacao: bool = False) -> pd.DataFrame:
        """Prepara as features do modelo v9.\n        \n        Args:\n            df: DataFrame com dados do mercado\n            modo_simulacao: Se True, calcula média do histórico (sem data leakage)\n                           Se False, usa media_num do CSV (para escalação ao vivo)\n        """
        df = df.copy()
        
        # Mapeamento de colunas
        col_map = {
            'atletas.atleta_id': 'atleta_id',
            'atletas.apelido': 'apelido',
            'atletas.pontos_num': 'pontos_num',
            'atletas.preco_num': 'preco_num',
            'atletas.media_num': 'media_num',
            'atletas.variacao_num': 'variacao_num',
            'atletas.clube.id.full.name': 'clube_nome',
            'atletas.clube_id': 'clube_id',
            'atletas.posicao_id': 'posicao_id',
            'atletas.entrou_em_campo': 'entrou_em_campo',
            'atletas.status_id': 'status_id'
        }
        df = df.rename(columns=col_map)
        
        # Garantir colunas necessárias
        if 'preco_num' in df.columns:
            df['preco'] = pd.to_numeric(df['preco_num'], errors='coerce').fillna(5)
        elif 'preco' not in df.columns:
            df['preco'] = 5
            
        # CORREÇÃO DATA LEAKAGE: Em modo_simulacao, não usar media_num (tem leakage)
        # A média será calculada do histórico na função calc_features
        if modo_simulacao:
            # Em simulação, inicializar com 0 - será calculado do histórico
            df['media'] = 0
            df['media_oficial'] = pd.to_numeric(df.get('media_num', 0), errors='coerce').fillna(0)
        else:
            # Em escalação ao vivo, usar media_num (não tem leakage pois rodada não aconteceu)
            if 'media_num' in df.columns:
                df['media'] = pd.to_numeric(df['media_num'], errors='coerce').fillna(0)
            elif 'media' not in df.columns:
                df['media'] = 0
            
        if 'posicao_id' not in df.columns:
            df['posicao_id'] = 0
        df['posicao_id'] = pd.to_numeric(df['posicao_id'], errors='coerce').fillna(0).astype(int)
        
        # Mapear coluna 'id' da API para 'atleta_id'
        if 'atleta_id' not in df.columns:
            if 'id' in df.columns:
                df['atleta_id'] = df['id']
            else:
                df['atleta_id'] = range(len(df))
        
        # Usar coluna 'apelido' da API (nome curto do jogador)
        if 'apelido' not in df.columns:
            if 'apelido_abreviado' in df.columns:
                df['apelido'] = df['apelido_abreviado']
            elif 'nome' in df.columns:
                # Se nome for DataFrame (colunas duplicadas), pegar a primeira
                if isinstance(df['nome'], pd.DataFrame):
                    df['apelido'] = df['nome'].iloc[:, 0]
                else:
                    df['apelido'] = df['nome']
            else:
                df['apelido'] = 'Jogador'
            
        # Status do jogador
        # 7 = Provável, 6 = Nulo, 5 = Contundido, 3 = Suspenso, 2 = Dúvida
        # CORREÇÃO: Filtrar APENAS status 7 (Provável)
        if 'status_id' in df.columns:
            df['status_ok'] = (df['status_id'] == 7).astype(int)
        else:
            df['status_ok'] = 1
        
        # Calcular features baseadas no histórico
        def calc_features(row, usar_historico=modo_simulacao):
            aid = str(row.get('atleta_id', ''))
            hist = self.historico.get(aid, {'pts': [], 'entrou': [], 'variacao': [], 'total_jogos': 0})
            stats_ant = self.stats_ano_anterior.get(aid, {'pts': [], 'entrou': []})
            
            pts = hist.get('pts', []) or stats_ant.get('pts', [])
            entrou = hist.get('entrou', []) or stats_ant.get('entrou', [])
            variacao = hist.get('variacao', [])
            total_jogos = hist.get('total_jogos', 0)
            
            # CORREÇÃO DATA LEAKAGE: Em modo_simulacao, calcular média do histórico
            if usar_historico:
                # Calcular média apenas do histórico (sem a rodada atual)
                media_base = np.mean(pts) if pts else 0
            else:
                # Usar média do CSV (para escalação ao vivo)
                media_base = row['media'] if row['media'] > 0 else (np.mean(pts) if pts else 0)
            
            # Médias móveis - usar media_base como fallback
            media_ultimas_3 = np.mean(pts[-3:]) if len(pts) >= 3 else media_base
            media_ultimas_5 = np.mean(pts[-5:]) if len(pts) >= 5 else media_base
            media_ultimas_10 = np.mean(pts[-10:]) if len(pts) >= 10 else media_base
            std_ultimas_5 = np.std(pts[-5:]) if len(pts) >= 5 else 5
            max_ultimas_5 = max(pts[-5:]) if len(pts) >= 5 else media_base
            pontos_ultima = pts[-1] if pts else 0
            media_historica = np.mean(pts) if pts else media_base
            
            # CORREÇÃO: sequencia_jogos = total de jogos no campeonato (não últimas 5)
            # Isso permite filtrar apenas quem NUNCA jogou
            sequencia_jogos = total_jogos if total_jogos > 0 else sum(entrou) if entrou else 0
            
            # Tendência e momentum
            if len(pts) >= 3:
                tendencia = 1 if pts[-1] > pts[-3] else (-1 if pts[-1] < pts[-3] else 0)
                momentum = pts[-1] - np.mean(pts[-3:])
            else:
                tendencia = 0
                momentum = 0
            
            # Variação acumulada
            variacao_acum_3 = sum(variacao[-3:]) if len(variacao) >= 3 else 0
            
            # Sequência de valorização
            seq_val = 0
            for v in reversed(variacao[-5:] if variacao else []):
                if v > 0: seq_val += 1
                else: break
            seq_valorizacao = seq_val
            
            # Padrão de evolução
            if len(pts) >= 5:
                primeira_metade = np.mean(pts[:len(pts)//2])
                segunda_metade = np.mean(pts[len(pts)//2:])
                if segunda_metade > primeira_metade * 1.1:
                    padrao_evolucao = 1  # Crescente
                elif segunda_metade < primeira_metade * 0.9:
                    padrao_evolucao = -1  # Decrescente
                else:
                    padrao_evolucao = 0  # Estável
            else:
                padrao_evolucao = 0
            
            # Distância da média (regressão à média)
            # CORREÇÃO DATA LEAKAGE: usar media_base ao invés de row['media']
            media_ref = media_base if media_base > 0 else 1
            distancia_media = (media_ultimas_3 - media_ref) / media_ref
            abaixo_media = 1 if distancia_media < -0.1 else 0
            
            # Oportunidade de regressão
            oportunidade_regressao = 1 if (abaixo_media == 1 and padrao_evolucao >= 0) else 0
            
            # Scores - CORREÇÃO DATA LEAKAGE: usar media_base
            score_oportunidade = media_base * (1 + abs(distancia_media)) if abaixo_media else 0
            score_recuperacao = media_base * 1.2 if (padrao_evolucao == 0 and abaixo_media == 1) else 0
            risco_regressao = 1 if (distancia_media > 0.2 and padrao_evolucao == 1) else 0
            
            # Custo benefício - CORREÇÃO DATA LEAKAGE: usar media_base
            custo_beneficio = media_base / row['preco'] if row['preco'] > 0 else 0
            
            return pd.Series({
                'media_base': media_base,  # CORREÇÃO DATA LEAKAGE: média calculada do histórico
                'media_ultimas_3': media_ultimas_3,
                'media_ultimas_5': media_ultimas_5,
                'media_ultimas_10': media_ultimas_10,
                'std_ultimas_5': std_ultimas_5,
                'max_ultimas_5': max_ultimas_5,
                'pontos_ultima': pontos_ultima,
                'media_historica': media_historica,
                'sequencia_jogos': sequencia_jogos,
                'tendencia': tendencia,
                'momentum': momentum,
                'variacao_acum_3': variacao_acum_3,
                'seq_valorizacao': seq_valorizacao,
                'padrao_evolucao': padrao_evolucao,
                'distancia_media': distancia_media,
                'abaixo_media': abaixo_media,
                'oportunidade_regressao': oportunidade_regressao,
                'score_oportunidade': score_oportunidade,
                'score_recuperacao': score_recuperacao,
                'risco_regressao': risco_regressao,
                'custo_beneficio': custo_beneficio
            })
        
        # Aplicar cálculo de features
        features_calc = df.apply(calc_features, axis=1)
        for col in features_calc.columns:
            df[col] = features_calc[col]
        
        # CORREÇÃO DATA LEAKAGE: Em modo_simulacao, atualizar 'media' com media_base
        # CORREÇÃO RODADA 1: Se média = 0 para todos, usar media_base do histórico
        if modo_simulacao:
            df['media'] = df['media_base']
        elif (df['media'] == 0).all():
            # Primeira rodada: usar média do histórico do ano anterior
            df['media'] = df['media_base']
        
        # Score geral v9
        df['score_geral_v9'] = (
            df['score_oportunidade'] * 0.3 +
            df['score_recuperacao'] * 0.2 +
            df['media'] * 0.2 +
            df['seq_valorizacao'] * 0.1 +
            df['sequencia_jogos'].clip(0, 5) * 0.1 +  # Limitar a 5 para não distorcer
            df['custo_beneficio'] * 0.1
        )
        
        # Bônus para oportunidade de regressão
        df['score_geral_v9'] = np.where(
            df['oportunidade_regressao'] == 1,
            df['score_geral_v9'] * 1.2,
            df['score_geral_v9']
        )
        
        # Criar colunas de prioridade para desempate determinístico
        # Prioridade de padrão: CRESCENTE (1) > ESTÁVEL (0) > DECRESCENTE (-1)
        df['prioridade_padrao'] = df['padrao_evolucao']
        
        # Prioridade de tendência: SUBINDO (1) > ESTÁVEL (0) > CAINDO (-1)
        # Calcular tendência baseada em momentum
        df['prioridade_tendencia'] = np.where(
            df['momentum'] > 0.1, 1,  # SUBINDO
            np.where(df['momentum'] < -0.1, -1, 0)  # CAINDO ou ESTÁVEL
        )
        
        # Prioridade de regressão: PROVÁVEL RECUPERAÇÃO (1) > NORMAL (0) > PROVÁVEL QUEDA (-1)
        df['prioridade_regressao'] = np.where(
            df['oportunidade_regressao'] == 1, 1,
            np.where(df['risco_regressao'] == 1, -1, 0)
        )
        
        return df.fillna(0)

    def escalar_time(self, df_mercado: pd.DataFrame, formacao: str = '4-3-3', 
                     orcamento: float = 100.0, incluir_explicacao: bool = True,
                     modo_simulacao: bool = False) -> Dict:
        """
        Escala o time usando o modelo v9 com otimização de orçamento.
        
        CORREÇÕES:
        1. Usar pred (previsão do modelo) como score - NÃO sobrescrever
        2. Filtrar por status: excluir apenas Suspenso (3) e Contundido (5)
        3. Filtro de sequência: excluir apenas quem NUNCA jogou no campeonato
        4. modo_simulacao: se True, filtra apenas quem realmente jogou (para validação histórica)
        """
        df = self.preparar_features_v9(df_mercado, modo_simulacao=modo_simulacao)
        
        # CORREÇÃO 1: Usar previsão do modelo como score
        if self.modelo:
            try:
                df['pred'] = self.modelo.predict(df[self.features])
            except Exception as e:
                df['pred'] = df['score_geral_v9']
        else:
            df['pred'] = df['score_geral_v9']
        
        # CORREÇÃO: Usar pred como score (NÃO sobrescrever com score_geral_v9)
        df['score'] = df['pred']
        
        # APLICAR PESOS POR POSIÇÃO (aprendidos automaticamente)
        # Carrega parâmetros do arquivo de aprendizado
        try:
            import json
            params_file = os.path.join(os.path.dirname(__file__), 'parametros_aprendidos.json')
            if os.path.exists(params_file):
                with open(params_file, 'r') as f:
                    params_aprendidos = json.load(f)
                    pesos_posicao = params_aprendidos.get('peso_por_posicao', {})
                    bonus_premium = params_aprendidos.get('bonus_premium', 0.5)
            else:
                pesos_posicao = {}
                bonus_premium = 0.5
        except:
            pesos_posicao = {}
            bonus_premium = 0.5
        
        # Aplicar pesos por posição ao score
        for pos_id, pos_sigla in POSICAO_MAP.items():
            peso = pesos_posicao.get(pos_sigla, 1.0)
            mask_pos = df['posicao_id'] == pos_id
            df.loc[mask_pos, 'score'] = df.loc[mask_pos, 'score'] * peso
        
        # BONUS PREMIUM: Adicionar bonus no score de MEI e ATA premium
        # Premium = preço >= 12 E média >= 6
        # Isso prioriza jogadores de maior qualidade que pontuam mais
        mask_premium = (df['preco'] >= 12) & (df['media'] >= 6)
        mask_mei_ata = df['posicao_id'].isin([4, 5])  # MEI=4, ATA=5
        df.loc[mask_premium & mask_mei_ata, 'score'] = df.loc[mask_premium & mask_mei_ata, 'score'] + bonus_premium
        
        # CORREÇÃO 2: Filtros de disponibilidade
        tem_medias = (df['media'] > 0).any()  # Verificar se há jogadores com média > 0
        
        if modo_simulacao:
            # Simulação histórica: filtrar apenas quem realmente jogou
            # (para validar o modelo com dados reais)
            df_filtrado = df[
                (df['media'] > 0) &
                (df.get('entrou_em_campo', pd.Series([True]*len(df))).fillna(True).astype(bool))
            ].copy()
        else:
            # Escalação real: filtrar por status e histórico
            # CORREÇÃO: Na primeira rodada (média = 0 para todos), usar histórico do ano anterior
            # O filtro de média > 0 só se aplica se houver jogadores com média > 0
            if tem_medias:
                # Rodada normal: filtrar por média, status e histórico
                df_filtrado = df[
                    (df['media'] > 0) &
                    (df['status_ok'] == 1) &
                    (df['sequencia_jogos'] >= 1)
                ].copy()
            else:
                # Primeira rodada: usar apenas status e histórico do ano anterior
                # sequencia_jogos vem do histórico (stats_ano_anterior)
                df_filtrado = df[
                    (df['status_ok'] == 1) &
                    (df['sequencia_jogos'] >= 1)  # Jogou no ano anterior
                ].copy()
        
        # Se não tiver jogadores suficientes, relaxar filtro
        if len(df_filtrado) < 50:
            if tem_medias:
                df_filtrado = df[df['media'] > 0].copy()
            else:
                # Primeira rodada: usar todos com status ok
                df_filtrado = df[df['status_ok'] == 1].copy()
        
        # FILTRO DE ARMADILHAS: Excluir jogadores com média alta mas que não pontuam
        # Critério: média > 5 E (entrou < 30% OU ratio pts/média < 0.2)
        armadilhas = self.identificar_armadilhas(df)
        if armadilhas:
            df_filtrado = df_filtrado[~df_filtrado['atleta_id'].astype(str).isin(armadilhas)].copy()
        
        if formacao not in FORMACOES:
            formacao = '4-3-3'
        
        config_formacao = FORMACOES[formacao]
        
        # ========== OTIMIZAÇÃO GLOBAL (ILP) ==========
        # Usar Programação Linear Inteira para encontrar a combinação ótima
        # que maximiza a pontuação prevista dentro do orçamento
        
        if OTIMIZADOR_DISPONIVEL:
            try:
                # Tentar otimização global com ILP
                ids_otimizados = otimizar_escalacao_ilp(
                    df_filtrado,
                    config_formacao,
                    orcamento,
                    top_n_por_posicao=20
                )
                
                if len(ids_otimizados) == sum(config_formacao.values()):
                    # Sucesso! Usar solução otimizada
                    titulares = []
                    custo_total = 0
                    ids_usados = set()
                    
                    for atleta_id in ids_otimizados:
                        row = df_filtrado[df_filtrado['atleta_id'] == atleta_id].iloc[0]
                        titular_data = self._formatar_jogador(row, incluir_explicacao)
                        titulares.append(titular_data)
                        custo_total += row['preco']
                        ids_usados.add(str(atleta_id))
                    
                    # Pular para a seção de reservas (já temos os titulares)
                    # Ordenar por posição para exibição
                    titulares = sorted(titulares, key=lambda x: [1, 3, 2, 4, 5, 6].index(x['pos_id']) if x['pos_id'] in [1, 3, 2, 4, 5, 6] else 99)
                    
                    # Ir direto para reservas
                    return self._finalizar_escalacao(
                        titulares, custo_total, ids_usados, df, df_filtrado,
                        orcamento, formacao, config_formacao, incluir_explicacao
                    )
            except Exception as e:
                # Fallback para algoritmo greedy
                pass
        
        # ========== LÓGICA GREEDY (FALLBACK) ==========
        titulares = []
        custo_total = 0
        ids_usados = set()
        
        # Ordem de posições para seleção
        ordem_posicoes = [1, 3, 2, 4, 5, 6]  # GOL, ZAG, LAT, MEI, ATA, TEC
        
        for pos_id in ordem_posicoes:
            qtd = config_formacao.get(pos_id, 0)
            if qtd == 0:
                continue
            
            # Todos os candidatos da posição, ordenados por score (pred)
            pos_df = df_filtrado[df_filtrado['posicao_id'] == pos_id].sort_values(
                by=['score', 'prioridade_padrao', 'prioridade_tendencia', 'prioridade_regressao', 'custo_beneficio', 'atleta_id'],
                ascending=[False, False, False, False, False, True]
            )
            
            # Se não tiver jogadores suficientes filtrados, usar todos
            if len(pos_df) < qtd:
                pos_df = df[df['posicao_id'] == pos_id].sort_values(
                    by=['score', 'prioridade_padrao', 'prioridade_tendencia', 'prioridade_regressao', 'custo_beneficio', 'atleta_id'],
                    ascending=[False, False, False, False, False, True]
                )
            
            selected = 0
            for _, row in pos_df.iterrows():
                if selected >= qtd:
                    break
                
                aid = str(row['atleta_id'])
                if aid in ids_usados:
                    continue
                
                # Verificar se cabe no orçamento
                # Calcular custo mínimo REAL para os jogadores restantes
                custo_minimo_restante = 0
                for p in ordem_posicoes:
                    if p == pos_id:
                        qtd_restante = qtd - selected - 1
                    elif ordem_posicoes.index(p) > ordem_posicoes.index(pos_id):
                        qtd_restante = config_formacao.get(p, 0)
                    else:
                        qtd_restante = 0
                    
                    if qtd_restante > 0:
                        # Pegar os jogadores mais baratos disponíveis da posição
                        pos_disponiveis = df_filtrado[
                            (df_filtrado['posicao_id'] == p) & 
                            (~df_filtrado['atleta_id'].astype(str).isin(ids_usados | {aid}))
                        ].nsmallest(qtd_restante, 'preco')
                        custo_minimo_restante += pos_disponiveis['preco'].sum()
                
                orcamento_restante = orcamento - custo_total - row['preco']
                
                # Verificar se cabe no orçamento considerando custo mínimo real
                if orcamento_restante >= custo_minimo_restante:
                    titular_data = self._formatar_jogador(row, incluir_explicacao)
                    titulares.append(titular_data)
                    custo_total += row['preco']
                    ids_usados.add(aid)
                    selected += 1
        
        # ========== GARANTIR 12 JOGADORES ==========
        total_esperado = sum(config_formacao.values())
        
        if len(titulares) < total_esperado:
            for pos_id in ordem_posicoes:
                qtd = config_formacao.get(pos_id, 0)
                atual = len([t for t in titulares if t['pos_id'] == pos_id])
                
                while atual < qtd:
                    disponiveis = df[
                        (df['posicao_id'] == pos_id) & 
                        (~df['atleta_id'].astype(str).isin(ids_usados))
                    ].sort_values(
                        by=['score', 'prioridade_padrao', 'prioridade_tendencia', 'prioridade_regressao', 'custo_beneficio', 'atleta_id'],
                        ascending=[False, False, False, False, False, True]
                    )
                    
                    if len(disponiveis) == 0:
                        break
                    
                    encontrou = False
                    for _, row in disponiveis.iterrows():
                        if custo_total + row['preco'] <= orcamento:
                            novo_titular = self._formatar_jogador(row, incluir_explicacao)
                            titulares.append(novo_titular)
                            custo_total += row['preco']
                            ids_usados.add(str(row['atleta_id']))
                            atual += 1
                            encontrou = True
                            break
                    
                    if not encontrou:
                        # Tentar encontrar o jogador mais barato que caiba no orçamento
                        disponiveis_baratos = disponiveis[disponiveis['preco'] <= (orcamento - custo_total)]
                        if len(disponiveis_baratos) > 0:
                            row = disponiveis_baratos.nsmallest(1, 'preco').iloc[0]
                            novo_titular = self._formatar_jogador(row, incluir_explicacao)
                            titulares.append(novo_titular)
                            custo_total += row['preco']
                            ids_usados.add(str(row['atleta_id']))
                            atual += 1
                        else:
                            # Não há jogadores que caibam no orçamento - parar
                            break
        
        # ========== OTIMIZAÇÃO: Usar orçamento restante ==========
        orcamento_restante = orcamento - custo_total
        
        if orcamento_restante > 1:
            max_iteracoes = 100
            for _ in range(max_iteracoes):
                melhor_upgrade = None
                melhor_ganho = 0
                
                for i, jogador_atual in enumerate(titulares):
                    pos_id = jogador_atual['pos_id']
                    
                    upgrades = df_filtrado[
                        (df_filtrado['posicao_id'] == pos_id) & 
                        (~df_filtrado['atleta_id'].astype(str).isin(ids_usados)) &
                        (df_filtrado['score'] > jogador_atual['score']) &
                        (df_filtrado['preco'] <= jogador_atual['preco'] + orcamento_restante)
                    ].sort_values(
                        by=['score', 'prioridade_padrao', 'prioridade_tendencia', 'prioridade_regressao', 'custo_beneficio', 'atleta_id'],
                        ascending=[False, False, False, False, False, True]
                    )
                    
                    if len(upgrades) > 0:
                        upgrade = upgrades.iloc[0]
                        ganho_score = upgrade['score'] - jogador_atual['score']
                        
                        if ganho_score > melhor_ganho:
                            melhor_ganho = ganho_score
                            melhor_upgrade = (i, jogador_atual, upgrade)
                
                if melhor_upgrade:
                    i, jogador_atual, upgrade = melhor_upgrade
                    
                    ids_usados.discard(str(jogador_atual['atleta_id']))
                    custo_total -= jogador_atual['preco']
                    
                    novo_titular = self._formatar_jogador(upgrade, incluir_explicacao)
                    titulares[i] = novo_titular
                    custo_total += upgrade['preco']
                    ids_usados.add(str(upgrade['atleta_id']))
                    orcamento_restante = orcamento - custo_total
                else:
                    break
        
        # ========== CAPITÃO: jogador com maior score_capitao ==========
        # Nova lógica: prioriza atacantes e meias que têm maior potencial de "explosão"
        # Baseado em análise histórica: 63% dos capitães ideais são atacantes, 18% meias
        # Pesos otimizados: ATA=1.7, MEI=1.45, LAT=1.1, outros=1.0
        BONUS_CAPITAO = {
            5: 1.7,   # Atacante - maior potencial de explosão
            4: 1.45,  # Meia - segundo maior potencial
            2: 1.1,   # Lateral - ocasionalmente explode
            1: 1.0,   # Goleiro
            3: 1.0,   # Zagueiro
            6: 0.8    # Técnico - raramente é o melhor
        }
        
        def calcular_score_capitao(jogador):
            """Calcula score para escolha do capitão com bonus por posição."""
            score_base = jogador.get('score', 0)
            pos_id = jogador.get('pos_id', 0)
            bonus = BONUS_CAPITAO.get(pos_id, 1.0)
            return score_base * bonus
        
        capitao = max(titulares, key=calcular_score_capitao) if titulares else None
        
        # ========== RESERVA DE LUXO: preço <= mais barato escalado na posição do capitão ==========
        # O reserva de luxo é selecionado PRIMEIRO, pois ele substitui o reserva normal da posição do capitão
        reserva_luxo = None
        pos_capitao = None
        if capitao:
            pos_capitao = capitao['pos_id']
            jogadores_posicao_capitao = [t for t in titulares if t['pos_id'] == pos_capitao]
            # Reserva de luxo deve ter preço <= mais barato escalado na posição
            preco_max_luxo = min(j['preco'] for j in jogadores_posicao_capitao) if jogadores_posicao_capitao else 0
            
            luxo_df = df_filtrado[
                (df_filtrado['posicao_id'] == pos_capitao) &
                (~df_filtrado['atleta_id'].astype(str).isin(ids_usados)) &
                (df_filtrado['preco'] <= preco_max_luxo)
            ].sort_values(
                by=['score', 'prioridade_padrao', 'prioridade_tendencia', 'prioridade_regressao', 'custo_beneficio', 'atleta_id'],
                ascending=[False, False, False, False, False, True]
            )
            
            if luxo_df.empty:
                luxo_df = df[
                    (df['posicao_id'] == pos_capitao) &
                    (~df['atleta_id'].astype(str).isin(ids_usados)) &
                    (df['preco'] <= preco_max_luxo)
                ].sort_values(
                by=['score', 'prioridade_padrao', 'prioridade_tendencia', 'prioridade_regressao', 'custo_beneficio', 'atleta_id'],
                ascending=[False, False, False, False, False, True]
            )
            
            if not luxo_df.empty:
                reserva_luxo = self._formatar_jogador(luxo_df.iloc[0], incluir_explicacao)
        
        # ========== RESERVAS: apenas para posições que existem na formação ==========
        # O reserva de luxo substitui o reserva normal da posição do capitão
        reservas = {}
        for pos_id in [1, 2, 3, 4, 5]:
            # Só criar reserva se a posição existe na formação
            if config_formacao.get(pos_id, 0) == 0:
                continue  # Pula posições que não existem na formação
            
            # Se esta é a posição do capitão, o reserva de luxo é o reserva
            if pos_id == pos_capitao and reserva_luxo:
                reservas[pos_id] = reserva_luxo
                reservas[pos_id]['is_reserva_luxo'] = True
                continue
            
            # Encontrar o preço do jogador mais barato escalado nesta posição
            titulares_posicao = [t for t in titulares if t['pos_id'] == pos_id]
            if titulares_posicao:
                preco_min_titular = min(t['preco'] for t in titulares_posicao)
            else:
                preco_min_titular = float('inf')  # Se não há titular, qualquer preço serve
            
            # IDs já usados incluindo reserva de luxo
            ids_usados_reservas = list(ids_usados)
            if reserva_luxo:
                ids_usados_reservas.append(str(reserva_luxo['atleta_id']))
            
            # Reserva deve ter preço MENOR que o mais barato escalado
            res_df = df_filtrado[
                (df_filtrado['posicao_id'] == pos_id) & 
                (~df_filtrado['atleta_id'].astype(str).isin(ids_usados_reservas)) &
                (df_filtrado['preco'] < preco_min_titular)
            ]
            if res_df.empty:
                res_df = df[
                    (df['posicao_id'] == pos_id) & 
                    (~df['atleta_id'].astype(str).isin(ids_usados_reservas)) &
                    (df['preco'] < preco_min_titular)
                ]
            if not res_df.empty:
                reservas[pos_id] = self._formatar_jogador(res_df.nsmallest(1, 'preco').iloc[0], incluir_explicacao)
        
        # ========== PONTUAÇÃO ESPERADA ==========
        pontuacao_esperada = sum(t['score'] for t in titulares)
        if capitao:
            pontuacao_esperada += capitao['score'] * 0.5
        
        # ========== VALORIZAÇÃO TOTAL ESPERADA ==========
        valorizacao_total = sum(t.get('valorizacao_prevista', 0) for t in titulares)
        
        return {
            'titulares': titulares,
            'reservas': reservas,
            'reserva_luxo': reserva_luxo,
            'capitao': capitao,
            'custo_total': custo_total,
            'orcamento_restante': orcamento - custo_total,
            'pontuacao_esperada': pontuacao_esperada,
            'valorizacao_total': round(valorizacao_total, 2),
            'formacao': formacao,
            'df_ranqueado': df  # DataFrame com todos os jogadores e scores calculados
        }

    def _formatar_jogador(self, j, incluir_explicacao):
        """Formata os dados do jogador para retorno."""
        if isinstance(j, pd.Series):
            j = j.to_dict()
        
        # Calcular previsão de valorização baseada no score esperado
        # Fórmula aproximada: (pontos_esperados - média) / 10
        score = float(j.get('score', j.get('pred', j.get('score_geral_v9', 0))))
        media = float(j.get('media', 0))
        
        # Usar o score como proxy para pontos esperados
        # Ajustar para escala mais realista (score já considera média)
        if score > 0:
            valorizacao_prevista = (score - media * 0.3) / 8  # Ajuste para escala realista
        else:
            valorizacao_prevista = -0.3  # Valor padrão negativo se não tiver score
        
        res = {
            'atleta_id': str(j.get('atleta_id', '')),
            'apelido': j.get('apelido', 'N/A'),
            'pos_id': int(j.get('posicao_id', 0)),
            'posicao': POSICAO_MAP.get(int(j.get('posicao_id', 0)), ''),
            'preco': float(j.get('preco', 0)),
            'media': media,
            'score': score,
            'clube': j.get('clube_nome', j.get('clube', '')),
            'valorizacao_prevista': round(valorizacao_prevista, 2)
        }
        
        if incluir_explicacao:
            padrao = j.get('padrao_evolucao', 0)
            oportunidade = j.get('oportunidade_regressao', 0)
            distancia = j.get('distancia_media', 0)
            media = j.get('media', 0)
            preco = j.get('preco', 0)
            custo_beneficio = media / preco if preco > 0 else 0
            
            fatores = []
            fatores.append(f"📊 Score: {res['score']:.2f}")
            fatores.append(f"📈 Tendência: {'Crescente' if padrao > 0 else 'Decrescente' if padrao < 0 else 'Estável'}")
            
            if oportunidade == 1:
                fatores.append("🎯 Oportunidade de Regressão: SIM")
            
            if distancia < -0.1:
                fatores.append(f"📉 Abaixo da média ({distancia*100:.0f}%)")
            elif distancia > 0.1:
                fatores.append(f"📈 Acima da média (+{distancia*100:.0f}%)")
            
            # Determinar justificativa, significado e motivo
            if oportunidade == 1:
                resumo = "🔄 Jogador em recuperação - oportunidade de regressão à média"
                significado = "O jogador teve pontuações ruins recentemente, mas seu histórico geral é muito bom."
                motivo = "O sistema identifica uma 'regressão à média'. Acredita que a má fase é temporária e que ele tem grandes chances de voltar a pontuar bem. Geralmente o preço está baixo, tornando-o uma aposta de alto potencial."
            elif padrao > 0.5:
                resumo = "📈 Boa fase - consistência"
                significado = "O jogador vem de uma sequência de boas pontuações nas últimas rodadas."
                motivo = "É uma escolha segura e confiável, com alta probabilidade de manter o bom desempenho."
            elif padrao < -0.3:
                resumo = "📉 Jogador em queda - atenção"
                significado = "Alerta! As últimas pontuações do jogador estão abaixo de sua média histórica."
                motivo = "Mesmo em má fase, a pontuação prevista para esta rodada específica ainda é alta. O sistema considera que ele pode se recuperar, ou ele é uma opção necessária para o time caber no orçamento. É uma aposta de risco calculado."
            elif media >= 6:
                resumo = "⭐ Jogador premium - alta média"
                significado = "É um dos melhores jogadores do campeonato, com média de pontuação elevada."
                motivo = "Jogadores premium são escolhas naturais quando o orçamento permite. Eles têm histórico comprovado de boas pontuações."
            elif custo_beneficio >= 0.5:
                resumo = "💰 Custo-benefício - bom preço"
                significado = "O jogador tem uma boa relação entre pontuação esperada e preço."
                motivo = "Quando o orçamento é limitado, o sistema prioriza jogadores que entregam boas pontuações por um preço acessível."
            elif res['score'] > media * 1.2:
                resumo = "🎲 Aposta da rodada - alto potencial"
                significado = "O jogador não é uma escolha óbvia, mas o modelo identificou uma oportunidade específica."
                motivo = "O cérebro digital identificou variáveis que indicam um potencial diferenciado para esta rodada."
            else:
                resumo = "✅ Jogador consistente"
                significado = "O jogador mantém um desempenho estável ao longo das rodadas."
                motivo = "Consistência é valorizada pelo sistema, pois reduz o risco de pontuações muito baixas."
            
            res['explicacao'] = {
                'fatores': fatores,
                'resumo': resumo,
                'significado': significado,
                'motivo': motivo
            }
        
        return res

    def _finalizar_escalacao(self, titulares, custo_total, ids_usados, df, df_filtrado,
                              orcamento, formacao, config_formacao, incluir_explicacao):
        """
        Finaliza a escalação: seleciona capitão, reservas e monta o retorno.
        Usada após a otimização ILP encontrar os titulares.
        """
        # ========== CAPITÃO: jogador com maior score_capitao ==========
        BONUS_CAPITAO = {
            5: 1.7,   # Atacante
            4: 1.45,  # Meia
            2: 1.1,   # Lateral
            1: 1.0,   # Goleiro
            3: 1.0,   # Zagueiro
            6: 0.8    # Técnico
        }
        
        def calcular_score_capitao(jogador):
            score_base = jogador.get('score', 0)
            pos_id = jogador.get('pos_id', 0)
            bonus = BONUS_CAPITAO.get(pos_id, 1.0)
            return score_base * bonus
        
        capitao = max(titulares, key=calcular_score_capitao) if titulares else None
        
        # ========== RESERVA DE LUXO ==========
        reserva_luxo = None
        pos_capitao = None
        if capitao:
            pos_capitao = capitao['pos_id']
            jogadores_posicao_capitao = [t for t in titulares if t['pos_id'] == pos_capitao]
            preco_max_luxo = min(j['preco'] for j in jogadores_posicao_capitao) if jogadores_posicao_capitao else 0
            
            luxo_df = df_filtrado[
                (df_filtrado['posicao_id'] == pos_capitao) &
                (~df_filtrado['atleta_id'].astype(str).isin(ids_usados)) &
                (df_filtrado['preco'] <= preco_max_luxo)
            ].sort_values(by=['score'], ascending=False)
            
            if luxo_df.empty:
                luxo_df = df[
                    (df['posicao_id'] == pos_capitao) &
                    (~df['atleta_id'].astype(str).isin(ids_usados)) &
                    (df['preco'] <= preco_max_luxo)
                ].sort_values(by=['score'], ascending=False)
            
            if not luxo_df.empty:
                reserva_luxo = self._formatar_jogador(luxo_df.iloc[0], incluir_explicacao)
        
        # ========== RESERVAS ==========
        reservas = {}
        for pos_id in [1, 2, 3, 4, 5]:
            if config_formacao.get(pos_id, 0) == 0:
                continue
            
            if pos_id == pos_capitao and reserva_luxo:
                reservas[pos_id] = reserva_luxo
                reservas[pos_id]['is_reserva_luxo'] = True
                continue
            
            titulares_posicao = [t for t in titulares if t['pos_id'] == pos_id]
            if titulares_posicao:
                preco_min_titular = min(t['preco'] for t in titulares_posicao)
            else:
                preco_min_titular = float('inf')
            
            ids_usados_reservas = list(ids_usados)
            if reserva_luxo:
                ids_usados_reservas.append(str(reserva_luxo['atleta_id']))
            
            res_df = df_filtrado[
                (df_filtrado['posicao_id'] == pos_id) & 
                (~df_filtrado['atleta_id'].astype(str).isin(ids_usados_reservas)) &
                (df_filtrado['preco'] < preco_min_titular)
            ]
            if res_df.empty:
                res_df = df[
                    (df['posicao_id'] == pos_id) & 
                    (~df['atleta_id'].astype(str).isin(ids_usados_reservas)) &
                    (df['preco'] < preco_min_titular)
                ]
            if not res_df.empty:
                reservas[pos_id] = self._formatar_jogador(res_df.nsmallest(1, 'preco').iloc[0], incluir_explicacao)
        
        # ========== PONTUAÇÃO ESPERADA ==========
        pontuacao_esperada = sum(t['score'] for t in titulares)
        if capitao:
            pontuacao_esperada += capitao['score'] * 0.5
        
        # ========== VALORIZAÇÃO TOTAL ==========
        valorizacao_total = sum(t.get('valorizacao_prevista', 0) for t in titulares)
        
        return {
            'titulares': titulares,
            'reservas': reservas,
            'reserva_luxo': reserva_luxo,
            'capitao': capitao,
            'custo_total': custo_total,
            'orcamento_restante': orcamento - custo_total,
            'pontuacao_esperada': pontuacao_esperada,
            'valorizacao_total': round(valorizacao_total, 2),
            'formacao': formacao,
            'df_ranqueado': df
        }

    def analisar_todas_formacoes(self, df_mercado: pd.DataFrame, orcamento: float = 100.0,
                                  modo_simulacao: bool = False) -> List[Dict]:
        """Analisa todas as formações e retorna ordenadas por pontuação esperada."""
        resultados = []
        
        for formacao in FORMACOES.keys():
            try:
                escalacao = self.escalar_time(df_mercado, formacao=formacao, 
                                              orcamento=orcamento, modo_simulacao=modo_simulacao)
                if escalacao and len(escalacao.get('titulares', [])) == 12:
                    resultados.append(escalacao)
            except Exception as e:
                continue
        
        resultados.sort(key=lambda x: x.get('pontuacao_esperada', 0), reverse=True)
        
        return resultados

    # ========== ESTRATÉGIAS ESPECIAIS PARA RODADAS 1 E 2 ==========
    
    def _carregar_estado_especial(self) -> Dict:
        """Carrega estado das estratégias especiais."""
        state_file = Path(os.path.dirname(__file__)) / "estrategia_especial_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'ultimo_retreinamento': None,
            'ano_retreinamento': None,
            'dados_rodada_1': {},
            'historico_valorizacao': {}
        }
    
    def _salvar_estado_especial(self, estado: Dict):
        """Salva estado das estratégias especiais."""
        state_file = Path(os.path.dirname(__file__)) / "estrategia_especial_state.json"
        with open(state_file, 'w') as f:
            json.dump(estado, f, indent=2)
    
    def verificar_necessidade_retreinamento(self, ano_atual: int, rodada_atual: int) -> bool:
        """
        Verifica se é necessário retreinar o modelo.
        Regra: Retreinar antes da rodada 1 de cada ano.
        """
        if rodada_atual != 1:
            return False
        
        estado = self._carregar_estado_especial()
        ano_retreinamento = estado.get('ano_retreinamento')
        
        if ano_retreinamento == ano_atual:
            return False
        
        return True
    
    def retreinar_modelo_para_nova_temporada(self, ano_atual: int) -> Dict:
        """
        Retreina o modelo com todos os dados históricos até o ano anterior.
        Deve ser chamado antes da rodada 1 de cada temporada.
        
        Args:
            ano_atual: Ano da temporada atual (ex: 2026)
            
        Returns:
            Dicionário com resultado do retreinamento
        """
        print(f"[RETREINAMENTO] Iniciando para temporada {ano_atual}")
        
        data_dir = Path(os.path.dirname(__file__)) / "data"
        
        # Identificar anos disponíveis (até ano_atual - 1)
        anos_disponiveis = []
        for item in data_dir.iterdir():
            if item.is_dir() and item.name.isdigit():
                ano = int(item.name)
                if ano < ano_atual:
                    rodadas = list(item.glob("rodada-*.csv"))
                    if rodadas:
                        anos_disponiveis.append(ano)
        
        anos_disponiveis = sorted(anos_disponiveis)
        
        if not anos_disponiveis:
            return {'sucesso': False, 'erro': 'Nenhum dado histórico disponível'}
        
        print(f"[RETREINAMENTO] Anos disponíveis: {anos_disponiveis}")
        
        # Carregar todos os dados
        todos_dados = []
        for ano in anos_disponiveis:
            ano_dir = data_dir / str(ano)
            for arquivo in sorted(ano_dir.glob("rodada-*.csv")):
                try:
                    df = pd.read_csv(arquivo)
                    rodada = int(arquivo.stem.split('-')[1])
                    df['ano'] = ano
                    df['rodada'] = rodada
                    todos_dados.append(df)
                except Exception as e:
                    continue
        
        if not todos_dados:
            return {'sucesso': False, 'erro': 'Não foi possível carregar dados'}
        
        df = pd.concat(todos_dados, ignore_index=True)
        print(f"[RETREINAMENTO] Total de registros: {len(df)}")
        
        # Preparar features
        df = self._preparar_features_treino(df)
        
        features_existentes = [f for f in self.features if f in df.columns]
        
        if len(features_existentes) < 10:
            return {'sucesso': False, 'erro': f'Features insuficientes: {len(features_existentes)}'}
        
        # Filtrar dados válidos
        df_treino = df[df['pontos'].notna() & (df['pontos'] != 0)].copy()
        
        if len(df_treino) < 1000:
            return {'sucesso': False, 'erro': f'Dados insuficientes: {len(df_treino)}'}
        
        # Treinar modelo
        modelo = RandomForestRegressor(
            n_estimators=100, max_depth=20, min_samples_leaf=5,
            n_jobs=-1, random_state=42
        )
        
        X = df_treino[features_existentes].fillna(0)
        y = df_treino['pontos']
        modelo.fit(X, y)
        
        # Salvar modelo
        model_path = Path(os.path.dirname(__file__)) / MODEL_FILE
        joblib.dump(modelo, model_path)
        self.modelo = modelo
        
        # Atualizar estado
        estado = self._carregar_estado_especial()
        estado['ultimo_retreinamento'] = datetime.now().isoformat()
        estado['ano_retreinamento'] = ano_atual
        self._salvar_estado_especial(estado)
        
        print(f"[RETREINAMENTO] Modelo salvo com {len(df_treino)} registros")
        
        return {
            'sucesso': True,
            'anos_usados': anos_disponiveis,
            'total_registros': len(df_treino),
            'features_usadas': len(features_existentes)
        }
    
    def _preparar_features_treino(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepara features para treinamento do modelo."""
        df = df.copy()
        
        # Renomear colunas
        col_map = {
            'atletas.atleta_id': 'atleta_id',
            'atletas.pontos_num': 'pontos',
            'atletas.media_num': 'media',
            'atletas.preco_num': 'preco',
            'atletas.variacao_num': 'variacao',
            'atletas.posicao_id': 'posicao_id',
            'atletas.entrou_em_campo': 'entrou_em_campo',
        }
        for old, new in col_map.items():
            if old in df.columns:
                df = df.rename(columns={old: new})
        
        # Garantir colunas numéricas
        for col in ['pontos', 'media', 'preco', 'variacao']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Ordenar
        df = df.sort_values(['atleta_id', 'ano', 'rodada']).reset_index(drop=True)
        
        # Médias móveis (shift para evitar data leakage)
        for n in [3, 5, 10]:
            df[f'media_ultimas_{n}'] = df.groupby('atleta_id')['pontos'].transform(
                lambda x: x.shift(1).rolling(n, min_periods=1).mean()
            )
        
        df['std_ultimas_5'] = df.groupby('atleta_id')['pontos'].transform(
            lambda x: x.shift(1).rolling(5, min_periods=2).std()
        )
        df['max_ultimas_5'] = df.groupby('atleta_id')['pontos'].transform(
            lambda x: x.shift(1).rolling(5, min_periods=1).max()
        )
        df['pontos_ultima'] = df.groupby('atleta_id')['pontos'].shift(1)
        df['media_historica'] = df.groupby('atleta_id')['pontos'].transform(
            lambda x: x.shift(1).expanding().mean()
        )
        
        # Valorização
        if 'variacao' not in df.columns:
            df['variacao'] = 0
        df['variacao_acum_3'] = df.groupby('atleta_id')['variacao'].transform(
            lambda x: x.shift(1).rolling(3, min_periods=1).sum()
        )
        df['valorizou'] = (df['variacao'] > 0).astype(int)
        df['seq_valorizacao'] = df.groupby('atleta_id')['valorizou'].transform(
            lambda x: x.shift(1).rolling(5, min_periods=1).sum()
        )
        
        # Sequência de jogos
        if 'entrou_em_campo' not in df.columns:
            df['entrou_em_campo'] = 1
        df['sequencia_jogos'] = df.groupby('atleta_id')['entrou_em_campo'].transform(
            lambda x: x.shift(1).rolling(5, min_periods=1).sum()
        )
        
        # Features calculadas
        df['custo_beneficio'] = df['media'] / (df['preco'] + 1)
        df['tendencia'] = (df['media_ultimas_3'] - df['media_historica']) / (df['media_historica'].abs() + 1)
        df['momentum'] = df['media_ultimas_3'] - df['media_ultimas_10']
        
        df['padrao_evolucao'] = 0
        df.loc[df['media_ultimas_3'] > df['media_ultimas_10'] * 1.1, 'padrao_evolucao'] = 1
        df.loc[df['media_ultimas_3'] < df['media_ultimas_10'] * 0.9, 'padrao_evolucao'] = -1
        
        df['distancia_media'] = (df['media_ultimas_3'] - df['media']) / (df['media'].abs() + 1)
        df['abaixo_media'] = (df['distancia_media'] < -0.15).astype(int)
        df['oportunidade_regressao'] = ((df['abaixo_media'] == 1) & (df['padrao_evolucao'] >= 0)).astype(int)
        
        df['score_oportunidade'] = np.where(
            df['abaixo_media'] == 1,
            df['media'] * (1 + df['distancia_media'].abs()),
            df['media'] * 0.8
        )
        df['score_recuperacao'] = np.where(
            (df['padrao_evolucao'] == 0) & (df['abaixo_media'] == 1),
            df['media'] * 1.3,
            df['media']
        )
        df['risco_regressao'] = np.where(
            df['distancia_media'] > 0.15,
            df['media'] * 0.7,
            df['media']
        )
        
        df['score_geral_v9'] = (
            df['score_oportunidade'] * 0.3 +
            df['score_recuperacao'] * 0.2 +
            df['media'] * 0.2 +
            df['seq_valorizacao'] * 0.1 +
            df['sequencia_jogos'] * 0.1 +
            df['custo_beneficio'] * 0.1
        )
        
        return df.fillna(0)
    
    def aplicar_estrategia_rodada1(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica estratégia especial para rodada 1: Valorização Fácil.
        
        Prioriza jogadores com:
        - Boa previsão de pontuação
        - Mínimo para valorizar baixo (Preço × 0,50)
        - Maior delta entre score previsto e mínimo para valorizar
        
        Fórmula do Cartola para rodada 1:
        Mínimo para Valorizar = Preço × 0,50
        """
        df = df.copy()
        
        if 'score' not in df.columns:
            df['score'] = df.get('pred', df.get('score_geral_v9', 0))
        
        if 'preco' not in df.columns:
            df['preco'] = df.get('preco_num', 5)
        
        # Mínimo para valorizar na rodada 1 = Preço × 0,50
        df['minimo_valorizar'] = df['preco'] * 0.50
        
        # Delta de valorização (quanto acima do mínimo o jogador deve pontuar)
        df['delta_valorizacao'] = df['score'] - df['minimo_valorizar']
        
        # Probabilidade de valorização (baseada no delta)
        # Se delta > 0, há chance de valorizar
        # Se delta > 3, chance muito alta
        df['prob_valorizacao'] = np.clip(df['delta_valorizacao'] / 5, 0, 1)
        
        # Score de valorização R1
        # Prioriza: alto delta (fácil valorizar) + bom score previsto + preço baixo (mínimo baixo)
        df['score_valorizacao_r1'] = (
            df['score'] * 0.5 +                    # Peso no score previsto
            df['delta_valorizacao'] * 0.35 +       # Bonus por margem de valorização
            (1 / (df['minimo_valorizar'] + 1)) * 3  # Bonus para mínimo baixo (preço baixo)
        )
        
        # Bonus extra para jogadores com alta probabilidade de valorizar
        df.loc[df['prob_valorizacao'] > 0.6, 'score_valorizacao_r1'] *= 1.1
        
        # Penalizar jogadores com preço muito alto (difícil valorizar)
        df.loc[df['preco'] > 15, 'score_valorizacao_r1'] *= 0.9
        
        # Substituir score pelo score de valorização
        df['score_original'] = df['score']
        df['score'] = df['score_valorizacao_r1']
        
        return df
    
    def salvar_dados_rodada1(self, df_resultado: pd.DataFrame):
        """
        Salva dados de valorização da rodada 1 para usar na rodada 2.
        """
        estado = self._carregar_estado_especial()
        dados_r1 = {}
        
        for _, row in df_resultado.iterrows():
            atleta_id = str(row.get('atleta_id', row.get('id', '')))
            if not atleta_id:
                continue
            
            dados_r1[atleta_id] = {
                'pontos_r1': float(row.get('pontos_num', row.get('pontos', 0))),
                'variacao_r1': float(row.get('variacao_num', row.get('variacao', 0))),
                'media_apos_r1': float(row.get('media_num', row.get('media', 0)))
            }
        
        estado['dados_rodada_1'] = dados_r1
        self._salvar_estado_especial(estado)
        print(f"[RODADA 2] Dados de {len(dados_r1)} jogadores salvos")
    
    def aplicar_estrategia_rodada2(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica estratégia especial para rodada 2: Momentum de Valorização.
        
        Prioriza jogadores que:
        - Valorizaram muito na rodada 1
        - Têm boa previsão de pontuação
        - Mesmo com pontuação mediana, ainda valorizam
        """
        df = df.copy()
        
        if 'score' not in df.columns:
            df['score'] = df.get('pred', df.get('score_geral_v9', 0))
        
        estado = self._carregar_estado_especial()
        dados_r1 = estado.get('dados_rodada_1', {})
        
        if not dados_r1:
            print("[RODADA 2] AVISO: Dados da rodada 1 não encontrados")
            return df
        
        # Adicionar dados da rodada 1
        df['pontos_r1'] = df['atleta_id'].astype(str).map(
            lambda x: dados_r1.get(x, {}).get('pontos_r1', 0)
        )
        df['variacao_r1'] = df['atleta_id'].astype(str).map(
            lambda x: dados_r1.get(x, {}).get('variacao_r1', 0)
        )
        df['media_apos_r1'] = df['atleta_id'].astype(str).map(
            lambda x: dados_r1.get(x, {}).get('media_apos_r1', 0)
        )
        
        # Estimar média inicial
        df['media_inicial_est'] = np.where(
            df['media_apos_r1'] > 0,
            df['media_apos_r1'] * 2 - df['pontos_r1'],
            df.get('media', 0)
        )
        df['media_inicial_est'] = df['media_inicial_est'].clip(lower=0)
        
        # Mínimo na R2 para continuar valorizando
        df['minimo_r2_para_valorizar'] = 2 * df['media_inicial_est'] - df['pontos_r1']
        df['minimo_r2_para_valorizar'] = df['minimo_r2_para_valorizar'].clip(lower=0)
        
        # Margem de segurança
        df['margem_seguranca'] = df['score'] - df['minimo_r2_para_valorizar']
        
        # Score de valorização R2
        df['score_valorizacao_r2'] = (
            df['score'] * 0.4 +
            df['variacao_r1'] * 3 +
            df['margem_seguranca'] * 0.3 +
            df['pontos_r1'] * 0.1
        )
        
        # Bonus para alta valorização R1
        df.loc[df['variacao_r1'] > 1.0, 'score_valorizacao_r2'] *= 1.2
        
        # Bonus para margem de segurança alta
        df.loc[df['margem_seguranca'] > 3, 'score_valorizacao_r2'] *= 1.1
        
        # Substituir score
        df['score_original'] = df['score']
        df['score'] = df['score_valorizacao_r2']
        
        return df
    
    def escalar_time_real(self, df_mercado: pd.DataFrame, formacao: str = '4-3-3',
                          orcamento: float = 100.0, ano: int = None, rodada: int = None) -> Dict:
        """
        Escala o time para escalação real, aplicando estratégias especiais nas rodadas 1 e 2.
        
        Args:
            df_mercado: DataFrame com dados do mercado
            formacao: Formação desejada
            orcamento: Orçamento disponível
            ano: Ano da temporada (se None, usa ano atual)
            rodada: Rodada atual (se None, usa rodada_atual)
            
        Returns:
            Dicionário com escalação
        """
        if ano is None:
            ano = datetime.now().year
        if rodada is None:
            rodada = self.rodada_atual
        
        # Verificar necessidade de retreinamento antes da rodada 1
        if self.verificar_necessidade_retreinamento(ano, rodada):
            resultado = self.retreinar_modelo_para_nova_temporada(ano)
            if resultado['sucesso']:
                print(f"[ESCALAÇÃO REAL] Modelo retreinado para {ano}")
            else:
                print(f"[ESCALAÇÃO REAL] AVISO: Falha no retreinamento: {resultado.get('erro')}")
        
        # Preparar features
        df = self.preparar_features_v9(df_mercado, modo_simulacao=False)
        
        # Aplicar previsão do modelo
        if self.modelo:
            try:
                df['pred'] = self.modelo.predict(df[self.features])
            except:
                df['pred'] = df['score_geral_v9']
        else:
            df['pred'] = df['score_geral_v9']
        
        df['score'] = df['pred']
        
        # Aplicar estratégia especial baseada na rodada
        estrategia_aplicada = "PADRÃO"
        
        if rodada == 1:
            df = self.aplicar_estrategia_rodada1(df)
            estrategia_aplicada = "VALORIZAÇÃO FÁCIL (R1)"
            print(f"[ESCALAÇÃO REAL] Estratégia aplicada: {estrategia_aplicada}")
        
        elif rodada == 2:
            df = self.aplicar_estrategia_rodada2(df)
            estrategia_aplicada = "MOMENTUM DE VALORIZAÇÃO (R2)"
            print(f"[ESCALAÇÃO REAL] Estratégia aplicada: {estrategia_aplicada}")
        
        # Continuar com a escalação normal usando o score ajustado
        resultado = self.escalar_time(df, formacao=formacao, orcamento=orcamento, 
                                       incluir_explicacao=True, modo_simulacao=False)
        
        if resultado:
            resultado['estrategia_especial'] = estrategia_aplicada
        
        return resultado
    
    def obter_info_estrategia(self, rodada: int) -> Dict:
        """Retorna informações sobre a estratégia aplicada na rodada."""
        if rodada == 1:
            return {
                'nome': 'VALORIZAÇÃO FÁCIL',
                'descricao': 'Prioriza jogadores com boa previsão e baixo mínimo para valorizar',
                'objetivo': 'Maximizar jogadores que valorizam na rodada 1',
                'criterios': ['Score previsto alto', 'Média baixa', 'Delta positivo', 'Bom custo-benefício']
            }
        elif rodada == 2:
            return {
                'nome': 'MOMENTUM DE VALORIZAÇÃO',
                'descricao': 'Prioriza jogadores que valorizaram muito na rodada 1',
                'objetivo': 'Aproveitar o colchão de valorização da rodada 1',
                'criterios': ['Alta valorização R1', 'Score previsto bom', 'Margem de segurança', 'Pontuação alta R1']
            }
        else:
            return {
                'nome': 'ESTRATÉGIA PADRÃO',
                'descricao': 'Usa o modelo preditivo v9',
                'objetivo': 'Maximizar pontuação esperada',
                'criterios': ['Score ML', 'Oportunidade regressão', 'Tendência', 'Custo-benefício']
            }
