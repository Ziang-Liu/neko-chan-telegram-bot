from telegram import Update
from telegram.ext import ConversationHandler, ContextTypes


async def introduce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_markdown(
        f"👀 Wink, {update.message.from_user.full_name}\n"
        f"Here is Neko Chan, a self hosted bot featured with a lot of useful functions. You can use "
        f"/help to get detailed command list.\n"
        f"\nThis [project](https://github.com/Ziang-Liu/Neko-Chan) will add more features in the future, "
        f"you can star it if you like this bot)."
    )

    return ConversationHandler.END


async def instructions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_markdown(
        f"_Command List_:\n"
        f"/SyncTelegraph : Neko Chan will parse telegraph manga links from bot creator's message and "
        f"download those manga into your server.\n"
        f"/ConvertTelegraph2Epub : Parse single Telegraph link and send you converted epub book. However, "
        f"if the file size is beyond the official limitations(50MB), "
        f"Neko Chan will send you a temp file sharing link.\n"
    )

    return ConversationHandler.END
