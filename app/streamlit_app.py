"""
Interface da camada de IA — persona "Ana" conversando com os dados.
Rode com:  streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path

import streamlit as st

# permite importar o pacote ai/ (raiz do projeto no path)
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ai.agent import perguntar           # noqa: E402
from ai.tools import get_kpi, DB_PATH     # noqa: E402

# ----------------------------------------------------------------------
# Configuracao da pagina
# ----------------------------------------------------------------------
st.set_page_config(page_title="Ana — Analista de BI", page_icon="📊", layout="wide")

AZUL = "#0070AD"
st.markdown(
    f"""
    <div style="background:{AZUL};padding:16px 22px;border-radius:10px;margin-bottom:8px">
      <span style="color:#fff;font-size:24px;font-weight:700">📊 Ana — Analista de BI</span><br>
      <span style="color:#cdeaf7;font-size:14px">
        Pergunte sobre receita, clientes, produtos ou descontos. Toda resposta vem dos dados reais.
      </span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# Barra lateral: status + KPIs + exemplos
# ----------------------------------------------------------------------
with st.sidebar:
    st.subheader("Status")
    st.caption(f"Banco: `{DB_PATH.name}`")
    if DB_PATH.exists():
        st.success("Banco conectado")
    else:
        st.error("Banco nao encontrado — rode `python etl/etl.py`")

    st.divider()
    st.subheader("Exemplos de perguntas")
    exemplos = [
        "Quem sao meus clientes mais valiosos e quanto representam?",
        "A politica de desconto esta saudavel?",
        "Quais categorias dao mais lucro?",
        "Qual estado tem a maior receita?",
        "Qual a margem por fornecedor?",
    ]
    for ex in exemplos:
        if st.button(ex, use_container_width=True):
            st.session_state.pendente = ex

# ----------------------------------------------------------------------
# Estado da conversa
# ----------------------------------------------------------------------
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []  # {role, content, evidencias}

# Renderiza historico
for m in st.session_state.mensagens:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("evidencias"):
            with st.expander("🔎 Ver evidência (consultas executadas)"):
                for e in m["evidencias"]:
                    st.markdown(f"**{e['ferramenta']}** → _{e['resumo']}_")
                    if e["entrada"] and e["entrada"] != "-":
                        st.code(e["entrada"], language="sql")

# ----------------------------------------------------------------------
# Entrada do usuario
# ----------------------------------------------------------------------
pergunta = st.chat_input("Pergunte algo sobre os dados…")
if "pendente" in st.session_state and not pergunta:
    pergunta = st.session_state.pop("pendente")

if pergunta:
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)

    # historico (apenas texto) para dar contexto ao modelo
    historico = [
        ("user" if m["role"] == "user" else "model", m["content"])
        for m in st.session_state.mensagens[:-1]
    ]

    with st.chat_message("assistant"):
        with st.spinner("Ana está consultando os dados…"):
            try:
                resposta, evidencias = perguntar(pergunta, historico)
            except Exception as e:
                resposta, evidencias = f"⚠️ Erro: {e}", []
        st.markdown(resposta)
        if evidencias:
            with st.expander("🔎 Ver evidência (consultas executadas)"):
                for e in evidencias:
                    st.markdown(f"**{e['ferramenta']}** → _{e['resumo']}_")
                    if e["entrada"] and e["entrada"] != "-":
                        st.code(e["entrada"], language="sql")

    st.session_state.mensagens.append(
        {"role": "assistant", "content": resposta, "evidencias": evidencias}
    )
