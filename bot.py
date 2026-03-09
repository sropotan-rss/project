import os
import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

from parser import parse_hh
from ats_engine import analyze
from resume_reader import read_pdf
from hh_search import search_jobs


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

resume_text = ""


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "🤖 ATS Job Bot\n\n"
        "1️⃣ Send PDF resume\n"
        "2️⃣ Send hh.ru vacancy link\n"
        "3️⃣ Command:\n"
        "/jobs Product Manager"
    )

    await update.message.reply_text(text)


async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global resume_text

    try:

        file = await update.message.document.get_file()

        path = "resume.pdf"

        await file.download_to_drive(path)

        resume_text = read_pdf(path)

        await update.message.reply_text("✅ Resume uploaded")

    except Exception as e:

        logging.error(e)

        await update.message.reply_text("❌ Error reading PDF")


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global resume_text

    try:

        url = update.message.text

        if "hh.ru" not in url:

            await update.message.reply_text("Send hh.ru vacancy link")

            return

        if not resume_text:

            await update.message.reply_text("⚠ Upload resume first")

            return

        await update.message.reply_text("🔎 Analyzing vacancy...")

        vacancy = parse_hh(url)

        result = analyze(resume_text, vacancy)

        if len(result) > 4000:
            result = result[:4000]

        await update.message.reply_text(result)

    except Exception as e:

        logging.error(e)

        await update.message.reply_text("❌ Error analyzing vacancy")


async def jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:

        query = " ".join(context.args)

        if not query:

            await update.message.reply_text(
                "Example:\n/jobs Product Manager"
            )
            return

        await update.message.reply_text("🔎 Searching jobs...")

        links = search_jobs(query)

        if not links:

            await update.message.reply_text("No jobs found")

            return

        text = "🔥 Top vacancies:\n\n"

        for l in links[:10]:
            text += l + "\n"

        await update.message.reply_text(text)

    except Exception as e:

        logging.error(e)

        await update.message.reply_text("❌ Error searching jobs")


def main():

    token = os.getenv("BOT_TOKEN")

    if not token:

        raise ValueError("BOT_TOKEN not set")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("jobs", jobs))

    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    print("🚀 BOT STARTED")

    app.run_polling()


if __name__ == "__main__":
    main()
