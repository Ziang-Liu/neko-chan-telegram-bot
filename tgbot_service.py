import logging, os
from dotenv import load_dotenv
from urlextract import URLExtract
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

#load ".env"
load_dotenv()
bot_token = os.getenv('TGBOT_TOKEN')

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

#定义状态值
TASK_COMPLETE, TELEGRAPH_KOMGA_LINK_RECEIVED, TELEGRAPH_ZIP_LINK_RECEIVED = range(3)

#接受"/telegraph"执行
async def start_tgraph_komga(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Send me messages contain telegraph links, then use /complete to stop.')
    
    return TELEGRAPH_KOMGA_LINK_RECEIVED

async def start_tgraph_zip(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Send me a message contains telegraph links.')

    return TELEGRAPH_ZIP_LINK_RECEIVED

async def telegraph_komga_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    message = update.message.text_markdown
    logger.info("Received Text %s %s", user.first_name, message)
    
    urls = URLExtract().find_urls(message) #提取消息包含的所有链接
    telegraph_urls = [url for url in urls if "telegra.ph" in url] #筛选出 telegraph 链接
    #把链接写入临时文件
    current_directory = os.path.dirname(__file__)
    with open(os.path.join(current_directory,'temp_file'), "a", encoding='utf-8') as file:
        for url in telegraph_urls:
            file.write(url + '\n')
    
    await update.message.reply_text('Link received')
    
    return TELEGRAPH_KOMGA_LINK_RECEIVED

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
    user = update.message.from_user
    logger.info("User %s end task 'telegraph_link_received'.", user.first_name)
    await update.message.reply_text('Links are collected.')
    os.rename('temp_file', 'links')

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text('User canceled the conversation.')

    return ConversationHandler.END

def main() -> None:
    
    #启动bot
    application = Application.builder().token(bot_token).build()

    tgraph_komga_handler = ConversationHandler(
        entry_points=[CommandHandler("tgraph_2_komga", start_tgraph_komga)], #接受'/tgraph_2_komga'指令
        states={
            TELEGRAPH_KOMGA_LINK_RECEIVED: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, telegraph_komga_link_received),
                CommandHandler("complete", task_complete)
                ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    '''
    tgraph_zip_handler = ConversationHandler(
        entry_points=[CommandHandler("tgraph_2_zip",start_tgraph_zip)],
        states={
            TELEGRAPH_ZIP_LINK_RECEIVED: [MessageHandler(filters.TEXT & ~filters.COMMAND, telegraph_zip_link_received)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    '''
    application.add_handler(tgraph_komga_handler)
    #application.add_handler(tgraph_zip_handler)
    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
