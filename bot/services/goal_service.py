from decimal import Decimal
from datetime import date
from sqlalchemy import select
from bot.database.session import async_session
from bot.database.models import Goal, GoalStatus, User


async def get_goals(telegram_id: int, status: GoalStatus = None) -> list[Goal]:
    async with async_session() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user.scalar_one()

        query = select(Goal).where(Goal.user_id == user.id)
        if status:
            query = query.where(Goal.status == status)
        query = query.order_by(Goal.created_at.desc())

        result = await session.execute(query)
        return result.scalars().all()


async def add_goal(
    telegram_id: int,
    title: str,
    target_amount: Decimal,
    deadline: date = None,
    icon: str = "🎯",
) -> Goal:
    async with async_session() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user.scalar_one()

        goal = Goal(
            user_id=user.id,
            title=title,
            target_amount=target_amount,
            deadline=deadline,
            icon=icon,
        )
        session.add(goal)
        await session.commit()
        return goal


async def add_to_goal(goal_id: int, amount: Decimal) -> Goal:
    async with async_session() as session:
        goal = await session.get(Goal, goal_id)
        if not goal:
            raise ValueError("Goal not found")

        goal.current_amount += amount
        if goal.current_amount >= goal.target_amount:
            goal.status = GoalStatus.COMPLETED

        await session.commit()
        return goal


def calculate_progress(goal: Goal) -> dict:
    progress = float(goal.current_amount) / float(goal.target_amount) * 100
    remaining = float(goal.target_amount) - float(goal.current_amount)

    days_left = None
    monthly_needed = None
    if goal.deadline:
        days_left = (goal.deadline - date.today()).days
        if days_left > 0:
            months_left = days_left / 30
            monthly_needed = remaining / max(months_left, 1)

    return {
        "progress": min(progress, 100),
        "remaining": remaining,
        "days_left": days_left,
        "monthly_needed": monthly_needed,
    }
