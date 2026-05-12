import re
from decimal import Decimal, InvalidOperation
from telegram import Update
from telegram.ext import ContextTypes
from bot.services.transaction_service import add_transaction
from bot.services.ai_service import ai_analyze
from bot.services.user_service import get_or_create_user
from bot.database.models import TransactionType


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages - quick transaction input or AI chat."""
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    user = await get_or_create_user(update.effective_user)

    # Try to parse as quick transaction
    tx_result = await try_parse_transaction(text, update.effective_user.id)
    if tx_result:
        await update.message.reply_text(tx_result, parse_mode="Markdown")
        return

    # Handle awaiting states
    awaiting = context.user_data.get("awaiting")
    if awaiting == "income":
        result = await handle_income_input(text, update.effective_user.id, context)
        await update.message.reply_text(result, parse_mode="Markdown")
        context.user_data.pop("awaiting", None)
        return

    if awaiting == "expense":
        result = await handle_expense_input(text, update.effective_user.id, context)
        await update.message.reply_text(result, parse_mode="Markdown")
        context.user_data.pop("awaiting", None)
        return

    if awaiting == "debt_add":
        result = await handle_debt_input(text, update.effective_user.id, context)
        await update.message.reply_text(result, parse_mode="Markdown")
        context.user_data.pop("awaiting", None)
        return

    if awaiting == "goal_add":
        result = await handle_goal_input(text, update.effective_user.id, context)
        await update.message.reply_text(result, parse_mode="Markdown")
        context.user_data.pop("awaiting", None)
        return

    # AI chat fallback
    response = await ai_analyze(text)
    await update.message.reply_text(response, parse_mode="Markdown")


async def try_parse_transaction(text: str, telegram_id: int) -> str | None:
    """Try to parse quick transaction format: '500 кофе' or '+50000 зп'"""

    # Pattern: +amount description (income)
    match = re.match(r'^\+\s*(\d+[\d\s.,]*)\s*(.*)$', text)
    if match:
        amount = parse_amount(match.group(1))
        if amount:
            desc = match.group(2).strip() or "Доход"
            await add_transaction(
                telegram_id=telegram_id,
                amount=amount,
                transaction_type=TransactionType.INCOME,
                description=desc,
            )
            amount_str = f"{float(amount):,.0f}".replace(",", " ")
            return f"✅ Доход записан!\n💰 `+{amount_str} ₽` — {desc}"

    # Pattern: -amount description or just amount description (expense)
    match = re.match(r'^-?\s*(\d+[\d\s.,]*)\s+(.+)$', text)
    if match:
        amount = parse_amount(match.group(1))
        if amount and amount < Decimal("10000000"):  # sanity check
            desc = match.group(2).strip()
            await add_transaction(
                telegram_id=telegram_id,
                amount=amount,
                transaction_type=TransactionType.EXPENSE,
                description=desc,
            )
            amount_str = f"{float(amount):,.0f}".replace(",", " ")
            return f"✅ Расход записан!\n💸 `-{amount_str} ₽` — {desc}"

    return None


def parse_amount(text: str) -> Decimal | None:
    """Parse amount from text, handling spaces and commas."""
    try:
        cleaned = text.replace(" ", "").replace(",", ".")
        amount = Decimal(cleaned)
        if amount > 0:
            return amount
    except (InvalidOperation, ValueError):
        pass
    return None


async def handle_income_input(text: str, telegram_id: int, context) -> str:
    amount = parse_amount(text.split()[0] if text.split() else text)
    if not amount:
        return "❌ Не могу распознать сумму. Попробуйте: `50000`"

    desc = " ".join(text.split()[1:]) or context.user_data.get("income_category", "Доход")
    await add_transaction(
        telegram_id=telegram_id,
        amount=amount,
        transaction_type=TransactionType.INCOME,
        description=desc,
    )
    amount_str = f"{float(amount):,.0f}".replace(",", " ")
    return f"✅ Доход записан!\n💰 `+{amount_str} ₽` — {desc}"


async def handle_expense_input(text: str, telegram_id: int, context) -> str:
    amount = parse_amount(text.split()[0] if text.split() else text)
    if not amount:
        return "❌ Не могу распознать сумму. Попробуйте: `1500`"

    desc = " ".join(text.split()[1:]) or context.user_data.get("expense_category", "Расход")
    await add_transaction(
        telegram_id=telegram_id,
        amount=amount,
        transaction_type=TransactionType.EXPENSE,
        description=desc,
    )
    amount_str = f"{float(amount):,.0f}".replace(",", " ")
    return f"✅ Расход записан!\n💸 `-{amount_str} ₽` — {desc}"


async def handle_debt_input(text: str, telegram_id: int, context) -> str:
    from bot.services.debt_service import add_debt
    from bot.database.models import DebtType

    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 2:
        return "❌ Формат: `Название | Сумма | Кому`"

    title = parts[0]
    amount = parse_amount(parts[1])
    if not amount:
        return "❌ Не могу распознать сумму."

    person = parts[2] if len(parts) > 2 else None
    debt_type_str = context.user_data.get("debt_type", "i_owe")

    type_map = {
        "i_owe": DebtType.I_OWE,
        "owe_me": DebtType.OWE_ME,
        "credit": DebtType.CREDIT,
        "mortgage": DebtType.MORTGAGE,
    }

    await add_debt(
        telegram_id=telegram_id,
        debt_type=type_map.get(debt_type_str, DebtType.I_OWE),
        title=title,
        total_amount=amount,
        person_name=person,
    )
    amount_str = f"{float(amount):,.0f}".replace(",", " ")
    return f"✅ Долг добавлен!\n🏦 *{title}*: `{amount_str} ₽`"


async def handle_goal_input(text: str, telegram_id: int, context) -> str:
    from bot.services.goal_service import add_goal
    from datetime import date

    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 2:
        return "❌ Формат: `Название | Сумма | Дедлайн`"

    title = parts[0]
    amount = parse_amount(parts[1])
    if not amount:
        return "❌ Не могу распознать сумму."

    deadline = None
    if len(parts) > 2:
        try:
            deadline = date.fromisoformat(parts[2].strip())
        except ValueError:
            pass

    await add_goal(
        telegram_id=telegram_id,
        title=title,
        target_amount=amount,
        deadline=deadline,
    )
    amount_str = f"{float(amount):,.0f}".replace(",", " ")
    return f"✅ Цель создана!\n🎯 *{title}*: `{amount_str} ₽`"
