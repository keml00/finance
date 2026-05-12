from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.session import async_session
from bot.database.models import User, Account, AccountType, Currency, Category, TransactionType


async def get_or_create_user(tg_user) -> User:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == tg_user.id)
        )
        user = result.scalar_one_or_none()

        if user:
            user.username = tg_user.username
            user.first_name = tg_user.first_name
            await session.commit()
            return user

        user = User(
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
        )
        session.add(user)
        await session.flush()

        # Create default accounts
        default_accounts = [
            Account(user_id=user.id, name="Наличные", account_type=AccountType.CASH, icon="💵", color="#10B981"),
            Account(user_id=user.id, name="Карта", account_type=AccountType.CARD, icon="💳", color="#3B82F6"),
        ]
        session.add_all(default_accounts)

        # Copy system categories for user
        result = await session.execute(
            select(Category).where(Category.is_system == True)
        )
        system_cats = result.scalars().all()
        for cat in system_cats:
            new_cat = Category(
                user_id=user.id,
                name=cat.name,
                icon=cat.icon,
                color=cat.color,
                transaction_type=cat.transaction_type,
                is_system=False,
            )
            session.add(new_cat)

        await session.commit()
        return user


async def get_user_by_telegram_id(telegram_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
