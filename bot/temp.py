import asyncio
import concurrent.futures
import os
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

from src.Environment import EnvironmentReader
from src.service.Search import AggregationSearch
from src.service.Telegraph import Telegraph
from src.utils.Logger import logger

constants = EnvironmentReader()
bot_token = constants.get_variable('BOT_TOKEN')
proxy = constants.get_variable('HTTP_PROXY')
myself = constants.get_variable('SELF_USER_ID')
komga_path = constants.get_variable('KOMGA_PATH')
epub_path = constants.get_variable('EPUB_PATH')
threads = constants.get_variable('TELEGRAPH_MAX_THREAD')

telegraph_queue = Queue()
image_queue = Queue()

(MONITOR, EPUB) = range(2)


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


async def monitor_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"USER {update.message.from_user.id}: start monitoring service")
    await update.message.reply_text('I will monitor messages now 👋\nYou can use /monitor_finish to stop')

    return MONITOR


async def t2epub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"USER {update.message.from_user.id}: start epub service")
    await update.message.reply_text("Send or forward me a telegraph manga post 😎")

    return EPUB


async def fetch_telegraph_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handled by monitor_handler, only read specific user id's text message and add
    contained telegraph links to the queue
    """
    if update.message.from_user.id == myself:
        log_message = update.message.text.replace('\n', '->')
        logger.info(f"USER {myself}: {log_message}")
        urls = URLExtract().find_urls(update.message.text_markdown)
        [telegraph_queue.put(url) for url in [url for url in urls if "telegra.ph" in url]]


async def epub_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handled by epub_handler, search local directory for existed epub or
    be downloaded and converted to epub from telegraph link then upload it to the user
    """

    async def upload():
        with open(os.path.join(epub.download_path, epub.title_raw + '.epub'), 'rb') as book:
            logger.info(f"USER {update.message.from_user.id}: Send epub '{file}'")
            await context.bot.send_document(
                chat_id = update.message.chat_id, document = book,
                read_timeout = 60, connect_timeout = 60, write_timeout = 60)

    log_message = update.message.text.replace('\n', '->')
    logger.info(f"USER {update.message.from_user.id}: {log_message}")
    urls = URLExtract().find_urls(update.message.text_markdown)

    epub = Telegraph()
    epub.download_path = epub_path
    epub._threads = threads
    epub._proxy = {"http": proxy, "https": proxy}
    url = next((url for url in urls if "telegra.ph" in url), None)
    epub.get_info(url)

    if url is None:
        await update.message.reply_text("I can not find valid link 🤔")

    for file in os.listdir(epub.download_path):
        if epub.title_raw + '.epub' == file:
            await upload()

            return ConversationHandler.END

    epub.get_epub(url)
    await upload()

    return ConversationHandler.END


async def fetch_image_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handled by monitor_handler, use PicImageSearch API to search photo type messages
    """
    logger.info(f"USER {update.message.from_user.id}: IMAGE {update.message.photo[2].file_id}")
    image_url = (await context.bot.get_file(update.message.photo[2].file_id)).file_path
    image_queue.put(image_url)


async def image_search(update: Update):
    while True:
        async def search_thread(queue):
            search = AggregationSearch()
            await search.iqdb_search(queue.get(), proxy)

            if search.similarity >= 80.0:
                await update.message.reply_markdown(
                    f"🔎 **_Auto image search result_**\n"
                    f"🖼️ [Image]({search.url}) from "
                    f"{search.source} with {search.similarity}% similarity, "
                    f"size {search.image_size}")

        with concurrent.futures.ThreadPoolExecutor(max_workers = 4) as executor:
            future_to_queue = {executor.submit(search_thread)}

            for future in concurrent.futures.as_completed(future_to_queue):
                await future.result()

        await asyncio.sleep(5)


async def monitor_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"USER {update.message.from_user.id} finish monitoring service")
    await update.message.reply_text('See you next time 😊')

    return ConversationHandler.END


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update:", exc_info = context.error)


async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"USER {update.message.from_user.id} trigger callback")
    return ConversationHandler.END


def create_thread(target, args):
    thread = threading.Thread(target = target, args = args)
    thread.daemon = True
    thread.start()


def telegraph_thread(queue_input):
    """
    Create a thread to monitor telegraph link queue and trigger pack_zip() task
    """
    while True:
        down_instance = Telegraph()
        down_instance.download_path = komga_path
        down_instance._threads = threads
        down_instance._proxy = {"http": proxy, "https": proxy}
        down_instance.get_zip(queue_input.get())


if __name__ == "__main__":
    start_handler = ConversationHandler(
        entry_points = [CommandHandler("start", start)],
        states = {}, fallbacks = [])

    monitor_handler = ConversationHandler(
        entry_points = [CommandHandler("monitor_start", monitor_start)],
        states = {
            MONITOR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, fetch_telegraph_link),
                MessageHandler(filters.PHOTO & ~filters.COMMAND, fetch_image_link),
                CommandHandler("monitor_finish", monitor_finish)]},
        fallbacks = [])

    epub_handler = ConversationHandler(
        entry_points = [CommandHandler("t2epub", t2epub)],
        states = {EPUB: [MessageHandler(filters.TEXT & ~filters.COMMAND, epub_upload)]},
        fallbacks = [CommandHandler("cancel", callback)])

    create_thread(target = telegraph_thread, args = (telegraph_queue,))

    neko_chan = (ApplicationBuilder().token(bot_token).proxy(proxy).get_updates_proxy(proxy).build())
    neko_chan.add_handler(start_handler)
    neko_chan.add_handler(monitor_handler)
    neko_chan.add_handler(epub_handler)
    neko_chan.add_error_handler(error_handler)

    try:
        logger.info("Neko Chan, link start!!!")
        neko_chan.run_polling(
            allowed_updates = Update.ALL_TYPES, timeout = 60)
    except Exception as exception:
        logger.error(exception)
        neko_chan.stop_running()
