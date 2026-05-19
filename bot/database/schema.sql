-- FinAI Assistant Database Schema
-- PostgreSQL 16

CREATE TYPE transaction_type AS ENUM ('income', 'expense', 'transfer');
CREATE TYPE account_type AS ENUM ('cash', 'card', 'crypto', 'savings', 'investment');
CREATE TYPE debt_type AS ENUM ('i_owe', 'owe_me', 'credit', 'mortgage', 'installment');
CREATE TYPE debt_status AS ENUM ('active', 'paid', 'overdue');
CREATE TYPE goal_status AS ENUM ('active', 'completed', 'cancelled');
CREATE TYPE currency_enum AS ENUM ('RUB', 'USD', 'EUR', 'USDT');

-- Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    language VARCHAR(10) DEFAULT 'ru',
    default_currency currency_enum DEFAULT 'RUB',
    pin_hash VARCHAR(255),
    is_premium BOOLEAN DEFAULT FALSE,
    timezone VARCHAR(50) DEFAULT 'Europe/Moscow',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_telegram_id ON users(telegram_id);

-- Accounts
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(100) NOT NULL,
    account_type account_type NOT NULL,
    currency currency_enum DEFAULT 'RUB',
    balance NUMERIC(15,2) DEFAULT 0,
    icon VARCHAR(10) DEFAULT '💳',
    color VARCHAR(7) DEFAULT '#3B82F6',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Categories
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    icon VARCHAR(10) DEFAULT '📦',
    color VARCHAR(7) DEFAULT '#6B7280',
    transaction_type transaction_type NOT NULL,
    is_system BOOLEAN DEFAULT FALSE,
    budget_limit NUMERIC(15,2),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Transactions
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    transaction_type transaction_type NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    currency currency_enum DEFAULT 'RUB',
    description TEXT,
    date DATE DEFAULT CURRENT_DATE,
    is_recurring BOOLEAN DEFAULT FALSE,
    recurring_period VARCHAR(20),
    receipt_data TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_transactions_user_date ON transactions(user_id, date);
CREATE INDEX idx_transactions_user_type ON transactions(user_id, transaction_type);

-- Debts
CREATE TABLE debts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    debt_type debt_type NOT NULL,
    title VARCHAR(200) NOT NULL,
    person_name VARCHAR(200),
    total_amount NUMERIC(15,2) NOT NULL,
    remaining_amount NUMERIC(15,2) NOT NULL,
    currency currency_enum DEFAULT 'RUB',
    interest_rate NUMERIC(5,2) DEFAULT 0,
    monthly_payment NUMERIC(15,2),
    start_date DATE NOT NULL,
    due_date DATE,
    status debt_status DEFAULT 'active',
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Debt Payments
CREATE TABLE debt_payments (
    id SERIAL PRIMARY KEY,
    debt_id INTEGER REFERENCES debts(id) ON DELETE CASCADE NOT NULL,
    amount NUMERIC(15,2) NOT NULL,
    date DATE DEFAULT CURRENT_DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Goals
CREATE TABLE goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(200) NOT NULL,
    target_amount NUMERIC(15,2) NOT NULL,
    current_amount NUMERIC(15,2) DEFAULT 0,
    currency currency_enum DEFAULT 'RUB',
    deadline DATE,
    icon VARCHAR(10) DEFAULT '🎯',
    status goal_status DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Budgets
CREATE TABLE budgets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    amount NUMERIC(15,2) NOT NULL,
    period VARCHAR(20) DEFAULT 'monthly',
    currency currency_enum DEFAULT 'RUB',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Default categories
INSERT INTO categories (name, icon, color, transaction_type, is_system) VALUES
    ('Продукты', '🛒', '#10B981', 'expense', TRUE),
    ('Транспорт', '🚗', '#F59E0B', 'expense', TRUE),
    ('Кафе и рестораны', '🍽️', '#EF4444', 'expense', TRUE),
    ('Подписки', '📱', '#8B5CF6', 'expense', TRUE),
    ('Коммунальные', '🏠', '#6366F1', 'expense', TRUE),
    ('Аренда', '🔑', '#EC4899', 'expense', TRUE),
    ('Развлечения', '🎮', '#F97316', 'expense', TRUE),
    ('Одежда', '👕', '#14B8A6', 'expense', TRUE),
    ('Здоровье', '💊', '#06B6D4', 'expense', TRUE),
    ('Образование', '📚', '#0EA5E9', 'expense', TRUE),
    ('Путешествия', '✈️', '#A855F7', 'expense', TRUE),
    ('Инвестиции', '📈', '#22C55E', 'expense', TRUE),
    ('Кредиты', '🏦', '#DC2626', 'expense', TRUE),
    ('Другое', '📦', '#6B7280', 'expense', TRUE),
    ('Зарплата', '💰', '#10B981', 'income', TRUE),
    ('Фриланс', '💻', '#3B82F6', 'income', TRUE),
    ('Инвестиции', '📊', '#8B5CF6', 'income', TRUE),
    ('Подарки', '🎁', '#F59E0B', 'income', TRUE),
    ('Другое', '📦', '#6B7280', 'income', TRUE);
