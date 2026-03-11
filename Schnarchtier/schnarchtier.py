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
    {"file": "Vulkan1.jpg", "caption": "Es grüßt ganz herzlich das Team Mäuschen und Schnarchtier. Dieser kleien Schnarchtier_bot führt dich durch schöne Erinnerungen und Beschreibung warum Schnarchtier und Mäuschen so perfekt zusammen passen."},
    {"file": "aperol.jpg", "caption": "Die beiden können gut gemeinsam spontan sein und wenn das Wetter danach ruft, dann wird mal schnell alles stehen und liegen gelassen und der nächste beste Platz für einen Aperol in der Sonne gesucht. Dabei geht es viel weniger um den Aperol also viel mehr um das gemeinsame genießen und bewusst Zeit für einader nehmen! <3 Es hilft natürlich wenn das Lieblingsgetränk dann das gleiche ist"},
    {"file": "eis.jpg", "caption": "Das gilt natürlich nicht nur für Aperol sondern auch für ein schönes Eis...und wenn die Sonne aus dem Herzen von Team Mäuschen und Schnarchtier lacht, dann ist es auch egal, dass es vllt gerade regnet, dann kann man trotzdem mit Begeisterung ein Eis vernaschen!"},
    {"file": "drink.jpg", "caption": "Die beiden funktionieren soooo gut zusammen, dass sie auch die 5 Wochen auf engstem Raum im Urlaub miteinader total schön und harmonisch miteinader verbracht haben. Sodass am Ende der Abschied schwer gefallen ist weil man sich schon an die gemeinsame Zeit gewöhnt hatte und es sehr genossen wurde. Dieser kurze Zwischenstopp in dem Minihäuschen bei Regen ist das perfekte Sinnbild dafür, dass Mäuschen und Schnarchtier auch auf engstem Raum miteinader perfekt funktionieren und deswegen werden sie es auch ohne Probleme in der kleinen Wohnung in der Neckarstraße 23 schaffen ein gemeinsames zuhasue einzurichten."},
    {"file": "Sonne.jpg", "caption": "Die beiden verbindet die Lust nach Abendteuern, auch wenn es auf dem Weg dahin, manchmal etwas stürmisch ist, sei es beim Kapf gegen die Höhenmeter des Vulkans oder die Ungewissheit beim erobern einer Höhle, so ist am Ende nur eins wichtig. Gemeinsam neue Erfahrungen und Erinnerungen sammeln, denn wenn sie diese Dinge teilen dann werden sie besonders. Immer zusammen :) "},
    {"file": "schlafen.jpg", "caption": "Und nur da wo Geborgenheit, Liebe und Zuneigung besteht, da kann eine so wunderbare tiefe und innige Bindung entstehen. Ein Bindung die die Nächte schöner macht und das Einschlafen in einen entspannten Tagesabschluss verwandelt "},
    {"file": "aufwachen.jpg", "caption": "Wer gemeinsam einschläft, der wacht auch gerne gemeinsam auf. Und wenn das erste am Tag das Lächeln des Partners ist, dann weiß man, dass man auf dem richtigen Weg ist und dann das gibt einem Gewissheit und Sicherheit die richtige Person gefunden zu haben. <3 Vamos: Wir zusammen, niemals allein"},
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