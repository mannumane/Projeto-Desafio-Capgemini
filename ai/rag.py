"""
RAG — busca no documento de regras de negócio.
------------------------------------------------
Indexa o documento `ai/rag/documento_negocio.md` e devolve os trechos mais
relevantes para uma pergunta. Usado pela Ana para complementar a análise dos
dados com contexto de negócio (definições, políticas, playbooks).

Estratégia de busca:
1. Tenta embeddings semânticos com a API do Gemini (text-embedding-004).
2. Se a API não estiver disponível (sem chave / erro), cai para uma busca
   lexical por sobreposição de termos. Assim o RAG nunca quebra o app.
"""

from pathlib import Path
import os
import re
import math

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DOC_PATH = Path(__file__).resolve().parent / "rag" / "documento_negocio.md"
EMBED_MODEL = os.environ.get("RAG_EMBED_MODEL", "text-embedding-004")

_STOP = set("de da do das dos a o e em um uma para por com que se na no as os à é são ser".split())


def _chunk(texto: str) -> list[str]:
    """Divide o documento em trechos por seção (heading markdown)."""
    partes = re.split(r"\n(?=#{1,6}\s)", texto)
    return [p.strip() for p in partes if p.strip()]


def _titulo(chunk: str) -> str:
    primeira = chunk.splitlines()[0]
    return primeira.lstrip("# ").strip()


def _tokens(texto: str) -> list[str]:
    palavras = re.findall(r"[a-zà-ÿ0-9]+", texto.lower())
    return [p for p in palavras if p not in _STOP and len(p) > 2]


# ----------------------------------------------------------------------
# Embeddings (Gemini) com fallback lexical
# ----------------------------------------------------------------------
def _embed(textos: list[str]):
    """Retorna lista de vetores ou None se a API não estiver disponível."""
    if not os.environ.get("GEMINI_API_KEY"):
        return None
    try:
        from google import genai
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        resp = client.models.embed_content(model=EMBED_MODEL, contents=textos)
        return [e.values for e in resp.embeddings]
    except Exception:
        return None


def _cosseno(a, b) -> float:
    num = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return num / (na * nb) if na and nb else 0.0


def _score_lexical(query_tokens, chunk_set, idf) -> float:
    """Soma o IDF dos termos distintos da pergunta presentes no trecho.
    Pesar por IDF faz termos raros e informativos (ex: 'margem', 'desconto',
    'campeoes') pesarem mais que palavras comuns."""
    return sum(idf.get(t, 0.0) for t in set(query_tokens) if t in chunk_set)


class BaseConhecimento:
    """Índice em memória do documento de negócio."""

    def __init__(self, doc_path: Path = DOC_PATH, texto: str | None = None,
                 origem: str | None = None):
        if texto is None:
            texto = doc_path.read_text(encoding="utf-8") if doc_path.exists() else ""
            self.origem = origem or (doc_path.name if doc_path.exists() else "—")
        else:
            self.origem = origem or "documento enviado"
        self.chunks = _chunk(texto)
        self.vetores = _embed(self.chunks) if self.chunks else None
        self.modo = "embeddings" if self.vetores else "lexical"
        # índice lexical (usado como fallback): conjunto de termos por trecho + IDF
        self._sets = [set(_tokens(c)) for c in self.chunks]
        n = len(self.chunks) or 1
        df = {}
        for s in self._sets:
            for t in s:
                df[t] = df.get(t, 0) + 1
        self._idf = {t: math.log(1 + n / d) for t, d in df.items()}

    def buscar(self, query: str, k: int = 3) -> list[dict]:
        if not self.chunks:
            return []
        if self.vetores:
            qv = _embed([query])
            if qv:
                pares = [(_cosseno(qv[0], v), c) for v, c in zip(self.vetores, self.chunks)]
            else:
                pares = self._lexical(query)
        else:
            pares = self._lexical(query)
        pares.sort(key=lambda x: x[0], reverse=True)
        top = [p for p in pares[:k] if p[0] > 0]
        return [{"titulo": _titulo(c), "texto": c, "score": round(s, 3)} for s, c in top]

    def _lexical(self, query):
        qt = _tokens(query)
        return [(_score_lexical(qt, s, self._idf), c)
                for s, c in zip(self._sets, self.chunks)]


# instância única (carrega uma vez)
_BASE = None


def base() -> BaseConhecimento:
    global _BASE
    if _BASE is None:
        _BASE = BaseConhecimento()
    return _BASE


def construir_base(texto: str, origem: str = "documento enviado") -> BaseConhecimento:
    """Cria uma base de conhecimento a partir de texto cru (ex: upload do usuário)."""
    return BaseConhecimento(texto=texto, origem=origem)


if __name__ == "__main__":
    b = base()
    print(f"modo: {b.modo} | {len(b.chunks)} trechos\n")
    for q in ["o que faço com clientes em risco?", "posso dar 30% de desconto?", "o que é margem?"]:
        print("PERGUNTA:", q)
        for r in b.buscar(q, k=2):
            print(f"  [{r['score']}] {r['titulo']}")
        print()
