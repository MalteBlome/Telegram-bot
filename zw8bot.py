import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============================================
# ENV VARIABLES (Railway)
# ============================================
TOKEN = os.environ.get("TELEGRAM_TOKEN")
RAILWAY_URL = os.environ.get("RAILWAY_STATIC_URL")

# ============================================
# TELEGRAM APPLICATION – nur EINMAL erstellen
# ============================================
application = Application.builder().token(TOKEN).build()

# ============================================
# DEINE ZUSTÄNDE UND DATEN
# ============================================
STATE_CODE = 1
STATE_TOM = 2
STATE_PASCHA = 3
STATE_SONG = 4

user_state = {}
user_data = {}
user_help_count = {}

# ============================================
# START-KOMMANDO
# ============================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_state[chat_id] = STATE_CODE
    user_help_count[chat_id] = 0

    await update.message.reply_text(
        "Hallo! Nenne mir zuerst den geheimen Code ..."
    )

# ============================================
# HELP-KOMMANDO
# ============================================
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in user_state:
        await update.message.reply_text("Bitte starte zuerst mit /start.")
        return

    count = user_help_count.get(chat_id, 0) + 1
    user_help_count[chat_id] = count
    state = user_state[chat_id]

    if state == STATE_CODE:
        if count == 1:
            await update.message.reply_text("Hinweis 1: Der Code ist fünfstellig.")
        elif count == 2:
            await update.message.reply_text("Hinweis 2: Etwas, das Z-Walhalla zeigt.")
        else:
            await update.message.reply_text("Keine weiteren Hinweise. 😉")

    elif state == STATE_TOM:
        if count == 1:
            await update.message.reply_text("Tipp: Schau die Zahlen an.")
        elif count == 2:
            await update.message.reply_text("Vielleicht erste + letzte Zahl?")
        else:
            await update.message.reply_text("Jetzt musst du selbst denken! 🧠")

    elif state == STATE_PASCHA:
        await update.message.reply_text("Tipp: Schreibe *BO*.")

    else:
        await update.message.reply_text("Keine weiteren Tipps!")

# ============================================
# HAUPT MESSAGE HANDLER
# ============================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    if chat_id not in user_state:
        await update.message.reply_text("Bitte starte zuerst mit /start.")
        return

    state = user_state[chat_id]

    if state == STATE_CODE:
        if text == "50674":
            user_state[chat_id] = STATE_TOM
            user_help_count[chat_id] = 0
            await update.message.reply_text("Code akzeptiert! ✅")
            await send_tom(update)
        else:
            await update.message.reply_text("❌ Falscher Code!")

    elif state == STATE_TOM:
        if text == "7231":
            user_state[chat_id] = STATE_PASCHA
            user_help_count[chat_id] = 0
            await update.message.reply_text("Richtig! Weiter geht's …")
            await send_pascha(update)
        else:
            await update.message.reply_text("❌ Falscher Code!")

    elif state == STATE_PASCHA:
        if text.lower().strip() == "bo":
            user_state[chat_id] = STATE_SONG
            user_help_count[chat_id] = 0

            with open("DJBO.jpg", "rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption="OK! Sag mir deinen Lieblings-Songtext 🎵"
                )
        else:
            await update.message.reply_text("Schreib *BO*.")

    elif state == STATE_SONG:
        await update.message.reply_text(f"Cooler Text! 🎤\n„{text}“")
        await update.message.reply_text("Du hast alle Schritte abgeschlossen! ✅")

        user_state.pop(chat_id, None)
        user_data.pop(chat_id, None)
        user_help_count.pop(chat_id, None)

# ============================================
# EXTRA-FUNKTIONEN (Bilder senden)
# ============================================
async def send_tom(update: Update):
    await update.message.reply_text("Hier sind deine Hinweise:")

    with open("TOM.png", "rb") as p:
        await update.message.reply_photo(photo=p, caption="7231")
    with open("Arni.png", "rb") as p:
        await update.message.reply_photo(photo=p, caption="3115")
    with open("Ronny.png", "rb") as p:
        await update.message.reply_photo(photo=p, caption="8726")

async def send_pascha(update: Update):
    await update.message.reply_text("Die Truhe führt dich zu einer Location:")
    await update.message.reply_text("https://maps.app.goo.gl/tMCEBn7d2c69L41a7")
    await update.message.reply_text("Schreib *BO*, wenn du dort bist.")

# ============================================
# HANDLER REGISTRIEREN
# ============================================
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ============================================
# RAILWAY STARTBLOCK (RICHTIG!)
# ============================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=f"webhook/{TOKEN}",
        webhook_url=f"{RAILWAY_URL}/webhook/{TOKEN}",
    )
