from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from bot.services.goal_service import get_goals, calculate_progress
from bot.database.models import GoalStatus


async def goals_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    goals = await get_goals(update.effective_user.id, status=GoalStatus.ACTIVE)

    text = (
        "🎯 *Финансовые цели*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    if goals:
        for g in goals:
            progress = calculate_progress(g)
            bar = _progress_bar(progress["progress"])
            current = f"{float(g.current_amount):,.0f}".replace(",", " ")
            target = f"{float(g.target_amount):,.0f}".replace(",", " ")

            text += f"{g.icon} *{g.title}*\n"
            text += f"   {bar} {progress['progress']:.0f}%\n"
            text += f"   `{current} / {target} ₽`\n"

            if progress["monthly_needed"]:
                monthly = f"{progress['monthly_needed']:,.0f}".replace(",", " ")
                text += f"   📅 Нужно в месяц: `{monthly} ₽`\n"
            if progress["days_left"] and progress["days_left"] > 0:
                text += f"   ⏰ Осталось дней: `{progress['days_left']}`\n"
            text += "\n"
    else:
        text += "У вас пока нет целей.\nСоздайте первую! 🚀\n\n"

    keyboard = [
        [
            InlineKeyboardButton("➕ Новая цель", callback_data="goal_add"),
            InlineKeyboardButton("💰 Пополнить", callback_data="goal_deposit"),
        ],
        [
            InlineKeyboardButton("📋 Все цели", callback_data="goal_list"),
        ],
    ]

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def goals_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "goal_add":
        context.user_data["awaiting"] = "goal_add"
        await query.edit_message_text(
            "🎯 *Новая цель*\n\n"
            "Отправь в формате:\n"
            "`Название | Сумма | Дедлайн (опционально)`\n\n"
            "Примеры:\n"
            "`iPhone 16 | 150000`\n"
            "`Подушка безопасности | 500000 | 2026-12-31`\n"
            "`Отпуск | 200000 | 2026-07-01`",
            parse_mode="Markdown",
        )

    elif data == "goal_deposit":
        context.user_data["awaiting"] = "goal_deposit"
        await query.edit_message_text(
            "💰 *Пополнить цель*\n\n"
            "Отправь: `Название цели | Сумма`\n\n"
            "Пример: `iPhone | 10000`",
            parse_mode="Markdown",
        )

    elif data == "goal_list":
        goals = await get_goals(query.from_user.id)
        if not goals:
            await query.edit_message_text("📋 Целей пока нет. Создайте первую!")
            return

        text = "📋 *Все цели:*\n\n"
        for g in goals:
            progress = calculate_progress(g)
            status = "✅" if g.status == GoalStatus.COMPLETED else "🔄"
            current = f"{float(g.current_amount):,.0f}".replace(",", " ")
            target = f"{float(g.target_amount):,.0f}".replace(",", " ")
            text += f"{status} {g.icon} *{g.title}*\n"
            text += f"   `{current} / {target} ₽` ({progress['progress']:.0f}%)\n\n"

        await query.edit_message_text(text, parse_mode="Markdown")


def _progress_bar(percent: float) -> str:
    filled = int(percent / 10)
    empty = 10 - filled
    return "▓" * filled + "░" * empty
