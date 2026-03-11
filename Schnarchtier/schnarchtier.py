import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Bilder + Captions
STEPS = [
    {"file": "Vulkan1.jpg", "caption": "Es grüßt ganz herzlich das Team Schnarchtier"},
    {"file": "bild2.jpg", "caption": "Caption für Bild 2"},
    {"file": "bild3.jpg", "caption": "Caption für Bild 3"},
    {"file": "bild4.jpg", "caption": "Caption für Bild 4"},
    {"file": "bild5.jpg", "caption": "Caption für Bild 5"},
    {"file": "bild6.jpg", "caption": "Caption für Bild 6"},
    {"file": "bild7.jpg", "caption": "Caption für Bild 7"},
]


async def send_step(update: Update, context: ContextTypes.DEFAULT_TYPE, step_index: int):
    step = STEPS[step_index]

    with open(step["file"], "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=step["caption"]
        )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["step"] = 0

    await send_step(update, context, 0)

    context.user_data["step"] = 1


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get("step")

    if step is None:
        await update.message.reply_text("Bitte starte zuerst mit /start")
        return

    if step < len(STEPS):
        await send_step(update, context, step)
        context.user_data["step"] = step + 1
    else:
        await update.message.reply_text(
            "Alle 7 Bilder wurden bereits angezeigt. Starte mit /start neu."
        )
        context.user_data["step"] = None


def main():
    if not TOKEN:
        raise ValueError("Die Umgebungsvariable TELEGRAM_BOT_TOKEN fehlt.")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot läuft...")
    app.run_polling()


if __name__ == "__main__":
    main()