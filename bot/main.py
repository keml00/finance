import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from bot.config import get_settings
from bot.handlers.start import start_handler, help_handler
from bot.handlers.income import income_handler, income_callback
from bot.handlers.expense import expense_handler, expense_callback
from bot.handlers.balance import balance_handler
from bot.handlers.stats import stats_handler
from bot.handlers.debts import debts_handler, debts_callback
from bot.handlers.goals import goals_handler, goals_callback
from bot.handlers.analytics import analytics_handler
from bot.handlers.settings_handler import settings_handler
from bot.handlers.messages import message_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main():
    settings = get_settings()

    app = ApplicationBuilder().token(settings.telegram_bot_token).build()

    # Commands
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("income", income_handler))
    app.add_handler(CommandHandler("expense", expense_handler))
    app.add_handler(CommandHandler("balance", balance_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("debts", debts_handler))
    app.add_handler(CommandHandler("goals", goals_handler))
    app.add_handler(CommandHandler("analytics", analytics_handler))
    app.add_handler(CommandHandler("settings", settings_handler))

    # Callbacks
    app.add_handler(CallbackQueryHandler(income_callback, pattern=r"^income_"))
    app.add_handler(CallbackQueryHandler(expense_callback, pattern=r"^expense_"))
    app.add_handler(CallbackQueryHandler(debts_callback, pattern=r"^debt_"))
    app.add_handler(CallbackQueryHandler(goals_callback, pattern=r"^goal_"))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.PHOTO, message_handler))

    logger.info("FinAI Assistant bot started!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
