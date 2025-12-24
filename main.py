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

    img = file_path("schnuffel.png")

    if img.exists():
        with img.open("rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=(
                    "Hallo Team Schnuffel!\n\n"
                    "Heute gibt es vom Weihnachtsmann 🎅 die Geschenke 🎁 "
                    "nicht einfach soo… ihr müsst sie euch wohl verdienen.\n\n"
                    "Daher beginnt hier euer Rätsel:\n"
                    "Das in der Ruschwedelerstraße weit bekannte Gedicht von "
                    "Reiner Kunze – *Rudern Zwei* – wird auf welches Jahr datiert?"
                ),
            )
    else:
        await update.message.reply_text("⚠️ Datei schnuffel.png fehlt auf dem Server.")

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
    await update.message.reply_text("Hier geht es weiter:")

    p = file_path("Song1.ogg")  # z. B. mp3, wav, m4a
    if p.exists():
        with p.open("rb") as f:
            await update.message.reply_audio(
                audio=f,
                caption="Hier ist die Audio für euer zweites Rätsel 🎶 Wer singt denn hier diesen wunderbaren Song?",
            )
    else:
        await update.message.reply_text("⚠️ Datei fehlt auf dem Server.")



async def send_pascha(update: Update):
    await update.message.reply_text("Welche Maßnahme trägt am effektivsten zur Reduktion der Strahlenbelastung des Patienten bei?\n"
"A) Erhöhung der mAs\n"
"B) Vergrößerung des Fokus-Film-Abstands\n"
"C) Verwendung von Bleigummischürzen\n"
"D) Verkleinerung des Strahlenfeldes (Einblenden)")



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
        if text == "1977":
            user_state[chat_id] = STATE_TOM
            user_help_count[chat_id] = 0
            await update.message.reply_text("Sehr gut - damit habt ihr das erste Rätsel gelöst und seid eurem Geschenk schon etwas näher✅")
            await send_tom(update)
        else:
            await update.message.reply_text("❌ Falscher Code!")

    elif state == STATE_TOM:
        if text == "Kurt Mühlhardt":
            user_state[chat_id] = STATE_PASCHA
            user_help_count[chat_id] = 0
            await update.message.reply_text("Richtig! Nun zurück mit euch auf die Schulbank… erste Frage geht an dich Miss Marple: ")
            await send_pascha(update)
        else:
            await update.message.reply_text("❌ Falscher Code!")

    elif state == STATE_PASCHA:
        if text.lower() == "d":
            user_state[chat_id] = STATE_SONG
            user_help_count[chat_id] = 0

            img = file_path("elektro.png")
            if img.exists():
                with img.open("rb") as photo:
                    await update.message.reply_photo(
                        photo=photo,
                        caption="Jetzt du Scherlock - wie sieht es mit der Elektrotechnik aus - Was passiert mit dem Strom, wenn die Widerstand halbiert wird?\n"
                        "A.) Der Strom wird viermal so groß.\n"
                        "B.) Der Strom bleibt unverändert.\n"
                        "C.) Der Strom halbiert sich ebenfalls.\n"
                        "C.) Der Strom wird doppelt so groß.\n"
                    )
            else:
                await update.message.reply_text("⚠️ Datei DJBO.jpg fehlt auf dem Server.")
                await update.message.reply_text("Sag mir trotzdem deinen Lieblings-Songtext 🎵")
        else:
            await update.message.reply_text("Falsche Antwort")

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
