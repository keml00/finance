from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from decimal import Decimal
from datetime import date
from typing import Optional
from bot.services.transaction_service import add_transaction, get_balance, get_monthly_stats
from bot.services.debt_service import get_debts, get_debt_summary, add_debt, make_payment
from bot.services.goal_service import get_goals, add_goal, add_to_goal, calculate_progress
from bot.database.models import TransactionType, DebtType, DebtStatus, GoalStatus

router = APIRouter()


# --- Schemas ---

class TransactionCreate(BaseModel):
    amount: Decimal
    transaction_type: str  # income, expense
    category_id: Optional[int] = None
    account_id: Optional[int] = None
    description: str = ""
    date: Optional[date] = None


class DebtCreate(BaseModel):
    debt_type: str
    title: str
    total_amount: Decimal
    person_name: Optional[str] = None
    interest_rate: Decimal = Decimal("0")
    monthly_payment: Optional[Decimal] = None
    due_date: Optional[date] = None


class GoalCreate(BaseModel):
    title: str
    target_amount: Decimal
    deadline: Optional[date] = None
    icon: str = "🎯"


class GoalDeposit(BaseModel):
    amount: Decimal


class DebtPaymentCreate(BaseModel):
    amount: Decimal
    notes: Optional[str] = None


# --- Transactions ---

@router.post("/transactions")
async def create_transaction(data: TransactionCreate, telegram_id: int = Query(...)):
    tx_type = TransactionType(data.transaction_type)
    tx = await add_transaction(
        telegram_id=telegram_id,
        amount=data.amount,
        transaction_type=tx_type,
        category_id=data.category_id,
        account_id=data.account_id,
        description=data.description,
        tx_date=data.date,
    )
    return {"id": tx.id, "status": "created"}


@router.get("/balance")
async def api_get_balance(telegram_id: int = Query(...)):
    accounts = await get_balance(telegram_id)
    total = sum(a["balance"] for a in accounts)
    return {"accounts": accounts, "total": total}


@router.get("/stats")
async def api_get_stats(
    telegram_id: int = Query(...),
    year: Optional[int] = None,
    month: Optional[int] = None,
):
    stats = await get_monthly_stats(telegram_id, year=year, month=month)
    return stats


# --- Debts ---

@router.get("/debts")
async def api_get_debts(telegram_id: int = Query(...)):
    debts = await get_debts(telegram_id)
    summary = await get_debt_summary(telegram_id)
    return {
        "debts": [
            {
                "id": d.id,
                "title": d.title,
                "debt_type": d.debt_type.value,
                "total_amount": float(d.total_amount),
                "remaining_amount": float(d.remaining_amount),
                "interest_rate": float(d.interest_rate),
                "monthly_payment": float(d.monthly_payment) if d.monthly_payment else None,
                "status": d.status.value,
                "due_date": d.due_date.isoformat() if d.due_date else None,
            }
            for d in debts
        ],
        "summary": summary,
    }


@router.post("/debts")
async def api_create_debt(data: DebtCreate, telegram_id: int = Query(...)):
    debt = await add_debt(
        telegram_id=telegram_id,
        debt_type=DebtType(data.debt_type),
        title=data.title,
        total_amount=data.total_amount,
        person_name=data.person_name,
        interest_rate=data.interest_rate,
        monthly_payment=data.monthly_payment,
        due_date=data.due_date,
    )
    return {"id": debt.id, "status": "created"}


@router.post("/debts/{debt_id}/pay")
async def api_pay_debt(debt_id: int, data: DebtPaymentCreate):
    payment = await make_payment(debt_id, data.amount, data.notes)
    return {"id": payment.id, "status": "paid"}


# --- Goals ---

@router.get("/goals")
async def api_get_goals(telegram_id: int = Query(...)):
    goals = await get_goals(telegram_id)
    return {
        "goals": [
            {
                "id": g.id,
                "title": g.title,
                "target_amount": float(g.target_amount),
                "current_amount": float(g.current_amount),
                "icon": g.icon,
                "status": g.status.value,
                "deadline": g.deadline.isoformat() if g.deadline else None,
                "progress": calculate_progress(g),
            }
            for g in goals
        ]
    }


@router.post("/goals")
async def api_create_goal(data: GoalCreate, telegram_id: int = Query(...)):
    goal = await add_goal(
        telegram_id=telegram_id,
        title=data.title,
        target_amount=data.target_amount,
        deadline=data.deadline,
        icon=data.icon,
    )
    return {"id": goal.id, "status": "created"}


@router.post("/goals/{goal_id}/deposit")
async def api_deposit_goal(goal_id: int, data: GoalDeposit):
    goal = await add_to_goal(goal_id, data.amount)
    return {"status": "deposited", "current_amount": float(goal.current_amount)}
