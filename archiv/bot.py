from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8596653896:AAFqU1kAhw-fMrY-6xikAyz8j69s1fUlyvo"

# --- Befehle ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hallo! Ich bin dein Telegram-Bot 🤖")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Du hast gesagt: {update.message.text}")

# --- Hauptprogramm ---
def main():
    # Application bauen
    app = Application.builder().token(TOKEN).build()

    # Handler registrieren
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("Bot läuft...")  
    app.run_polling()  # Startet den Bot

if __name__ == "__main__":
    main()
