import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from logger import BotLogger

logger = BotLogger("telegram_media_bot")

WELCOME_MESSAGE = "Welcome to Part-Time Intelligence!"
HELP_MESSAGE = (
    "Available commands:\n"
    "/start — Start the bot\n"
    "/help — Show help\n"
    "/music — Generate music"
)
MUSIC_PROMPT_MESSAGE = "Send me a positive prompt for the music."


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Command received: /start")
    await update.message.reply_text(WELCOME_MESSAGE)
    logger.info("Response sent: /start")


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Command received: /help")
    await update.message.reply_text(HELP_MESSAGE)
    logger.info("Response sent: /help")


async def music(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Command received: /music")
    await update.message.reply_text(MUSIC_PROMPT_MESSAGE)
    logger.info("Response sent: /music")


async def on_error(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception(
        "Unexpected error while handling update: %s",
        context.error,
        exc_info=context.error,
    )


def main() -> None:
    load_dotenv()
    application = (
        Application.builder()
        .token(os.environ["TELEGRAM_BOT_TOKEN"])
        .build()
    )
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(CommandHandler("music", music))
    application.add_error_handler(on_error)
    logger.info("Bot backend started")
    application.run_polling()


if __name__ == "__main__":
    main()
