from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ConversationHandler, filters, MessageHandler

import bot.BasicCommand as Basic
from bot.FunctionCommand import PandoraBox, TelegraphHandler, KOMGA
from src.Environment import EnvironmentReader
from src.utils.Logger import logger
from src.utils.Proxy import proxy_init

if __name__ == "__main__":
    logger.info("""
      _   _          _                 ____   _                      
     | \ | |   ___  | | __   ___      / ___| | |__     __ _   _ __   
     |  \| |  / _ \ | |/ /  / _ \    | |     | '_ \   / _` | | '_ \  
     | |\  | |  __/ |   <  | (_) |   | |___  | | | | | (_| | | | | | 
     |_| \_|  \___| |_|\_\  \___/     \____| |_| |_|  \__,_| |_| |_| 
    """)
    # import envs
    env = EnvironmentReader()
    # bot_token = env.get_variable("BOT_TOKEN")
    bot_token = "6707614408:AAHgM84j-lpvFr2wzDR-N42sdnEb4tsQrD0"
    # myself_id = env.get_variable("MY_USER_ID")
    myself_id = 5229239723
    # proxy_env = env.get_variable("PROXY")
    proxy_env = "http://127.0.0.1:7890"

    if not bot_token:
        logger.error("Bot token not set, please fill right params and try again.")
        exit(1)

    if not myself_id:
        logger.warning("Master's user id not set, telegraph syncing service will not work.")

    # Hello there? Neko Chan is built!!!
    if proxy_env:
        proxy = proxy_init(proxy_env)
        neko_chan = ApplicationBuilder().token(bot_token).proxy(proxy).get_updates_proxy(proxy).build()
    else:
        proxy = None
        neko_chan = ApplicationBuilder().token(bot_token).build()

    if not proxy:
        logger.info("Proxy not set, make sure you can directly connect to telegram server.")

    # Base Handlers
    command_start = CommandHandler("start", Basic.introduce)
    command_help = CommandHandler("help", Basic.instructions)
    neko_chan.add_handler(command_start)
    neko_chan.add_handler(command_help)

    # Featured Handlers
    pandora = PandoraBox(proxy)
    neko_chan.add_handler(
        CommandHandler(
            command = ["hug", "cuddle", "kiss", "snog", "pet"], callback = pandora.query,
            filters = filters.REPLY | filters.TEXT
        )
    )

    telegraph_tasks = TelegraphHandler(proxy = proxy, user_id = myself_id)
    telegraph_message = ConversationHandler(
        entry_points = [CommandHandler(command = "komga", callback = telegraph_tasks.komga_start)],
        states = {
            KOMGA: [MessageHandler(filters = filters.TEXT, callback = telegraph_tasks.get_link)]
        },
        fallbacks = []
    )
    neko_chan.add_handler(telegraph_message)

    try:
        env.print_env()
        logger.info("[Main]: Neko Chan, link start!!!")
        neko_chan.run_polling(allowed_updates = Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"[Main]: An error occurred: {e}")
        exit(1)
