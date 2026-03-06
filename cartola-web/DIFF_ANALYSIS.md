# Análise de Diferenças: Streamlit vs Web App

## 1. SIDEBAR
### Streamlit:
- Logo Dervé FC centralizado com glassmorphism card
- Menu: 🏠 Dashboard, ⚽ Escalação, 📊 Mercado Completo, 🔬 Simulação Histórica, 📜 Histórico, 🔄 Atualizar Resultados, 📡 Status Coleta
- Sem "Análise" como item separado (análise é dentro do Mercado)

### Web App:
- Menu: Dashboard, Escalação, Mercado, Análise (separado!), Simulação, Histórico, Atualizar, Status Coleta
- Análise é um item separado no menu (no Streamlit está dentro do Mercado)

### FIX: Remover "Análise" do sidebar. A análise de jogador deve ser acessível via Mercado (clicando no jogador).

## 2. ESCALAÇÃO - Campo de Futebol
### Streamlit (campo_layout.py):
- Zagueiros ficam NO CENTRO da linha de defesa
- Laterais ficam NAS PONTAS da linha de defesa
- Layout: LAT_ESQ | ZAG | ZAG | LAT_DIR
- Lista lateral ao lado do campo com todos os jogadores

### Web App:
- Zagueiros e laterais são misturados e ordenados por pos_id (errado!)
- Sem lista lateral

### FIX: Reordenar defesa para LAT-ZAG-ZAG-LAT. Adicionar lista lateral.

## 3. ESCALAÇÃO - Lista Lateral
### Streamlit:
- Lista ao lado do campo mostrando todos os titulares com:
  - Nome, posição badge, clube, preço, score previsto
  - Capitão marcado com 👑
  - Reservas e reserva de luxo
  - Custo total e saldo

### Web App:
- Não tem lista lateral

### FIX: Adicionar lista lateral igual ao Streamlit.

## 4. MERCADO - Gráfico de Análise do Jogador
### Streamlit (analise_jogador.py):
- Gráfico ÚNICO com TODAS as rodadas (brasileiro + coleta paralela)
- Eixo X mostra todas as rodadas sequencialmente
- Linhas: pontuação real, média móvel, previsão

### Web App:
- Gráficos SEPARADOS para brasileiro e coleta paralela

### FIX: Combinar todos os dados em um único gráfico.

## 5. SIMULAÇÃO HISTÓRICA
### Streamlit:
- Sidebar com configurações (orçamento, formação)
- Modo "Todas as Rodadas" e "Rodada Específica" via radio no sidebar
- Detalhes expandidos por rodada incluem:
  - Justificativas completas de cada jogador
  - Comparação lado a lado com time ideal
  - Gauges de aproveitamento por justificativa
  - Métricas detalhadas

### Web App:
- Faltam justificativas nos detalhes da rodada
- Faltam gauges de velocímetro
- Detalhes da rodada não mostram justificativas

### FIX: Adicionar justificativas nos detalhes, gauges de velocímetro.

## 6. HISTÓRICO
### Streamlit:
- Gráfico de evolução de pontuação
- Gráfico de aproveitamento por rodada
- Análise evolutiva 2026 vs 2025
- Aproveitamento por posição (gráfico de barras)
- Distribuição de justificativas (donut chart)
- Gauges de aproveitamento por justificativa (7 gauges)
- Formações utilizadas
- Top 5 jogadores
- Tabela de resultados
- Detalhes por rodada (com campo visual + lista lateral)
- Histórico de ajustes automáticos

### Web App:
- Faltam vários elementos (verificar)

### FIX: Verificar e adicionar todos os elementos faltantes.

## 7. SIDEBAR ICONS
### Streamlit:
- 🏠 Dashboard
- ⚽ Escalação  
- 📊 Mercado Completo
- 🔬 Simulação Histórica
- 📜 Histórico
- 🔄 Atualizar Resultados
- 📡 Status Coleta

### Web App:
- Usa ícones Lucide em vez de emojis
- Tem "Análise" extra

### FIX: Manter ícones Lucide mas ajustar labels e remover Análise.
