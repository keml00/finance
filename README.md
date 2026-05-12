# FinAI Assistant

**AI-powered Telegram bot for personal finance management**

*by keml00, telegram*

---

## Features

- Income & expense tracking with multiple accounts
- Debt & credit management with payment schedules
- Financial goals with progress tracking
- AI-powered analytics and recommendations
- Receipt scanning (OCR/QR)
- Beautiful Telegram Mini App dashboard
- Multi-currency support
- PDF/Excel/CSV export
- Family mode

## Tech Stack

**Backend:** Python 3.12, python-telegram-bot, FastAPI, SQLAlchemy  
**Frontend:** Next.js 14, TypeScript, TailwindCSS, Framer Motion, Recharts  
**Database:** PostgreSQL 16, Redis  
**AI:** OpenRouter / Gemini / DeepSeek  
**Infrastructure:** Docker, Docker Compose

## Quick Start

```bash
# 1. Clone
git clone https://github.com/keml00/finance.git
cd finance

# 2. Configure
cp .env.example .env
# Edit .env with your values

# 3. Run
docker-compose up -d

# 4. Check logs
docker-compose logs -f bot
```

## Project Structure

```
finance/
├── bot/                    # Telegram bot + API
│   ├── handlers/           # Bot command handlers
│   ├── services/           # Business logic
│   ├── database/           # Models & migrations
│   ├── ai/                 # AI integration
│   ├── utils/              # Helpers
│   └── api/                # FastAPI endpoints
├── miniapp/                # Telegram Mini App
│   ├── src/
│   │   ├── app/            # Next.js pages
│   │   ├── components/     # React components
│   │   └── lib/            # Utils & API client
│   └── public/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Start bot |
| `/income` | Add income |
| `/expense` | Add expense |
| `/balance` | Show balance |
| `/stats` | Statistics |
| `/debts` | Manage debts |
| `/goals` | Financial goals |
| `/analytics` | AI analytics |
| `/export` | Export data |
| `/settings` | Settings |

## Deployment

```bash
# Production with SSL
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## License

MIT
