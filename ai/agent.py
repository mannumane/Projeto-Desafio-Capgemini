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
except ImportError:  # rodando como script solto
    from tools import TOOLS, EXECUTION_LOG
    from persona import SYSTEM_PROMPT

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def _client() -> genai.Client:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY nao definida. Crie um arquivo .env com "
            "GEMINI_API_KEY=sua_chave (veja .env.example)."
        )
    return genai.Client(api_key=key)


def perguntar(pergunta: str, historico: list[tuple[str, str]] | None = None):
    """Envia a pergunta para a Ana e retorna (resposta, evidencias).

    Args:
        pergunta: texto do usuario.
        historico: lista opcional de (role, texto) com role em {"user","model"}.

    Returns:
        (resposta_texto, lista_de_evidencias)
        onde cada evidencia = {"ferramenta", "entrada", "resumo"}.
    """
    EXECUTION_LOG.clear()
    client = _client()

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=TOOLS,            # function calling automatico
        temperature=0.2,        # baixa = respostas mais factuais
    )

    contents = []
    for role, texto in (historico or []):
        contents.append(types.Content(role=role, parts=[types.Part(text=texto)]))
    contents.append(types.Content(role="user", parts=[types.Part(text=pergunta)]))

    resp = client.models.generate_content(model=MODEL, contents=contents, config=config)
    return (resp.text or "").strip(), list(EXECUTION_LOG)


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
