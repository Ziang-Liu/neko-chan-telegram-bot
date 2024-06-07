from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup


async def introduce(update: Update, _):
    await update.message.reply_markdown(
        f"Heart heart heart, {update.message.from_user.full_name}\n\n"
        f"这里是 Neko Chan (=^‥^=)，一个自托管的”高性能“机器人，拥有许多实用的功能哦（TLDR）。"
        f"想了解详细信息使用 /help 来获取命令列表与功能介绍喵~\n\n"
        f"如果你喜欢这个[项目](https://github.com/Ziang-Liu/Neko-Chan), 不妨给它点个 star ฅ(＾・ω・＾ฅ)。"
    )


async def instructions(update: Update, _):
    await update.message.reply_markdown(
        f"_Command List_:\n\n"
        f"/hug , /pet , /kiss , /cuddle , /snog :"
        f"只是对待猫猫的不同手段而已（搂搂抱抱随意选择），会根据你左滑消息引用的内容自动匹配出你想要什么"
        f"(filters.PHOTO: 搜图模式，filters.Document.IMAGE: 搜图模式，"
        f"filters.Sticker.ALL: 贴纸下载，message.text 包含 Telegraph 漫画: 上传 epub，message.text 包含链接：尝试链接搜图)\n"
        f"/komga [Auto close: 5min]:"
        f"仅限于所有者填写环境变量中的个人ID后启用，使用命令后将 Telegraph 漫画交给 Neko 就好，她会帮你妥善整理在服务器里的 c:\n"
        f"/chat [Fallback: /bye, Auto close: 5min]:"
        f"支持 ChatAnywhere API 的 GPT 模式，和 Neko 愉快交流吧！(免费令牌会时不时出现请求错误，后面考虑换一个接口)\n"
    )


async def handle_inline_button(update: Update, _):
    choices = [
        [InlineKeyboardButton("猫娘交流模式", callback_data = "gpt")],
        [InlineKeyboardButton("Telegraph 队列", callback_data = "komga")],
        [InlineKeyboardButton("帮助", callback_data = "help")],
        [InlineKeyboardButton("关于", callback_data = "start")],
    ]
    reply_markup = InlineKeyboardMarkup(choices)
    await update.message.reply_text("需要什么帮助瞄", reply_markup = reply_markup)
