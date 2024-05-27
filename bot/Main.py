from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, filters

import bot.BasicCommand as Basic
from bot.FunctionCommand import PandoraBox
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
    myself_id = env.get_variable("MY_USER_ID")
    # proxy_url = env.get_variable("PROXY")
    proxy_url = "http://127.0.0.1:7890"
    proxy = proxy_init(proxy_url)

    if not bot_token:
        logger.error("Bot token not set, please fill right params and try again.")
        exit(1)

    if not myself_id:
        logger.warning("Master's user id not set, telegraph syncing service will not work.")

    if not proxy:
        logger.info("Http proxy not set, make sure you can directly connect to telegram server.")

    # Hello there? Neko Chan is built!!!
    neko_chan = ApplicationBuilder().token(bot_token).proxy(proxy).get_updates_proxy(proxy).build()

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
            filters = filters.REPLY
        )
    )

    try:
        env.print_env()
        logger.info("Neko Chan, link start!!!")
        neko_chan.run_polling(allowed_updates = Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        exit(1)
