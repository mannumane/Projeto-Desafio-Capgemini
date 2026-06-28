"""
Agente — integra a persona "Ana" ao Gemini com tool calling.
------------------------------------------------------------
Usa o SDK google-genai. As ferramentas (tools.py) sao passadas ao modelo,
que decide quando chama-las (function calling automatico). Cada execucao
fica registrada em EXECUTION_LOG, devolvido junto da resposta como evidencia.

Variaveis de ambiente (arquivo .env):
    GEMINI_API_KEY = sua chave do Google AI Studio
    GEMINI_MODEL   = (opcional) modelo, padrao gemini-2.5-flash
    DB_PATH        = (opcional) caminho do banco
"""

import os
import time

try:
    from dotenv import load_dotenv
    load_dotenv()  # carrega .env se existir
except ImportError:
    pass

from google import genai
from google.genai import types

# imports relativos ao pacote ai/
try:
    from .tools import TOOLS, EXECUTION_LOG
    from .persona import SYSTEM_PROMPT
    from . import rag
except ImportError:  # rodando como script solto
    from tools import TOOLS, EXECUTION_LOG
    from persona import SYSTEM_PROMPT
    import rag

# gemini-2.5-flash-lite: free tier com 1.000 req/dia (vs apenas 20 do flash).
# Otimo para tool calling + RAG e sem custo. Troque via GEMINI_MODEL no .env.
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")


def _client() -> genai.Client:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY nao definida. Crie um arquivo .env com "
            "GEMINI_API_KEY=sua_chave (veja .env.example)."
        )
    return genai.Client(api_key=key)


def perguntar(pergunta: str, historico: list[tuple[str, str]] | None = None,
              usar_rag: bool = False, base_rag=None):
    """Envia a pergunta para a Ana e retorna (resposta, evidencias).

    Args:
        pergunta: texto do usuario.
        historico: lista opcional de (role, texto) com role em {"user","model"}.
        usar_rag: se True, consulta o documento de regras de negocio (RAG) e
                  injeta os trechos relevantes como contexto extra.

    Returns:
        (resposta_texto, lista_de_evidencias)
        onde cada evidencia = {"ferramenta", "entrada", "resumo"}.
    """
    EXECUTION_LOG.clear()
    client = _client()

    system = SYSTEM_PROMPT
    if usar_rag:
        base = base_rag if base_rag is not None else rag.base()
        trechos = base.buscar(pergunta, k=3)
        if trechos:
            contexto = "\n\n".join(f"## {t['titulo']}\n{t['texto']}" for t in trechos)
            system += (
                "\n\n# Contexto de negocio (documento da empresa)\n"
                "Os trechos abaixo vem de um documento enviado. Use-os APENAS se tiverem "
                "relacao com a analise de vendas/negocio (definicoes, politicas, playbooks). "
                "Se o conteudo NAO tiver relacao com o negocio (ex: videogames, esportes), "
                "IGNORE-o completamente e nao responda sobre esse assunto — siga focada nos "
                "dados. Quando usar algo relevante, cite como 'documento de regras de negocio' "
                "e combine com os numeros do banco. Nao invente regras alem do que esta escrito.\n\n"
                + contexto
            )
            EXECUTION_LOG.append({
                "ferramenta": f"rag ({base.origem})",
                "entrada": pergunta,
                "resumo": "trechos: " + ", ".join(t["titulo"] for t in trechos),
            })

    config = types.GenerateContentConfig(
        system_instruction=system,
        tools=TOOLS,            # function calling automatico
        temperature=0.2,        # baixa = respostas mais factuais
    )

    contents = []
    for role, texto in (historico or []):
        contents.append(types.Content(role=role, parts=[types.Part(text=texto)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=pergunta)]))

    resp = _gerar_com_retry(client, contents, config)
    texto = (resp.text or "").strip()
    # Garantia de formatacao: remove crases (que renderizam como texto verde/codigo)
    texto = texto.replace("`", "")
    return texto, list(EXECUTION_LOG)


def _gerar_com_retry(client, contents, config, tentativas: int = 4):
    """Chama o modelo com retry em erros transitorios (503/sobrecarga).
    Protege a demo de instabilidades momentaneas do servico."""
    for i in range(tentativas):
        try:
            return client.models.generate_content(model=MODEL, contents=contents, config=config)
        except Exception as e:
            msg = str(e)
            transitorio = ("503" in msg or "UNAVAILABLE" in msg
                           or "overloaded" in msg.lower() or "high demand" in msg.lower())
            if transitorio and i < tentativas - 1:
                time.sleep(2 * (i + 1))   # espera crescente: 2s, 4s, 6s
                continue
            raise


if __name__ == "__main__":
    # Teste rapido via linha de comando (precisa da GEMINI_API_KEY)
    perguntas = [
        "Quem sao meus clientes mais valiosos e quanto representam da receita?",
        "A politica de desconto esta saudavel?",
        "Qual a margem de lucro por fornecedor?",  # deve responder que nao da
    ]
    for p in perguntas:
        print("\n" + "=" * 70)
        print("PERGUNTA:", p)
        resposta, evid = perguntar(p)
        print("\nANA:", resposta)
        print("\nEVIDENCIAS:")
        for e in evid:
            print(f"  - {e['ferramenta']}({e['entrada'][:60]}) -> {e['resumo']}")
