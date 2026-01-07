# Datathon FIAP - Passos Mágicos
## Análise de Dados e Modelo Preditivo de Risco de Defasagem

---

## Slide 1: Capa
**Título:** Transformando Vidas Através dos Dados
**Subtítulo:** Datathon FIAP - Passos Mágicos
**Elementos:**
- Logo da Passos Mágicos
- Logo da FIAP
- Pós-Tech em Data Analytics - Fase 5
- Data: Janeiro 2025

---

## Slide 2: A Associação Passos Mágicos
**Título:** 32 Anos Transformando Vidas em Embu-Guaçu

**Conteúdo:**
A Associação Passos Mágicos atua há mais de três décadas na transformação da vida de crianças e jovens de baixa renda através da educação de qualidade. A organização utiliza uma metodologia própria de avaliação do desenvolvimento educacional chamada PEDE (Pesquisa Extensiva do Desenvolvimento Educacional).

**Dados-chave:**
- 32 anos de atuação
- Localização: Embu-Guaçu, SP
- Foco: Educação como ferramenta de transformação social
- Metodologia: PEDE com 7 indicadores de desenvolvimento

---

## Slide 3: O Desafio do Datathon
**Título:** Identificar Padrões e Prever Riscos para Intervenção Precoce

**Problema:**
Como utilizar os dados educacionais coletados pela Passos Mágicos para identificar alunos em risco de defasagem antes que o problema se agrave?

**Objetivos:**
1. Analisar a evolução dos indicadores educacionais (2022-2024)
2. Responder às 11 perguntas de negócio propostas
3. Desenvolver modelo preditivo de risco de defasagem
4. Criar ferramenta interativa para apoio à decisão

---

## Slide 4: Os Dados - PEDE 2022-2024
**Título:** Base de Dados com 3.030 Registros de Alunos

**Estrutura dos dados:**
| Ano | Alunos | Variáveis |
|-----|--------|-----------|
| 2022 | 860 | 42 |
| 2023 | 1.014 | 48 |
| 2024 | 1.156 | 50 |

**Indicadores principais:**
- **INDE** - Índice de Desenvolvimento Educacional (global)
- **IAN** - Adequação ao Nível (defasagem)
- **IDA** - Desempenho Acadêmico
- **IEG** - Engajamento
- **IAA** - Autoavaliação
- **IPS** - Aspectos Psicossociais
- **IPV** - Ponto de Virada

---

## Slide 5: Evolução da Defasagem
**Título:** Redução Consistente da Defasagem Média ao Longo dos Anos

**Insight principal:**
A defasagem média dos alunos reduziu de -1.42 anos em 2022 para -1.18 anos em 2024, demonstrando a efetividade das intervenções educacionais da Passos Mágicos.

**Dados:**
- 2022: -1.42 anos de defasagem média
- 2023: -1.28 anos de defasagem média
- 2024: -1.18 anos de defasagem média
- Melhoria: 17% de redução na defasagem

**Visualização:** Gráfico de linha mostrando evolução temporal

---

## Slide 6: Distribuição das Pedras
**Título:** Sistema de Classificação por Pedras Mostra Progresso dos Alunos

**O sistema de Pedras:**
- **Quartzo** (INDE 2.405-5.506): Nível inicial
- **Ágata** (INDE 5.506-6.868): Em desenvolvimento
- **Ametista** (INDE 6.868-8.230): Bom desempenho
- **Topázio** (INDE 8.230-9.294): Excelência

**Evolução 2022-2024:**
- Aumento de 5.2% no percentual de alunos em Ametista + Topázio
- Redução no percentual de alunos em Quartzo
- Demonstra progressão consistente no desenvolvimento

---

## Slide 7: Correlações Entre Indicadores
**Título:** Engajamento é o Motor do Desenvolvimento Educacional

**Descobertas principais:**
O IEG (Engajamento) apresenta forte correlação com todos os demais indicadores, sendo o fator mais influente no desenvolvimento global do aluno.

**Correlações com IEG:**
- IEG x INDE: r = 0.85 (muito forte)
- IEG x IDA: r = 0.72 (forte)
- IEG x IPV: r = 0.68 (moderada-forte)

**Implicação:** Investir em engajamento gera impacto em cascata em todos os indicadores.

---

## Slide 8: O Ponto de Virada (IPV)
**Título:** IPV Identifica Momentos Críticos de Transformação

**O que é o IPV:**
O Indicador de Ponto de Virada mede momentos em que o aluno demonstra mudança significativa de comportamento e atitude em relação aos estudos.

**Indicadores mais correlacionados com IPV:**
1. IEG (Engajamento): r = 0.68
2. IDA (Desempenho): r = 0.54
3. IAA (Autoavaliação): r = 0.48

**Insight:** Alunos com alto IPV tendem a apresentar melhorias sustentadas em todos os indicadores.

---

## Slide 9: Modelo Preditivo de Risco
**Título:** Machine Learning para Identificação Precoce de Alunos em Risco

**Metodologia:**
- Algoritmo: Random Forest Classifier
- Variável alvo: Defasagem ≤ -2 anos
- Features: 10 indicadores (6 base + 4 derivadas)
- Balanceamento: Class weights ajustados
- Threshold otimizado: 0.35

**Métricas de desempenho:**
| Métrica | Valor |
|---------|-------|
| Recall | 87.06% |
| Precisão | 35.41% |
| F1-Score | 50.34% |
| AUC-ROC | 83.25% |

---

## Slide 10: Features Mais Importantes
**Título:** IAN é o Principal Preditor de Risco de Defasagem

**Ranking de importância das features:**
1. **IAN** (34%) - Adequação ao Nível
2. **MEDIA_INDICADORES** (16%) - Desempenho geral
3. **IPV** (10%) - Ponto de Virada
4. **STD_INDICADORES** (9%) - Variabilidade
5. **IEG** (8%) - Engajamento

**Interpretação:**
O IAN é naturalmente o mais importante pois mede diretamente a defasagem. A média dos indicadores captura o desempenho global, enquanto o IPV indica potencial de recuperação.

---

## Slide 11: Aplicação Streamlit
**Título:** Ferramenta Interativa para Apoio à Decisão

**Funcionalidades:**
1. **Dashboard** - Visualizações interativas dos dados históricos
2. **Predição de Risco** - Interface para avaliar alunos individualmente
3. **Análise de Perfil** - Radar chart com os indicadores do aluno
4. **Recomendações** - Sugestões de intervenção baseadas no risco

**Tecnologias:**
- Streamlit para interface web
- Plotly para visualizações interativas
- Scikit-learn para modelo preditivo

**Deploy:** Streamlit Community Cloud

---

## Slide 12: Demonstração da Predição
**Título:** Como Funciona a Predição de Risco

**Exemplo de uso:**
1. Educador insere os 6 indicadores do aluno (escala 0-10)
2. Sistema calcula features derivadas automaticamente
3. Modelo retorna probabilidade de risco
4. Interface exibe classificação e recomendações

**Saída do modelo:**
- Probabilidade de risco (0-100%)
- Classificação: Em Risco / Baixo Risco
- Radar chart do perfil do aluno
- Recomendações de intervenção personalizadas

---

## Slide 13: Recomendações Estratégicas
**Título:** Ações Baseadas em Dados para Maximizar Impacto

**Para alunos em alto risco:**
- Acompanhamento pedagógico intensivo
- Suporte psicossocial prioritário
- Monitoramento frequente dos indicadores
- Plano de intervenção personalizado

**Para a organização:**
- Priorizar investimentos em engajamento (IEG)
- Identificar e replicar fatores de Ponto de Virada
- Usar o modelo para triagem inicial de novos alunos
- Monitorar evolução trimestral dos indicadores

---

## Slide 14: Conclusões
**Título:** Dados Como Ferramenta de Transformação Social

**Principais descobertas:**
1. A Passos Mágicos demonstra impacto positivo consistente (redução de 17% na defasagem)
2. Engajamento é o indicador mais influente no desenvolvimento global
3. O modelo preditivo identifica 87% dos alunos em risco
4. IAN, média dos indicadores e IPV são os principais preditores

**Valor entregue:**
- Análise completa dos dados 2022-2024
- Modelo preditivo com alta sensibilidade
- Ferramenta interativa para uso prático
- Insights acionáveis para intervenção

---

## Slide 15: Próximos Passos
**Título:** Evolução Contínua do Projeto

**Melhorias futuras:**
1. Incorporar dados longitudinais (acompanhamento do mesmo aluno)
2. Adicionar variáveis socioeconômicas ao modelo
3. Desenvolver modelo de recomendação de intervenções
4. Implementar alertas automáticos para educadores

**Impacto esperado:**
- Redução no tempo de identificação de alunos em risco
- Aumento na efetividade das intervenções
- Melhor alocação de recursos da organização
- Mais vidas transformadas através da educação

---

## Slide 16: Agradecimentos
**Título:** Obrigado!

**Agradecimentos:**
- Associação Passos Mágicos pela parceria e dados
- FIAP pela oportunidade do Datathon
- Professores e mentores do curso

**Contato:**
- GitHub: [link do repositório]
- Streamlit: [link da aplicação]

**Mensagem final:**
"Transformando dados em oportunidades, e oportunidades em vidas transformadas."

---
