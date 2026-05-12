from telegram import Update, CallbackQuery
from telegram.ext import ContextTypes
from bot.services.transaction_service import get_balance


async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    accounts = await get_balance(update.effective_user.id)
    text = format_balance(accounts)
    await update.message.reply_text(text, parse_mode="Markdown")


async def show_balance(query: CallbackQuery, context: ContextTypes.DEFAULT_TYPE):
    accounts = await get_balance(query.from_user.id)
    text = format_balance(accounts)
    await query.edit_message_text(text, parse_mode="Markdown")


def format_balance(accounts: list[dict]) -> str:
    if not accounts:
        return "📊 У вас пока нет счетов. Отправьте первую транзакцию!"

    total = sum(a["balance"] for a in accounts)

    text = (
        "📊 *Баланс счетов*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    for acc in accounts:
        balance_str = f"{acc['balance']:,.2f}".replace(",", " ")
        text += f"{acc['icon']} *{acc['name']}*\n"
        text += f"    `{balance_str} {acc['currency']}`\n\n"

    total_str = f"{total:,.2f}".replace(",", " ")
    text += (
        "━━━━━━━━━━━━━━━━━━\n"
        f"💎 *Итого:* `{total_str} ₽`"
    )

    return text
