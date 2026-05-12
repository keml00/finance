from telegram import Update, CallbackQuery
from telegram.ext import ContextTypes
from bot.services.transaction_service import get_monthly_stats


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = await get_monthly_stats(update.effective_user.id)
    text = format_stats(stats)
    await update.message.reply_text(text, parse_mode="Markdown")


async def show_stats(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    stats = await get_monthly_stats(query.from_user.id)
    text = format_stats(stats)
    await query.edit_message_text(text, parse_mode="Markdown")


def format_stats(stats: dict) -> str:
    months_ru = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
    }
    month_name = months_ru.get(stats["month"], "")

    income_str = f"{stats['total_income']:,.0f}".replace(",", " ")
    expense_str = f"{stats['total_expense']:,.0f}".replace(",", " ")
    balance_str = f"{stats['balance']:,.0f}".replace(",", " ")
    avg_str = f"{stats['avg_daily_expense']:,.0f}".replace(",", " ")

    text = (
        f"📈 *Статистика за {month_name} {stats['year']}*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 Доходы: `{income_str} ₽`\n"
        f"💸 Расходы: `{expense_str} ₽`\n"
        f"📊 Баланс: `{balance_str} ₽`\n"
        f"📅 Среднее в день: `{avg_str} ₽`\n"
        f"🔢 Операций: `{stats['transaction_count']}`\n\n"
    )

    if stats["categories"]:
        text += "*Топ расходов:*\n"
        for i, cat in enumerate(stats["categories"][:7], 1):
            cat_total = f"{cat['total']:,.0f}".replace(",", " ")
            pct = cat["total"] / max(stats["total_expense"], 1) * 100
            text += f"{cat['icon']} {cat['name']}: `{cat_total} ₽` ({pct:.0f}%)\n"

    return text
