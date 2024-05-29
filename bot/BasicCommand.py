from telegram import Update
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
)


async def introduce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_markdown(
        f"Heart heart heart, {update.message.from_user.full_name}\n\n"
        f"Meow~，这里是 Neko Chan (=^‥^=)，一个自托管的机器人，拥有许多实用的功能哦（TLDR）。"
        f"你可以使用 /help 来获取详细的命令列表喵~\n\n"
        f"如果你喜欢这个[项目](https://github.com/Ziang-Liu/Neko-Chan), 不妨给它点个 star ฅ(＾・ω・＾ฅ)。"
    )

    return ConversationHandler.END


async def instructions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_markdown(
        f"_Command List_:\n\n"
        f"/hug | /pet | /kiss | /cuddle | /snog : "
        f"只是对待猫猫的不同手段而已（搂搂抱抱随意选择），会根据你左滑消息引用的内容自动匹配出你想要什么 XD\n"
        f"/komga : "
        f"仅限于所有者填写环境变量中的个人ID后启用，使用命令后将Telegraph漫画交给猫猫就好，她会帮你妥善整理在服务器里的 c:\n"
    )

    return ConversationHandler.END
