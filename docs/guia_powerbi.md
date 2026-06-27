# Guia Power BI — Dashboard conectado ao SQLite (Dia 2)

> **Objetivo:** conectar o Power BI Desktop (Windows) ao banco `data/warehouse.db` via ODBC, montar o modelo, criar as medidas DAX e as 3 páginas do dashboard.
>
> **Por que ODBC:** o Power BI não tem conector nativo de SQLite. O driver ODBC resolve isso — é a forma padrão e funciona com refresh dinâmico (cumpre o requisito "atualizar sem reconstruir").

---

## Passo 0 — Levar o projeto para o Windows

O Power BI roda no Windows, então o banco precisa estar lá. Mais simples e à prova de erro:

1. Copie a pasta **`Projeto Desafio Capgemini`** inteira para o Windows (pen drive, OneDrive, etc.).
2. No Windows, instale Python e rode o ETL lá também, para o `warehouse.db` ficar local ao Power BI:
   ```powershell
   pip install pandas
   python etl\etl.py
   ```
   (Como o `etl.py` é reprodutível, gera um banco idêntico ao do Mac.)

> Alternativa: copiar só o `data\warehouse.db`. Mas ter o projeto inteiro no Windows facilita o refresh depois.

Anote o caminho completo do banco, ex: `C:\Projeto Desafio Capgemini\data\warehouse.db`

---

## Passo 1 — Instalar o driver ODBC de SQLite

1. Baixe o driver de **http://www.ch-werner.de/sqliteodbc/**
2. Pegue a versão **64 bits**: `sqliteodbc_w64.exe` (precisa ser 64-bit para casar com o Power BI Desktop, que é 64-bit).
3. Instale (next, next, finish).

---

## Passo 2 — Criar o DSN (apelido da conexão)

1. No menu Iniciar do Windows, procure por **"ODBC Data Sources (64-bit)"** e abra.
2. Aba **System DSN** (ou User DSN) → botão **Add**.
3. Selecione **"SQLite3 ODBC Driver"** → **Finish**.
4. Preencha:
   - **Data Source Name:** `SuperstoreDB`  (esse nome vamos usar no Power BI)
   - **Database Name:** clique em **Browse** e aponte para `...\data\warehouse.db`
5. **OK** → **OK**. DSN criado.

---

## Passo 3 — Conectar o Power BI

1. Abra o **Power BI Desktop**.
2. **Get Data** → procure **ODBC** → **Connect**.
3. Em "Data Source Name (DSN)", escolha **SuperstoreDB** → **OK**.
4. Se pedir credenciais: na aba **"Default or Custom"**, deixe em branco → **Connect**.
   - **Se reclamar "nome de usuário não especificado"**: vá na aba **"Database"** e digite qualquer valor (ex: usuário `admin`, senha `admin`). O SQLite não tem autenticação e ignora isso — só serve pra satisfazer a tela. → **Connect**.
5. No **Navigator**, marque estas tabelas e views:
   - `fact_sales`  ← tabela fato (obrigatória)
   - `dim_customer`
   - `dim_product`
   - `rfm_clientes`  ← segmentação RFM
   - (opcional, para conferência rápida) `v_kpis_gerais`, `v_rfm_resumo`
6. Clique em **Load** (modo Import). 

> **Import vs DirectQuery:** use **Import** — é mais rápido e estável para o desafio. Para atualizar os dados, basta clicar **Refresh** (Passo 7). Se quiser citar DirectQuery na apresentação como "atualização em tempo real", é possível, mas Import já cumpre o requisito.

---

## Passo 4 — Modelo (relacionamentos)

Vá em **Model view** (ícone à esquerda) e crie estes relacionamentos arrastando os campos:

| De (dimensão) | Para (fato) | Cardinalidade |
|---|---|---|
| `dim_customer[customer_id]` | `fact_sales[customer_id]` | 1 → muitos |
| `dim_product[product_id]` | `fact_sales[product_id]` | 1 → muitos |
| `rfm_clientes[customer_id]` | `dim_customer[customer_id]` | 1 → 1 |

> Geografia (region, state, city) **já está dentro de `fact_sales`** — use esses campos direto, não precisa de tabela separada. Por isso não importamos `dim_geo` (ela não tem uma chave única limpa).

---

## Passo 5 — Medidas DAX

Veja o arquivo **`docs/medidas_dax.md`** — copie e cole cada medida (Home → New Measure). Elas são o coração do dashboard interativo: ao filtrar/segmentar, os KPIs recalculam sozinhos.

---

## Passo 6 — Montar as páginas

Veja o desenho das 3 páginas em **`docs/medidas_dax.md`** (seção "Layout das páginas"). Resumo:
1. **Visão Executiva** — cartões de KPI, tendência mensal, mapa por estado, receita por categoria.
2. **Clientes (RFM)** — segmentos, top clientes, % da receita dos Campeões.
3. **Produtos & Descontos** — top produtos, e o insight de desconto × lucro.

---

## Passo 7 — Atualizar os dados (requisito "sem reconstruir")

Este é o requisito que você demonstra ao vivo:

1. Troque/adicione linhas no CSV `Database CSV\Sample - Superstore.csv`.
2. Rode de novo: `python etl\etl.py` (recria o `warehouse.db`).
3. No Power BI: **Home → Refresh**. Pronto — todos os visuais e KPIs se atualizam, **sem refazer nada** do layout, medidas ou relacionamentos.

> Frase para a apresentação: *"O dashboard não tem dado embutido — ele lê o banco. Atualizar é trocar a fonte e clicar Refresh; e a IA, que lê o mesmo banco, reflete o novo dado na hora."*

---

## Checklist de entrega do Dia 2

- [ ] Driver ODBC instalado, DSN `SuperstoreDB` criado
- [ ] Power BI conectado, tabelas carregadas
- [ ] Relacionamentos do Passo 4 criados
- [ ] Medidas DAX adicionadas
- [ ] 3 páginas montadas com slicers funcionando
- [ ] Refresh testado (troquei o CSV → rodei etl → Refresh → número mudou)
- [ ] Arquivo salvo como `dashboard/dashboard.pbix`
