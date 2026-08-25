import logging
import os
import tempfile

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import config
import db
from cover_letter import CoverLetterError, generate_cover_letter
from resume_reader import ResumeReadError, read_pdf
from vacancy_parser import VacancyFetchError, fetch_vacancy

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

HELP_TEXT = (
    "🤖 Cover Letter Bot\n\n"
    "1️⃣ Пришли резюме в PDF\n"
    "2️⃣ Пришли ссылку на вакансию hh.ru (например https://hh.ru/vacancy/12345678)\n\n"
    "Бот напишет сопроводительное письмо под эту вакансию на основе твоего резюме.\n"
    "Резюме можно обновить в любой момент, просто прислав новый PDF."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)


async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    await update.message.reply_text("📄 Читаю резюме...")

    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "resume.pdf")
        file = await update.message.document.get_file()
        await file.download_to_drive(path)

        try:
            resume_text = read_pdf(path)
        except ResumeReadError as e:
            await update.message.reply_text(f"❌ {e}")
            return

    db.save_resume(chat_id, resume_text)
    await update.message.reply_text(
        f"✅ Резюме сохранено ({len(resume_text)} символов).\n"
        "Теперь пришли ссылку на вакансию hh.ru."
    )


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    url = update.message.text.strip()

    if "hh.ru" not in url:
        await update.message.reply_text(
            "Пришли ссылку на вакансию hh.ru (например https://hh.ru/vacancy/12345678) "
            "или сначала PDF с резюме."
        )
        return

    resume_text = db.get_resume(chat_id)
    if not resume_text:
        await update.message.reply_text("⚠️ Сначала пришли резюме в PDF")
        return

    await update.message.reply_text("🔎 Читаю вакансию и пишу письмо...")

    try:
        vacancy = fetch_vacancy(url)
    except VacancyFetchError as e:
        await update.message.reply_text(f"❌ {e}")
        return

    try:
        letter = generate_cover_letter(resume_text, vacancy)
    except CoverLetterError as e:
        await update.message.reply_text(f"❌ {e}")
        return

    for chunk_start in range(0, len(letter), 4000):
        await update.message.reply_text(letter[chunk_start : chunk_start + 4000])


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Unhandled exception", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text("❌ Произошла ошибка, попробуйте позже")


def main():
    if not config.BOT_TOKEN:
        raise ValueError("BOT_TOKEN not set")

    db.init_db()

    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    app.add_error_handler(on_error)

    print("🚀 Cover Letter Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
