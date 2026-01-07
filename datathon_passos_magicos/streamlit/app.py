"""
Datathon FIAP - Passos Mágicos
Aplicação Streamlit para Predição de Risco de Defasagem

Esta aplicação permite:
1. Visualizar análises exploratórias dos dados
2. Prever o risco de defasagem de alunos
3. Explorar os insights do modelo preditivo
"""

import streamlit as st
import pandas as pd
import numpy as np
import pickle
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configuração da página
st.set_page_config(
    page_title="Passos Mágicos - Análise de Risco",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E3A5F;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .risk-high {
        background-color: #ffcccc;
        border-left: 5px solid #e74c3c;
        padding: 1rem;
        border-radius: 5px;
    }
    .risk-low {
        background-color: #ccffcc;
        border-left: 5px solid #2ecc71;
        padding: 1rem;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Funções auxiliares
@st.cache_resource
def carregar_modelo():
    """Carrega o modelo treinado e o scaler"""
    try:
        with open('modelo_risco_defasagem.pkl', 'rb') as f:
            modelo = pickle.load(f)
        with open('scaler.pkl', 'rb') as f:
            scaler = pickle.load(f)
        with open('features.txt', 'r') as f:
            features = f.read().strip().split('\n')
        with open('threshold.txt', 'r') as f:
            threshold = float(f.read().strip())
        return modelo, scaler, features, threshold
    except Exception as e:
        st.error(f"Erro ao carregar modelo: {e}")
        return None, None, None, 0.5

@st.cache_data
def carregar_dados():
    """Carrega os dados do PEDE"""
    try:
        xlsx = pd.ExcelFile('BASE_DE_DADOS_PEDE_2024_DATATHON.xlsx')
        df_2022 = pd.read_excel(xlsx, sheet_name='PEDE2022')
        df_2023 = pd.read_excel(xlsx, sheet_name='PEDE2023')
        df_2024 = pd.read_excel(xlsx, sheet_name='PEDE2024')
        return df_2022, df_2023, df_2024
    except:
        return None, None, None

def preparar_dados(df, ano):
    """Prepara os dados de um ano específico"""
    df_prep = df.copy()
    df_prep['ANO'] = ano
    col_map = {}
    for col in df_prep.columns:
        col_lower = col.lower()
        if col_lower == 'iaa': col_map[col] = 'IAA'
        elif col_lower == 'ieg' and 'destaque' not in col_lower: col_map[col] = 'IEG'
        elif col_lower == 'ips': col_map[col] = 'IPS'
        elif col_lower == 'ida' and 'destaque' not in col_lower: col_map[col] = 'IDA'
        elif col_lower == 'ipv' and 'destaque' not in col_lower: col_map[col] = 'IPV'
        elif col_lower == 'ian': col_map[col] = 'IAN'
        elif 'defas' in col_lower: col_map[col] = 'DEFASAGEM'
    
    if ano == 2022:
        col_map['INDE 22'] = 'INDE'
        col_map['Pedra 22'] = 'PEDRA'
    elif ano == 2023:
        col_map['INDE 2023'] = 'INDE'
        col_map['Pedra 2023'] = 'PEDRA'
    elif ano == 2024:
        col_map['INDE 2024'] = 'INDE'
        col_map['Pedra 2024'] = 'PEDRA'
    
    df_prep = df_prep.rename(columns=col_map)
    return df_prep

def prever_risco(modelo, scaler, features, threshold, indicadores):
    """Realiza a predição de risco para um aluno"""
    # Criar features derivadas
    features_base = ['IDA', 'IEG', 'IAA', 'IPS', 'IPV', 'IAN']
    valores_base = [indicadores[f] for f in features_base]
    
    media_ind = np.mean(valores_base)
    std_ind = np.std(valores_base)
    gap_ida_iaa = indicadores['IDA'] - indicadores['IAA']
    ratio_ieg_ida = indicadores['IEG'] / (indicadores['IDA'] + 0.1)
    
    # Criar array de features
    X = np.array([[
        indicadores['IDA'], indicadores['IEG'], indicadores['IAA'],
        indicadores['IPS'], indicadores['IPV'], indicadores['IAN'],
        media_ind, std_ind, gap_ida_iaa, ratio_ieg_ida
    ]])
    
    # Normalizar
    X_scaled = scaler.transform(X)
    
    # Predição
    prob = modelo.predict_proba(X_scaled)[0, 1]
    em_risco = prob >= threshold
    
    return prob, em_risco

# Sidebar
st.sidebar.image("https://passosmagicos.org.br/wp-content/uploads/2021/09/logo-passos-magicos.png", width=200)
st.sidebar.title("🎓 Navegação")

pagina = st.sidebar.radio(
    "Selecione a página:",
    ["🏠 Início", "📊 Dashboard", "🔮 Predição de Risco", "📈 Sobre o Modelo", "ℹ️ Sobre"]
)

# Carregar modelo
modelo, scaler, features, threshold = carregar_modelo()

# Páginas
if pagina == "🏠 Início":
    st.markdown('<p class="main-header">🎓 Passos Mágicos</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Sistema de Análise e Predição de Risco de Defasagem Educacional</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📊 Análise de Dados
        Explore os indicadores educacionais dos alunos da Passos Mágicos através de visualizações interativas.
        """)
    
    with col2:
        st.markdown("""
        ### 🔮 Predição de Risco
        Utilize nosso modelo de Machine Learning para identificar alunos em risco de defasagem educacional.
        """)
    
    with col3:
        st.markdown("""
        ### 📈 Insights
        Descubra os fatores que mais influenciam o desenvolvimento educacional dos alunos.
        """)
    
    st.divider()
    
    st.markdown("""
    ## Sobre a Associação Passos Mágicos
    
    A **Associação Passos Mágicos** tem uma trajetória de 32 anos de atuação, trabalhando na transformação 
    da vida de crianças e jovens de baixa renda em Embu-Guaçu. A missão da organização é promover a 
    educação de qualidade como ferramenta de transformação social.
    
    ### Indicadores Avaliados (PEDE)
    
    | Indicador | Descrição |
    |-----------|-----------|
    | **IAN** | Indicador de Adequação ao Nível (defasagem escolar) |
    | **IDA** | Indicador de Desempenho Acadêmico |
    | **IEG** | Indicador de Engajamento |
    | **IAA** | Indicador de Autoavaliação |
    | **IPS** | Indicador Psicossocial |
    | **IPV** | Indicador de Ponto de Virada |
    | **INDE** | Índice de Desenvolvimento Educacional (global) |
    """)

elif pagina == "📊 Dashboard":
    st.markdown('<p class="main-header">📊 Dashboard de Indicadores</p>', unsafe_allow_html=True)
    
    # Carregar dados
    df_2022, df_2023, df_2024 = carregar_dados()
    
    if df_2022 is not None:
        # Preparar dados
        df_2022_prep = preparar_dados(df_2022, 2022)
        df_2023_prep = preparar_dados(df_2023, 2023)
        df_2024_prep = preparar_dados(df_2024, 2024)
        
        colunas = ['ANO', 'INDE', 'IAA', 'IEG', 'IPS', 'IDA', 'IPV', 'IAN', 'DEFASAGEM', 'PEDRA']
        df_unificado = pd.concat([
            df_2022_prep[[c for c in colunas if c in df_2022_prep.columns]],
            df_2023_prep[[c for c in colunas if c in df_2023_prep.columns]],
            df_2024_prep[[c for c in colunas if c in df_2024_prep.columns]]
        ], ignore_index=True)
        
        for col in ['INDE', 'IAA', 'IEG', 'IPS', 'IDA', 'IPV', 'IAN', 'DEFASAGEM']:
            if col in df_unificado.columns:
                df_unificado[col] = pd.to_numeric(df_unificado[col], errors='coerce')
        
        df_unificado['PEDRA'] = df_unificado['PEDRA'].replace({'Agata': 'Ágata'})
        
        # Métricas gerais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total de Alunos (2024)", f"{len(df_2024):,}")
        with col2:
            inde_medio = df_unificado[df_unificado['ANO']==2024]['INDE'].mean()
            st.metric("INDE Médio (2024)", f"{inde_medio:.2f}")
        with col3:
            def_media = df_unificado[df_unificado['ANO']==2024]['DEFASAGEM'].mean()
            st.metric("Defasagem Média (2024)", f"{def_media:.2f} anos")
        with col4:
            pct_risco = (df_unificado[df_unificado['ANO']==2024]['DEFASAGEM'] <= -2).mean() * 100
            st.metric("% em Risco (2024)", f"{pct_risco:.1f}%")
        
        st.divider()
        
        # Gráficos
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Evolução do INDE Médio")
            inde_ano = df_unificado.groupby('ANO')['INDE'].mean().reset_index()
            fig = px.line(inde_ano, x='ANO', y='INDE', markers=True,
                         title='INDE Médio por Ano')
            fig.update_traces(line_color='#3498db', line_width=3, marker_size=12)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Distribuição das Pedras (2024)")
            pedras_2024 = df_unificado[df_unificado['ANO']==2024]['PEDRA'].value_counts()
            cores_pedras = {'Quartzo': '#C0C0C0', 'Ágata': '#9370DB', 
                          'Ametista': '#8B008B', 'Topázio': '#FFD700'}
            fig = px.pie(values=pedras_2024.values, names=pedras_2024.index,
                        title='Distribuição por Pedra',
                        color=pedras_2024.index,
                        color_discrete_map=cores_pedras)
            st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Evolução da Defasagem")
            def_ano = df_unificado.groupby('ANO')['DEFASAGEM'].mean().reset_index()
            fig = px.bar(def_ano, x='ANO', y='DEFASAGEM',
                        title='Defasagem Média por Ano',
                        color='DEFASAGEM',
                        color_continuous_scale='RdYlGn_r')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Correlação entre Indicadores")
            indicadores = ['IDA', 'IEG', 'IAA', 'IPS', 'IPV', 'IAN', 'INDE']
            corr = df_unificado[indicadores].corr()
            fig = px.imshow(corr, text_auto='.2f', aspect='auto',
                           title='Matriz de Correlação',
                           color_continuous_scale='RdBu_r')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Dados não disponíveis. Por favor, faça upload do arquivo de dados.")

elif pagina == "🔮 Predição de Risco":
    st.markdown('<p class="main-header">🔮 Predição de Risco de Defasagem</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Insira os indicadores do aluno para prever o risco de defasagem</p>', unsafe_allow_html=True)
    
    if modelo is not None:
        st.info("ℹ️ Insira os valores dos indicadores do aluno (escala de 0 a 10)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ida = st.slider("IDA - Desempenho Acadêmico", 0.0, 10.0, 5.0, 0.1)
            ieg = st.slider("IEG - Engajamento", 0.0, 10.0, 5.0, 0.1)
        
        with col2:
            iaa = st.slider("IAA - Autoavaliação", 0.0, 10.0, 5.0, 0.1)
            ips = st.slider("IPS - Psicossocial", 0.0, 10.0, 5.0, 0.1)
        
        with col3:
            ipv = st.slider("IPV - Ponto de Virada", 0.0, 10.0, 5.0, 0.1)
            ian = st.slider("IAN - Adequação ao Nível", 0.0, 10.0, 5.0, 0.1)
        
        st.divider()
        
        if st.button("🔍 Analisar Risco", type="primary", use_container_width=True):
            indicadores = {
                'IDA': ida, 'IEG': ieg, 'IAA': iaa,
                'IPS': ips, 'IPV': ipv, 'IAN': ian
            }
            
            prob, em_risco = prever_risco(modelo, scaler, features, threshold, indicadores)
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Gauge de probabilidade
                fig = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = prob * 100,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Probabilidade de Risco"},
                    gauge = {
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#e74c3c" if em_risco else "#2ecc71"},
                        'steps': [
                            {'range': [0, 35], 'color': "#d4edda"},
                            {'range': [35, 65], 'color': "#fff3cd"},
                            {'range': [65, 100], 'color': "#f8d7da"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': threshold * 100
                        }
                    }
                ))
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                if em_risco:
                    st.markdown("""
                    <div class="risk-high">
                        <h3>⚠️ ALUNO EM RISCO</h3>
                        <p>O modelo identificou que este aluno apresenta <strong>alto risco</strong> de defasagem educacional.</p>
                        <p><strong>Probabilidade:</strong> {:.1f}%</p>
                    </div>
                    """.format(prob * 100), unsafe_allow_html=True)
                    
                    st.markdown("""
                    ### Recomendações:
                    - 📚 Acompanhamento pedagógico intensivo
                    - 👥 Suporte psicossocial
                    - 📊 Monitoramento frequente dos indicadores
                    - 🎯 Plano de intervenção personalizado
                    """)
                else:
                    st.markdown("""
                    <div class="risk-low">
                        <h3>✅ BAIXO RISCO</h3>
                        <p>O modelo indica que este aluno apresenta <strong>baixo risco</strong> de defasagem educacional.</p>
                        <p><strong>Probabilidade:</strong> {:.1f}%</p>
                    </div>
                    """.format(prob * 100), unsafe_allow_html=True)
                    
                    st.markdown("""
                    ### Recomendações:
                    - 📈 Manter acompanhamento regular
                    - 🌟 Incentivar participação em atividades
                    - 🎯 Estabelecer metas de desenvolvimento
                    """)
            
            # Radar chart dos indicadores
            st.subheader("Perfil do Aluno")
            
            categorias = ['IDA', 'IEG', 'IAA', 'IPS', 'IPV', 'IAN']
            valores = [ida, ieg, iaa, ips, ipv, ian]
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=valores + [valores[0]],
                theta=categorias + [categorias[0]],
                fill='toself',
                name='Aluno',
                line_color='#3498db'
            ))
            
            # Adicionar média de referência
            fig.add_trace(go.Scatterpolar(
                r=[5, 5, 5, 5, 5, 5, 5],
                theta=categorias + [categorias[0]],
                fill='toself',
                name='Média (5.0)',
                line_color='#95a5a6',
                opacity=0.3
            ))
            
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
                showlegend=True,
                title="Radar de Indicadores"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Modelo não carregado. Verifique se os arquivos do modelo estão disponíveis.")

elif pagina == "📈 Sobre o Modelo":
    st.markdown('<p class="main-header">📈 Sobre o Modelo Preditivo</p>', unsafe_allow_html=True)
    
    st.markdown("""
    ## Metodologia
    
    O modelo de predição de risco de defasagem foi desenvolvido utilizando técnicas de Machine Learning
    para identificar padrões nos indicadores educacionais que possam indicar alunos em risco.
    
    ### Algoritmo Utilizado
    
    **Random Forest Classifier** - Um ensemble de árvores de decisão que combina múltiplas árvores
    para fazer predições mais robustas e precisas.
    
    ### Features Utilizadas
    
    | Feature | Descrição |
    |---------|-----------|
    | IDA | Indicador de Desempenho Acadêmico |
    | IEG | Indicador de Engajamento |
    | IAA | Indicador de Autoavaliação |
    | IPS | Indicador Psicossocial |
    | IPV | Indicador de Ponto de Virada |
    | IAN | Indicador de Adequação ao Nível |
    | MEDIA_INDICADORES | Média de todos os indicadores |
    | STD_INDICADORES | Desvio padrão dos indicadores |
    | GAP_IDA_IAA | Diferença entre IDA e IAA |
    | RATIO_IEG_IDA | Razão entre IEG e IDA |
    
    ### Métricas de Desempenho
    """)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Recall", "87.06%", help="Capacidade de identificar alunos em risco")
    with col2:
        st.metric("Precisão", "35.41%", help="Proporção de predições corretas de risco")
    with col3:
        st.metric("F1-Score", "50.34%", help="Média harmônica entre precisão e recall")
    with col4:
        st.metric("AUC-ROC", "83.25%", help="Área sob a curva ROC")
    
    st.markdown("""
    ### Importância das Features
    
    O gráfico abaixo mostra quais indicadores têm maior influência na predição de risco:
    """)
    
    # Gráfico de importância
    features_imp = {
        'IAN': 0.34,
        'MEDIA_INDICADORES': 0.16,
        'IPV': 0.10,
        'STD_INDICADORES': 0.09,
        'IEG': 0.08,
        'RATIO_IEG_IDA': 0.07,
        'GAP_IDA_IAA': 0.06,
        'IDA': 0.05,
        'IPS': 0.03,
        'IAA': 0.02
    }
    
    fig = px.bar(
        x=list(features_imp.values()),
        y=list(features_imp.keys()),
        orientation='h',
        title='Importância das Features no Modelo',
        labels={'x': 'Importância', 'y': 'Feature'},
        color=list(features_imp.values()),
        color_continuous_scale='Blues'
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("""
    ### Interpretação
    
    - **IAN** é o indicador mais importante, o que faz sentido pois mede diretamente a adequação ao nível
    - **MEDIA_INDICADORES** captura o desempenho geral do aluno
    - **IPV** (Ponto de Virada) indica momentos críticos de transformação
    
    ### Limitações
    
    - O modelo foi treinado com dados de 2022-2024
    - A precisão pode variar para perfis de alunos muito diferentes dos dados de treino
    - Recomenda-se usar as predições como apoio à decisão, não como única fonte
    """)

elif pagina == "ℹ️ Sobre":
    st.markdown('<p class="main-header">ℹ️ Sobre o Projeto</p>', unsafe_allow_html=True)
    
    st.markdown("""
    ## Datathon FIAP - Passos Mágicos
    
    Este projeto foi desenvolvido como parte do Datathon da FIAP, com o objetivo de analisar
    os dados educacionais da Associação Passos Mágicos e criar ferramentas para apoiar
    a identificação de alunos em risco de defasagem.
    
    ### Equipe
    
    - **Curso:** Pós-Tech em Data Analytics
    - **Instituição:** FIAP
    - **Fase:** 5 - Deep Learning e Analytics
    
    ### Tecnologias Utilizadas
    
    - **Python** - Linguagem de programação
    - **Pandas/NumPy** - Análise de dados
    - **Scikit-learn** - Machine Learning
    - **Streamlit** - Interface web
    - **Plotly** - Visualizações interativas
    
    ### Contato
    
    Para mais informações sobre a Associação Passos Mágicos:
    - 🌐 [passosmagicos.org.br](https://passosmagicos.org.br)
    
    ---
    
    *Desenvolvido com ❤️ para transformar vidas através da educação*
    """)

# Footer
st.sidebar.divider()
st.sidebar.markdown("---")
st.sidebar.markdown("**Datathon FIAP 2024**")
st.sidebar.markdown("Passos Mágicos")
