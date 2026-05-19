from decimal import Decimal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.services.transaction_service import add_transaction
from bot.database.models import TransactionType
from bot.services.user_service import get_or_create_user


async def income_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💰 *Добавить доход*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Выбери категорию или отправь сумму:\n"
        "`+50000 зарплата`\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("💰 Зарплата", callback_data="income_cat_salary"),
            InlineKeyboardButton("💻 Фриланс", callback_data="income_cat_freelance"),
        ],
        [
            InlineKeyboardButton("📊 Инвестиции", callback_data="income_cat_invest"),
            InlineKeyboardButton("🎁 Подарок", callback_data="income_cat_gift"),
        ],
        [
            InlineKeyboardButton("📦 Другое", callback_data="income_cat_other"),
        ],
    ]

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def income_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "income_new":
        await query.edit_message_text(
            "💰 *Добавить доход*\n\n"
            "Отправь сумму и описание:\n"
            "`+50000 зарплата`\n"
            "`+15000 фриланс проект`",
            parse_mode="Markdown",
        )
        context.user_data["awaiting"] = "income"

    elif data == "income_balance":
        from bot.handlers.balance import show_balance
        await show_balance(query, context)

    elif data == "income_stats":
        from bot.handlers.stats import show_stats
        await show_stats(query, context)

    elif data.startswith("income_cat_"):
        category_map = {
            "salary": "Зарплата",
            "freelance": "Фриланс",
            "invest": "Инвестиции",
            "gift": "Подарки",
            "other": "Другое",
        }
        cat_key = data.replace("income_cat_", "")
        cat_name = category_map.get(cat_key, "Другое")

        await query.edit_message_text(
            f"💰 Категория: *{cat_name}*\n\n"
            "Отправь сумму:\n"
            "`50000`",
            parse_mode="Markdown",
        )
        context.user_data["awaiting"] = "income"
        context.user_data["income_category"] = cat_name
