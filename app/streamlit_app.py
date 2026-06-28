"""
Interface da camada de IA — persona "Ana" conversando com os dados.
Rode com:  streamlit run app/streamlit_app.py
"""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Deploy: traz os secrets do Streamlit Cloud para variaveis de ambiente
# (localmente isso e ignorado, pois usamos o arquivo .env).
import os
try:
    for _k in ("GEMINI_API_KEY", "GEMINI_MODEL"):
        if _k in st.secrets:
            os.environ[_k] = str(st.secrets[_k])
except Exception:
    pass

from ai.agent import perguntar, MODEL     # noqa: E402
from ai.tools import get_kpi, DB_PATH     # noqa: E402
from ai import rag                        # noqa: E402

import base64

ASSETS = Path(__file__).resolve().parent / "assets"
ANA_AVATAR = str(ASSETS / "ana_avatar.png")
USER_AVATAR = str(ASSETS / "user_avatar.png")
ANA_B64 = base64.b64encode(Path(ANA_AVATAR).read_bytes()).decode()


def _extrair_texto(arquivo) -> str:
    """Lê o texto de um upload (.md, .txt ou .pdf)."""
    nome = arquivo.name.lower()
    if nome.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            reader = PdfReader(arquivo)
            return "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception as e:
            return f""  # falha de leitura -> texto vazio
    return arquivo.getvalue().decode("utf-8", errors="ignore")


# ── Configuração da página ─────────────────────────────────────────────
st.set_page_config(
    page_title="Ana — Analista de BI",
    page_icon="📊",
    layout="wide",
)

# Banco: normalmente vem versionado no repo. Se faltar (ex: rodando local sem ETL),
# tenta gerar a partir do CSV — protegido para nao derrubar o app em ambiente
# somente-leitura (Streamlit Cloud).
if not DB_PATH.exists():
    try:
        with st.spinner("Preparando o banco de dados pela primeira vez…"):
            import runpy
            runpy.run_path(str(ROOT / "etl" / "etl.py"), run_name="__main__")
    except Exception:
        st.error(
            "Banco de dados não encontrado e não foi possível gerá-lo neste ambiente. "
            "Garanta que `data/warehouse.db` está versionado no repositório "
            "(rode `python etl/etl.py` localmente e faça commit do arquivo)."
        )
        st.stop()

# ── CSS customizado ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Base ─────────────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
}
.block-container {
    padding-top: 4rem !important;
    padding-bottom: 3rem !important;
    max-width: 900px !important;
}
/* Neutraliza a barra superior padrao do Streamlit (evitava cortar o cabecalho) */
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"] { background: transparent !important; }

/* ── Header HTML ─────────────────────────────────────────────────────── */
.ana-header {
    display: flex;
    align-items: center;
    gap: 16px;
    background: linear-gradient(135deg, #0D2236 0%, #091929 100%);
    border: 1px solid #1D3046;
    border-left: 4px solid #17ABDA;
    border-radius: 12px;
    padding: 18px 24px;
    margin-bottom: 16px;
    position: relative;
    overflow: hidden;
}
.ana-header::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, rgba(23,171,218,0.5) 0%, transparent 70%);
}
.ana-badge {
    width: 52px; height: 52px; min-width: 52px;
    border-radius: 50%;
    overflow: hidden;
    border: 2px solid rgba(23,171,218,0.45);
    box-shadow: 0 4px 18px rgba(23,171,218,0.28);
    flex-shrink: 0;
}
.ana-badge img { width: 100%; height: 100%; object-fit: cover; display: block; }
.ana-text { flex: 1; min-width: 0; }
.ana-title {
    font-size: 19px; font-weight: 700;
    color: #E8EEF3; letter-spacing: -0.35px; line-height: 1.2;
}
.ana-sub {
    font-size: 12px; color: #6A90A8;
    margin-top: 4px; line-height: 1.45;
}
.ana-right {
    display: flex; align-items: center; gap: 8px;
    flex-shrink: 0; margin-left: auto;
}
.ana-dot {
    width: 7px; height: 7px;
    background: #17ABDA; border-radius: 50%;
    animation: live-pulse 2.6s ease-in-out infinite;
}
@keyframes live-pulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(23,171,218,0.5); opacity: 1; }
    55%      { box-shadow: 0 0 0 6px rgba(23,171,218,0); opacity: 0.75; }
}
.ana-pill {
    font-size: 10px; font-weight: 700;
    color: #17ABDA; letter-spacing: 0.1em; text-transform: uppercase;
    background: rgba(23,171,218,0.09);
    border: 1px solid rgba(23,171,218,0.22);
    border-radius: 20px; padding: 4px 12px; white-space: nowrap;
}

/* ── Tela inicial (sem mensagens) ─────────────────────────────────────── */
.ana-empty {
    text-align: center;
    margin: 4.5rem auto 0;
    max-width: 480px;
    padding: 0 1rem;
}
.ana-empty .ana-empty-icon {
    width: 76px; height: 76px; margin: 0 auto 16px;
    border-radius: 50%;
    overflow: hidden;
    border: 2px solid rgba(23,171,218,0.45);
    box-shadow: 0 6px 24px rgba(23,171,218,0.22);
}
.ana-empty .ana-empty-icon img { width: 100%; height: 100%; object-fit: cover; display: block; }
.ana-empty .ana-empty-title {
    color: #D8E6F0; font-size: 16px; font-weight: 600;
}
.ana-empty .ana-empty-sub {
    color: #6A90A8; font-size: 13px; margin-top: 8px; line-height: 1.55;
}

/* ── Sidebar ─────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #0A1520 !important;
    border-right: 1px solid #172438 !important;
}
/* Cobre variações do testid entre versões do Streamlit */
[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"],
[data-testid="stSidebar"] > div > div {
    background-color: #0A1520 !important;
    padding-top: 1.1rem !important;
    padding-bottom: 1rem !important;
}

/* Títulos de seção */
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] h4 {
    color: #17ABDA !important;
    font-size: 0.68rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    margin-bottom: 0.4rem !important;
    margin-top: 0 !important;
}

/* Texto e legendas */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] .stMarkdown p {
    color: #7A9DB5 !important;
    font-size: 0.77rem !important;
    line-height: 1.45 !important;
}
code, [data-testid="stSidebar"] code {
    background: rgba(23,171,218,0.08) !important;
    border: none !important;
    padding: 1px 5px !important;
    border-radius: 4px !important;
    font-size: 0.74rem !important;
    color: #9DCCE0 !important;
}

/* Divisores */
[data-testid="stSidebar"] hr {
    border: none !important;
    border-top: 1px solid #1A2D3E !important;
    margin: 0.65rem 0 !important;
}

/* Labels (toggle, uploader) */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] label p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
    color: #C2D8EA !important;
    font-size: 0.81rem !important;
    font-weight: 500 !important;
}

/* Botões de exemplos */
[data-testid="stSidebar"] .stButton > button {
    background: #0E1D2C !important;
    border: 1px solid #1A2D3E !important;
    color: #97B6CB !important;
    border-radius: 7px !important;
    font-size: 0.77rem !important;
    text-align: left !important;
    padding: 0.45rem 0.7rem !important;
    width: 100% !important;
    margin-bottom: 3px !important;
    line-height: 1.4 !important;
    transition: border-color 0.14s, background 0.14s, color 0.14s !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    border-color: #17ABDA !important;
    background: #132232 !important;
    color: #E8EEF3 !important;
}
[data-testid="stSidebar"] .stButton > button:active {
    background: #1A2D3E !important;
}
[data-testid="stSidebar"] .stButton > button:focus:not(:focus-visible) {
    box-shadow: none !important;
}

/* File uploader */
[data-testid="stFileUploadDropzone"],
[data-testid="stFileUploader"] section {
    background: #0E1D2C !important;
    border: 1px dashed #1A2D3E !important;
    border-radius: 8px !important;
}

/* Status badges customizados (substituem st.success/error) */
.status-badge {
    display: flex;
    align-items: center;
    gap: 7px;
    border-radius: 7px;
    padding: 6px 10px;
    font-size: 0.77rem;
    font-weight: 500;
    margin: 2px 0;
    line-height: 1.4;
}
.status-ok {
    background: rgba(0,112,173,0.13);
    border: 1px solid rgba(23,171,218,0.28);
    color: #8FCCE0;
}
.status-ok::before { content: '✓'; font-weight: 700; color: #17ABDA; }
.status-err {
    background: rgba(200,50,50,0.1);
    border: 1px solid rgba(200,80,80,0.3);
    color: #F0A0A0;
}
.status-err::before { content: '✗'; font-weight: 700; color: #E07070; }

/* ── Chat — mensagens ─────────────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    border-radius: 10px !important;
    padding: 0.65rem 0.9rem !important;
    margin: 0.28rem 0 !important;
    animation: msg-in 0.2s ease;
}
@keyframes msg-in {
    from { opacity: 0; transform: translateY(4px); }
    to   { opacity: 1; transform: translateY(0); }
}
[data-testid="stChatMessage"][data-message-author-role="user"] {
    background: #112030 !important;
    border-left: 3px solid #17ABDA !important;
}
[data-testid="stChatMessage"][data-message-author-role="assistant"] {
    background: #0D1C2A !important;
    border-left: 3px solid #0070AD !important;
}
[data-testid="stChatMessage"] p {
    font-size: 0.89rem !important;
    line-height: 1.6 !important;
    color: #DDE8F0 !important;
}

/* ── Chat — campo de entrada ──────────────────────────────────────────── */
[data-testid="stChatInputContainer"],
[data-testid="stChatInput"] {
    background: #0F1D2B !important;
    border: 1px solid #1A2D3E !important;
    border-radius: 12px !important;
    transition: border-color 0.18s, box-shadow 0.18s !important;
}
[data-testid="stChatInputContainer"]:focus-within,
[data-testid="stChatInput"]:focus-within {
    border-color: #17ABDA !important;
    box-shadow: 0 0 0 2px rgba(23,171,218,0.1) !important;
}
[data-testid="stChatInputContainer"] textarea,
[data-testid="stChatInput"] textarea {
    color: #E8EEF3 !important;
    font-size: 0.88rem !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Expander (evidências SQL) ────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: #091420 !important;
    border: 1px solid #1A2D3E !important;
    border-radius: 8px !important;
    margin-top: 0.5rem !important;
    overflow: hidden !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] details > summary {
    color: #587E97 !important;
    font-size: 0.77rem !important;
    padding: 0.45rem 0.7rem !important;
    cursor: pointer !important;
    transition: color 0.14s !important;
    user-select: none !important;
}
[data-testid="stExpander"] summary:hover { color: #17ABDA !important; }

/* ── Bloco de código SQL ─────────────────────────────────────────────── */
[data-testid="stCodeBlock"],
[data-testid="stCode"],
.stCodeBlock {
    background: #07111A !important;
    border: 1px solid #1A2D3E !important;
    border-radius: 6px !important;
    font-size: 0.76rem !important;
}
[data-testid="stCodeBlock"] pre,
[data-testid="stCode"] pre {
    background: transparent !important;
    font-size: 0.76rem !important;
}

/* ── Spinner ─────────────────────────────────────────────────────────── */
[data-testid="stSpinner"] p,
[data-testid="stSpinner"] span {
    color: #5E8299 !important;
    font-size: 0.82rem !important;
}

/* ── Scrollbar ────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #0B1520; }
::-webkit-scrollbar-thumb { background: #1A2D3E; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #17ABDA; }
</style>
""", unsafe_allow_html=True)

# ── Cabeçalho ─────────────────────────────────────────────────────────
st.markdown(f"""
<div class="ana-header">
  <div class="ana-badge"><img src="data:image/png;base64,{ANA_B64}" alt="Ana"/></div>
  <div class="ana-text">
    <div class="ana-title">Ana — Analista de BI</div>
    <div class="ana-sub">Receita · Clientes · Produtos · Descontos — respostas com base nos dados reais</div>
  </div>
  <div class="ana-right">
    <div class="ana-dot"></div>
    <div class="ana-pill">Capgemini</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Barra lateral: status + RAG + exemplos ────────────────────────────
with st.sidebar:
    st.subheader(":material/database: Status")
    st.caption(f"Banco: `{DB_PATH.name}`")
    st.caption(f"Modelo: `{MODEL}`")
    if DB_PATH.exists():
        st.markdown('<div class="status-badge status-ok">Banco conectado</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-badge status-err">Banco não encontrado — rode <code>python etl/etl.py</code></div>',
                    unsafe_allow_html=True)

    st.divider()
    usar_rag = st.toggle(
        ":material/hub: Incluir contexto de negócio (RAG)",
        value=False,
        help="Quando ligado, a Ana também consulta um documento de regras de negócio "
             "(definições, políticas, playbooks) além dos dados.",
    )

    base_rag = None
    if usar_rag:
        upload = st.file_uploader(
            ":material/upload_file: Documento de regras (opcional)",
            type=["md", "txt", "pdf"],
            help="Suba o seu próprio documento de negócio. Se não enviar, "
                 "a Ana usa o manual padrão do projeto.",
        )
        if upload is not None:
            chave = f"{upload.name}-{upload.size}"
            if st.session_state.get("rag_chave") != chave:
                texto = _extrair_texto(upload)
                if texto.strip():
                    st.session_state.base_rag = rag.construir_base(texto, origem=upload.name)
                    st.session_state.rag_chave = chave
                else:
                    st.warning("Não consegui ler texto desse arquivo.")
                    st.session_state.base_rag = None
            base_rag = st.session_state.get("base_rag")
            if base_rag is not None:
                st.caption(f":material/description: Base ativa: **{base_rag.origem}** ({base_rag.modo})")
        else:
            st.caption(":material/description: Base ativa: **manual padrão do projeto**")

    st.divider()
    st.subheader(":material/lightbulb: Exemplos de perguntas")
    exemplos = [
        "Quem são meus clientes mais valiosos e quanto representam?",
        "A política de desconto está saudável?",
        "Quais categorias dão mais lucro?",
        "Qual estado tem a maior receita?",
        "Qual a margem por fornecedor?",
    ]
    for ex in exemplos:
        if st.button(ex, use_container_width=True):
            st.session_state.pendente = ex

# ── Estado da conversa ─────────────────────────────────────────────────
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []


def _exibir(texto: str):
    """Exibe texto escapando o cifrão para o Streamlit não interpretar como LaTeX."""
    st.markdown(texto.replace("$", "\\$"))


# Tela inicial quando ainda nao ha conversa
if not st.session_state.mensagens:
    st.markdown(f"""
    <div class="ana-empty">
      <div class="ana-empty-icon"><img src="data:image/png;base64,{ANA_B64}" alt="Ana"/></div>
      <div class="ana-empty-title">Converse com a Ana sobre os seus dados</div>
      <div class="ana-empty-sub">
        Pergunte sobre receita, clientes, produtos ou descontos —
        ou escolha um exemplo na barra lateral. Toda resposta vem dos dados reais.
      </div>
    </div>
    """, unsafe_allow_html=True)

# Renderiza histórico
for m in st.session_state.mensagens:
    avatar = USER_AVATAR if m["role"] == "user" else ANA_AVATAR
    with st.chat_message(m["role"], avatar=avatar):
        _exibir(m["content"])
        if m.get("evidencias"):
            with st.expander(":material/search: Ver evidência (consultas executadas)"):
                for e in m["evidencias"]:
                    st.markdown(f"**{e['ferramenta']}** → _{e['resumo']}_")
                    if e["entrada"] and e["entrada"] != "-":
                        st.code(e["entrada"], language="sql")

# ── Entrada do usuário ─────────────────────────────────────────────────
pergunta = st.chat_input("Pergunte algo sobre os dados…")
if "pendente" in st.session_state and not pergunta:
    pergunta = st.session_state.pop("pendente")

if pergunta:
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    with st.chat_message("user", avatar=USER_AVATAR):
        _exibir(pergunta)

    historico = [
        ("user" if m["role"] == "user" else "model", m["content"])
        for m in st.session_state.mensagens[:-1]
    ]

    with st.chat_message("assistant", avatar=ANA_AVATAR):
        with st.spinner("Ana está consultando os dados…"):
            try:
                resposta, evidencias = perguntar(pergunta, historico,
                                                 usar_rag=usar_rag, base_rag=base_rag)
            except Exception as e:
                resposta, evidencias = f"⚠️ Erro: {e}", []
        _exibir(resposta)
        if evidencias:
            with st.expander(":material/search: Ver evidência (consultas executadas)"):
                for e in evidencias:
                    st.markdown(f"**{e['ferramenta']}** → _{e['resumo']}_")
                    if e["entrada"] and e["entrada"] != "-":
                        st.code(e["entrada"], language="sql")

    st.session_state.mensagens.append(
        {"role": "assistant", "content": resposta, "evidencias": evidencias}
    )
