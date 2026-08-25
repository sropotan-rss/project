import logging

from telegram import Bot

import db
from monitors.mentions import fetch_mentions
from monitors.price import PriceFetchError, fetch_price_text

logger = logging.getLogger(__name__)


async def check_price_watch(bot: Bot, watch: dict) -> None:
    try:
        current = fetch_price_text(watch["url"], watch["selector"])
    except PriceFetchError as e:
        logger.warning("Price check failed for watch #%s: %s", watch["id"], e)
        return

    previous = watch["last_price"]
    db.update_price(watch["id"], current)

    if previous is not None and current != previous:
        await bot.send_message(
            chat_id=watch["chat_id"],
            text=(
                f"💰 Изменение цены: {watch['name']}\n"
                f"{previous} → {current}\n"
                f"{watch['url']}"
            ),
        )


async def check_mention_watch(bot: Bot, watch: dict) -> None:
    try:
        mentions = fetch_mentions(watch["keyword"])
    except Exception as e:
        logger.warning("Mention check failed for watch #%s: %s", watch["id"], e)
        return

    new_items = [m for m in mentions if db.mark_seen_if_new(watch["id"], m["link"])]
    if not new_items:
        return

    lines = [f"📰 Новые упоминания «{watch['keyword']}»:"]
    for m in new_items[:10]:
        lines.append(f"• {m['title']}\n{m['link']}")

    await bot.send_message(
        chat_id=watch["chat_id"],
        text="\n\n".join(lines),
        disable_web_page_preview=True,
    )


async def check_all(bot: Bot) -> None:
    for watch in db.all_price_watches():
        await check_price_watch(bot, watch)
    for watch in db.all_mention_watches():
        await check_mention_watch(bot, watch)


async def check_for_chat(bot: Bot, chat_id: int) -> None:
    for watch in db.list_price_watches(chat_id):
        await check_price_watch(bot, watch)
    for watch in db.list_mention_watches(chat_id):
        await check_mention_watch(bot, watch)
