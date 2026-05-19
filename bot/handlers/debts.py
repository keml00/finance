from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.services.debt_service import get_debts, get_debt_summary
from bot.database.models import DebtType, DebtStatus


async def debts_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    summary = await get_debt_summary(update.effective_user.id)
    debts = await get_debts(update.effective_user.id, status=DebtStatus.ACTIVE)

    text = (
        "🏦 *Долги и кредиты*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    i_owe_str = f"{summary['total_i_owe']:,.0f}".replace(",", " ")
    owe_me_str = f"{summary['total_owe_me']:,.0f}".replace(",", " ")
    monthly_str = f"{summary['monthly_payments']:,.0f}".replace(",", " ")

    text += (
        f"📤 Я должен: `{i_owe_str} ₽`\n"
        f"📥 Мне должны: `{owe_me_str} ₽`\n"
        f"📅 Ежемесячные платежи: `{monthly_str} ₽`\n"
        f"📋 Активных: `{summary['active_debts']}`\n\n"
    )

    if debts:
        text += "*Активные долги:*\n"
        for d in debts[:10]:
            icon = "📤" if d.debt_type in (DebtType.I_OWE, DebtType.CREDIT) else "📥"
            remaining = f"{float(d.remaining_amount):,.0f}".replace(",", " ")
            text += f"{icon} {d.title}: `{remaining} ₽`\n"

    keyboard = [
        [
            InlineKeyboardButton("➕ Добавить долг", callback_data="debt_add"),
            InlineKeyboardButton("💳 Внести платёж", callback_data="debt_pay"),
        ],
        [
            InlineKeyboardButton("📋 Все долги", callback_data="debt_list"),
            InlineKeyboardButton("📊 Аналитика", callback_data="debt_analytics"),
        ],
    ]

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def debts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "debt_add":
        await query.edit_message_text(
            "🏦 *Добавить долг*\n\n"
            "Выбери тип:\n",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📤 Я должен", callback_data="debt_type_i_owe"),
                    InlineKeyboardButton("📥 Мне должны", callback_data="debt_type_owe_me"),
                ],
                [
                    InlineKeyboardButton("🏦 Кредит", callback_data="debt_type_credit"),
                    InlineKeyboardButton("🏠 Ипотека", callback_data="debt_type_mortgage"),
                ],
            ]),
        )

    elif data.startswith("debt_type_"):
        debt_type = data.replace("debt_type_", "")
        context.user_data["awaiting"] = "debt_add"
        context.user_data["debt_type"] = debt_type
        await query.edit_message_text(
            "Отправь информацию о долге в формате:\n"
            "`Название | Сумма | Кому/Кто`\n\n"
            "Пример:\n"
            "`Кредит Сбер | 500000 | Сбербанк`\n"
            "`Долг Петя | 15000 | Петя`",
            parse_mode="Markdown",
        )

    elif data == "debt_pay":
        context.user_data["awaiting"] = "debt_payment"
        await query.edit_message_text(
            "💳 *Внести платёж*\n\n"
            "Отправь: `ID долга | сумма`\n"
            "Или: `название долга | сумма`",
            parse_mode="Markdown",
        )

    elif data == "debt_list":
        debts = await get_debts(query.from_user.id)
        if not debts:
            await query.edit_message_text("📋 У вас нет долгов! 🎉")
            return

        text = "📋 *Все долги:*\n\n"
        for d in debts:
            status_icon = "✅" if d.status == DebtStatus.PAID else "🔴"
            remaining = f"{float(d.remaining_amount):,.0f}".replace(",", " ")
            total = f"{float(d.total_amount):,.0f}".replace(",", " ")
            text += f"{status_icon} *{d.title}*\n"
            text += f"   Остаток: {remaining} / {total} ₽\n\n"

        await query.edit_message_text(text, parse_mode="Markdown")

    elif data == "debt_analytics":
        summary = await get_debt_summary(query.from_user.id)
        text = (
            "📊 *Аналитика долгов*\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"💳 Общий долг: `{summary['total_i_owe']:,.0f} ₽`\n"
            f"📅 Ежемесячная нагрузка: `{summary['monthly_payments']:,.0f} ₽`\n"
            f"📋 Активных долгов: `{summary['active_debts']}`\n"
        )
        await query.edit_message_text(text, parse_mode="Markdown")
