import os.path as path
import threading
from queue import Queue

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from urlextract import URLExtract

from download import TelegraphDownloader
from env import *
from logger import logger
from search import ImageSearch

(MONITOR, EPUB) = range(2)
bot_token = str(BOT_TOKEN)
special_user_id = int(USER_ID)
telegraph_task_queue = Queue()

try:
    proxy = str(PROXY_URL)
except ValueError:
    proxy = None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_markdown(
        f"👀 Wink, {update.message.from_user.full_name}\n\n"
        f"Here is Neko-Chan, designed to turn Telegraph links into local manga source "
        f"that supports Komga and Tachiyomi, along with other useful features.\n\n"
        f"_Command instructions_:\n"
        f"`/monitor_start` : Start service for link fetching and image search, etc.\n"
        f"`/monitor_finish` : Neko-Chan stop read messages.\n"
        f"`/t2epub` : Read Telegraph link and send you converted epub book.\n\n"
        f"This [project](https://github.com/Ziang-Liu/Neko-Chan) will add more features in the future, "
        f"you can star it if you like this bot)."
    )

    return ConversationHandler.END


async def monitor_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('I will monitor messages now 👋\nYou can use /monitor_finish to stop')
    logger.info(f"USER {update.message.from_user.id}: start monitoring service")

    return MONITOR


async def epub_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send or forward me a telegraph manga post 😎")
    logger.info(f"USER {update.message.from_user.id}: start epub service")

    return EPUB


async def telegraph_thread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    # sync telegraph links to komga format
    if message.from_user.id == special_user_id:
        logger.info(f"USER {special_user_id}: {message.text.replace('\n', '->')}")

        urls = URLExtract().find_urls(message.text_markdown)
        [telegraph_task_queue.put(url) for url in [url for url in urls if "telegra.ph" in url]]


async def epub_thread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    async def send_epub():
        with open(path.join(down_instance.download_path, down_instance.title + '.epub'), 'rb') as book:
            logger.info(f"USER {message.from_user.id}: Send epub '{file}'")
            await context.bot.send_document(
                chat_id = message.chat_id, document = book,
                read_timeout = 60, connect_timeout = 60, write_timeout = 60)

    message = update.message
    # sync telegraph links to epub files and upload
    logger.info(f"USER {message.from_user.id}: {message.text.replace('\n', '->')}")
    down_instance = TelegraphDownloader()
    down_instance.download_path = DOWNLOAD_PATH
    urls = URLExtract().find_urls(message.text_markdown)
    down_instance.url = next((url for url in urls if "telegra.ph" in url), None)
    down_instance.get_title()

    if down_instance.url is None:
        await message.reply_text("I can not find valid link 🤔")

    try:
        down_instance.threads = int(DOWNLOAD_THREADS)
        down_instance.proxy = {"http": PROXY_URL, "https": PROXY_URL}
    except Exception as exception:
        logger.warning(exception)
        down_instance.threads = 4
        down_instance.proxy = None

    for file in os.listdir(down_instance.download_path):
        if down_instance.title + '.epub' == file:
            await send_epub()
            return ConversationHandler.END

    down_instance.pack_epub()
    await send_epub()

    return ConversationHandler.END


async def search_thread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    # use iqdb to search images
    logger.info(f"USER {message.from_user.id}: IMAGE {message.photo[2].file_id}")

    image_url = await context.bot.get_file(message.photo[2].file_id)
    search_instance = ImageSearch()
    search_instance.url = image_url.file_path
    search_instance.proxy = proxy
    await search_instance.sync()

    if search_instance.similarity >= 80:
        await message.reply_markdown(
            f"🔎 **_Auto image search result_**\n"
            f"🖼️ [Image]({search_instance.source_url}) from "
            f"{search_instance.source} with {search_instance.similarity}% similarity, "
            f"size {search_instance.size}")


async def finish_monitor_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"USER {update.message.from_user.id} finish monitoring service")
    await update.message.reply_text('See you next time 😊')

    return ConversationHandler.END


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"USER {update.message.from_user.id} trigger /cancel")
    return ConversationHandler.END


def start_thread(target, args):
    thread = threading.Thread(target = target, args = args)
    thread.daemon = True
    thread.start()


def telegraph_task(queue_input):
    while True:
        down_instance = TelegraphDownloader()
        down_instance.download_path = DOWNLOAD_PATH
        down_instance.url = queue_input.get()

        try:
            down_instance.threads = int(DOWNLOAD_THREADS)
            down_instance.proxy = {"http": PROXY_URL, "https": PROXY_URL}
        except Exception as exception:
            logger.warning(exception)
            down_instance.threads = 4
            down_instance.proxy = None

        down_instance.pack_zip()


if __name__ == "__main__":
    neko_chan = (
        ApplicationBuilder()
        .token(bot_token)
        .proxy(proxy)
        .get_updates_proxy(proxy)
        .build())

    start_handler = ConversationHandler(
        entry_points = [CommandHandler("start", start)],
        states = {},
        fallbacks = [],
    )

    monitor_handler = ConversationHandler(
        entry_points = [CommandHandler("monitor_start", monitor_service)],
        states = {
            MONITOR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, telegraph_thread),
                MessageHandler(filters.PHOTO & ~filters.COMMAND, search_thread),
                CommandHandler("monitor_finish", finish_monitor_service)
            ],
        },
        fallbacks = []
    )

    epub_handler = ConversationHandler(
        entry_points = [CommandHandler("t2epub", epub_service)],
        states = {
            EPUB: [MessageHandler(filters.TEXT & ~filters.COMMAND, epub_thread)]
        },
        fallbacks = [CommandHandler("cancel", callback)]
    )

    start_thread(target = telegraph_task, args = (telegraph_task_queue,))

    neko_chan.add_handler(start_handler)
    neko_chan.add_handler(monitor_handler)
    neko_chan.add_handler(epub_handler)

    try:
        logger.info("Neko Chan, link start!!!")
        neko_chan.run_polling(allowed_updates = Update.ALL_TYPES, timeout = 30)
    except Exception as e:
        logger.error(e)
        neko_chan.stop_running()
