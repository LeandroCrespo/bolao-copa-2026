# Roteiro para Vídeo de 5 Minutos - Datathon Passos Mágicos

**Objetivo:** Apresentar os resultados da análise, o storytelling e o modelo preditivo em até 5 minutos.

---

### Estrutura e Tempos

| Slide # | Título do Slide | Tempo (segundos) | Pontos Chave |
|:---:|---|:---:|---|
| 1 | Capa | 10s | Apresentação inicial e introdução ao tema. |
| 2 | Contexto | 20s | Quem é a Passos Mágicos e sua missão. |
| 3 | O Desafio | 15s | O objetivo do projeto: usar dados para prever o risco de defasagem. |
| 4 | Nossos Dados | 15s | Visão geral do dataset (PEDE 2022-2024). |
| 5-8 | Análise Exploratória | 60s | Principais descobertas: queda na defasagem, importância do engajamento e do ponto de virada. |
| 9-10 | Modelo Preditivo | 60s | Explicação do modelo (Random Forest), métricas (Recall de 87%) e as features mais importantes (IAN, Média, IPV). |
| 11-12 | Aplicação Streamlit | 40s | Demonstração da ferramenta interativa e como ela pode ser usada no dia a dia. |
| 13 | Recomendações | 30s | Ações estratégicas para a ONG e para os alunos em risco. |
| 14 | Conclusões | 20s | Resumo do valor entregue: análise completa, modelo preditivo e ferramenta prática. |
| 15-16 | Próximos Passos & Obrigado | 20s | Encerramento, agradecimentos e visão de futuro. |
| **Total** | | **~290s (4m 50s)** | |

---

### Script Detalhado

**(Slide 1: Capa - 10s)**
> "Olá a todos. Nosso projeto para o Datathon FIAP se concentra em usar a ciência de dados para apoiar a incrível missão da Associação Passos Mágicos: transformar vidas através da educação."

**(Slide 2: Contexto - 20s)**
> "A Passos Mágicos atua há mais de 30 anos em Embu-Guaçu, oferecendo um futuro melhor para crianças e jovens. O trabalho deles é a inspiração para este projeto, que busca usar os dados que eles já coletam para potencializar ainda mais seu impacto."

**(Slide 3: O Desafio - 15s)**
> "Nosso desafio foi claro: como podemos usar os dados para identificar, de forma precoce, os alunos com maior risco de defasagem escolar? O objetivo é criar uma solução que ajude a equipe pedagógica a intervir antes que o problema se agrave."

**(Slide 4: Nossos Dados - 15s)**
> "Para isso, analisamos a Pesquisa de Desenvolvimento Educacional de 2022 a 2024, um rico dataset com mais de mil alunos e dezenas de indicadores, como desempenho, engajamento e aspectos psicossociais."

**(Slide 5-8: Análise Exploratória - 60s)**
> "Nossa análise revelou insights poderosos. Primeiro, vimos uma **redução de 17% na defasagem média** de 2022 para 2024, mostrando o impacto positivo do trabalho da ONG. Descobrimos que o **Engajamento** é o indicador mais correlacionado com o sucesso geral do aluno. E o **Ponto de Virada**, que mede uma mudança positiva de atitude, também se mostrou um fator crucial de recuperação."

**(Slide 9-10: Modelo Preditivo - 60s)**
> "Com base nesses insights, construímos um modelo de Machine Learning usando Random Forest para prever o risco de defasagem. Nosso modelo alcançou um **Recall de 87%**, o que significa que ele consegue identificar corretamente 9 em cada 10 alunos em risco, permitindo uma ação preventiva muito eficaz. As três variáveis mais importantes para o modelo foram o **IAN**, que mede a defasagem, a **média dos indicadores** e o **Ponto de Virada**."

**(Slide 11-12: Aplicação Streamlit - 40s)**
> "Para transformar essa análise em algo prático, desenvolvemos uma aplicação com Streamlit. Com ela, a equipe pedagógica pode visualizar os dados em um dashboard interativo e, o mais importante, inserir os dados de um aluno e receber uma predição instantânea do seu nível de risco, junto com recomendações de ação."

**(Slide 13: Recomendações - 30s)**
> "Nossas recomendações são diretas: para os alunos em risco, sugerimos acompanhamento intensivo e suporte psicossocial. Para a organização, recomendamos usar a ferramenta para triagem preditiva e focar em programas que aumentem o engajamento, o principal motor de desenvolvimento que identificamos."

**(Slide 14: Conclusões - 20s)**
> "Em resumo, este projeto entrega uma análise completa, um modelo preditivo de alta sensibilidade e uma ferramenta interativa pronta para uso, transformando dados em insights acionáveis para o dia a dia da Passos Mágicos."

**(Slide 15-16: Próximos Passos & Obrigado - 20s)**
> "Como próximos passos, sugerimos enriquecer o modelo com mais dados e criar alertas automáticos. Agradecemos à Passos Mágicos, à FIAP e a todos os mentores por esta oportunidade de gerar impacto real. Obrigado!"
