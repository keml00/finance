from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.session import async_session
from bot.database.models import (
    Transaction, TransactionType, Account, Category, User, Currency
)


async def add_transaction(
    telegram_id: int,
    amount: Decimal,
    transaction_type: TransactionType,
    category_id: int | None = None,
    account_id: int | None = None,
    description: str = "",
    tx_date: date | None = None,
) -> Transaction:
    async with async_session() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user.scalar_one()

        # Get default account if not specified
        if not account_id:
            acc = await session.execute(
                select(Account).where(
                    and_(Account.user_id == user.id, Account.is_active == True)
                ).limit(1)
            )
            account = acc.scalar_one()
            account_id = account.id
        else:
            account = await session.get(Account, account_id)

        tx = Transaction(
            user_id=user.id,
            account_id=account_id,
            category_id=category_id,
            transaction_type=transaction_type,
            amount=amount,
            currency=user.default_currency,
            description=description,
            date=tx_date or date.today(),
        )
        session.add(tx)

        # Update account balance
        if transaction_type == TransactionType.INCOME:
            account.balance += amount
        elif transaction_type == TransactionType.EXPENSE:
            account.balance -= amount

        await session.commit()
        return tx


async def get_balance(telegram_id: int) -> list[dict]:
    async with async_session() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user.scalar_one()

        accounts = await session.execute(
            select(Account).where(
                and_(Account.user_id == user.id, Account.is_active == True)
            )
        )
        result = []
        for acc in accounts.scalars().all():
            result.append({
                "id": acc.id,
                "name": acc.name,
                "type": acc.account_type.value,
                "balance": float(acc.balance),
                "currency": acc.currency.value,
                "icon": acc.icon,
                "color": acc.color,
            })
        return result


async def get_monthly_stats(telegram_id: int, year: int = None, month: int = None) -> dict:
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    async with async_session() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user.scalar_one()

        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        # Total income
        income_result = await session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    Transaction.user_id == user.id,
                    Transaction.transaction_type == TransactionType.INCOME,
                    Transaction.date >= start_date,
                    Transaction.date < end_date,
                )
            )
        )
        total_income = float(income_result.scalar())

        # Total expense
        expense_result = await session.execute(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                and_(
                    Transaction.user_id == user.id,
                    Transaction.transaction_type == TransactionType.EXPENSE,
                    Transaction.date >= start_date,
                    Transaction.date < end_date,
                )
            )
        )
        total_expense = float(expense_result.scalar())

        # By category
        cat_stats = await session.execute(
            select(
                Category.name,
                Category.icon,
                func.sum(Transaction.amount).label("total")
            ).join(Category, Transaction.category_id == Category.id).where(
                and_(
                    Transaction.user_id == user.id,
                    Transaction.transaction_type == TransactionType.EXPENSE,
                    Transaction.date >= start_date,
                    Transaction.date < end_date,
                )
            ).group_by(Category.name, Category.icon).order_by(func.sum(Transaction.amount).desc())
        )

        categories = [
            {"name": row.name, "icon": row.icon, "total": float(row.total)}
            for row in cat_stats.all()
        ]

        # Count transactions
        tx_count = await session.execute(
            select(func.count()).where(
                and_(
                    Transaction.user_id == user.id,
                    Transaction.date >= start_date,
                    Transaction.date < end_date,
                )
            )
        )

        days_passed = min((datetime.now().date() - start_date).days + 1, 30)

        return {
            "year": year,
            "month": month,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "categories": categories,
            "transaction_count": tx_count.scalar(),
            "avg_daily_expense": total_expense / max(days_passed, 1),
        }
