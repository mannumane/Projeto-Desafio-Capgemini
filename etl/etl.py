"""
ETL — Desafio Capgemini (Data + Analytics + IA)
------------------------------------------------
Le o CSV do Sample Superstore, limpa, modela em esquema estrela e
carrega tudo num banco SQLite (data/warehouse.db) com VIEWS de KPI.

Caracteristicas:
- Idempotente: rodar de novo recria o banco do zero a partir do CSV atual.
  -> Trocar/atualizar o CSV e rodar `python etl.py` = dados atualizados,
     sem reconstruir dashboard nem codigo da IA.
- Fonte unica de verdade: Power BI e a camada de IA leem deste mesmo banco.

Uso:
    python etl.py
"""

from pathlib import Path
import sqlite3
import sys
import pandas as pd

# ----------------------------------------------------------------------
# Caminhos (relativos a raiz do projeto, independente de onde rodar)
# ----------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "Database CSV" / "Sample - Superstore.csv"
DB_PATH = PROJECT_ROOT / "data" / "warehouse.db"


# ----------------------------------------------------------------------
# 1. INGESTAO + LIMPEZA
# ----------------------------------------------------------------------
def carregar_e_limpar(csv_path: Path) -> pd.DataFrame:
    # O Superstore costuma vir em latin-1; utf-8 falha em alguns nomes.
    try:
        df = pd.read_csv(csv_path, encoding="latin-1")
    except FileNotFoundError:
        sys.exit(f"[ERRO] CSV nao encontrado em: {csv_path}")

    # Padroniza nomes de coluna -> snake_case
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"[ \-]+", "_", regex=True)
    )

    # Datas: formato americano M/D/AAAA
    df["order_date"] = pd.to_datetime(df["order_date"], format="%m/%d/%Y", errors="coerce")
    df["ship_date"] = pd.to_datetime(df["ship_date"], format="%m/%d/%Y", errors="coerce")

    # Tipos numericos
    for col in ["sales", "profit", "discount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Int64")

    # postal_code: famoso por ter nulos (Burlington, VT). Vira texto, nulo -> 'N/D'
    df["postal_code"] = df["postal_code"].astype("string").fillna("N/D")

    # Higiene basica
    df = df.drop_duplicates()
    df = df.dropna(subset=["order_date", "sales"])  # registros inutilizaveis
    df["customer_name"] = df["customer_name"].str.strip()
    df["product_name"] = df["product_name"].str.strip()

    # Campos derivados de tempo (uteis pro BI e pra IA)
    df["ano"] = df["order_date"].dt.year
    df["mes"] = df["order_date"].dt.month
    df["ano_mes"] = df["order_date"].dt.strftime("%Y-%m")
    df["dias_envio"] = (df["ship_date"] - df["order_date"]).dt.days

    return df


# ----------------------------------------------------------------------
# 2. MODELAGEM — esquema estrela
# ----------------------------------------------------------------------
def montar_modelo(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    dim_customer = (
        df[["customer_id", "customer_name", "segment"]]
        .drop_duplicates(subset="customer_id")
        .reset_index(drop=True)
    )

    dim_product = (
        df[["product_id", "product_name", "category", "sub_category"]]
        .drop_duplicates(subset="product_id")
        .reset_index(drop=True)
    )

    dim_geo = (
        df[["country", "region", "state", "city", "postal_code"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # Fato: granularidade = linha de item de pedido (1 linha do CSV)
    fact_sales = df[
        [
            "row_id", "order_id", "order_date", "ship_date", "ship_mode",
            "ano", "mes", "ano_mes", "dias_envio",
            "customer_id", "product_id",
            "region", "state", "city", "postal_code",
            "sales", "quantity", "discount", "profit",
        ]
    ].copy()
    # margem por linha (lucro / receita), guardada para conveniencia
    fact_sales["margem"] = (fact_sales["profit"] / fact_sales["sales"]).round(4)

    return {
        "dim_customer": dim_customer,
        "dim_product": dim_product,
        "dim_geo": dim_geo,
        "fact_sales": fact_sales,
    }


# ----------------------------------------------------------------------
# 3. RFM — segmentacao de clientes (materializada como tabela)
# ----------------------------------------------------------------------
def calcular_rfm(df: pd.DataFrame) -> pd.DataFrame:
    data_ref = df["order_date"].max()  # "hoje" do dataset

    rfm = df.groupby(["customer_id", "customer_name"]).agg(
        recencia_dias=("order_date", lambda s: (data_ref - s.max()).days),
        frequencia=("order_id", "nunique"),
        valor_monetario=("sales", "sum"),
        lucro_total=("profit", "sum"),
    ).reset_index()

    # Scores 1-4 por quartil (5 = melhor). Recencia: menor = melhor (labels invertidos)
    def quartil(serie, invertido=False):
        labels = [4, 3, 2, 1] if invertido else [1, 2, 3, 4]
        try:
            return pd.qcut(serie.rank(method="first"), 4, labels=labels).astype(int)
        except ValueError:
            return pd.Series([2] * len(serie), index=serie.index)

    rfm["r_score"] = quartil(rfm["recencia_dias"], invertido=True)
    rfm["f_score"] = quartil(rfm["frequencia"])
    rfm["m_score"] = quartil(rfm["valor_monetario"])
    rfm["rfm_total"] = rfm[["r_score", "f_score", "m_score"]].sum(axis=1)

    def segmentar(row):
        if row["rfm_total"] >= 10:
            return "Campeoes"
        if row["rfm_total"] >= 8:
            return "Leais"
        if row["r_score"] >= 3 and row["f_score"] <= 2:
            return "Promissores"
        if row["r_score"] <= 2 and row["m_score"] >= 3:
            return "Em risco (alto valor)"
        if row["r_score"] <= 2:
            return "Perdidos"
        return "Atencao"

    rfm["segmento"] = rfm.apply(segmentar, axis=1)
    rfm["valor_monetario"] = rfm["valor_monetario"].round(2)
    rfm["lucro_total"] = rfm["lucro_total"].round(2)
    return rfm


# ----------------------------------------------------------------------
# 4. VIEWS DE KPI (mesma fonte que alimenta o Power BI e a IA)
# ----------------------------------------------------------------------
VIEWS_SQL = """
DROP VIEW IF EXISTS v_kpis_gerais;
CREATE VIEW v_kpis_gerais AS
SELECT
    ROUND(SUM(sales), 2)                         AS receita_total,
    ROUND(SUM(profit), 2)                        AS lucro_total,
    ROUND(100.0 * SUM(profit) / SUM(sales), 2)   AS margem_pct,
    COUNT(DISTINCT order_id)                      AS qtd_pedidos,
    COUNT(DISTINCT customer_id)                   AS qtd_clientes,
    ROUND(SUM(sales) / COUNT(DISTINCT order_id), 2) AS ticket_medio
FROM fact_sales;

DROP VIEW IF EXISTS v_receita_mensal;
CREATE VIEW v_receita_mensal AS
SELECT ano_mes,
       ROUND(SUM(sales), 2)  AS receita,
       ROUND(SUM(profit), 2) AS lucro,
       COUNT(DISTINCT order_id) AS pedidos
FROM fact_sales
GROUP BY ano_mes
ORDER BY ano_mes;

DROP VIEW IF EXISTS v_receita_categoria;
CREATE VIEW v_receita_categoria AS
SELECT p.category,
       p.sub_category,
       ROUND(SUM(f.sales), 2)  AS receita,
       ROUND(SUM(f.profit), 2) AS lucro,
       ROUND(100.0 * SUM(f.profit) / SUM(f.sales), 2) AS margem_pct
FROM fact_sales f
JOIN dim_product p ON p.product_id = f.product_id
GROUP BY p.category, p.sub_category
ORDER BY receita DESC;

DROP VIEW IF EXISTS v_receita_regiao;
CREATE VIEW v_receita_regiao AS
SELECT region,
       state,
       ROUND(SUM(sales), 2)  AS receita,
       ROUND(SUM(profit), 2) AS lucro,
       ROUND(100.0 * SUM(profit) / SUM(sales), 2) AS margem_pct
FROM fact_sales
GROUP BY region, state
ORDER BY receita DESC;

DROP VIEW IF EXISTS v_top_produtos;
CREATE VIEW v_top_produtos AS
SELECT p.product_name,
       p.category,
       ROUND(SUM(f.sales), 2)  AS receita,
       ROUND(SUM(f.profit), 2) AS lucro,
       SUM(f.quantity)         AS qtd_vendida
FROM fact_sales f
JOIN dim_product p ON p.product_id = f.product_id
GROUP BY p.product_name, p.category
ORDER BY receita DESC;

DROP VIEW IF EXISTS v_top_clientes;
CREATE VIEW v_top_clientes AS
SELECT c.customer_name,
       c.segment,
       ROUND(SUM(f.sales), 2)  AS receita,
       ROUND(SUM(f.profit), 2) AS lucro,
       COUNT(DISTINCT f.order_id) AS pedidos
FROM fact_sales f
JOIN dim_customer c ON c.customer_id = f.customer_id
GROUP BY c.customer_name, c.segment
ORDER BY receita DESC;

DROP VIEW IF EXISTS v_segmento;
CREATE VIEW v_segmento AS
SELECT c.segment,
       ROUND(SUM(f.sales), 2)  AS receita,
       ROUND(SUM(f.profit), 2) AS lucro,
       COUNT(DISTINCT f.customer_id) AS clientes,
       COUNT(DISTINCT f.order_id)    AS pedidos
FROM fact_sales f
JOIN dim_customer c ON c.customer_id = f.customer_id
GROUP BY c.segment
ORDER BY receita DESC;

DROP VIEW IF EXISTS v_desconto_lucro;
CREATE VIEW v_desconto_lucro AS
SELECT
    CASE
        WHEN discount = 0 THEN '0%'
        WHEN discount <= 0.2 THEN '1-20%'
        WHEN discount <= 0.4 THEN '21-40%'
        WHEN discount <= 0.6 THEN '41-60%'
        ELSE '60%+'
    END AS faixa_desconto,
    COUNT(*)                AS linhas,
    ROUND(AVG(profit), 2)   AS lucro_medio,
    ROUND(SUM(profit), 2)   AS lucro_total
FROM fact_sales
GROUP BY faixa_desconto
ORDER BY faixa_desconto;

DROP VIEW IF EXISTS v_rfm_resumo;
CREATE VIEW v_rfm_resumo AS
SELECT segmento,
       COUNT(*)                          AS qtd_clientes,
       ROUND(SUM(valor_monetario), 2)    AS receita_total,
       ROUND(AVG(valor_monetario), 2)    AS ticket_medio_cliente,
       ROUND(100.0 * SUM(valor_monetario) /
             (SELECT SUM(valor_monetario) FROM rfm_clientes), 2) AS pct_receita
FROM rfm_clientes
GROUP BY segmento
ORDER BY receita_total DESC;
"""


# ----------------------------------------------------------------------
# 5. CARGA NO SQLITE
# ----------------------------------------------------------------------
def carregar_no_banco(tabelas: dict[str, pd.DataFrame], rfm: pd.DataFrame, db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()  # idempotente: recria do zero

    conn = sqlite3.connect(db_path)
    try:
        for nome, tdf in tabelas.items():
            tdf.to_sql(nome, conn, if_exists="replace", index=False)
        rfm.to_sql("rfm_clientes", conn, if_exists="replace", index=False)

        # Indices para acelerar joins/consultas da IA
        cur = conn.cursor()
        cur.execute("CREATE INDEX idx_fact_customer ON fact_sales(customer_id);")
        cur.execute("CREATE INDEX idx_fact_product  ON fact_sales(product_id);")
        cur.execute("CREATE INDEX idx_fact_anomes   ON fact_sales(ano_mes);")

        # Views de KPI
        cur.executescript(VIEWS_SQL)
        conn.commit()
    finally:
        conn.close()


# ----------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------
def main():
    print(f"[1/4] Lendo e limpando: {CSV_PATH.name}")
    df = carregar_e_limpar(CSV_PATH)
    print(f"      -> {len(df):,} linhas validas")

    print("[2/4] Montando esquema estrela...")
    tabelas = montar_modelo(df)
    for nome, tdf in tabelas.items():
        print(f"      -> {nome}: {len(tdf):,} linhas")

    print("[3/4] Calculando RFM...")
    rfm = calcular_rfm(df)
    print(f"      -> {len(rfm):,} clientes segmentados")

    print(f"[4/4] Carregando no banco: {DB_PATH}")
    carregar_no_banco(tabelas, rfm, DB_PATH)
    print("\nOK. Banco pronto. Conecte o Power BI e a IA em data/warehouse.db")


if __name__ == "__main__":
    main()
