from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ContextTypes
from bot.config import get_settings


async def settings_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    settings = get_settings()

    text = (
        "⚙️ *Настройки*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🌐 Язык: Русский\n"
        "💱 Валюта: RUB\n"
        "🕐 Часовой пояс: Europe/Moscow\n"
        "🔔 Уведомления: Включены\n"
    )

    keyboard = [
        [
            InlineKeyboardButton("💱 Валюта", callback_data="settings_currency"),
            InlineKeyboardButton("🕐 Часовой пояс", callback_data="settings_tz"),
        ],
        [
            InlineKeyboardButton("🔔 Уведомления", callback_data="settings_notify"),
            InlineKeyboardButton("🔒 PIN-код", callback_data="settings_pin"),
        ],
        [
            InlineKeyboardButton(
                "📱 Открыть Mini App",
                web_app=WebAppInfo(url=settings.webapp_url)
            ),
        ],
    ]

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
