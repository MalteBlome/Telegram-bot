import os
import logging
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ============================================================
# Logging (hilft extrem beim Debuggen in Railway Logs)
# ============================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ============================================================
# ENV VARS (Railway)
# ============================================================
# In Railway -> Variables setzen:
# TELEGRAM_TOKEN = 123456:ABC...
# PUBLIC_URL     = https://deinprojekt.up.railway.app
# PORT           = wird von Railway gesetzt (optional, fallback vorhanden)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
PUBLIC_URL = os.environ.get("PUBLIC_URL")
PORT = int(os.environ.get("PORT", "8080"))

if not TOKEN:
    raise RuntimeError("ENV Variable TELEGRAM_TOKEN fehlt.")
if not PUBLIC_URL:
    raise RuntimeError("ENV Variable PUBLIC_URL fehlt (deine Railway-URL).")

# ============================================================
# Paths (damit Files auf Railway zuverlässig gefunden werden)
# ============================================================
BASE_DIR = Path(__file__).resolve().parent

def file_path(filename: str) -> Path:
    return BASE_DIR / filename


# ============================================================
# Zustände
# ============================================================
STATE_CODE = 1
STATE_TOM = 2
STATE_PASCHA = 3
STATE_SONG = 4

user_state: dict[int, int] = {}
user_help_count: dict[int, int] = {}


# ============================================================
# Commands
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_state[chat_id] = STATE_CODE
    user_help_count[chat_id] = 0

    await update.message.reply_text("Hallo! Nenne mir zuerst den geheimen Code ...")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


# ============================================================
# Helper: Bilder senden
# ============================================================
async def send_tom(update: Update):
    await update.message.reply_text("Hier sind deine Hinweise:")

    # TOM.png
    p = file_path("TOM.png")
    if p.exists():
        with p.open("rb") as f:
            await update.message.reply_photo(photo=f, caption="7231")
    else:
        await update.message.reply_text("⚠️ Datei TOM.png fehlt auf dem Server.")

    # Arni.png
    p = file_path("Arni.png")
    if p.exists():
        with p.open("rb") as f:
            await update.message.reply_photo(photo=f, caption="3115")
    else:
        await update.message.reply_text("⚠️ Datei Arni.png fehlt auf dem Server.")

    # Ronny.png
    p = file_path("Ronny.png")
    if p.exists():
        with p.open("rb") as f:
            await update.message.reply_photo(photo=f, caption="8726")
    else:
        await update.message.reply_text("⚠️ Datei Ronny.png fehlt auf dem Server.")


async def send_pascha(update: Update):
    await update.message.reply_text("Die Truhe führt dich zu einer Location:")
    await update.message.reply_text("https://maps.app.goo.gl/tMCEBn7d2c69L41a7")
    await update.message.reply_text("Schreib *BO*, wenn du dort bist.")


# ============================================================
# Message Handler
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip()

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
        if text.lower() == "bo":
            user_state[chat_id] = STATE_SONG
            user_help_count[chat_id] = 0

            img = file_path("DJBO.jpg")
            if img.exists():
                with img.open("rb") as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption="OK! Sag mir deinen Lieblings-Songtext 🎵",
                    )
            else:
                await update.message.reply_text("⚠️ Datei DJBO.jpg fehlt auf dem Server.")
                await update.message.reply_text("Sag mir trotzdem deinen Lieblings-Songtext 🎵")
        else:
            await update.message.reply_text("Schreib *BO*.")

    elif state == STATE_SONG:
        await update.message.reply_text(f"Cooler Text! 🎤\n„{text}“")
        await update.message.reply_text("Du hast alle Schritte abgeschlossen! ✅")

        # Reset
        user_state.pop(chat_id, None)
        user_help_count.pop(chat_id, None)


# ============================================================
# Main: Webhook für Railway
# ============================================================
def main():
    # App bauen
    application = Application.builder().token(TOKEN).build()

    # Handler registrieren
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Webhook Pfad (kannst du so lassen)
    url_path = f"webhook/{TOKEN}"
    webhook_url = f"{PUBLIC_URL.rstrip('/')}/{url_path}"

    logger.info("Starting webhook server on port %s", PORT)
    logger.info("Webhook URL: %s", webhook_url)

    # Start Webhook
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=url_path,
        webhook_url=webhook_url,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
