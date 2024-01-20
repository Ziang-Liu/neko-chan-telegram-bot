import os
from env import *
from logger import logger
from urlextract import URLExtract
from telegram import Update, Chat
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

# import from env (used by docker)
bot_token = TGBOT_TOKEN
download_path = DOWNLOAD_PATH

TELEGRAPH_EPUB_LINK_RECEIVED, TELEGRAPH_KOMGA_LINK_RECEIVED, TASK_KOMGA_COMPLETE, TASK_EPUB_COMPLETE = range(4)
#->telegraph message logic start
async def start_tgraph_komga(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Send me messages contain telegraph links.\nUse /komga_complete to stop.')
    logger.info("BOT SERVICE(Komga): Start Telegraph to Komga task.")
    return TELEGRAPH_KOMGA_LINK_RECEIVED
##########↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓##########################################################
async def telegraph_komga_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message.text_markdown
    logger.info("BOT SERVICE(Message): Receive message %s", message)
    urls = URLExtract().find_urls(message) # 提取消息包含的所有链接
    telegraph_urls = [url for url in urls if "telegra.ph" in url] # 筛选出 telegraph 链接
    # 把链接写入 temp_file
    current_directory = os.path.dirname(__file__)
    if len(telegraph_urls) != 0:
        with open(os.path.join(current_directory,'temp_komga_link'), "a", encoding='utf-8') as file:
            for url in telegraph_urls:
                file.write(url + '\n')
                logger.info(f"BOT SERVICE(Komga): {url} is added.")
        await update.message.reply_text('Link received.')
    
    return TELEGRAPH_KOMGA_LINK_RECEIVED

async def task_komga_complete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("BOT SERVICE(Komga): User finished sending links.")
    if os.path.exists(os.path.join(os.path.dirname(__file__), "temp_komga_link")):
        await update.message.reply_text('Links are collected and will be downloaded to your server.')
        os.rename('temp_komga_link', 'komga_link')
    else:
        await update.message.reply_text('No valid links provided.')

    #return TASK_KOMGA_COMPLETE
    return ConversationHandler.END
#<-telegraph message logic end
'''
#->epub message logic start
async def start_tgraph_epub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("Epub: '/tgraph_2_epub' trigered")
    await update.message.reply_text('Send me messages contain telegraph links. If you want to stop, use /epub_complete')
    return TELEGRAPH_EPUB_LINK_RECEIVED
##########↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓↓##########################################################
async def telegraph_epub_link_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message.text_markdown
    logger.info("Epub: Receive message %s", message)
    url = URLExtract().find_urls(message)
    telegraph_urls = [i for i in url if "telegra.ph" in i]
    current_directory = os.path.dirname(__file__)
    if len(telegraph_urls) != 0:
        with open(os.path.join(current_directory,'epub_link'), "w", encoding='utf-8') as file:
            for url in telegraph_urls:
                file.write(url)
                logger.info("Epub: {} is added to 'epub_link'".format(url))
        await update.message.reply_text('EPUB: Telegraph link received')

    return TELEGRAPH_EPUB_LINK_RECEIVED

async def task_epub_complete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    chat_id = update.message.chat_id
    logger.info("Epub: Func telegraph_link_received() closed.")
    epub_found = False
    for file in os.listdir(download_path):
        if file.endswith('.epub'):
            epub_found = True  # 如果找到了.epub文件, 则True
            await update.message.reply_text(f"Uploading '{file}', please wait a few seconds.")
            with open(os.path.join(download_path, file), 'rb') as f:
                await context.bot.send_document(chat_id, f)
            os.remove(os.path.join(download_path, file))
    if not epub_found:
        await update.message.reply_text('EPUB: No valid links provided.')
        
    return TASK_EPUB_COMPLETE
#<-epub message logic end
'''
#->fallback handler start
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info("BOT SERVICE: Conversation canceled or Fallback is triggered.")
    
    return ConversationHandler.END
#<-fallback handler end

def main() -> None:

    #启动bot
    application = ApplicationBuilder().token(bot_token).build()
    
    tgraph_komga_handler = ConversationHandler(
        entry_points=[CommandHandler("tgraph_2_komga", start_tgraph_komga)], # >>接受 /tgraph_2_komga
        states={
            TELEGRAPH_KOMGA_LINK_RECEIVED: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, telegraph_komga_link_received), # >>接受链接
                CommandHandler("komga_complete", task_komga_complete) # >>停止接受链接
                ],
            #TASK_KOMGA_COMPLETE: [MessageHandler(filters.COMMAND, cancel)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    '''
    tgraph_epub_handler = ConversationHandler(
        entry_points=[CommandHandler("tgraph_2_epub", start_tgraph_epub)], # >>接受 /tgraph_2_epub
        states={
            TELEGRAPH_EPUB_LINK_RECEIVED: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, telegraph_epub_link_received),
                CommandHandler("epub_complete", task_epub_complete)
                ],
            TASK_EPUB_COMPLETE: [MessageHandler(filters.COMMAND, cancel)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    '''
    application.add_handler(tgraph_komga_handler)
    #application.add_handler(tgraph_epub_handler)
    #application.add_error_handler(callback = cancel, block = True)
    # Run the bot until the user presses Ctrl-C
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception:
        logger.error('BOT SERVICE: Unexpected timeout error, quiting...')
        return

if __name__ == "__main__":
    main()
