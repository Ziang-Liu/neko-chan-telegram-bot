from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# custom
from bot import (
    Basic,
    KOMGA,  # var
    PandoraBox,  # class
    TelegraphHandler  # class
)
from src import (
    EnvironmentReader,  # class
    logger,  # var
    proxy_init  # fun
)

# from httpx import RemoteProtocolError

if __name__ == "__main__":
    async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
        """
        if RemoteProtocolError:
            logger.error("这种情况一般是代理状态下切换节点导致TCP连接中断\n 建议：使用手动模式 | 替换官方Api")
        """
        logger.error(context.error)


    # ascii logo
    logger.info("""
      _   _          _                 ____   _                      
     | \ | |   ___  | | __   ___      / ___| | |__     __ _   _ __   
     |  \| |  / _ \ | |/ /  / _ \    | |     | '_ \   / _` | | '_ \  
     | |\  | |  __/ |   <  | (_) |   | |___  | | | | | (_| | | | | | 
     |_| \_|  \___| |_|\_\  \___/     \____| |_| |_|  \__,_| |_| |_| 
    """)

    # environment var
    _env = EnvironmentReader()
    _base_url = _env.get_variable("BASE_URL")
    _base_file_url = _env.get_variable("BASE_FILE_URL")
    _bot_token = _env.get_variable("BOT_TOKEN")
    _myself_id = _env.get_variable("MY_USER_ID")
    _proxy = _env.get_variable("PROXY")

    if not _bot_token:
        logger.error("[Main]: Bot token not set, please fill right params and try again.")
        exit(1)

    # Hello there? Neko Chan is built!!!
    if _proxy:
        proxy = proxy_init(_proxy)
        neko_chan = (ApplicationBuilder().token(_bot_token).
                     proxy(proxy).get_updates_proxy(proxy).
                     pool_timeout(30.).connect_timeout(30.).
                     base_url(_base_url).base_file_url(_base_file_url).build())
    else:
        proxy = None
        neko_chan = (ApplicationBuilder().token(_bot_token).
                     pool_timeout(30.).connect_timeout(30.).
                     base_url(_base_url).base_file_url(_base_file_url).build())

    if not proxy:
        logger.info("[Main]: Proxy not set, make sure you can directly connect to telegram server.")

    # Base Handlers
    command_start = CommandHandler("start", Basic.introduce)
    command_help = CommandHandler("help", Basic.instructions)
    neko_chan.add_handler(command_start)
    neko_chan.add_handler(command_help)

    # Featured Handlers
    pandora = PandoraBox(proxy)  # standalone async process

    neko_chan.add_handler(
        CommandHandler(
            command = ["hug", "cuddle", "kiss", "snog", "pet"], callback = pandora.auto_parse_reply,
            filters = filters.REPLY | filters.TEXT
        )
    )

    if not _myself_id:
        logger.info("[Main]: Master's user id not set, telegraph syncing service will not work.")
    else:
        telegraph = TelegraphHandler(proxy = proxy, user_id = int(_myself_id))

        telegraph_message = ConversationHandler(
            entry_points = [CommandHandler(command = "komga", callback = telegraph.komga_start)],
            states = {
                KOMGA: [MessageHandler(filters = filters.TEXT, callback = telegraph.put_link_for_komga)]
            },
            fallbacks = [],
            conversation_timeout = 300
        )

        neko_chan.add_handler(telegraph_message)

    # error handler
    neko_chan.add_error_handler(error_handler)

    try:
        _env.print_env()
        logger.info("[Main]: Neko Chan, link start!!!")
        neko_chan.run_polling(allowed_updates = Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"[Main]: An error occurred: {e}")
        exit(1)
