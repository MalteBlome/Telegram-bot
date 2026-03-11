import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hallo Team Schnarchtier")


def main() -> None:
    if not TOKEN:
        raise ValueError("Die Umgebungsvariable TELEGRAM_BOT_TOKEN fehlt.")

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("Bot läuft...")
    app.run_polling()


if __name__ == "__main__":
    main()