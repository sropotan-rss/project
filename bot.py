import logging
from datetime import timedelta

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import checks
import config
import db
from monitors.mentions import fetch_mentions
from monitors.price import PriceFetchError, fetch_price_text

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

HELP_TEXT = (
    "🤖 Бот мониторинга конкурентов\n\n"
    "Цены и наличие на сайте:\n"
    "/add_price Название | https://site.ru/product | .price-selector\n"
    "/list — список отслеживаемых цен и упоминаний\n"
    "/remove_price <id>\n\n"
    "Упоминания в интернете (по бренду/ключевому слову):\n"
    "/add_mention Название конкурента\n"
    "/remove_mention <id>\n\n"
    "/check_now — проверить всё прямо сейчас\n\n"
    f"Автопроверка выполняется каждые {config.CHECK_INTERVAL_HOURS} ч."
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)


async def add_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.message.text.partition(" ")[2]
    parts = [p.strip() for p in raw.split("|")]

    if len(parts) != 3 or not all(parts):
        await update.message.reply_text(
            "Формат:\n/add_price Название | https://site.ru/product | .price-selector\n\n"
            "CSS-селектор — это то, где на странице находится цена "
            "(например .price, #price, span.product-price)."
        )
        return

    name, url, selector = parts

    await update.message.reply_text("🔎 Проверяю страницу...")
    try:
        price_text = fetch_price_text(url, selector)
    except PriceFetchError as e:
        await update.message.reply_text(f"❌ Не удалось добавить: {e}")
        return

    watch_id = db.add_price_watch(update.effective_chat.id, name, url, selector)
    db.update_price(watch_id, price_text)

    await update.message.reply_text(
        f"✅ Добавлено #{watch_id}: {name}\nТекущая цена: {price_text}"
    )


async def add_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = " ".join(context.args).strip()

    if not keyword:
        await update.message.reply_text("Формат:\n/add_mention Название конкурента")
        return

    watch_id = db.add_mention_watch(update.effective_chat.id, keyword)

    try:
        mentions = fetch_mentions(keyword)
    except Exception as e:
        logger.warning("Initial mention fetch failed: %s", e)
        mentions = []

    for m in mentions:
        db.mark_seen_if_new(watch_id, m["link"])

    await update.message.reply_text(
        f"✅ Слежу за упоминаниями #{watch_id}: «{keyword}»\n"
        f"Найдено {len(mentions)} текущих публикаций — они взяты за отправную точку, "
        "уведомления придут только о новых."
    )


async def list_watches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    prices = db.list_price_watches(chat_id)
    mentions = db.list_mention_watches(chat_id)

    if not prices and not mentions:
        await update.message.reply_text(
            "Список пуст. Добавьте через /add_price или /add_mention"
        )
        return

    lines = []
    if prices:
        lines.append("💰 Цены:")
        for w in prices:
            lines.append(f"#{w['id']} {w['name']} — {w['last_price'] or '—'}\n{w['url']}")

    if mentions:
        if lines:
            lines.append("")
        lines.append("📰 Упоминания:")
        for w in mentions:
            lines.append(f"#{w['id']} {w['keyword']}")

    await update.message.reply_text("\n".join(lines), disable_web_page_preview=True)


async def remove_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Формат: /remove_price <id>")
        return

    removed = db.remove_price_watch(update.effective_chat.id, int(context.args[0]))
    await update.message.reply_text("✅ Удалено" if removed else "❌ Не найдено")


async def remove_mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Формат: /remove_mention <id>")
        return

    removed = db.remove_mention_watch(update.effective_chat.id, int(context.args[0]))
    await update.message.reply_text("✅ Удалено" if removed else "❌ Не найдено")


async def check_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔎 Проверяю все источники...")
    await checks.check_for_chat(context.bot, update.effective_chat.id)
    await update.message.reply_text("✅ Проверка завершена")


async def scheduled_check(context: ContextTypes.DEFAULT_TYPE):
    logger.info("Running scheduled competitor check")
    await checks.check_all(context.bot)


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
    app.add_handler(CommandHandler("add_price", add_price))
    app.add_handler(CommandHandler("add_mention", add_mention))
    app.add_handler(CommandHandler("list", list_watches))
    app.add_handler(CommandHandler("remove_price", remove_price))
    app.add_handler(CommandHandler("remove_mention", remove_mention))
    app.add_handler(CommandHandler("check_now", check_now))
    app.add_error_handler(on_error)

    app.job_queue.run_repeating(
        scheduled_check,
        interval=timedelta(hours=config.CHECK_INTERVAL_HOURS),
        first=60,
    )

    print("🚀 Competitor Monitor Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
