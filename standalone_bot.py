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

BOT_TOKEN = '8642157349:AAFLqyX57ws20ARgM-wX2aov6q0qv_KmKbA'
ADMIN_ID = 232400016
DB_PATH = '/opt/finai-bot/finai.db'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

EXPENSE_CATEGORIES = {
    'food': ('🛒', 'Продукты'),
    'transport': ('🚗', 'Транспорт'),
    'cafe': ('🍽️', 'Кафе и рестораны'),
    'subs': ('📱', 'Подписки'),
    'utilities': ('🏠', 'Коммунальные'),
    'rent': ('🔑', 'Аренда'),
    'fun': ('🎮', 'Развлечения'),
    'clothes': ('👕', 'Одежда'),
    'health': ('💊', 'Здоровье'),
    'education': ('📚', 'Образование'),
    'travel': ('✈️', 'Путешествия'),
    'credit': ('🏦', 'Кредиты'),
    'other': ('📦', 'Другое'),
}


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT, first_name TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL, name TEXT NOT NULL,
            account_type TEXT DEFAULT 'card', balance REAL DEFAULT 0,
            icon TEXT DEFAULT '💳',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL, account_id INTEGER,
            tx_type TEXT NOT NULL, amount REAL NOT NULL,
            description TEXT, category TEXT DEFAULT '',
            date TEXT DEFAULT CURRENT_DATE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL, debt_type TEXT NOT NULL,
            title TEXT NOT NULL, person_name TEXT,
            total_amount REAL NOT NULL, remaining_amount REAL NOT NULL,
            interest_rate REAL DEFAULT 0, monthly_payment REAL,
            start_date TEXT, due_date TEXT, status TEXT DEFAULT 'active',
            notes TEXT, FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL, title TEXT NOT NULL,
            target_amount REAL NOT NULL, current_amount REAL DEFAULT 0,
            deadline TEXT, icon TEXT DEFAULT '🎯', status TEXT DEFAULT 'active',
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')
    conn.commit()
    c.execute("PRAGMA table_info(transactions)")
    cols = [col[1] for col in c.fetchall()]
    if 'category' not in cols:
        c.execute("ALTER TABLE transactions ADD COLUMN category TEXT DEFAULT ''")
        conn.commit()
    conn.close()


def get_or_create_user(tg_user):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE telegram_id=?', (tg_user.id,))
    row = c.fetchone()
    if row:
        conn.close()
        return row[0]
    c.execute('INSERT INTO users (telegram_id,username,first_name) VALUES (?,?,?)',
              (tg_user.id, tg_user.username, tg_user.first_name))
    uid = c.lastrowid
    c.execute('INSERT INTO accounts (user_id,name,account_type,icon) VALUES (?,?,?,?)', (uid,'Наличные','cash','💵'))
    c.execute('INSERT INTO accounts (user_id,name,account_type,icon) VALUES (?,?,?,?)', (uid,'Карта','card','💳'))
    conn.commit()
    conn.close()
    return uid


def guess_category(desc):
    d = desc.lower()
    rules = {
        'food': ['продукт','магазин','пятёрочка','пятерочка','перекрёсток','ашан','лента','магнит','дикси','молоко','хлеб'],
        'transport': ['такси','uber','метро','бензин','азс','парковка','платная дорога','автодор','каршеринг'],
        'cafe': ['кафе','ресторан','кофе','бар','пицца','суши','доставка','макдональдс','бургер'],
        'subs': ['подписка','netflix','youtube','spotify','apple','icloud','premium'],
        'utilities': ['жкх','коммуналка','электричество','вода','газ','интернет','связь','мтс','билайн','мегафон'],
        'rent': ['аренда','квартплата'],
        'fun': ['кино','игра','steam','клуб','концерт','театр'],
        'clothes': ['одежда','обувь','zara','hm','uniqlo'],
        'health': ['аптека','лекарств','врач','клиника','стоматолог'],
        'education': ['курс','обучение','книга'],
        'travel': ['отель','билет','перелёт','перелет','отпуск'],
        'credit': ['кредит','ипотека','рассрочка'],
    }
    for cat, kws in rules.items():
        if any(kw in d for kw in kws):
            return cat
    return 'other'


def add_tx(user_id, amount, tx_type, description='', category=''):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM accounts WHERE user_id=? LIMIT 1', (user_id,))
    acc = c.fetchone()
    acc_id = acc[0] if acc else None
    if not category and tx_type == 'expense' and description:
        category = guess_category(description)
    c.execute('INSERT INTO transactions (user_id,account_id,tx_type,amount,description,category) VALUES (?,?,?,?,?,?)',
              (user_id, acc_id, tx_type, amount, description, category))
    if acc_id:
        if tx_type == 'income':
            c.execute('UPDATE accounts SET balance=balance+? WHERE id=?', (amount, acc_id))
        else:
            c.execute('UPDATE accounts SET balance=balance-? WHERE id=?', (amount, acc_id))
    conn.commit()
    conn.close()


def get_balance(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT name,icon,balance FROM accounts WHERE user_id=?', (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows


def get_stats(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    ms = date.today().replace(day=1).isoformat()
    c.execute('SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND tx_type=? AND date>=?', (user_id,'income',ms))
    income = c.fetchone()[0]
    c.execute('SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND tx_type=? AND date>=?', (user_id,'expense',ms))
    expense = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM transactions WHERE user_id=? AND date>=?', (user_id,ms))
    count = c.fetchone()[0]
    conn.close()
    return income, expense, count


def get_category_stats(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    ms = date.today().replace(day=1).isoformat()
    c.execute('SELECT category, SUM(amount), COUNT(*) FROM transactions WHERE user_id=? AND tx_type=? AND date>=? AND category!="" GROUP BY category ORDER BY SUM(amount) DESC',
              (user_id, 'expense', ms))
    rows = c.fetchall()
    conn.close()
    return rows


def fmt(n):
    return f"{n:,.0f}".replace(",", " ")



async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_or_create_user(update.effective_user)
    name = update.effective_user.first_name
    text = (
        f"*FinAI Assistant*\n{'━'*18}\n\n"
        f"Привет, *{name}*! 👋\n\n"
        "Я твой финансовый AI-ассистент.\n\n"
        "*Возможности:*\n├ 💰 Учёт доходов/расходов\n├ 📈 Статистика по категориям\n├ 🏦 Долги и кредиты\n├ 🎯 Финансовые цели\n├ 🧾 Сканирование чеков\n└ 🤖 AI-аналитика\n\n"
        "*Быстрый старт:*\n`500 кофе` — расход\n`+50000 зарплата` — доход\n\n_by keml00, telegram_"
    )
    kb = [
        [InlineKeyboardButton("💰 Доход", callback_data="cb_income"), InlineKeyboardButton("💸 Расход", callback_data="cb_expense")],
        [InlineKeyboardButton("📊 Баланс", callback_data="cb_balance"), InlineKeyboardButton("📈 Статистика", callback_data="cb_stats")],
        [InlineKeyboardButton("🏦 Долги", callback_data="cb_debts"), InlineKeyboardButton("🎯 Цели", callback_data="cb_goals")],
    ]
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "*Команды:*\n/income — доход\n/expense — расход (с категориями)\n/balance — баланс\n/stats — статистика по категориям\n/debts — долги\n/goals — цели\n/analytics — аналитика\n/debt\\_add — добавить долг\n/goal\\_add — новая цель\n/goal\\_deposit — пополнить цель\n\n*Быстрый ввод:*\n`500 продукты` — расход (авто-категория)\n`+30000 зп` — доход\n\n🧾 Отправь фото чека — распознаю!",
        parse_mode='Markdown')


async def income_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['awaiting'] = 'income'
    await update.message.reply_text("💰 Отправь сумму и описание:\n`50000 зарплата`", parse_mode='Markdown')


async def expense_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🛒 Продукты", callback_data="cat_food"), InlineKeyboardButton("🚗 Транспорт", callback_data="cat_transport")],
        [InlineKeyboardButton("🍽️ Кафе", callback_data="cat_cafe"), InlineKeyboardButton("📱 Подписки", callback_data="cat_subs")],
        [InlineKeyboardButton("🏠 Коммунальные", callback_data="cat_utilities"), InlineKeyboardButton("🎮 Развлечения", callback_data="cat_fun")],
        [InlineKeyboardButton("👕 Одежда", callback_data="cat_clothes"), InlineKeyboardButton("💊 Здоровье", callback_data="cat_health")],
        [InlineKeyboardButton("📚 Образование", callback_data="cat_education"), InlineKeyboardButton("✈️ Путешествия", callback_data="cat_travel")],
        [InlineKeyboardButton("📦 Без категории", callback_data="cat_other")],
    ]
    await update.message.reply_text("💸 *Добавить расход*\n\nВыбери категорию:", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))


async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = get_or_create_user(update.effective_user)
    accs = get_balance(uid)
    total = sum(a[2] for a in accs)
    text = "*Баланс счетов*\n" + "━"*18 + "\n\n"
    for name, icon, bal in accs:
        text += f"{icon} *{name}*: `{fmt(bal)} ₽`\n"
    text += f"\n💎 *Итого:* `{fmt(total)} ₽`"
    await update.message.reply_text(text, parse_mode='Markdown')


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = get_or_create_user(update.effective_user)
    inc, exp, cnt = get_stats(uid)
    months = {1:'Январь',2:'Февраль',3:'Март',4:'Апрель',5:'Май',6:'Июнь',7:'Июль',8:'Август',9:'Сентябрь',10:'Октябрь',11:'Ноябрь',12:'Декабрь'}
    m = datetime.now().month
    text = f"*Статистика за {months[m]}*\n" + "━"*18 + f"\n\n💰 Доходы: `{fmt(inc)} ₽`\n💸 Расходы: `{fmt(exp)} ₽`\n📊 Баланс: `{fmt(inc-exp)} ₽`\n🔢 Операций: `{cnt}`\n"
    cat_stats = get_category_stats(uid)
    if cat_stats:
        text += "\n*Расходы по категориям:*\n"
        for cat_key, total_cat, count in cat_stats:
            ci = EXPENSE_CATEGORIES.get(cat_key, ('📦', cat_key))
            pct = (total_cat / exp * 100) if exp > 0 else 0
            text += f"{ci[0]} {ci[1]}: `{fmt(total_cat)} ₽` ({pct:.0f}%)\n"
    await update.message.reply_text(text, parse_mode='Markdown')


async def debts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = get_or_create_user(update.effective_user)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT title,remaining_amount,debt_type FROM debts WHERE user_id=? AND status=?', (uid,'active'))
    debts = c.fetchall()
    conn.close()
    if not debts:
        text = "*Долги*\n" + "━"*18 + "\n\nДолгов нет! 🎉\n\n`/debt_add Название | Сумма | Кому`"
    else:
        total = sum(d[1] for d in debts)
        text = "*Долги*\n" + "━"*18 + f"\n\n📋 Активных: {len(debts)}\n💳 Общий: `{fmt(total)} ₽`\n\n"
        for title, rem, dtype in debts:
            icon = '📤' if dtype in ('i_owe','credit') else '📥'
            text += f"{icon} {title}: `{fmt(rem)} ₽`\n"
    await update.message.reply_text(text, parse_mode='Markdown')


async def debt_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = get_or_create_user(update.effective_user)
    raw = update.message.text.replace('/debt_add','').strip()
    if not raw:
        await update.message.reply_text("Формат: `/debt_add Название | Сумма | Кому`", parse_mode='Markdown')
        return
    parts = [p.strip() for p in raw.split('|')]
    if len(parts) < 2:
        await update.message.reply_text("❌ Формат: `Название | Сумма | Кому`", parse_mode='Markdown')
        return
    title = parts[0]
    try:
        amount = float(parts[1].replace(' ','').replace(',','.'))
    except ValueError:
        await update.message.reply_text("❌ Не распознал сумму")
        return
    person = parts[2] if len(parts) > 2 else ''
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO debts (user_id,debt_type,title,person_name,total_amount,remaining_amount,start_date) VALUES (?,?,?,?,?,?,?)',
              (uid,'i_owe',title,person,amount,amount,date.today().isoformat()))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Долг добавлен!\n🏦 *{title}*: `{fmt(amount)} ₽`", parse_mode='Markdown')


async def goals_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = get_or_create_user(update.effective_user)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT title,target_amount,current_amount,icon FROM goals WHERE user_id=? AND status=?', (uid,'active'))
    goals = c.fetchall()
    conn.close()
    if not goals:
        text = "*Цели*\n" + "━"*18 + "\n\nЦелей нет.\n`/goal_add Название | Сумма`"
    else:
        text = "*Финансовые цели*\n" + "━"*18 + "\n\n"
        for title, target, current, icon in goals:
            pct = (current/target*100) if target > 0 else 0
            bar = '▓'*int(pct/10) + '░'*(10-int(pct/10))
            text += f"{icon} *{title}*\n   {bar} {pct:.0f}%\n   `{fmt(current)} / {fmt(target)} ₽`\n\n"
    await update.message.reply_text(text, parse_mode='Markdown')


async def goal_add_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = get_or_create_user(update.effective_user)
    raw = update.message.text.replace('/goal_add','').strip()
    if not raw:
        await update.message.reply_text("Формат: `/goal_add Название | Сумма`", parse_mode='Markdown')
        return
    parts = [p.strip() for p in raw.split('|')]
    if len(parts) < 2:
        await update.message.reply_text("❌ Формат: `Название | Сумма`", parse_mode='Markdown')
        return
    title = parts[0]
    try:
        amount = float(parts[1].replace(' ','').replace(',','.'))
    except ValueError:
        await update.message.reply_text("❌ Не распознал сумму")
        return
    deadline = parts[2] if len(parts) > 2 else None
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO goals (user_id,title,target_amount,deadline) VALUES (?,?,?,?)', (uid,title,amount,deadline))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ Цель создана!\n🎯 *{title}*: `{fmt(amount)} ₽`", parse_mode='Markdown')


async def goal_deposit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = get_or_create_user(update.effective_user)
    raw = update.message.text.replace('/goal_deposit','').strip()
    parts = [p.strip() for p in raw.split('|')]
    if len(parts) < 2:
        await update.message.reply_text("Формат: `/goal_deposit Название | Сумма`", parse_mode='Markdown')
        return
    title, amt_str = parts[0], parts[1]
    try:
        amount = float(amt_str.replace(' ','').replace(',','.'))
    except ValueError:
        await update.message.reply_text("❌ Не распознал сумму")
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE goals SET current_amount=current_amount+? WHERE user_id=? AND title LIKE ? AND status=?', (amount,uid,f'%{title}%','active'))
    if c.rowcount == 0:
        conn.close()
        await update.message.reply_text(f"❌ Цель '{title}' не найдена")
        return
    c.execute("UPDATE goals SET status='completed' WHERE user_id=? AND current_amount>=target_amount AND status='active'", (uid,))
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
    rate = ((inc-exp)/inc*100) if inc > 0 else 0
    text = "*AI-аналитика*\n" + "━"*18 + f"\n\n📊 Среднее/день: `{fmt(avg)} ₽`\n💰 Накопления: `{rate:.0f}%`\n📈 Доход/расход: `{fmt(inc)} / {fmt(exp)} ₽`\n\n"
    if rate > 20:
        text += "✅ Отличная финансовая дисциплина!"
    elif rate > 0:
        text += "⚠️ Норма накоплений ниже 20%."
    else:
        text += "🔴 Расходы превышают доходы!"
    cat_stats = get_category_stats(uid)
    if cat_stats and len(cat_stats) >= 1:
        top = cat_stats[0]
        ci = EXPENSE_CATEGORIES.get(top[0], ('📦', top[0]))
        text += f"\n\n📌 Топ категория: {ci[0]} {ci[1]} (`{fmt(top[1])} ₽`)"
    await update.message.reply_text(text, parse_mode='Markdown')



async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = get_or_create_user(update.effective_user)
    if not OCR_AVAILABLE:
        await update.message.reply_text("🧾 OCR не установлен. Отправь текстом: `597 платная дорога`", parse_mode='Markdown')
        return
    await update.message.reply_text("🔍 Сканирую чек...")
    try:
        photo = update.message.photo[-1]
        file = await photo.get_file()
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name
            await file.download_to_drive(tmp_path)
        img = Image.open(tmp_path)
        text = pytesseract.image_to_string(img, lang='rus+eng')
        os.unlink(tmp_path)
        if not text.strip():
            await update.message.reply_text("❌ Не удалось распознать. Введи вручную.")
            return
        amount, description = parse_receipt(text)
        if amount:
            category = guess_category(description)
            add_tx(uid, amount, 'expense', description, category)
            ci = EXPENSE_CATEGORIES.get(category, ('📦','Другое'))
            await update.message.reply_text(f"✅ Чек распознан!\n💸 `-{fmt(amount)} ₽` — {description}\n📂 {ci[0]} {ci[1]}", parse_mode='Markdown')
        else:
            await update.message.reply_text(f"🧾 Текст:\n`{text[:300]}`\n\nОтправь вручную: `597 платная дорога`", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Photo error: {e}")
        await update.message.reply_text("❌ Ошибка. Введи вручную: `сумма описание`", parse_mode='Markdown')


def parse_receipt(text):
    amount = None
    description = 'Чек'
    for pattern in [r'[Оо]плачено[:\s]*(\d[\d\s.,]+)', r'[Ии]того[:\s]*(\d[\d\s.,]+)', r'[Сс]умма[:\s]*(\d[\d\s.,]+)', r'(\d[\d\s]*[.,]\d{2})\s*[₽руб]', r'(\d{2,}[.,]\d{2})']:
        match = re.search(pattern, text)
        if match:
            raw = match.group(1).replace(' ','').replace(',','.')
            try:
                amount = float(raw)
                if 0 < amount < 10000000:
                    break
            except ValueError:
                continue
    if re.search(r'АВТОДОР|автодор', text, re.IGNORECASE):
        description = 'Платная дорога (Автодор)'
    elif re.search(r'[Пп]латн.*[Дд]орог', text):
        description = 'Платная дорога'
    elif re.search(r'ООО\s+(.+?)[\n"]', text):
        description = re.search(r'ООО\s+(.+?)[\n"]', text).group(1).strip()[:40]
    return amount, description


async def msg_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    uid = get_or_create_user(update.effective_user)

    match = re.match(r'^\+\s*(\d[\d\s.,]*)\s*(.*)?$', text)
    if match:
        amount = float(match.group(1).replace(' ','').replace(',','.'))
        desc = (match.group(2) or '').strip() or 'Доход'
        add_tx(uid, amount, 'income', desc)
        await update.message.reply_text(f"✅ Доход!\n💰 `+{fmt(amount)} ₽` — {desc}", parse_mode='Markdown')
        return

    match = re.match(r'^-?\s*(\d[\d\s.,]*)\s+(.+)$', text)
    if match:
        amount = float(match.group(1).replace(' ','').replace(',','.'))
        desc = match.group(2).strip()
        if amount < 10000000:
            category = guess_category(desc)
            add_tx(uid, amount, 'expense', desc, category)
            ci = EXPENSE_CATEGORIES.get(category, ('📦','Другое'))
            await update.message.reply_text(f"✅ Расход!\n💸 `-{fmt(amount)} ₽` — {desc}\n📂 {ci[0]} {ci[1]}", parse_mode='Markdown')
            return

    awaiting = context.user_data.get('awaiting')
    if awaiting in ('income','expense'):
        parts = text.split(None, 1)
        try:
            amount = float(parts[0].replace(',','.').replace(' ',''))
        except ValueError:
            await update.message.reply_text("❌ Не распознал сумму")
            return
        desc = parts[1] if len(parts) > 1 else awaiting
        category = context.user_data.get('category', '')
        if not category and awaiting == 'expense':
            category = guess_category(desc)
        add_tx(uid, amount, awaiting, desc, category)
        icon = '💰' if awaiting == 'income' else '💸'
        sign = '+' if awaiting == 'income' else '-'
        reply = f"✅ {icon} `{sign}{fmt(amount)} ₽` — {desc}"
        if category and awaiting == 'expense':
            ci = EXPENSE_CATEGORIES.get(category, ('📦',''))
            reply += f"\n📂 {ci[0]} {ci[1]}"
        await update.message.reply_text(reply, parse_mode='Markdown')
        context.user_data.pop('awaiting', None)
        context.user_data.pop('category', None)
        return

    await update.message.reply_text("💡 `500 кофе` — расход, `+50000 зп` — доход\n/help — все команды", parse_mode='Markdown')


async def cb_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    d = q.data

    if d.startswith('cat_'):
        cat_key = d[4:]
        ci = EXPENSE_CATEGORIES.get(cat_key, ('📦','Другое'))
        context.user_data['awaiting'] = 'expense'
        context.user_data['category'] = cat_key
        await q.edit_message_text(f"💸 Категория: *{ci[0]} {ci[1]}*\n\nОтправь сумму и описание:\n`500 кофе`", parse_mode='Markdown')
        return

    if d == 'cb_income':
        context.user_data['awaiting'] = 'income'
        await q.edit_message_text("💰 Отправь сумму и описание:\n`50000 зарплата`", parse_mode='Markdown')
    elif d == 'cb_expense':
        kb = [
            [InlineKeyboardButton("🛒 Продукты", callback_data="cat_food"), InlineKeyboardButton("🚗 Транспорт", callback_data="cat_transport")],
            [InlineKeyboardButton("🍽️ Кафе", callback_data="cat_cafe"), InlineKeyboardButton("📱 Подписки", callback_data="cat_subs")],
            [InlineKeyboardButton("🏠 Коммунальные", callback_data="cat_utilities"), InlineKeyboardButton("🎮 Развлечения", callback_data="cat_fun")],
            [InlineKeyboardButton("📦 Другое", callback_data="cat_other")],
        ]
        await q.edit_message_text("💸 *Расход — выбери категорию:*", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(kb))
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
        cat_stats = get_category_stats(uid)
        if cat_stats:
            text += "\n\n*По категориям:*\n"
            for ck, t, n in cat_stats[:7]:
                ci = EXPENSE_CATEGORIES.get(ck, ('📦',ck))
                text += f"{ci[0]} {ci[1]}: `{fmt(t)} ₽`\n"
        await q.edit_message_text(text, parse_mode='Markdown')
    elif d == 'cb_debts':
        await q.edit_message_text("🏦 /debts — долги\n/debt\\_add Назв | Сумма | Кому", parse_mode='Markdown')
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
