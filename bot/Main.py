from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler

import bot.BasicCommand as Basic
from bot.FunctionCommand import Search
from src.Environment import EnvironmentReader
from src.utils.Logger import logger

if __name__ == "__main__":
    # import envs
    env = EnvironmentReader()
    bot_token = env.get_variable("BOT_TOKEN")
    myself_id = env.get_variable("MY_USER_ID")
    proxy = env.get_variable("HTTP_PROXY")

    if bot_token is None:
        logger.error("Bot token not set, please fill right params and try again.")
        exit(1)
    if myself_id is None:
        logger.warning("My ID not set, telegraph syncing service will not work.")

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
        neko_chan.run_polling(allowed_updates = Update.ALL_TYPES, timeout = 60)
    except Exception as e:
        logger.error(e)
        neko_chan.stop_running()
