# Medidas DAX + Layout das páginas

> Cole cada medida no Power BI: **Home → New Measure**, apague o texto padrão e cole o bloco. Crie todas na tabela `fact_sales` (clique nela antes).

---

## Medidas principais

```dax
Receita Total = SUM(fact_sales[sales])
```

```dax
Lucro Total = SUM(fact_sales[profit])
```

```dax
Margem % = DIVIDE([Lucro Total], [Receita Total])
```
> Depois de criar, selecione a medida e formate como **Percentage** (aba Measure tools → Format → %).

```dax
Qtd Pedidos = DISTINCTCOUNT(fact_sales[order_id])
```

```dax
Qtd Clientes = DISTINCTCOUNT(fact_sales[customer_id])
```

```dax
Ticket Medio = DIVIDE([Receita Total], [Qtd Pedidos])
```

```dax
Qtd Vendida = SUM(fact_sales[quantity])
```

```dax
Desconto Medio = AVERAGE(fact_sales[discount])
```

---

## Medidas de RFM (clientes de alto valor)

```dax
Receita Campeoes =
CALCULATE(
    [Receita Total],
    FILTER(rfm_clientes, rfm_clientes[segmento] = "Campeoes")
)
```

```dax
% Receita Campeoes = DIVIDE([Receita Campeoes], [Receita Total])
```
> Formate como Percentage. Esse número (~40%) é o destaque da história: poucos clientes, muita receita.

```dax
Clientes Campeoes =
CALCULATE(
    DISTINCTCOUNT(rfm_clientes[customer_id]),
    rfm_clientes[segmento] = "Campeoes"
)
```

---

## (Opcional) Tabela Calendário para inteligência temporal

Se quiser comparações tipo "mês a mês" ou usar uma hierarquia de data bonita, crie uma tabela calendário: **Modeling → New Table**:

```dax
Calendario =
ADDCOLUMNS(
    CALENDAR(MIN(fact_sales[order_date]), MAX(fact_sales[order_date])),
    "Ano", YEAR([Date]),
    "Mes", FORMAT([Date], "MMM"),
    "AnoMes", FORMAT([Date], "YYYY-MM"),
    "NumMes", MONTH([Date])
)
```
Depois relacione `Calendario[Date]` → `fact_sales[order_date]` (1 → muitos). Lembre de ordenar a coluna `Mes` pela `NumMes` (Sort by column).

> Para 4 dias, isso é opcional. Os visuais funcionam usando `order_date` diretamente.

---

## Layout das páginas

### Página 1 — Visão Executiva
**Topo: 5 cartões (visual "Card")**, lado a lado:
- Receita Total · Lucro Total · Margem % · Ticket Medio · Qtd Pedidos

**Meio-esquerda: gráfico de linhas** — Tendência da receita
- Eixo X: `fact_sales[order_date]` (ou `Calendario[AnoMes]`) · Eixo Y: `[Receita Total]`

**Meio-direita: mapa** — Receita por estado
- Visual "Map" ou "Filled map" · Location: `fact_sales[state]` · Size/Color: `[Receita Total]`

**Base: gráfico de barras** — Receita por categoria
- Eixo: `dim_product[category]` · Valor: `[Receita Total]` · cor por `[Margem %]`

**Slicers (filtros) no topo/lateral:** `order_date` (ano), `region`, `category`

---

### Página 2 — Clientes (RFM)
**Cartões:** `% Receita Campeoes`, `Clientes Campeoes`, `Qtd Clientes`

**Gráfico de barras (principal):** Receita por segmento RFM
- Eixo: `rfm_clientes[segmento]` · Valor: `[Receita Total]`
- Ordene do maior pro menor — visualmente mostra Campeões + Leais dominando

**Tabela:** Top 10 clientes
- Colunas: `dim_customer[customer_name]`, `dim_customer[segment]`, `[Receita Total]`, `[Lucro Total]`
- Ordene por Receita desc, filtre Top 10 (Filter pane → Top N)

**Gráfico de dispersão (scatter):** valor × frequência
- X: `rfm_clientes[frequencia]` · Y: `rfm_clientes[valor_monetario]` · legenda: `segmento`

---

### Página 3 — Produtos & Descontos
**Gráfico de barras:** Top 10 produtos por receita
- Eixo: `dim_product[product_name]` · Valor: `[Receita Total]` · Top N = 10

**Treemap:** Receita por categoria → subcategoria
- Group: `category`, Details: `sub_category`, Values: `[Receita Total]`

**Gráfico de dispersão (o insight forte):** Desconto × Lucro
- X: `fact_sales[discount]` · Y: `[Lucro Total]` · detalhes: `dim_product[sub_category]`
- Mostra visualmente que desconto alto → lucro negativo

**Cartão de texto / caixa:** escreva o insight
- *"Descontos acima de 20% levam a prejuízo médio por venda. Política de desconto precisa de teto."*

---

## Dicas de apresentação visual
- **Tema:** Use um tema escuro ou da paleta Capgemini (azul). View → Themes.
- **Títulos claros** em cada visual (não deixe "Sum of sales").
- **Tooltips:** ative para mostrar lucro/margem ao passar o mouse.
- **Consistência com a IA:** o cartão "Receita Total" do Power BI deve mostrar o mesmo número que a IA responde (R$ 2.297.200) — isso é a prova viva da integração na demo.
