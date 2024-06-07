import os

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from bot import (
    Basic,
    ChatHandler,
    GPT_OK,
    GPT_INIT,
    KOMGA,
    PandoraBox,
    TelegraphHandler
)
from src import (
    EnvironmentReader,
    logger,
    proxy_init
)

if __name__ == "__main__":
    async def error_handler(_, context: ContextTypes.DEFAULT_TYPE):
        logger.error(context.error)


    # this project's working dirs are all declared here
    working_dirs = ['/neko/komga', '/neko/dmzj', '/neko/epub', '/neko/.temp']
    [os.makedirs(name = working_dir, exist_ok = True, mode = 0o777) for working_dir in working_dirs]

    print(R"""
              _   _          _                 ____   _                      
             | \ | |   ___  | | __   ___      / ___| | |__     __ _   _ __   
             |  \| |  / _ \ | |/ /  / _ \    | |     | '_ \   / _` | | '_ \  
             | |\  | |  __/ |   <  | (_) |   | |___  | | | | | (_| | | | | | 
             |_| \_|  \___| |_|\_\  \___/     \____| |_| |_|  \__,_| |_| |_| 
    """)

    _env = EnvironmentReader()
    _base_url = _env.get_variable("BASE_URL")
    _base_file_url = _env.get_variable("BASE_FILE_URL")
    _bot_token = _env.get_variable("BOT_TOKEN")
    _myself_id = _env.get_variable("MY_USER_ID")
    _proxy = _env.get_variable("PROXY")
    _gpt_key = _env.get_variable("CHAT_ANYWHERE_KEY")

    if not _bot_token:
        logger.error("[Main]: Bot token not set, please fill right params and try again.")
        exit(1)

    if _proxy:
        proxy = proxy_init(_proxy)
        neko_chan = (ApplicationBuilder().token(_bot_token).
                     proxy(proxy).get_updates_proxy(proxy).
                     pool_timeout(30.).connect_timeout(30.).
                     base_url(_base_url).base_file_url(_base_file_url).build())
    else:
        proxy = None
        logger.info("[Main]: Proxy not set, make sure you can directly connect to telegram server.")
        neko_chan = (ApplicationBuilder().token(_bot_token).
                     pool_timeout(30.).connect_timeout(30.).
                     base_url(_base_url).base_file_url(_base_file_url).build())

    neko_chan.add_handler(CommandHandler("start", Basic.introduce))
    neko_chan.add_handler(CommandHandler("help", Basic.instructions))

    pandora = PandoraBox(proxy = proxy)
    auto_parse_reply = CommandHandler(
        command = ["hug", "cuddle", "kiss", "snog", "pet"], callback = pandora.auto_parse_reply,
        filters = filters.REPLY | filters.TEXT
    )
    neko_chan.add_handler(auto_parse_reply)

    if _myself_id == -1:
        logger.info("[Main]: Master's user id not set, telegraph syncing service will not work.")
    else:
        telegraph = TelegraphHandler(proxy = proxy, user_id = _myself_id)
        telegraph_conversation = ConversationHandler(
            entry_points = [CommandHandler(command = "komga", callback = telegraph.komga_start)],
            states = {KOMGA: [MessageHandler(filters = filters.TEXT, callback = telegraph.add_task)]},
            fallbacks = [],
            conversation_timeout = 300
        )
        neko_chan.add_handler(telegraph_conversation)

    chat_mode = ChatHandler(
        proxy = proxy,
        user_id = int(_myself_id) if _myself_id else None,
        key = _gpt_key if _gpt_key else None
    )
    gpt_mode = ConversationHandler(
        entry_points = [CommandHandler(command = "chat", callback = chat_mode.key_init)],
        states = {
            GPT_INIT: [MessageHandler(filters = filters.TEXT & ~filters.COMMAND, callback = chat_mode.get_key)],
            GPT_OK: [MessageHandler(filters = filters.TEXT & ~filters.COMMAND, callback = chat_mode.chat)]
        },
        conversation_timeout = 300,
        fallbacks = [CommandHandler(command = "bye", callback = chat_mode.finish_chat)]
    )

    neko_chan.add_handler(gpt_mode)

    neko_chan.add_error_handler(error_handler)

    try:
        _env.print_env()
        logger.info("[Main]: Neko Chan, link start!!!")
        neko_chan.run_polling(allowed_updates = Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"[Main]: An error occurred: {e}")
        exit(1)
