import os
from telegram.ext import ApplicationBuilder, CommandHandler

# Função de comando simples
async def start(update, context):
    await update.message.reply_text("Olá! Eu sou seu bot. Como posso ajudar?")

# Função principal
def main():
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

    # Construir aplicação
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Adicionar comando /start
    application.add_handler(CommandHandler("start", start))

    # Rodar o bot
    application.run_polling()

if __name__ == "__main__":
    main()
