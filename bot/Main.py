from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler

import bot.BasicCommand as Basic
from bot.FunctionCommand import Search
from src.Environment import EnvironmentReader
from src.utils.Logger import logger
from src.utils.Proxy import proxy_init

if __name__ == "__main__":
    # import envs
    env = EnvironmentReader()
    # bot_token = env.get_variable("BOT_TOKEN")
    bot_token = "6707614408:AAG6nQbYkln_lowLSC95p57eTvQbatYo32M"
    myself_id = env.get_variable("MY_USER_ID")
    # proxy_url = env.get_variable("PROXY")
    proxy_url = "socks5://127.0.0.1:7891"
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
    search_instance = Search(proxy)

    # Command Handlers
    command_start = CommandHandler("start", Basic.introduce)
    command_help = CommandHandler("help", Basic.instructions)
    hug_neko_chan = CommandHandler("hug", search_instance.query)
    # Conversation Handlers

    # Add handlers
    neko_chan.add_handler(command_start)
    neko_chan.add_handler(command_help)
    neko_chan.add_handler(hug_neko_chan)

    try:
        env.print_env()
        logger.info("Neko Chan, link start!!!")
        neko_chan.run_polling(allowed_updates = Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        exit(1)
