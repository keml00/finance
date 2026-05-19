import sqlite3
import logging
import re
import os
import tempfile
from datetime import datetime, date
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

BOT_TOKEN = os.getenv('BOT_TOKEN', '')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
DB_PATH = os.getenv('DB_PATH', '/opt/finai-bot/finai.db')

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            account_type TEXT DEFAULT 'card',
            balance REAL DEFAULT 0,
            icon TEXT DEFAULT '💳',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            account_id INTEGER,
            tx_type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            date TEXT DEFAULT CURRENT_DATE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            debt_type TEXT NOT NULL,
            title TEXT NOT NULL,
            person_name TEXT,
            total_amount REAL NOT NULL,
            remaining_amount REAL NOT NULL,
            interest_rate REAL DEFAULT 0,
            monthly_payment REAL,
            start_date TEXT,
            due_date TEXT,
            status TEXT DEFAULT 'active',
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS debt_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            debt_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            date TEXT DEFAULT CURRENT_DATE,
            FOREIGN KEY (debt_id) REFERENCES debts(id)
        );
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL DEFAULT 0,
            deadline TEXT,
            icon TEXT DEFAULT '🎯',
            status TEXT DEFAULT 'active',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')
    conn.commit()
    conn.close()


def get_or_create_user(tg_user):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE telegram_id = ?', (tg_user.id,))
    row = c.fetchone()
    if row:
        conn.close()
        return row[0]
    c.execute('INSERT INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)',
              (tg_user.id, tg_user.username, tg_user.first_name))
    user_id = c.lastrowid
    c.execute('INSERT INTO accounts (user_id, name, account_type, icon) VALUES (?, ?, ?, ?)',
              (user_id, 'Наличные', 'cash', '💵'))
    c.execute('INSERT INTO accounts (user_id, name, account_type, icon) VALUES (?, ?, ?, ?)',
              (user_id, 'Карта', 'card', '💳'))
    conn.commit()
    conn.close()
    return user_id


def add_tx(user_id, amount, tx_type, description=''):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM accounts WHERE user_id = ? LIMIT 1', (user_id,))
    acc = c.fetchone()
    acc_id = acc[0] if acc else None
    c.execute('INSERT INTO transactions (user_id, account_id, tx_type, amount, description) VALUES (?, ?, ?, ?, ?)',
              (user_id, acc_id, tx_type, amount, description))
    if acc_id:
        if tx_type == 'income':
            c.execute('UPDATE accounts SET balance = balance + ? WHERE id = ?', (amount, acc_id))
        else:
            c.execute('UPDATE accounts SET balance = balance - ? WHERE id = ?', (amount, acc_id))
    conn.commit()
    conn.close()


def get_balance(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT name, icon, balance FROM accounts WHERE user_id = ?', (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_stats(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    ms = date.today().replace(day=1).isoformat()
    c.execute('SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND tx_type=? AND date>=?', (user_id, 'income', ms))
    income = c.fetchone()[0]
    c.execute('SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND tx_type=? AND date>=?', (user_id, 'expense', ms))
    expense = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM transactions WHERE user_id=? AND date>=?', (user_id, ms))
    count = c.fetchone()[0]
    conn.close()
    return income, expense, count


def fmt(n):
    return f"{n:,.0f}".replace(",", " ")


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_or_create_user(update.effective_user)
    name = update.effective_user.first_name
    text = (
        f"*FinAI Assistant*\n"
        f"{'━' * 18}\n\n"
        f"Привет, *{name}*! 👋\n\n"
        "Я твой финансовый AI-ассистент.\n\n"
        "*Возможности:*\n"
        "├ 💰 Учёт доходов/расходов\n"
        "├ 📈 Статистика\n"
        "├ 🏦 Долги и кредиты\n"
        "├ 🎯 Финансовые цели\n"
        "└ 🤖 AI-аналитика\n\n"
        "*Быстрый старт:*\n"
        "`500 кофе` — расход\n"
        "`+50000 зарплата` — доход\n\n"
        "_by keml00, telegram_"
    )
    kb = [
        [InlineKeyboardButton("💰 Доход", callback_data="cb_income"),
         InlineKeyboardButton("💸 Расход", callback_data="cb_expense")],
        [InlineKeyboardButton("📊 Баланс", callback_data="cb_balance"),
         InlineKeyboardButton("📈 Статистика", callback_data="cb_stats")],
        [InlineKeyboardButton("🏦 Долги", callback_data="cb_debts"),
         InlineKeyboardButton("🎯 Цели", callback_data="cb_goals")],
    ]
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "*Команды:*\n"
        "/income — доход\n"
        "/expense — расход\n"
        "/balance — баланс\n"
        "/stats — статистика\n"
        "/debts — долги\n"
        "/goals — цели\n"
        "/analytics — аналитика\n"
        "/debt\\_add — добавить долг\n"
        "/goal\\_add — новая цель\n"
        "/goal\\_deposit — пополнить цель\n\n"
        "*Быстрый ввод:*\n"
        "`500 продукты` — расход\n"
        "`+30000 зп` — доход"
    )
    await update.message.reply_text(text, parse_mode='Markdown')


async def income_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting'] = 'income'
    await update.message.reply_text("💰 Отправь сумму и описание:\n`50000 зарплата`", parse_mode='Markdown')


async def expense_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting'] = 'expense'
    await update.message.reply_text("💸 Отправь сумму и описание:\n`500 кофе`", parse_mode='Markdown')


async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = get_or_create_user(update.effective_user)
    accs = get_balance(uid)
    total = sum(a[2] for a in accs)
    text = "*Баланс счетов*\n" + "━" * 18 + "\n\n"
    for name, icon, bal in accs:
        text += f"{icon} *{name}*: `{fmt(bal)} ₽`\n"
    text += f"\n💎 *Итого:* `{fmt(total)} ₽`"
    await update.message.reply_text(text, parse_mode='Markdown')


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = get_or_create_user(update.effective_user)
    inc, exp, cnt = get_stats(uid)
    months = {1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь',
              7: 'Июль', 8: 'Август', 9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'}
    m = datetime.now().month
    text = (
        f"*Статистика за {months[m]}*\n" + "━" * 18 + "\n\n"
        f"💰 Доходы: `{fmt(inc)} ₽`\n"
        f"💸 Расходы: `{fmt(exp)} ₽`\n"
        f"📊 Баланс: `{fmt(inc - exp)} ₽`\n"
        f"🔢 Операций: `{cnt}`"
    )
    await update.message.reply_text(text, parse_mode='Markdown')


async def debts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = get_or_create_user(update.effective_user)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT title, remaining_amount, debt_type FROM debts WHERE user_id=? AND status=?', (uid, 'active'))
    debts = c.fetchall()
    conn.close()
    if not debts:
        text = "*Долги*\n" + "━" * 18 + "\n\nДолгов нет! 🎉\n\nДобавить:\n`/debt_add Название | Сумма | Кому`"
    else:
        total = sum(d[1] for d in debts)
        text = f"*Долги*\n" + "━" * 18 + f"\n\n📋 Активных: {len(debts)}\n💳 Общий: `{fmt(total)} ₽`\n\n"
        for title, rem, dtype in debts:
            icon = '📤' if dtype in ('i_owe', 'credit') else '📥'
            text += f"{icon} {title}: `{fmt(rem)} ₽`\n"
    await update.message.reply_text(text, parse_mode='Markdown')


async def debt_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = get_or_create_user(update.effective_user)
    raw = update.message.text.replace('/debt_add', '').strip()
    if not raw:
        await update.message.reply_text("Формат: `/debt_add Название | Сумма | Кому`", parse_mode='Markdown')
        return
    parts = [p.strip() for p in raw.split('|')]
    if len(parts) < 2:
        await update.message.reply_text("❌ Формат: `Название | Сумма | Кому`", parse_mode='Markdown')
        return
    title = parts[0]
    try:
        amount = float(parts[1].replace(' ', '').replace(',', '.'))
    except ValueError:
        await update.message.reply_text("❌ Не распознал сумму")
        return
    person = parts[2] if len(parts) > 2 else ''
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO debts (user_id, debt_type, title, person_name, total_amount, remaining_amount, start_date) VALUES (?,?,?,?,?,?,?)',
              (uid, 'i_owe', title, person, amount, amount, date.today().isoformat()))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Долг добавлен!\n🏦 *{title}*: `{fmt(amount)} ₽`", parse_mode='Markdown')


async def goals_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = get_or_create_user(update.effective_user)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT title, target_amount, current_amount, icon, deadline FROM goals WHERE user_id=? AND status=?', (uid, 'active'))
    goals = c.fetchall()
    conn.close()
    if not goals:
        text = "*Цели*\n" + "━" * 18 + "\n\nЦелей нет.\n\n`/goal_add Название | Сумма`"
    else:
        text = "*Финансовые цели*\n" + "━" * 18 + "\n\n"
        for title, target, current, icon, deadline in goals:
            pct = (current / target * 100) if target > 0 else 0
            filled = int(pct / 10)
            bar = '▓' * filled + '░' * (10 - filled)
            text += f"{icon} *{title}*\n   {bar} {pct:.0f}%\n   `{fmt(current)} / {fmt(target)} ₽`\n\n"
    await update.message.reply_text(text, parse_mode='Markdown')


async def goal_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = get_or_create_user(update.effective_user)
    raw = update.message.text.replace('/goal_add', '').strip()
    if not raw:
        await update.message.reply_text("Формат: `/goal_add Название | Сумма`", parse_mode='Markdown')
        return
    parts = [p.strip() for p in raw.split('|')]
    if len(parts) < 2:
        await update.message.reply_text("❌ Формат: `Название | Сумма`", parse_mode='Markdown')
        return
    title = parts[0]
    try:
        amount = float(parts[1].replace(' ', '').replace(',', '.'))
    except ValueError:
        await update.message.reply_text("❌ Не распознал сумму")
        return
    deadline = parts[2] if len(parts) > 2 else None
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO goals (user_id, title, target_amount, deadline) VALUES (?,?,?,?)',
              (uid, title, amount, deadline))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Цель создана!\n🎯 *{title}*: `{fmt(amount)} ₽`", parse_mode='Markdown')


async def goal_deposit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = get_or_create_user(update.effective_user)
    raw = update.message.text.replace('/goal_deposit', '').strip()
    parts = [p.strip() for p in raw.split('|')]
    if len(parts) < 2:
        await update.message.reply_text("Формат: `/goal_deposit Название | Сумма`", parse_mode='Markdown')
        return
    title = parts[0]
    try:
        amount = float(parts[1].replace(' ', '').replace(',', '.'))
    except ValueError:
        await update.message.reply_text("❌ Не распознал сумму")
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE goals SET current_amount = current_amount + ? WHERE user_id=? AND title LIKE ? AND status=?',
              (amount, uid, f'%{title}%', 'active'))
    if c.rowcount == 0:
        conn.close()
        await update.message.reply_text(f"❌ Цель '{title}' не найдена")
        return
    c.execute("UPDATE goals SET status = 'completed' WHERE user_id=? AND current_amount >= target_amount AND status='active'", (uid,))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Пополнено!\n🎯 *{title}*: `+{fmt(amount)} ₽`", parse_mode='Markdown')


async def analytics_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = get_or_create_user(update.effective_user)
    inc, exp, cnt = get_stats(uid)
    if cnt == 0:
        await update.message.reply_text("📊 Недостаточно данных. Добавьте операции!")
        return
    days = max(datetime.now().day, 1)
    avg = exp / days
    rate = ((inc - exp) / inc * 100) if inc > 0 else 0
    text = (
        "*AI-аналитика*\n" + "━" * 18 + "\n\n"
        f"📊 Среднее/день: `{fmt(avg)} ₽`\n"
        f"💰 Накопления: `{rate:.0f}%`\n"
        f"📈 Доход/расход: `{fmt(inc)} / {fmt(exp)} ₽`\n\n"
    )
    if rate > 20:
        text += "✅ Отличная финансовая дисциплина!"
    elif rate > 0:
        text += "⚠️ Норма накоплений ниже 20%. Рекомендую оптимизировать."
    else:
        text += "🔴 Расходы превышают доходы! Нужна оптимизация."
    await update.message.reply_text(text, parse_mode='Markdown')


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle photo messages - receipt/check scanning."""
    uid = get_or_create_user(update.effective_user)

    if not OCR_AVAILABLE:
        await update.message.reply_text(
            "🧾 Получил фото! Но OCR не установлен на сервере.\n"
            "Отправь данные текстом: `597 платная дорога`",
            parse_mode='Markdown'
        )
        return

    await update.message.reply_text("🔍 Сканирую чек...")

    try:
        photo = update.message.photo[-1]  # highest resolution
        file = await photo.get_file()

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name
            await file.download_to_drive(tmp_path)

        # OCR
        img = Image.open(tmp_path)
        text = pytesseract.image_to_string(img, lang='rus+eng')
        os.unlink(tmp_path)

        if not text.strip():
            await update.message.reply_text(
                "❌ Не удалось распознать текст.\n"
                "Попробуй отправить фото лучшего качества или введи вручную."
            )
            return

        # Parse amount from recognized text
        amount, description = parse_receipt(text)

        if amount:
            add_tx(uid, amount, 'expense', description)
            await update.message.reply_text(
                f"✅ Чек распознан!\n"
                f"💸 `-{fmt(amount)} ₽` — {description}\n\n"
                f"_Распознанный текст:_\n`{text[:200]}`",
                parse_mode='Markdown'
            )
        else:
            # Show what we recognized, ask user to confirm
            await update.message.reply_text(
                f"🧾 Текст распознан, но сумму не определил:\n\n"
                f"`{text[:300]}`\n\n"
                "Отправь сумму вручную: `597 платная дорога`",
                parse_mode='Markdown'
            )

    except Exception as e:
        logger.error(f"Photo processing error: {e}")
        await update.message.reply_text(
            "❌ Ошибка при обработке фото.\n"
            "Введи данные вручную: `сумма описание`",
            parse_mode='Markdown'
        )


def parse_receipt(text):
    """Parse amount and description from OCR text."""
    lines = text.strip().split('\n')
    amount = None
    description = 'Чек'

    # Look for common amount patterns in Russian receipts
    amount_patterns = [
        r'[Оо]плачено[:\s]*(\d[\d\s.,]+)',
        r'[Ии]того[:\s]*(\d[\d\s.,]+)',
        r'[Сс]умма[:\s]*(\d[\d\s.,]+)',
        r'[Вв]сего[:\s]*(\d[\d\s.,]+)',
        r'(\d[\d\s]*[.,]\d{2})\s*[₽руб]',
        r'(\d{2,}[.,]\d{2})',
    ]

    for pattern in amount_patterns:
        match = re.search(pattern, text)
        if match:
            raw = match.group(1).replace(' ', '').replace(',', '.')
            try:
                amount = float(raw)
                if amount > 0 and amount < 10000000:
                    break
            except ValueError:
                continue

    # Try to find description/shop name
    desc_patterns = [
        r'[Мм]агазин[:\s]*(.+)',
        r'[Оо]т кого[:\s]*(.+)',
        r'ООО\s+["\']?(.+?)["\']?\s',
        r'ИП\s+(.+)',
    ]

    for pattern in desc_patterns:
        match = re.search(pattern, text)
        if match:
            description = match.group(1).strip()[:50]
            break

    # Specific patterns for toll roads
    if re.search(r'[Пп]латн', text) and re.search(r'[Дд]орог', text):
        description = 'Платная дорога'
        road_match = re.search(r'(М-\d+|ЦКАД)', text)
        if road_match:
            description += f' {road_match.group(1)}'

    # Specific: AVTODOR
    if re.search(r'АВТОДОР|автодор|Avtodor', text, re.IGNORECASE):
        description = 'Платная дорога (Автодор)'

    return amount, description


async def msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    uid = get_or_create_user(update.effective_user)

    # +amount desc -> income
    match = re.match(r'^\+\s*(\d[\d\s.,]*)\s*(.*)?$', text)
    if match:
        amount = float(match.group(1).replace(' ', '').replace(',', '.'))
        desc = (match.group(2) or '').strip() or 'Доход'
        add_tx(uid, amount, 'income', desc)
        await update.message.reply_text(f"✅ Доход!\n💰 `+{fmt(amount)} ₽` — {desc}", parse_mode='Markdown')
        return

    # amount desc -> expense
    match = re.match(r'^-?\s*(\d[\d\s.,]*)\s+(.+)$', text)
    if match:
        amount = float(match.group(1).replace(' ', '').replace(',', '.'))
        desc = match.group(2).strip()
        if amount < 10000000:
            add_tx(uid, amount, 'expense', desc)
            await update.message.reply_text(f"✅ Расход!\n💸 `-{fmt(amount)} ₽` — {desc}", parse_mode='Markdown')
            return

    # Awaiting
    awaiting = context.user_data.get('awaiting')
    if awaiting in ('income', 'expense'):
        parts = text.split(None, 1)
        try:
            amount = float(parts[0].replace(',', '.').replace(' ', ''))
        except ValueError:
            await update.message.reply_text("❌ Не распознал сумму")
            return
        desc = parts[1] if len(parts) > 1 else awaiting
        add_tx(uid, amount, awaiting, desc)
        icon = '💰' if awaiting == 'income' else '💸'
        sign = '+' if awaiting == 'income' else '-'
        await update.message.reply_text(f"✅ {icon} `{sign}{fmt(amount)} ₽` — {desc}", parse_mode='Markdown')
        context.user_data.pop('awaiting', None)
        return

    await update.message.reply_text("💡 `500 кофе` — расход, `+50000 зп` — доход\n/help — все команды", parse_mode='Markdown')


async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data
    if d == 'cb_income':
        context.user_data['awaiting'] = 'income'
        await q.edit_message_text("💰 Отправь сумму и описание:\n`50000 зарплата`", parse_mode='Markdown')
    elif d == 'cb_expense':
        context.user_data['awaiting'] = 'expense'
        await q.edit_message_text("💸 Отправь сумму и описание:\n`500 кофе`", parse_mode='Markdown')
    elif d == 'cb_balance':
        uid = get_or_create_user(q.from_user)
        accs = get_balance(uid)
        total = sum(a[2] for a in accs)
        text = "*Баланс*\n\n"
        for name, icon, bal in accs:
            text += f"{icon} *{name}*: `{fmt(bal)} ₽`\n"
        text += f"\n💎 *Итого:* `{fmt(total)} ₽`"
        await q.edit_message_text(text, parse_mode='Markdown')
    elif d == 'cb_stats':
        uid = get_or_create_user(q.from_user)
        inc, exp, cnt = get_stats(uid)
        text = f"*Статистика*\n\n💰 `{fmt(inc)} ₽`\n💸 `{fmt(exp)} ₽`\n📊 `{fmt(inc-exp)} ₽`\n🔢 {cnt} операций"
        await q.edit_message_text(text, parse_mode='Markdown')
    elif d == 'cb_debts':
        await q.edit_message_text("🏦 /debts — управление долгами\n/debt\\_add Назв | Сумма | Кому", parse_mode='Markdown')
    elif d == 'cb_goals':
        await q.edit_message_text("🎯 /goals — цели\n/goal\\_add Назв | Сумма", parse_mode='Markdown')


def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start_handler))
    app.add_handler(CommandHandler('help', help_handler))
    app.add_handler(CommandHandler('income', income_cmd))
    app.add_handler(CommandHandler('expense', expense_cmd))
    app.add_handler(CommandHandler('balance', balance_cmd))
    app.add_handler(CommandHandler('stats', stats_cmd))
    app.add_handler(CommandHandler('debts', debts_cmd))
    app.add_handler(CommandHandler('debt_add', debt_add_cmd))
    app.add_handler(CommandHandler('goals', goals_cmd))
    app.add_handler(CommandHandler('goal_add', goal_add_cmd))
    app.add_handler(CommandHandler('goal_deposit', goal_deposit_cmd))
    app.add_handler(CommandHandler('analytics', analytics_cmd))
    app.add_handler(CallbackQueryHandler(cb_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg_handler))
    logger.info('FinAI Assistant started!')
    app.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
