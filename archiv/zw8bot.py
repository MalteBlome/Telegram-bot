import os
from flask import Flask, request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

# ---------------------------------------------------------
# 🔹 1. Token von Render Environment
# ---------------------------------------------------------
TOKEN = os.environ.get("TELEGRAM_TOKEN")

# ---------------------------------------------------------
# 🔹 2. Flask-App für Webhooks
# ---------------------------------------------------------
app = Flask(__name__)

# ---------------------------------------------------------
# 🔹 3. Telegram Application (NUR EINMAL!)
# ---------------------------------------------------------
application = Application.builder().token(TOKEN).build()

# ---------------------------------------------------------
# 🔹 4. Dein Original-Bot-Code (unverändert)
# ---------------------------------------------------------

STATE_START = 0
STATE_CODE = 1
STATE_TOM = 2
STATE_PASCHA = 3
STATE_SONG = 4

user_state = {}
user_data = {}
user_help_count = {}

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
            await update.message.reply_text("Hinweis 2: Es ist etwas, das Z-Walhalla zeigt.")
        else:
            await update.message.reply_text("Keine weiteren Hinweise mehr. 😉")

    elif state == STATE_TOM:
        if count == 1:
            await update.message.reply_text("Hinweis 1: Schau dir die Zahlen auf den Bildern genau an.")
        elif count == 2:
            await update.message.reply_text("Hinweis 2: Vielleicht ist der Code die erste Zahl des ersten Bildes und die letzte des letzten?")
        else:
            await update.message.reply_text("Du musst selbst knobeln! 🕵️‍♂️")

    elif state == STATE_PASCHA:
        if count == 1:
            await update.message.reply_text("Hinweis: Sprich mit DJ BO, indem du 'BO' schreibst.")
        else:
            await update.message.reply_text("Kein weiterer Hinweis verfügbar.")

    elif state == STATE_SONG:
        await update.message.reply_text("Hier kann ich dir leider keinen weiteren Tipp geben, hör auf dein Gefühl! 🎵")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_state[chat_id] = STATE_CODE
    user_help_count[chat_id] = 0
    await update.message.reply_text(
        "Hallo! Bevor ich dir die Beweise zukommen lasse, nenne mir den geheimen Code..."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    if chat_id not in user_state:
        await update.message.reply_text("Bitte starte zuerst mit /start.")
        return

    state = user_state[chat_id]

    if state == STATE_CODE:
        if text == "50674":
            user_data[chat_id] = {"Code": text}
            user_state[chat_id] = STATE_TOM
            user_help_count[chat_id] = 0
            await update.message.reply_text("Code akzeptiert ✅")
            await send_tom(update, chat_id)
        else:
            await update.message.reply_text("❌ Falscher Code!")

    elif state == STATE_TOM:
        if text == "7231":
            user_state[chat_id] = STATE_PASCHA
            user_help_count[chat_id] = 0
            await update.message.reply_text("✅ Richtiger Code!")
            await send_pascha(update, chat_id)
        else:
            await update.message.reply_text("❌ Falscher Code!")

    elif state == STATE_PASCHA:
        if text.strip().lower() == "bo":
            user_state[chat_id] = STATE_SONG
            user_help_count[chat_id] = 0
            with open("DJBO.jpg", "rb") as photo:
                await update.message.reply_photo(photo=photo, caption="DJ BO nickt...")
        else:
            await update.message.reply_text("Schreib *BO*.")

    elif state == STATE_SONG:
        user_data[chat_id]["Songtext"] = text
        await update.message.reply_text(f"Wow, starker Text!\n\n„{text}“")
        await update.message.reply_text("Alle Schritte abgeschlossen! ✅")

        user_state.pop(chat_id, None)
        user_data.pop(chat_id, None)
        user_help_count.pop(chat_id, None)


async def send_tom(update: Update, chat_id):
    await update.message.reply_text("Perfekt, ich kann dir also vertrauen...")

    with open("TOM.png", "rb") as p:
        await update.message.reply_photo(photo=p, caption="7231")
    with open("Arni.png", "rb") as p:
        await update.message.reply_photo(photo=p, caption="3115")
    with open("Ronny.png", "rb") as p:
        await update.message.reply_photo(photo=p, caption="8726")


async def send_pascha(update: Update, chat_id):
    await update.message.reply_text("Du hast den Code geknackt!")
    await update.message.reply_text("https://maps.app.goo.gl/tMCEBn7d2c69L41a7")
    await update.message.reply_text("Schreib *BO* zum weitermachen.")


# ---------------------------------------------------------
# 🔹 5. Handler registrieren
# ---------------------------------------------------------
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# ---------------------------------------------------------
# 🔹 6. Webhook-Route (Render ruft das auf)
# ---------------------------------------------------------
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "OK", 200


@app.route("/")
def home():
    return "Bot is running!", 200


# ---------------------------------------------------------
# 🔹 7. Render-Start (KEIN POLLING!)
# ---------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=f"webhook/{TOKEN}",
        webhook_url=f"{os.environ['RENDER_EXTERNAL_URL']}/webhook/{TOKEN}",
    )

    app.run(host="0.0.0.0", port=port)
