# Desafio Técnico — Data + Analytics + IA

Solução de análise de dados de vendas (varejo) com uma camada de IA capaz de interpretar os dados e responder perguntas de negócio **com base em evidências reais extraídas do próprio banco**.

> Projeto desenvolvido como case de consultoria em Data & AI.

## 🚀 Aplicação publicada

**Converse com a Ana (app web):** https://projeto-desafio-capgemini.streamlit.app

> Obs.: o app está hospedado no Streamlit Community Cloud (tier gratuito). Se ele estiver hibernando por inatividade, clique em **"Yes, get this app back up!"** e aguarde alguns segundos até ele acordar.

---

## 1. Problema abordado

Uma empresa de varejo precisa transformar dados de vendas em **insights acionáveis** e explorar IA para apoiar decisões. As perguntas de negócio que a solução responde:

- Qual a receita, o lucro e a margem do negócio? Como evoluem no tempo?
- Quem são os clientes mais valiosos e quanto representam da receita?
- Quais produtos e categorias trazem mais receita e lucro?
- A política de descontos está saudável ou corroendo o lucro?
- Onde (regiões/estados) estão as maiores oportunidades?

## 2. Base de dados

**Sample Superstore** (dataset público, ~10.000 linhas de pedidos de varejo nos EUA, 2014–2017). Contém pedidos, clientes, produtos, geografia, vendas, quantidade, desconto e **lucro** — o que permite análises de receita, margem, segmentação de clientes (RFM) e política de descontos.

Localização: `Database CSV/Sample - Superstore.csv`

## 3. Arquitetura da solução

O princípio central é uma **fonte única de verdade**: um banco SQLite que alimenta tanto o dashboard quanto a IA. Assim, dashboard e IA sempre falam dos mesmos números.

```
  CSV bruto
     │
     ▼
  ETL (Python/pandas)  ──►  Banco SQLite (warehouse.db)
                              ├── tabelas (esquema estrela)
                              └── views de KPI
                                     │
                  ┌──────────────────┴──────────────────┐
                  ▼                                      ▼
            Power BI                              App de IA (persona)
         (dashboard)                          tool calling → SQL no banco
```

- **Camada de dados:** `etl.py` lê o CSV, limpa, modela em esquema estrela (`fact_sales` + dimensões), calcula RFM e gera views de KPI no SQLite. Pipeline **idempotente** — rodar de novo recria o banco a partir do CSV atual.
- **Camada de visualização:** Power BI conectado ao SQLite via ODBC (Import + Refresh). Atualizar dados = trocar o CSV, rodar `etl.py` e dar Refresh — sem reconstruir o dashboard.
- **Camada de IA:** persona sintética que consulta o banco via *tool calling* (SQL) e responde sempre com número + evidência. *(detalhes na seção 6)*

## 4. Estrutura do repositório

```
.
├── README.md
├── requirements.txt
├── Database CSV/           # dataset de origem
├── etl/etl.py              # pipeline ETL -> SQLite
├── data/warehouse.db       # banco gerado (não versionado; rode etl.py)
├── sql/                    # (queries auxiliares)
├── dashboard/              # dashboard.pbix (Power BI)
├── ai/                     # camada de IA
│   ├── persona.py/.md      # persona "Ana" + system prompt
│   ├── tools.py            # ferramentas (SQL) que tocam o banco
│   ├── agent.py            # agente Gemini (tool calling + RAG)
│   ├── rag.py              # busca no documento de negócio
│   └── rag/documento_negocio.md  # base de conhecimento (regras de negócio)
├── app/                    # interface (Streamlit)
└── docs/                   # guias e documentação
    ├── guia_powerbi.md
    └── medidas_dax.md
```

## 5. Como executar

**Pré-requisitos:** Python 3.10+ e (para o dashboard) Power BI Desktop no Windows.

```bash
# 1. Ambiente
pip install -r requirements.txt

# 2. Gerar o banco a partir do CSV
python etl/etl.py
# -> cria data/warehouse.db com tabelas e views de KPI

# 3. Dashboard: ver docs/guia_powerbi.md (conexão ODBC ao SQLite)

# 4. App de IA: (instruções na seção 6, a completar no Dia 3)
```

## 6. Como funciona a IA

- **Persona:** "Ana — Analista de BI" — interpreta os dados, responde e sugere ações, sempre embasada. Definição completa em `ai/persona.md`.
- **Arquitetura:** *tool calling* com o modelo **Gemini**. O modelo decide chamar uma das ferramentas (`ai/tools.py`), que executam de verdade no banco:
  - `get_schema()` — lista tabelas/colunas disponíveis.
  - `query_database(sql)` — executa um `SELECT` (somente leitura) e retorna as linhas reais.
  - `get_kpi(nome)` — atalho para as mesmas views de KPI que alimentam o Power BI (garante consistência).
- **Fluxo:** pergunta → o modelo escolhe a ferramenta → executamos no banco → a IA responde citando o resultado.
- **RAG (camada extra, opcional):** além do tool calling sobre os dados, há um RAG sobre um **manual de regras de negócio** (`ai/rag/documento_negocio.md`) — glossário de métricas, definições de RFM, política de descontos e playbooks. No app, um seletor liga/desliga esse contexto: quando ligado, a Ana busca os trechos relevantes (`ai/rag.py`, embeddings Gemini com fallback lexical) e combina regra de negócio + número do banco. Mostra duas técnicas: **tool calling + RAG**.
- **Upload de documento (RAG dinâmico):** o usuário pode subir o próprio documento de regras (`.md`, `.txt` ou `.pdf`) pelo app; a Ana passa a usá-lo como base de conhecimento. Sem upload, usa o manual padrão. Isso torna a solução reutilizável: conecte seus dados, suba suas regras, e a IA analisa.
- **Regra crítica de evidência:** o system prompt (`ai/persona.py`) obriga a IA a consultar o banco antes de responder. Toda resposta traz afirmação + número + fonte. Se o dado não existe, responde *"Com os dados disponíveis, não é possível concluir isso."*
- **Segurança:** `query_database` aceita apenas `SELECT` (conexão read-only), bloqueia comandos de escrita e limita o número de linhas.
- **Interface:** `app/streamlit_app.py` — chat com a Ana e um painel "Ver evidência" que mostra o SQL executado em cada resposta.
- **Canal no Telegram (diferencial):** `app/telegram_bot.py` — a mesma Ana num bot de Telegram. Mostra que o núcleo é **desacoplado do canal**: tanto o app web quanto o Telegram são cascas finas que chamam a mesma função `perguntar()`. Setup do bot:
  ```bash
  # 1. No Telegram, fale com @BotFather -> /newbot -> copie o token
  # 2. Coloque no .env:  TELEGRAM_BOT_TOKEN=seu_token
  pip install -r requirements.txt
  python app/telegram_bot.py
  ```
- **Exemplos reais de perguntas e respostas:** `docs/exemplos_perguntas.md`.

### Como rodar a IA
```bash
cp .env.example .env        # e preencha GEMINI_API_KEY com sua chave (Google AI Studio)
pip install -r requirements.txt
python ai/agent.py                    # teste no terminal
streamlit run app/streamlit_app.py    # interface no navegador
```

## 7. Indicadores gerados (KPIs)

Receita total · Lucro total · Margem % · Ticket médio · Nº de pedidos/clientes · Receita por categoria/região/estado · Top produtos e clientes · Segmentação RFM de clientes · Relação desconto × lucro.

**Destaques do dataset:** receita de ~US$ 2,30M, margem de 12,5%; os clientes "Campeões" (RFM) são ~24% da base e geram ~40% da receita; descontos acima de 20% levam a prejuízo médio por venda.

## 8. Limitações

- A base não contém **custo de produto** (só preço e lucro registrado), então não é possível calcular margem de contribuição por insumo.
- Dataset histórico (2014–2017) e de um único mercado (EUA) — não reflete tempo real.
- A IA responde sobre os dados disponíveis no banco; perguntas fora desse escopo são respondidas com "não é possível concluir".
- Solução em SQLite, voltada ao desafio — não dimensionada para produção/alta escala.
