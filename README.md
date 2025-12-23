# ⚽ Bolão Copa do Mundo 2026

Sistema completo para gerenciar o bolão da família para a Copa do Mundo 2026.

## 🎮 Dados Pré-Cadastrados

O sistema já vem com todos os dados da Copa 2026:
- **48 seleções** cadastradas com bandeiras (emoji)
- **128 jogos** da tabela oficial da FIFA
- **Horários em Brasília** (convertidos do fuso horário original)
- **12 grupos** (A até L)
- **Todas as fases**: Grupos, Oitavas (32 e 16), Quartas, Semifinais, 3º Lugar e Final

## 🚀 Como Usar

### Passo 1: Extrair os arquivos
Extraia o conteúdo do ZIP em uma pasta de sua preferência, por exemplo:
- Windows: `C:\Bolao2026`
- Mac/Linux: `~/Bolao2026`

**⚠️ IMPORTANTE**: Evite pastas com espaços ou acentos no nome.

### Passo 2: Abrir o terminal
- **Windows**: Abra o Prompt de Comando (digite `cmd` no menu Iniciar)
- **Mac/Linux**: Abra o Terminal

### Passo 3: Navegar até a pasta do projeto
```bash
cd C:\Bolao2026
```

### Passo 4: Criar ambiente virtual (recomendado)
```bash
python -m venv venv
```

Ativar o ambiente:
- **Windows**: `venv\Scripts\activate`
- **Mac/Linux**: `source venv/bin/activate`

### Passo 5: Instalar dependências
```bash
pip install -r requirements.txt
```

### Passo 6: Executar o aplicativo
```bash
streamlit run app.py
```

O terminal mostrará um endereço (ex: `http://localhost:8501`). Abra no navegador.

## 🔐 Primeiro Acesso

Na primeira execução, o sistema cria automaticamente um usuário administrador:

- **Usuário**: `admin`
- **Senha**: `admin`

⚠️ **Importante**: Altere a senha do admin após o primeiro acesso!

## 👥 Cadastro de Participantes

Existem duas formas de cadastrar participantes:

### 1. Auto-cadastro
Os participantes podem criar sua própria conta clicando em **"Criar minha conta"** na tela de login.

### 2. Cadastro pelo administrador
O administrador pode cadastrar participantes manualmente no painel **Admin > Participantes**.

## 📱 Funcionalidades

### Para Participantes:
- ✅ Criar conta própria (auto-cadastro)
- ✅ Login com usuário e senha
- ✅ Fazer palpites para os jogos (editáveis até o início de cada partida)
- ✅ Fazer palpites de classificação dos grupos (1º e 2º de cada grupo)
- ✅ Fazer palpites de pódio (campeão, vice, 3º lugar)
- ✅ Ver ranking em tempo real
- ✅ Acompanhar estatísticas pessoais
- ✅ Alterar senha

### Para o Administrador:
- ✅ Cadastrar/gerenciar participantes
- ✅ Editar seleções (nome, bandeira)
- ✅ Editar jogos (times, data, horário, cidade)
- ✅ Lançar resultados oficiais
- ✅ Definir classificados de cada grupo
- ✅ Definir pódio final (campeão, vice, 3º)
- ✅ Configurar todas as pontuações
- ✅ Configurar premiação
- ✅ Definir data de início da Copa (bloqueia palpites de pódio)
- ✅ Editar palpites de qualquer participante

## 📊 Sistema de Pontuação (Ajustável)

### Pontuação por Jogo:
| Acerto | Pontos (padrão) |
|--------|-----------------|
| Placar exato | 20 pts |
| Resultado + gols de um time | 15 pts |
| Apenas resultado (vencedor/empate) | 10 pts |
| Apenas gols de um time | 5 pts |
| Errou tudo | 0 pts |

### Pontuação de Classificação dos Grupos:
| Acerto | Pontos (padrão) |
|--------|-----------------|
| Acertou 1º e 2º na ordem correta | 20 pts |
| Acertou os 2 classificados (ordem invertida) | 10 pts |
| Acertou 1 classificado (posição errada) | 5 pts |

### Pontuação do Pódio:
| Acerto | Pontos (padrão) |
|--------|-----------------|
| Pódio completo na ordem exata | 150 pts |
| Acertar o Campeão | 100 pts |
| Acertar o Vice-Campeão | 50 pts |
| Acertar o 3º Lugar | 30 pts |
| Pódio fora de ordem | 20 pts |

*Todos os valores podem ser alterados pelo administrador no painel Admin > Pontuação.*

## 🏆 Critérios de Desempate

Em ordem de prioridade:
1. Maior pontuação total
2. Mais acertos de placares exatos
3. Mais acertos de resultado + gols de uma equipe
4. Mais acertos de resultado sem gols
5. Mais acertos de gols de uma equipe
6. Menos palpites zerados
7. Ordem de inscrição

## ⏰ Regras de Prazos

### Palpites de Jogos:
- Podem ser alterados até o horário de início de cada partida
- Após o início, o palpite é automaticamente bloqueado

### Palpites de Grupos:
- Podem ser feitos/alterados a qualquer momento antes do fim da fase de grupos

### Palpites de Pódio:
- Podem ser alterados até a **data de início da Copa** (11/06/2026 13:00 - configurável pelo admin)
- Após essa data, ficam bloqueados

## 💰 Premiação

A premiação é totalmente configurável pelo administrador:
- Valor de inscrição
- Prêmio 1º, 2º e 3º lugar
- Observações adicionais

## 🔧 Edição de Jogos

Se a FIFA alterar algum jogo (data, horário, times), o administrador pode:
1. Acessar **Admin > Jogos**
2. Expandir o jogo desejado
3. Alterar times, data, horário ou cidade
4. Clicar em **Salvar Alterações**

As alterações são refletidas automaticamente para todos os participantes.

## 🌐 Deploy (Publicar na Internet)

### Opção 1: Streamlit Community Cloud (Gratuito)
1. Crie uma conta no [GitHub](https://github.com)
2. Suba o projeto para um repositório no GitHub
3. Acesse [share.streamlit.io](https://share.streamlit.io)
4. Conecte seu repositório
5. Deploy!

### Opção 2: Com Banco PostgreSQL (Recomendado para produção)
1. Crie um banco gratuito em [Supabase](https://supabase.com), [Neon](https://neon.tech) ou [Railway](https://railway.app)
2. Copie a string de conexão do banco
3. Defina a variável de ambiente `DATABASE_URL`:

**Windows:**
```bash
set DATABASE_URL=postgresql://usuario:senha@host:porta/banco
streamlit run app.py
```

**Mac/Linux:**
```bash
export DATABASE_URL=postgresql://usuario:senha@host:porta/banco
streamlit run app.py
```

## 📁 Estrutura do Projeto

```
bolao2026/
├── app.py              # Aplicativo principal (interface Streamlit)
├── models.py           # Modelos do banco de dados
├── db.py               # Conexão com banco de dados
├── auth.py             # Autenticação de usuários
├── scoring.py          # Lógica de pontuação e ranking
├── config.py           # Configurações padrão
├── copa2026_data.py    # Dados da Copa 2026 (seleções e jogos)
├── requirements.txt    # Dependências Python
├── bolao2026.db        # Banco de dados SQLite (criado automaticamente)
└── README.md           # Este arquivo
```

## ❓ Problemas Comuns

### "ModuleNotFoundError"
Certifique-se de que instalou as dependências:
```bash
pip install -r requirements.txt
```

### "O sistema não pode encontrar o caminho"
Verifique se você está na pasta correta.

### "database is locked" (SQLite)
Isso pode acontecer com muitos acessos simultâneos. Para uso em produção, use PostgreSQL.

## 📞 Suporte

Em caso de dúvidas ou problemas, entre em contato com o administrador do bolão.

---

**Bom bolão e que vença o melhor! 🏆**
