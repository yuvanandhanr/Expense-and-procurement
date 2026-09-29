from typing import Optional
from decimal import Decimal
from datetime import timezone, datetime
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.organization import BudgetCode
from src.models.budget import BudgetAllocation, BudgetReservation
from src.repositories.organization import BudgetCodeRepository
from src.repositories.budget import BudgetAllocationRepository, BudgetReservationRepository


class BudgetService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.budget_code_repo = BudgetCodeRepository(db)
        self.allocation_repo = BudgetAllocationRepository(db)
        self.reservation_repo = BudgetReservationRepository(db)

    async def validate_budget_availability(self, budget_code_str: str, amount: Decimal) -> BudgetCode:
        """
        Validates if a budget exists, is active, and has sufficient available balance.
        """
        # Find budget code
        budget_code = await self.budget_code_repo.get_by_code(budget_code_str)

        if not budget_code or budget_code.status != "Active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Budget code '{budget_code_str}' does not exist or is inactive"
            )

        # Check if allocation exists and has enough capacity
        # Since we use budget_code.available_budget directly, we check it:
        if budget_code.available_budget is None or budget_code.available_budget < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient funds under budget code '{budget_code_str}'. Available: {budget_code.available_budget or 0.00}, Required: {amount}"
            )

        return budget_code

    async def reserve_budget(self, pr_id: int, budget_code_str: str, amount: Decimal) -> BudgetReservation:
        """
        Deducts from available budget and creates a reservation entry.
        """
        budget_code = await self.validate_budget_availability(budget_code_str, amount)

        # Deduct from available budget
        budget_code.available_budget -= amount
        await self.budget_code_repo.update(budget_code)

        # Increment reserved amount in allocation if one exists
        allocation = await self.allocation_repo.get_by_budget_code_id(budget_code.budget_code_id)
        if allocation:
            allocation.reserved_amount = (allocation.reserved_amount or Decimal(0.00)) + amount
            await self.allocation_repo.update(allocation)

        # Create reservation record
        reservation = BudgetReservation(
            pr_id=pr_id,
            budget_code_id=budget_code.budget_code_id,
            reserved_amount=amount,
            status="Reserved",
            created_at=datetime.now(timezone.utc)
        )
        return await self.reservation_repo.create(reservation)

    async def release_budget(self, pr_id: int) -> None:
        """
        Releases budget reservations (e.g. on PR cancellation/rejection).
        """
        reservations = await self.reservation_repo.get_by_pr_id(pr_id)
        for res in reservations:
            if res.status != "Reserved":
                continue

            res.status = "Released"
            res.released_at = datetime.now(timezone.utc)
            await self.reservation_repo.update(res)

            # Return funds to available budget
            budget_code = await self.budget_code_repo.get_by_id(res.budget_code_id)
            if budget_code:
                budget_code.available_budget += res.reserved_amount
                await self.budget_code_repo.update(budget_code)

            # Deduct from allocated reserved amount
            allocation = await self.allocation_repo.get_by_budget_code_id(res.budget_code_id)
            if allocation:
                allocation.reserved_amount = max(Decimal(0.00), (allocation.reserved_amount or Decimal(0.00)) - res.reserved_amount)
                await self.allocation_repo.update(allocation)

    async def commit_budget(self, pr_id: int) -> None:
        """
        Commits reservations (on final PR approval).
        """
        reservations = await self.reservation_repo.get_by_pr_id(pr_id)
        for res in reservations:
            if res.status != "Reserved":
                continue

            res.status = "Committed"
            await self.reservation_repo.update(res)

            # Update allocation spent vs reserved amounts
            allocation = await self.allocation_repo.get_by_budget_code_id(res.budget_code_id)
            if allocation:
                allocation.reserved_amount = max(Decimal(0.00), (allocation.reserved_amount or Decimal(0.00)) - res.reserved_amount)
                allocation.spent_amount = (allocation.spent_amount or Decimal(0.00)) + res.reserved_amount
                await self.allocation_repo.update(allocation)
