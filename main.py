from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Substitua com o token gerado pelo @BotFather no Telegram
TELEGRAM_TOKEN = "8038213374:AAFocrOmpN5m38JDf37Pg9d3fwe9PZaPCHE"

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
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Iniciando o bot
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
