from telegram import Update
from telegram.ext import ContextTypes
from bot.services.transaction_service import get_monthly_stats
from bot.services.ai_service import get_financial_advice


async def analytics_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Анализирую ваши финансы...")

    stats = await get_monthly_stats(update.effective_user.id)

    if stats["transaction_count"] == 0:
        await update.message.reply_text(
            "📊 Недостаточно данных для анализа.\n"
            "Начните добавлять транзакции!"
        )
        return

    advice = await get_financial_advice(stats)

    text = (
        "🤖 *AI-аналитика*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{advice}"
    )

    await update.message.reply_text(text, parse_mode="Markdown")
