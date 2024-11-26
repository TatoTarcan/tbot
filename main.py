from telegram import Update
import os
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext

# Substitua com o token gerado pelo @BotFather no Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Comando /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Olá! Eu sou seu bot no Telegram. Como posso ajudar?")

# Mensagem de eco
def echo(update: Update, context: CallbackContext):
    user_message = update.message.text
    update.message.reply_text(f"Você disse: {user_message}")

# Função principal
def main():
    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher

    # Configurando o comando /start
    dispatcher.add_handler(CommandHandler("start", start))

    # Respondendo mensagens de texto
    dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Iniciando o bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
