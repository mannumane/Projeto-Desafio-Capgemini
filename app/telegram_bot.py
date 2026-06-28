"""
Bot de Telegram da Ana — a mesma persona/IA do app web, agora num canal de chat.
Demonstra que o núcleo está desacoplado: o Telegram é apenas uma "casca" fina
que chama ai.agent.perguntar(), exatamente como o Streamlit faz.

Setup:
  1. No Telegram, fale com @BotFather -> /newbot -> escolha nome e usuário -> copie o token.
  2. Coloque o token no arquivo .env:   TELEGRAM_BOT_TOKEN=seu_token_aqui
  3. pip install -r requirements.txt
  4. python app/telegram_bot.py
  5. Abra o seu bot no Telegram, mande /start e comece a perguntar.
"""

import os
import sys
import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (Application, CommandHandler, MessageHandler,
                          filters, ContextTypes)

from ai.agent import perguntar

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
MAX_TURNOS = 6  # quantos turnos de conversa manter como contexto

BOAS_VINDAS = (
    "Olá! Sou a Ana, analista de BI. 📊\n\n"
    "Pergunte sobre receita, clientes, produtos, descontos ou regiões — "
    "eu respondo com base nos dados reais de vendas.\n\n"
    "Comandos:\n"
    "/reset — limpa a conversa\n"
    "/negocio — liga/desliga o contexto de regras de negócio (RAG)"
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data["hist"] = []
    await update.message.reply_text(BOAS_VINDAS)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.chat_data["hist"] = []
    await update.message.reply_text("Conversa reiniciada. Pode perguntar de novo. 🔄")


async def negocio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    novo = not context.chat_data.get("rag", False)
    context.chat_data["rag"] = novo
    await update.message.reply_text(
        f"Contexto de regras de negócio (RAG): {'ligado ✅' if novo else 'desligado'}."
    )


def _limpar(texto: str) -> str:
    """Remove marcadores de bold do markdown (Telegram puro mostraria os asteriscos)."""
    return texto.replace("**", "")


async def mensagem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pergunta = update.message.text
    hist = context.chat_data.get("hist", [])
    usar_rag = context.chat_data.get("rag", False)

    await context.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)

    # perguntar() é síncrono (faz chamadas de rede); roda fora do event loop
    loop = asyncio.get_event_loop()
    try:
        resposta, _ = await loop.run_in_executor(
            None, lambda: perguntar(pergunta, list(hist), usar_rag)
        )
    except Exception as e:
        resposta = f"⚠️ {e}"

    hist.append(("user", pergunta))
    hist.append(("model", resposta))
    context.chat_data["hist"] = hist[-2 * MAX_TURNOS:]

    texto = _limpar(resposta) or "Não consegui responder agora. Tente novamente."
    # Telegram limita mensagens a 4096 caracteres
    for i in range(0, len(texto), 4000):
        await update.message.reply_text(texto[i:i + 4000])


def main():
    if not TOKEN:
        sys.exit("Defina TELEGRAM_BOT_TOKEN no .env (token gerado pelo @BotFather).")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("negocio", negocio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensagem))
    print("Bot da Ana rodando (polling). Ctrl+C para parar.")
    app.run_polling()


if __name__ == "__main__":
    main()
