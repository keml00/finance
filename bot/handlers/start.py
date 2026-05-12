from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from bot.config import get_settings
from bot.services.user_service import get_or_create_user


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = get_settings()
    user = await get_or_create_user(update.effective_user)

    welcome_text = (
        "🏦 *FinAI Assistant*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"Привет, *{update.effective_user.first_name}*! 👋\n\n"
        "Я твой персональный финансовый AI-ассистент.\n"
        "Помогу вести бюджет, управлять долгами и достигать финансовых целей.\n\n"
        "📊 *Возможности:*\n"
        "├ 💰 Учёт доходов и расходов\n"
        "├ 📈 Аналитика и отчёты\n"
        "├ 🏦 Управление долгами\n"
        "├ 🎯 Финансовые цели\n"
        "├ 🧾 Сканирование чеков\n"
        "├ 🤖 AI-рекомендации\n"
        "└ 📱 Mini App дашборд\n\n"
        "⚡ *Быстрый старт:*\n"
        "Просто напиши сумму с описанием:\n"
        '`500 кофе` — запишу расход\n'
        '`+50000 зарплата` — запишу доход\n\n'
        "Или используй команды ниже 👇"
    )

    keyboard = [
        [
            InlineKeyboardButton("💰 Доход", callback_data="income_new"),
            InlineKeyboardButton("💸 Расход", callback_data="expense_new"),
        ],
        [
            InlineKeyboardButton("📊 Баланс", callback_data="income_balance"),
            InlineKeyboardButton("📈 Статистика", callback_data="income_stats"),
        ],
        [
            InlineKeyboardButton("🏦 Долги", callback_data="debt_list"),
            InlineKeyboardButton("🎯 Цели", callback_data="goal_list"),
        ],
        [
            InlineKeyboardButton(
                "📱 Открыть Mini App",
                web_app=WebAppInfo(url=settings.webapp_url)
            ),
        ],
    ]

    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 *Команды FinAI Assistant*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "💰 /income — добавить доход\n"
        "💸 /expense — добавить расход\n"
        "📊 /balance — баланс счетов\n"
        "📈 /stats — статистика\n"
        "🏦 /debts — долги и кредиты\n"
        "🎯 /goals — финансовые цели\n"
        "🤖 /analytics — AI-аналитика\n"
        "⚙️ /settings — настройки\n\n"
        "💡 *Быстрый ввод:*\n"
        "`500 продукты` — расход 500₽\n"
        "`+30000 зарплата` — доход\n"
        "`-1500 такси` — расход\n\n"
        "🧾 *Чеки:*\n"
        "Отправь фото чека — распознаю автоматически\n\n"
        "🤖 *AI-чат:*\n"
        "Просто задай вопрос о финансах"
    )

    await update.message.reply_text(help_text, parse_mode="Markdown")
