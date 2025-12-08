import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# ---------------------------------------------------------
# 🔹 1. Token einlesen (Render → Environment Variable)
# ---------------------------------------------------------
TOKEN = os.environ.get("TELEGRAM_TOKEN")

app = Flask(__name__)

# ---------------------------------------------------------
# 🔹 2. Telegram Application erstellen
# ---------------------------------------------------------
application = Application.builder().token(TOKEN).build()


# ---------------------------------------------------------
# 🔹 3. HIER KOMMT DEIN NORMALER BOT-CODE HINEIN
# ---------------------------------------------------------

# Beispiel:
# async def start(update: Update, context):
#     await update.message.reply_text("Hallo!")

# application.add_handler(CommandHandler("start", start))

# ⬇️ Bitte DEINEN bisherigen Inhalt einfügen
# ---------------------------------------------------------

# ***** HIER deinen bestehenden Code einsetzen *****

# === Dein persönlicher Bot-Token ===
BOT_TOKEN = "8596653896:AAFqU1kAhw-fMrY-6xikAyz8j69s1fUlyvo"

# --- Zustände ---
STATE_START = 0
STATE_CODE = 1
STATE_TOM = 2
STATE_PASCHA = 3
STATE_SONG = 4   # 🆕 Neuer Zustand!

# --- Speicher für Benutzer ---
user_state = {}
user_data = {}
user_help_count = {}  # 🆕 Speicher für /help-Zähler pro User

# --- Hilfe-Funktion ---
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in user_state:
        await update.message.reply_text("Bitte starte zuerst mit /start.")
        return

    # 🆕 Zähler erhöhen
    count = user_help_count.get(chat_id, 0) + 1
    user_help_count[chat_id] = count

    state = user_state[chat_id]

    # --- Nachrichten abhängig vom State und Help-Zähler ---
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


# --- Startkommando ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_state[chat_id] = STATE_CODE
    user_help_count[chat_id] = 0  # 🆕 Zähler zurücksetzen beim Start
    await update.message.reply_text(
        "Hallo! Bevor ich dir die Beweise zukommen lasse, nenne mir den geheimen Code, "
        "den dir mein Kontaktmann gegeben hat! Nur so weiß ich, dass du vertrauenswürdig bist. "
        "Du weißt schon... Ich bin fünfstellig, doch kein Passwort. "
        "Ich zeige den Ort, doch bin kein Atlas. Ich führe dich zu Z-Walhalla. Was bin ich?"
    )


# --- Nachrichten-Handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    if chat_id not in user_state:
        await update.message.reply_text("Bitte starte zuerst mit /start.")
        return

    state = user_state[chat_id]

    # === Schritt 1: Code-Prüfung ===
    if state == STATE_CODE:
        if text == "50674":
            user_data[chat_id] = {"Code": text}
            user_state[chat_id] = STATE_TOM
            user_help_count[chat_id] = 0  # 🆕 Zähler zurücksetzen bei State-Wechsel
            await update.message.reply_text("Code akzeptiert ✅")
            await send_tom(update, chat_id)
        else:
            await update.message.reply_text("❌ Falscher Code! Probiere es erneut...")

    # === Schritt 2: TOM ===
    elif state == STATE_TOM:
        if text == "7231":
            user_state[chat_id] = STATE_PASCHA
            user_help_count[chat_id] = 0  # 🆕 Zähler zurücksetzen bei State-Wechsel
            await update.message.reply_text("✅ Richtiger Code! Willkommen bei Pascha...")
            await send_pascha(update, chat_id)
        else:
            await update.message.reply_text("❌ Falscher Code! Versuche es erneut...")

    # === Schritt 3: PASCHA ===
    elif state == STATE_PASCHA:
        if text.strip().lower() == "bo":
            user_state[chat_id] = STATE_SONG
            user_help_count[chat_id] = 0  # 🆕 Zähler zurücksetzen bei State-Wechsel
            with open("DJBO.jpg", "rb") as photo:
                await update.message.reply_photo(
                    photo=photo,
                    caption="DJ BO nickt dir zu und sagt: 'Wenn du wirklich dazugehören willst, "
                            "musst du mir deinen Lieblingssongtext sagen. Welcher Song geht dir nie aus dem Kopf?' 🎶"
                )
        else:
            await update.message.reply_text(
                "Frag nach DJ BO, indem du einfach *BO* schreibst."
            )

    # === Schritt 4: SONG (🆕) ===
    elif state == STATE_SONG:
        user_data[chat_id]["Songtext"] = text
        await update.message.reply_text(
            f"Wow, starker Text! 🎤 Danke für deinen Song:\n\n„{text}“\n\n"
            "DJ BO grinst: 'Das war genau der Vibe, den ich gesucht hab!' 😎"
        )

        # Optionaler Abschluss:
        await update.message.reply_text("Damit hast du alle Schritte abgeschlossen ✅")

        # Daten löschen
        user_state.pop(chat_id, None)
        user_data.pop(chat_id, None)
        user_help_count.pop(chat_id, None)  # 🆕 Help-Zähler ebenfalls löschen


# --- Funktion für TOM-Block ---
async def send_tom(update: Update, chat_id):
    await update.message.reply_text(
        "Perfekt, ich kann dir also vertrauen. Gut, dass du hier bist. "
        "Ich stehe hier vor der verschlossenen Truhe mit der Aufschrift "
        "'Der Mond öffnet die Truhe', aber ich brauche einen vierstelligen Code... "
        "Wenn ich nur wüsste, wie der Code ist, würde alles Sinn machen. "
        "Hier liegen drei Bilder mit Zahlen... Ich weiß nur nicht, welche die richtigen sind. "
        "Hätte ich bloß Maggus damals mehr zugehört, vielleicht wirst du ja schlau daraus..."
    )

    # Bilder senden
    with open("TOM.png", "rb") as photo:
        await update.message.reply_photo(photo=photo, caption="7231")
    with open("Arni.png", "rb") as photo:
        await update.message.reply_photo(photo=photo, caption="3115")
    with open("Ronny.png", "rb") as photo:
        await update.message.reply_photo(photo=photo, caption="8726")

    await update.message.reply_text(
        "Ich glaube, der vierstellige Code könnte sich in diesen Bildern verbergen... "
        "Was meinst du? Gib den Code ein:"
    )

# --- Funktion für PASCHA-Block ---
async def send_pascha(update: Update, chat_id):
    await update.message.reply_text(
        "Du hast den Code geknackt! 🔓\n"
        "Die Truhe öffnet sich langsam, und im Inneren liegt ein alter, vergilbter Zettel... "
        "Darauf steht nur ein Wort: *Pascha*.\n\n"
        "Unter dem Zettel ist eine kleine Karte eingezeichnet – vielleicht führt sie dich "
        "zum nächsten Hinweis... 🗺️"
    )

    await update.message.reply_text(
        f"Mit diesem Link solltest du zur Location kommen. Link:\n"
        f"https://maps.app.goo.gl/tMCEBn7d2c69L41a7"
    )

    await update.message.reply_text(
        "Wenn du am geheimen Versteck angekommen bist, frag nach DJ BO, "
        "indem du einfach *BO* in den Chat schreibst."
    )

# --- Hauptfunktion ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot läuft... (Drücke STRG + C zum Beenden)")
    app.run_polling()


if __name__ == "__main__":
    main()

# ---------------------------------------------------------
# 🔹 4. Flask Webhook Route
# ---------------------------------------------------------
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    """Empfängt Updates von Telegram"""
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "OK", 200


# ---------------------------------------------------------
# 🔹 5. Start Webhook (nur lokal nötig)
# ---------------------------------------------------------
@app.route("/")
def home():
    return "Bot is running!", 200


# ---------------------------------------------------------
# 🔹 6. Starten, wenn Render das Script startet
# ---------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        secret_token=None,
        url_path=f"webhook/{TOKEN}",
        webhook_url=f"{os.environ.get('RENDER_EXTERNAL_URL')}/webhook/{TOKEN}",
    )
    app.run(host="0.0.0.0", port=port)
