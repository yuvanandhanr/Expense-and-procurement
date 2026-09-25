# Goal Description
Address multiple specific issues across OCR performance, receipt duplication, receipt visibility for approvers, and strict approval tab filtering.

## Proposed Changes

### 1. OCR Performance and Duplicate Check (`src/api/expenses.py` & `src/services/ocr.py`)
- **[MODIFY] `src/api/expenses.py`**:
  - Update `upload_receipts` to use `await asyncio.to_thread(OCRService.process_receipt_image, content)`. This prevents the CPU-intensive Tesseract OCR from blocking the async event loop, massively speeding up the API's responsiveness and reducing load times.
  - Update the duplicate check to search the **entire database** instead of just the current report. If a receipt hash exists anywhere in the DB, it will be rejected as a duplicate.

### 2. Receipt Visibility for Approvers (`src/api/approvals_inbox.py`)
- **[MODIFY] `src/api/approvals_inbox.py`**:
  - Add `.options(selectinload(ExpenseReport.receipts))` to the SQLAlchemy query for `ExpenseReport`. This guarantees that when an approver views a claim, the attached receipts are loaded and visible to them, exactly as they are for the original employee.

### 3. Role-Based Claim Visibility Updates (`src/api/approvals_inbox.py`)
- **[MODIFY] `src/api/approvals_inbox.py`**:
  - **Admin / CEO / CFO:** Update their visibility conditions to simply bypass status filters: they will see **all non-draft claims** across the entire company.
  - **Finance Manager:** Update their visibility so they can see claims even when they are still at the "Pending Manager Approval" stage, fixing the issue where a submitted claim wasn't reflecting in the Finance Manager's portal early enough.

### 4. Frontend Tab Filtering Logic (`frontend/src/pages/Approvals.tsx`)
- **[MODIFY] `frontend/src/pages/Approvals.tsx`**:
  - Modify `isApprovedWf` to ONLY consider a claim "Approved" if its status is strictly `Closed` (or literally `Approved`).
  - Ensure that `Approved for Payment` falls under the "Submitted" tab until it is finally `Closed`.

## User Review Required
> [!IMPORTANT]
> The user stated: "admin and cfo, ceo will be able to see everyones claim." This is a significant change from standard strict visibility (where they only see claims assigned to them). Please confirm this global visibility is exactly what you want for these roles in the Approvals Inbox!

> [!TIP]
> The Finance Manager will now see claims even when they are just submitted to the immediate Manager. They won't be able to approve them yet, but they will see them in the "Submitted" tab.
