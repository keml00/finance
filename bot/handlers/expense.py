from decimal import Decimal
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.services.transaction_service import add_transaction
from bot.database.models import TransactionType


async def expense_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "💸 *Добавить расход*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Выбери категорию или отправь:\n"
        "`500 кофе`\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("🛒 Продукты", callback_data="expense_cat_food"),
            InlineKeyboardButton("🚗 Транспорт", callback_data="expense_cat_transport"),
        ],
        [
            InlineKeyboardButton("🍽️ Кафе", callback_data="expense_cat_cafe"),
            InlineKeyboardButton("📱 Подписки", callback_data="expense_cat_subs"),
        ],
        [
            InlineKeyboardButton("🏠 Комм. услуги", callback_data="expense_cat_utilities"),
            InlineKeyboardButton("🎮 Развлечения", callback_data="expense_cat_fun"),
        ],
        [
            InlineKeyboardButton("👕 Одежда", callback_data="expense_cat_clothes"),
            InlineKeyboardButton("💊 Здоровье", callback_data="expense_cat_health"),
        ],
        [
            InlineKeyboardButton("📦 Другое", callback_data="expense_cat_other"),
        ],
    ]

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def expense_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "expense_new":
        await query.edit_message_text(
            "💸 *Добавить расход*\n\n"
            "Отправь сумму и описание:\n"
            "`500 продукты`\n"
            "`1500 такси`",
            parse_mode="Markdown",
        )
        context.user_data["awaiting"] = "expense"

    elif data.startswith("expense_cat_"):
        category_map = {
            "food": "🛒 Продукты",
            "transport": "🚗 Транспорт",
            "cafe": "🍽️ Кафе и рестораны",
            "subs": "📱 Подписки",
            "utilities": "🏠 Коммунальные",
            "fun": "🎮 Развлечения",
            "clothes": "👕 Одежда",
            "health": "💊 Здоровье",
            "other": "📦 Другое",
        }
        cat_key = data.replace("expense_cat_", "")
        cat_name = category_map.get(cat_key, "📦 Другое")

        await query.edit_message_text(
            f"💸 Категория: *{cat_name}*\n\n"
            "Отправь сумму:\n"
            "`1500`",
            parse_mode="Markdown",
        )
        context.user_data["awaiting"] = "expense"
        context.user_data["expense_category"] = cat_name
