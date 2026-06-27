"""
Ferramentas (tools) que a IA usa para consultar o banco.
------------------------------------------------------------
Estas funcoes sao a PONTE entre o modelo de linguagem e os dados reais.
O Gemini decide quando chamar cada uma; nos executamos no SQLite e
devolvemos as linhas. Assim toda resposta da IA tem base factual.

Tres ferramentas:
- get_schema()        -> mostra ao modelo as tabelas/colunas disponiveis
- query_database(sql) -> executa um SELECT (somente leitura) e retorna os dados
- get_kpi(nome)       -> atalho para KPIs ja calculados (views)

Seguranca: query_database so aceita SELECT (somente leitura), bloqueia
qualquer comando de escrita e limita o numero de linhas retornadas.

Evidencia: toda chamada e registrada em EXECUTION_LOG, que a interface
(Streamlit) exibe como "evidencia" da resposta.
"""

from pathlib import Path
import os
import re
import sqlite3
import json

# ----------------------------------------------------------------------
# Localizacao do banco (permite override por variavel de ambiente)
# ----------------------------------------------------------------------
_DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "warehouse.db"
DB_PATH = Path(os.environ.get("DB_PATH", _DEFAULT_DB))

MAX_LINHAS = 100  # teto de linhas devolvidas ao modelo

# Trilha de evidencia: cada item = {ferramenta, entrada, resultado_resumo}
EXECUTION_LOG: list[dict] = []


def _conectar_ro() -> sqlite3.Connection:
    """Conexao SOMENTE LEITURA (read-only) ao banco."""
    uri = f"file:{DB_PATH}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _registrar(ferramenta: str, entrada: str, resumo: str):
    EXECUTION_LOG.append({"ferramenta": ferramenta, "entrada": entrada, "resumo": resumo})


# ----------------------------------------------------------------------
# 1. get_schema
# ----------------------------------------------------------------------
def get_schema() -> str:
    """Retorna o esquema do banco de dados: todas as tabelas e views com suas
    colunas. Use esta ferramenta PRIMEIRO quando precisar saber quais dados
    existem antes de escrever uma consulta SQL.

    Returns:
        Texto descrevendo tabelas, views e colunas disponiveis.
    """
    con = _conectar_ro()
    try:
        cur = con.cursor()
        objetos = cur.execute(
            "SELECT name, type FROM sqlite_master "
            "WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' "
            "ORDER BY type, name"
        ).fetchall()
        linhas = []
        for nome, tipo in objetos:
            cols = [c[1] for c in cur.execute(f"PRAGMA table_info('{nome}')").fetchall()]
            linhas.append(f"[{tipo.upper()}] {nome}({', '.join(cols)})")
        texto = "\n".join(linhas)
    finally:
        con.close()
    _registrar("get_schema", "-", f"{len(objetos)} objetos")
    return texto


# ----------------------------------------------------------------------
# 2. query_database  (somente SELECT)
# ----------------------------------------------------------------------
_PROIBIDO = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|attach|detach|"
    r"pragma|vacuum|reindex|truncate)\b",
    re.IGNORECASE,
)


def query_database(sql: str) -> str:
    """Executa uma consulta SQL de LEITURA (SELECT) no banco de vendas e
    retorna as linhas resultantes. Use para responder qualquer pergunta
    quantitativa sobre receita, lucro, clientes, produtos, regioes, descontos
    ou segmentacao RFM. Escreva SQL valido para SQLite.

    Args:
        sql: uma unica instrucao SELECT (ou WITH ... SELECT). Nao use comandos
             de escrita; eles serao rejeitados.

    Returns:
        As linhas em formato JSON (lista de objetos). Se nao houver resultado,
        retorna uma lista vazia. Em caso de erro, retorna a mensagem de erro.
    """
    sql_limpo = sql.strip().rstrip(";").strip()

    # Guard-rails de seguranca (somente leitura)
    if not re.match(r"^(select|with)\b", sql_limpo, re.IGNORECASE):
        msg = "ERRO: apenas consultas SELECT sao permitidas."
        _registrar("query_database", sql, msg)
        return msg
    if ";" in sql_limpo:
        msg = "ERRO: execute apenas uma instrucao por vez (sem ';')."
        _registrar("query_database", sql, msg)
        return msg
    if _PROIBIDO.search(sql_limpo):
        msg = "ERRO: comando de escrita/DDL nao permitido (somente leitura)."
        _registrar("query_database", sql, msg)
        return msg

    con = _conectar_ro()
    try:
        con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute(sql_limpo)
        rows = cur.fetchmany(MAX_LINHAS + 1)
        dados = [dict(r) for r in rows[:MAX_LINHAS]]
        truncado = len(rows) > MAX_LINHAS
    except sqlite3.Error as e:
        msg = f"ERRO de SQL: {e}"
        _registrar("query_database", sql, msg)
        return msg
    finally:
        con.close()

    resultado = json.dumps(dados, ensure_ascii=False, default=str)
    if truncado:
        resultado += f"\n(resultado truncado nas primeiras {MAX_LINHAS} linhas)"
    _registrar("query_database", sql_limpo, f"{len(dados)} linha(s)")
    return resultado


# ----------------------------------------------------------------------
# 3. get_kpi  (atalhos para as views ja calculadas)
# ----------------------------------------------------------------------
_KPIS = {
    "kpis_gerais": "SELECT * FROM v_kpis_gerais",
    "receita_mensal": "SELECT * FROM v_receita_mensal",
    "receita_categoria": "SELECT * FROM v_receita_categoria",
    "receita_regiao": "SELECT * FROM v_receita_regiao",
    "top_produtos": "SELECT * FROM v_top_produtos LIMIT 10",
    "top_clientes": "SELECT * FROM v_top_clientes LIMIT 10",
    "segmento": "SELECT * FROM v_segmento",
    "desconto_lucro": "SELECT * FROM v_desconto_lucro",
    "rfm_resumo": "SELECT * FROM v_rfm_resumo",
}


def get_kpi(nome: str) -> str:
    """Retorna um indicador (KPI) ja calculado, a partir das views do banco.
    Prefira esta ferramenta a escrever SQL quando o KPI desejado existir, pois
    garante consistencia com o dashboard Power BI.

    Args:
        nome: um de: kpis_gerais, receita_mensal, receita_categoria,
              receita_regiao, top_produtos, top_clientes, segmento,
              desconto_lucro, rfm_resumo.

    Returns:
        As linhas do KPI em JSON, ou a lista de nomes validos se o nome for invalido.
    """
    chave = nome.strip().lower()
    if chave not in _KPIS:
        msg = "KPI invalido. Validos: " + ", ".join(_KPIS)
        _registrar("get_kpi", nome, msg)
        return msg
    return query_database(_KPIS[chave])


# Lista de ferramentas exportadas para o agente
TOOLS = [get_schema, query_database, get_kpi]


if __name__ == "__main__":
    # Teste rapido manual
    print("SCHEMA:\n", get_schema()[:500], "\n")
    print("KPIs gerais:\n", get_kpi("kpis_gerais"), "\n")
    print("Query:\n", query_database("SELECT segmento, qtd_clientes FROM v_rfm_resumo"))
    print("Guard:\n", query_database("DROP TABLE fact_sales"))
