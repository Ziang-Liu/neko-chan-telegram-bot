import os.path
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


async def monitor_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('IM WORKING ;)\nUse /monitor_finish to stop.')
    logger.info(f"USER {update.message.from_user.id} start monitoring service")

    return MONITOR


async def epub_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a message contains telegraph link")
    logger.info(f"USER {update.message.from_user.id} start epub service")

    return EPUB


async def telegraph_thread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    # sync telegraph links to komga format
    if message.from_user.id == special_user_id:
        logger.info(f"USER:{special_user_id}-Message:{message.text.replace('\n', '->next line:')}")

        urls = URLExtract().find_urls(message.text_markdown)
        [telegraph_task_queue.put(url) for url in [url for url in urls if "telegra.ph" in url]]


async def epub_thread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    # sync telegraph links to epub files and upload
    logger.info(f"USER:{special_user_id}-Message:{message.text.replace('\n', '->next line:')}")
    down_instance = TelegraphDownloader()
    down_instance.download_path = DOWNLOAD_PATH
    urls = URLExtract().find_urls(message.text_markdown)
    down_instance.url = next((url for url in urls if "telegra.ph" in url), None)
    down_instance.get_title()

    if down_instance.url is None:
        await message.reply_text("No valid link provided")

    try:
        down_instance.threads = int(DOWNLOAD_THREADS)
        down_instance.proxy = {"http": PROXY_URL, "https": PROXY_URL}
    except Exception as exception:
        logger.warning(exception)
        down_instance.threads = 4
        down_instance.proxy = None

    file_list = os.listdir(down_instance.download_path)

    if not any(file.startswith(down_instance.title) for file in file_list):
        down_instance.pack_epub()

    for file in os.listdir(down_instance.download_path):
        if file.startswith(down_instance.title):
            with open(os.path.join(down_instance.download_path, file), 'rb') as book:
                logger.info(f"Upload '{file}' to USER:{message.from_user.id}")
                await context.bot.send_document(
                    chat_id = message.chat_id, document = book,
                    read_timeout = 60, connect_timeout = 60, write_timeout = 60)

    return ConversationHandler.END


async def search_thread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    # use iqdb to search images
    logger.info(f"USER:{message.from_user.id}-PhotoID:{message.photo[2].file_unique_id}")

    image_url = await context.bot.get_file(message.photo[2].file_id)
    search_instance = ImageSearch()
    search_instance.url = image_url.file_path
    search_instance.proxy = proxy
    await search_instance.sync()

    if search_instance.similarity >= 80:
        await message.reply_text(
            f"---Auto image search---\n"
            f"Image URL: {search_instance.source_url}\n"
            f"Site: {search_instance.source}\n"
            f"Similarity: {search_instance.similarity}")


async def finish_monitor_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"USER {update.message.from_user.id} finish monitoring service")
    await update.message.reply_text('See you next time XD')

    return ConversationHandler.END


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    monitor_handler = ConversationHandler(
        entry_points = [CommandHandler("monitor_start", monitor_service)],
        states = {
            MONITOR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, telegraph_thread),
                MessageHandler(filters.PHOTO & ~filters.COMMAND, search_thread),
                CommandHandler("monitor_finish", finish_monitor_service)
            ],
        },
        fallbacks = [CommandHandler("cancel", callback)]
    )

    epub_handler = ConversationHandler(
        entry_points = [CommandHandler("t2epub", epub_service)],
        states = {
            EPUB: [MessageHandler(filters.TEXT & ~filters.COMMAND, epub_thread)]
        },
        fallbacks = [CommandHandler("cancel", callback)]
    )

    start_thread(target = telegraph_task, args = (telegraph_task_queue,))

    neko_chan.add_handler(monitor_handler)
    neko_chan.add_handler(epub_handler)

    try:
        logger.info("Neko Chan, link start!!!")
        neko_chan.run_polling(allowed_updates = Update.ALL_TYPES, timeout = 30)
    except Exception as e:
        logger.error(e)
        neko_chan.stop_running()
