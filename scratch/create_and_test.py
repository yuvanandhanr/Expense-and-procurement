import asyncio
from src.database.session import async_session
from src.api.expenses import upload_receipts
from src.repositories.auth import UserRepository
from src.models.expense import ExpenseReport
from fastapi import UploadFile

class MockFile:
    def __init__(self, filename, content):
        self.filename = filename
        self._content = content
    async def read(self):
        return self._content

async def main():
    async with async_session() as db:
        user_repo = UserRepository(db)
        user = await user_repo.get_by_id(4) # David Kim
        
        report = ExpenseReport(employee_id=4, status="Draft", purpose="Test")
        db.add(report)
        await db.commit()
        await db.refresh(report)
        
        file = MockFile("test.png", b"fake image content for testing OCR failure?")
        
        try:
            await upload_receipts(report_id=report.expense_report_id, files=[file], db=db, current_user=user)
            print("Success")
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(main())
