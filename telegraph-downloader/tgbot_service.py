import logging, os
from env import *
from urlextract import URLExtract
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# import from env (used by docker)
proxy_url = PROXY_URL
bot_token = TGBOT_TOKEN

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

TASK_COMPLETE, TELEGRAPH_KOMGA_LINK_RECEIVED, TELEGRAPH_EPUB_LINK_RECEIVED = range(3)

async def start_tgraph_komga(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Send me messages contain telegraph links. If you want to stop, use /complete')
    logger.info("Command '/tgraph_2_komga' trigered")
    return TELEGRAPH_KOMGA_LINK_RECEIVED

'''
async def start_tgraph_epub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Send me a message contains telegraph links.')
    return TELEGRAPH_EPUB_LINK_RECEIVED
'''

async def telegraph_komga_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message.text_markdown
    logger.info("Receive message %s", message)
    urls = URLExtract().find_urls(message) # 提取消息包含的所有链接
    telegraph_urls = [url for url in urls if "telegra.ph" in url] # 筛选出 telegraph 链接
    # 把链接写入 temp_file
    current_directory = os.path.dirname(__file__)
    with open(os.path.join(current_directory,'temp_file'), "a", encoding='utf-8') as file:
        for url in telegraph_urls:
            file.write(url + '\n')
            logger.info(f"{url} is added to 'temp_file'")
        logger.info("links are stored")
    await update.message.reply_text('Telegraph link received')
    
    return TELEGRAPH_KOMGA_LINK_RECEIVED

# epub logics, writing...
'''
async def telegraph_zip_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    message = update.message.text_markdown
    logger.info("Received Text %s %s", user.first_name, message)
    url = URLExtract().find_urls(message)
    telegraph_url = [i for i in url if "telegra.ph" in i]
    directory_path = os.path.join(os.getcwd(), 'Download', 'ziphandler')
    os.makedirs(directory_path, exist_ok=True)
    start_download(telegraph_url, None, directory_path)

    return ConversationHandler.END
'''

async def task_complete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("User end task 'telegraph_link_received'.")
    await update.message.reply_text('Links are collected.')
    os.rename('temp_file', 'links')

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("User canceled the conversation.")
    await update.message.reply_text('User canceled the conversation.')

    return ConversationHandler.END

def main() -> None:

    #启动bot
    application = ApplicationBuilder().token(bot_token).proxy(proxy_url).get_updates_proxy(proxy_url).build()
    
    tgraph_komga_handler = ConversationHandler(
        entry_points=[CommandHandler("tgraph_2_komga", start_tgraph_komga)], # >>接受 /tgraph_2_komga
        states={
            TELEGRAPH_KOMGA_LINK_RECEIVED: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, telegraph_komga_link_received), # >>接受链接
                CommandHandler("complete", task_complete) # >>停止接受链接
                ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(tgraph_komga_handler)
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
