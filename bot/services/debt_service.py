from decimal import Decimal
from datetime import date
from sqlalchemy import select, and_
from bot.database.session import async_session
from bot.database.models import Debt, DebtPayment, DebtType, DebtStatus, User


async def get_debts(telegram_id: int, status: DebtStatus = None) -> list[Debt]:
    async with async_session() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user.scalar_one()

        query = select(Debt).where(Debt.user_id == user.id)
        if status:
            query = query.where(Debt.status == status)
        query = query.order_by(Debt.created_at.desc())

        result = await session.execute(query)
        return result.scalars().all()


async def add_debt(
    telegram_id: int,
    debt_type: DebtType,
    title: str,
    total_amount: Decimal,
    person_name: str = None,
    interest_rate: Decimal = Decimal("0"),
    monthly_payment: Decimal = None,
    start_date: date = None,
    due_date: date = None,
    notes: str = None,
) -> Debt:
    async with async_session() as session:
        user = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = user.scalar_one()

        debt = Debt(
            user_id=user.id,
            debt_type=debt_type,
            title=title,
            person_name=person_name,
            total_amount=total_amount,
            remaining_amount=total_amount,
            interest_rate=interest_rate,
            monthly_payment=monthly_payment,
            start_date=start_date or date.today(),
            due_date=due_date,
            notes=notes,
        )
        session.add(debt)
        await session.commit()
        return debt


async def make_payment(debt_id: int, amount: Decimal, notes: str = None) -> DebtPayment:
    async with async_session() as session:
        debt = await session.get(Debt, debt_id)
        if not debt:
            raise ValueError("Debt not found")

        payment = DebtPayment(
            debt_id=debt_id,
            amount=amount,
            notes=notes,
        )
        session.add(payment)

        debt.remaining_amount -= amount
        if debt.remaining_amount <= 0:
            debt.remaining_amount = Decimal("0")
            debt.status = DebtStatus.PAID

        await session.commit()
        return payment


async def get_debt_summary(telegram_id: int) -> dict:
    debts = await get_debts(telegram_id, status=DebtStatus.ACTIVE)

    total_i_owe = sum(
        float(d.remaining_amount) for d in debts
        if d.debt_type in (DebtType.I_OWE, DebtType.CREDIT, DebtType.MORTGAGE, DebtType.INSTALLMENT)
    )
    total_owe_me = sum(
        float(d.remaining_amount) for d in debts
        if d.debt_type == DebtType.OWE_ME
    )
    monthly_payments = sum(
        float(d.monthly_payment) for d in debts
        if d.monthly_payment
    )

    return {
        "total_i_owe": total_i_owe,
        "total_owe_me": total_owe_me,
        "active_debts": len(debts),
        "monthly_payments": monthly_payments,
    }
