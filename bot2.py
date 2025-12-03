from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

TOKEN = "8596653896:AAFqU1kAhw-fMrY-6xikAyz8j69s1fUlyvo"

# --- Befehle ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hallo! Ich bin dein Telegram-Bot 🤖\nSchreibe mir etwas!")

# --- Nachrichten-Handler ---
async def antwort(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower()

    # --- if/elif-Abfragen ---
    if "hallo" in user_text or "hi" in user_text:
        antwort = "Hey! Schön, dich zu sehen 😄"

    elif "findet" in user_text:
        antwort = "Malte liebt Jessica <3"
        # Erst Text senden:
        await update.message.reply_text(antwort)
        # Dann Bild schicken:
        with open("bild.jpg", "rb") as photo:
            await update.message.reply_photo(photo=photo, caption="Mein süßes Mäuschen!")
        return  # Wichtig: damit unten kein zweites reply_text ausgeführt wird

    elif "spät" in user_text:
        antwort = f"Die aktuelle Uhrzeit ist: {datetime.now().strftime('%H:%M:%S')}"

    elif "hilfe" in user_text:
        antwort = "Ich kann dir auf einfache Nachrichten antworten. Versuch z. B. 'Hallo' oder 'Wie geht's?'."
        
    else:
        antwort = "Ich weiß nicht genau, was du meinst 🤔"

    await update.message.reply_text(antwort)

# --- Hauptprogramm ---
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, antwort))

    print("Bot läuft...")  
    app.run_polling()

if __name__ == "__main__":
    main()