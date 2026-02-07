import os
import logging
import hashlib
from pathlib import Path
from typing import Optional

import asyncpg
from telegram import Update, InputMediaPhoto
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
TOKEN = os.environ.get("TELEGRAM_TOKEN")
PUBLIC_URL = os.environ.get("PUBLIC_URL")
PORT = int(os.environ.get("PORT", "8080"))

DATABASE_URL = os.environ.get("DATABASE_URL")

if not TOKEN:
    raise RuntimeError("ENV Variable TELEGRAM_TOKEN fehlt.")
if not PUBLIC_URL:
    raise RuntimeError("ENV Variable PUBLIC_URL fehlt (deine Railway-URL).")
if not DATABASE_URL:
    raise RuntimeError("ENV Variable DATABASE_URL fehlt (Railway Postgres).")

# ============================================================
# DB Pool (asyncpg)
# ============================================================
db_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    return db_pool


def normalize_code(code: str) -> str:
    return (code or "").strip().upper()


def hash_code(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


async def is_licensed(telegram_user_id: int) -> bool:
    """
    True, wenn diese Telegram-User-ID bereits eine eingelöste Lizenz hat.
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT 1 FROM licenses WHERE redeemed_telegram_id=$1 AND status='redeemed'",
            telegram_user_id,
        )
        return row is not None


async def redeem_license(telegram_user_id: int, code: str) -> bool:
    """
    Code einmalig einlösen und an Telegram-User-ID binden.
    Rückgabe True wenn erfolgreich, sonst False.
    """
    pool = await get_db_pool()
    code_norm = normalize_code(code)
    if not code_norm:
        return False

    code_h = hash_code(code_norm)

    async with pool.acquire() as conn:
        async with conn.transaction():
            lic = await conn.fetchrow(
                "SELECT id, status FROM licenses WHERE code_hash=$1 FOR UPDATE",
                code_h,
            )
            if not lic:
                return False
            if lic["status"] != "unused":
                return False

            await conn.execute(
                """
                UPDATE licenses
                SET status='redeemed',
                    redeemed_at=now(),
                    redeemed_telegram_id=$1
                WHERE id=$2
                """,
                telegram_user_id,
                lic["id"],
            )
            return True


# ============================================================
# Paths (damit Files auf Railway zuverlässig gefunden werden)
# ============================================================
BASE_DIR = Path(__file__).resolve().parent


def file_path(filename: str) -> Path:
    return BASE_DIR / filename


# ============================================================
# Zustände
# ============================================================
STATE_LICENSE = 0  # <-- NEU: wartet auf Zugangscode
STATE_CODE = 1
STATE_TOM = 2
STATE_PASCHA = 3
STATE_ELEKTRO = 4  # <-- eigener State für Elektrotechnik

# State-Tracking pro Chat (Rätsel laufen im Chat-Kontext)
user_state: dict[int, int] = {}
user_help_count: dict[int, int] = {}


# ============================================================
# Commands
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # --- Lizenz-Gate ---
    if not await is_licensed(user_id):
        user_state[chat_id] = STATE_LICENSE
        user_help_count[chat_id] = 0
        await update.message.reply_text(
            "🔐 Zugriff geschützt.\n"
            "Bitte sende mir deinen Zugangscode (z.B. ABCD-EFGH-IJKL-MNOP-QRST)."
        )
        return

    # --- Rätsel Start ---
    user_state[chat_id] = STATE_CODE
    user_help_count[chat_id] = 0

    # 1) Erst ein Bild mit Caption senden
    main_img = file_path("Andrea.png")

    caption_text = (
        "Hallo Yadegar! *schluchzt*\n\n"
        "Der lange Tünn hat mir schon erzählt, dass du vorbeikommen würdest..."
        "ich kann es noch immer nicht glaube dass Rosi nicht mehr bei uns ist....\n\n"
        "Alles was mir bleibt ist ihr letzter Brief und ich kann und will nicht glauben, dass sie sich selber umgebracht hat...nicht meien Rosi\n"
        "Ihr wollt Infos über Karate Jacky und wo er untergetaucht sein könnte, die gebe ich euch wenn ihr mir helft zu beweisen dass Rosi keinen Selbstmord begangen hat"
        "Hier ist ihr letzter Brief an mich...ich liebe dieses Foto....sie fehlt mir soooo....Gebt mir einen Namen für die Polizei und ich sage euch alles was ich weiß"
    )

    if main_img.exists():
        with main_img.open("rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=caption_text,
                parse_mode="Markdown",
            )
    else:
        await update.message.reply_text("⚠️ Datei Andrea.png fehlt auf dem Server.")
        return

    # 2) Danach die weiteren Bilder als MediaGroup (Album) hinterher
    extra_imgs = [
        file_path("Brief1.png"),
        file_path("Brief2.png"),
        file_path("Brief3.png"),
        file_path("Rosie_und_Andrea.png"),
        file_path("Zahlen.png"),
    ]

    existing = [p for p in extra_imgs if p.exists()]
    if existing:
        files = [p.open("rb") for p in existing]
        try:
            media = [InputMediaPhoto(media=f) for f in files]
            await update.message.reply_media_group(media=media)
        finally:
            for f in files:
                f.close()
    else:
        await update.message.reply_text("⚠️ Zusatzbilder fehlen auf dem Server.")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in user_state:
        await update.message.reply_text("Bitte starte zuerst mit /start.")
        return

    state = user_state[chat_id]

    # Optional: für Lizenz-State eigener Hinweis
    if state == STATE_LICENSE:
        await update.message.reply_text(
            "Tipp: Der Zugangscode steht in deiner Kaufbestätigung und sieht aus wie ABCD-EFGH-IJKL-...."
        )
        return

    count = user_help_count.get(chat_id, 0) + 1
    user_help_count[chat_id] = count

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

    elif state == STATE_ELEKTRO:
        await update.message.reply_text("Tipp: Ohmsches Gesetz 😉")

    else:
        await update.message.reply_text("Keine weiteren Tipps!")


# ============================================================
# Helper: Medien senden
# ============================================================
async def send_tom(update: Update):
    await update.message.reply_text("Hier geht es weiter:")

    p = file_path("Song1.ogg")
    if p.exists():
        with p.open("rb") as f:
            await update.message.reply_audio(
                audio=f,
                caption="Hier ist die Audio für euer zweites Rätsel 🎶 Wer singt denn hier diesen wunderbaren Song?",
            )
    else:
        await update.message.reply_text("⚠️ Datei fehlt auf dem Server.")


async def send_pascha(update: Update):
    await update.message.reply_text(
        "Welche Maßnahme trägt am effektivsten zur Reduktion der Strahlenbelastung des Patienten bei?\n"
        "A) Erhöhung der mAs\n"
        "B) Vergrößerung des Fokus-Film-Abstands\n"
        "C) Verwendung von Bleigummischürzen\n"
        "D) Verkleinerung des Strahlenfeldes (Einblenden)"
    )


async def send_elektro(update: Update):
    img = file_path("elektro.png")
    if img.exists():
        with img.open("rb") as photo:
            await update.message.reply_photo(
                photo=photo,
                caption=(
                    "Jetzt du Scherlock - wie sieht es mit der Elektrotechnik aus - "
                    "Was passiert mit dem Strom, wenn der Widerstand halbiert wird?\n"
                    "A.) Der Strom wird viermal so groß.\n"
                    "B.) Der Strom wird doppelt so groß.\n"
                    "C.) Der Strom halbiert sich ebenfalls.\n"
                    "D.) Der Strom bleibt unverändert.\n"
                    "\nAntwort bitte nur mit A, B, C oder D."
                ),
            )
    else:
        await update.message.reply_text("⚠️ Datei elektro.png fehlt auf dem Server.")
        await update.message.reply_text(
            "Elektrotechnik-Frage trotzdem:\n"
            "Was passiert mit dem Strom, wenn der Widerstand halbiert wird?\n"
            "A) viermal so groß\nB) doppelt so groß\nC) halbiert\nD) unverändert"
        )


async def send_final_video(update: Update):
    v = file_path("final.mp4")
    caption_text = "Ihr habt alle Rätsel gelöst und somit euer Geschenk verdient"

    if v.exists():
        with v.open("rb") as video:
            await update.message.reply_video(
                video=video,
                caption=caption_text,
            )
    else:
        await update.message.reply_text("⚠️ Final-Video fehlt auf dem Server (final.mp4).")
        await update.message.reply_text(caption_text)


# ============================================================
# Message Handler
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    text = (update.message.text or "").strip()

    if chat_id not in user_state:
        await update.message.reply_text("Bitte starte zuerst mit /start.")
        return

    state = user_state[chat_id]

    # --- Lizenz-Gate auch innerhalb der Session absichern ---
    if state != STATE_LICENSE and not await is_licensed(user_id):
        user_state[chat_id] = STATE_LICENSE
        user_help_count[chat_id] = 0
        await update.message.reply_text("🔐 Zugriff fehlt. Bitte sende zuerst deinen Zugangscode.")
        return

    # --- Lizenzcode einlösen ---
    if state == STATE_LICENSE:
        ok = await redeem_license(user_id, text)
        if ok:
            await update.message.reply_text(
                "✅ Code akzeptiert! Zugriff wurde aktiviert.\n"
                "Starte jetzt bitte erneut mit /start."
            )
            # Reset der Session, damit /start sauber neu beginnt
            user_state.pop(chat_id, None)
            user_help_count.pop(chat_id, None)
        else:
            await update.message.reply_text(
                "❌ Code ungültig oder bereits verwendet.\n"
                "Bitte prüfe ihn und sende ihn erneut."
            )
        return

    # --- Dein bestehender Rätsel-Flow ---
    if state == STATE_CODE:
        if text == "Denisa":
            user_state[chat_id] = STATE_TOM
            user_help_count[chat_id] = 0
            await update.message.reply_text(
                "Sehr gut - somit hast du dieses Rätsel gelöst mein kleines Mäuschen <3 Hier ein famoser Song für dich"
            )
            await send_tom(update)
        else:
            await update.message.reply_text("❌ Falscher Code!")

    elif state == STATE_TOM:
        if text == "Kurt Mühlhardt":
            user_state[chat_id] = STATE_PASCHA
            user_help_count[chat_id] = 0
            await update.message.reply_text(
                "Richtig! Nun zurück mit euch auf die Schulbank… erste Frage geht an dich Miss Marple: "
            )
            await send_pascha(update)
        else:
            await update.message.reply_text("❌ Falscher Code!")

    elif state == STATE_PASCHA:
        if text.strip().lower() == "d":
            user_state[chat_id] = STATE_ELEKTRO
            user_help_count[chat_id] = 0
            await update.message.reply_text("Richtig ✅ Weiter geht’s mit Elektrotechnik:")
            await send_elektro(update)
        else:
            await update.message.reply_text("❌ Falsche Antwort. Bitte A, B, C oder D.")

    elif state == STATE_ELEKTRO:
        answer = text.strip().lower()
        if answer in {"b", "b.", "b)", "b]"}:
            await send_final_video(update)

            # Reset
            user_state.pop(chat_id, None)
            user_help_count.pop(chat_id, None)
        else:
            await update.message.reply_text("❌ Leider falsch. Versucht es nochmal: A, B, C oder D.")


# ============================================================
# Main: Webhook für Railway
# ============================================================
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    url_path = f"webhook/{TOKEN}"
    webhook_url = f"{PUBLIC_URL.rstrip('/')}/{url_path}"

    logger.info("Starting webhook server on port %s", PORT)
    logger.info("Webhook URL: %s", webhook_url)

    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=url_path,
        webhook_url=webhook_url,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
