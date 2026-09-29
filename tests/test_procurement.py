import jwt
import pytest
from datetime import timezone, datetime, date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import status
from httpx import AsyncClient
from src.core.config import settings
from src.models.auth import User, Role
from src.models.vendor import Vendor, VendorContact, VendorDocument, VendorPerformance, VendorBlacklist
from src.models.rfq import RequestForQuotation, RFQItem, RFQVendor
from src.models.quotation import VendorQuotation, QuotationItem, QuotationComparison
from src.models.purchase_order import PurchaseOrder, PurchaseOrderItem, POApproval
from src.models.contract import Contract, SubscriptionContract, AMCContract, RateContract
from src.repositories.vendor import (
    VendorRepository,
    VendorDocumentRepository,
    VendorContactRepository,
    VendorCategoryRepository,
    VendorPerformanceRepository,
    VendorBlacklistRepository,
)
from src.repositories.rfq import RFQRepository, RFQItemRepository, RFQVendorRepository
from src.repositories.quotation import QuotationRepository, QuotationItemRepository, QuotationComparisonRepository
from src.repositories.purchase_order import PORepository, POItemRepository, POApprovalRepository
from src.repositories.contract import ContractRepository, RateContractRepository, SubscriptionContractRepository, AMCContractRepository
from src.repositories.purchase_requisition import PRRepository


@pytest.fixture
def mock_officer() -> User:
    role = Role(role_id=5, role_name="Procurement Officer", status=True)
    return User(
        user_id=10,
        employee_code="PRO001",
        first_name="Procurement",
        last_name="Officer",
        email="officer@example.com",
        status="Active",
        roles=[role]
    )


@pytest.fixture
def mock_proc_manager() -> User:
    role = Role(role_id=6, role_name="Procurement Manager", status=True)
    return User(
        user_id=11,
        employee_code="MGR001",
        first_name="Procurement",
        last_name="Manager",
        email="pmanager@example.com",
        status="Active",
        roles=[role]
    )


@pytest.fixture
def officer_jwt(mock_officer) -> str:
    payload = {"sub": str(mock_officer.user_id), "email": mock_officer.email, "exp": 9999999999}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


@pytest.fixture
def pmanager_jwt(mock_proc_manager) -> str:
    payload = {"sub": str(mock_proc_manager.user_id), "email": mock_proc_manager.email, "exp": 9999999999}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


@pytest.fixture
def authenticate_officer(mock_officer):
    async def _get_current_user_override():
        return mock_officer

    async def _jwt_bearer_override():
        return {"sub": str(mock_officer.user_id), "email": mock_officer.email}

    from src.main import app
    from src.auth.dependencies import get_current_user, JWTBearer

    app.dependency_overrides[get_current_user] = _get_current_user_override
    app.dependency_overrides[JWTBearer] = _jwt_bearer_override
    yield
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(JWTBearer, None)


@pytest.fixture
def mock_vendor() -> Vendor:
    return Vendor(
        vendor_id=1,
        vendor_code="VEND001",
        vendor_name="Acme Corp",
        legal_name="Acme Corporation Ltd",
        gst_vat_number="GST123456",
        tax_number="TAX98765",
        email="info@acme.com",
        phone="555-1234",
        status="Active",
        blacklist_status=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        contacts=[],
        documents=[],
        categories=[],
        performance=None,
        blacklist_records=[]
    )


# --- 1. VENDOR CRUD TESTS ---

@pytest.mark.anyio
@patch.object(VendorRepository, "get_by_code", new_callable=AsyncMock)
@patch.object(VendorRepository, "create", new_callable=AsyncMock)
@patch.object(VendorCategoryRepository, "create", new_callable=AsyncMock)
@patch.object(VendorPerformanceRepository, "create", new_callable=AsyncMock)
@patch.object(VendorRepository, "get_by_id", new_callable=AsyncMock)
async def test_create_vendor(
    mock_get_id,
    mock_perf_create,
    mock_cat_create,
    mock_vendor_create,
    mock_get_code,
    authenticate_officer,
    async_client: AsyncClient,
    mock_vendor
):
    mock_get_code.return_value = None
    mock_vendor_create.return_value = mock_vendor
    mock_get_id.return_value = mock_vendor

    response = await async_client.post(
        "/api/v1/vendors",
        json={
            "vendor_code": "VEND001",
            "vendor_name": "Acme Corp",
            "legal_name": "Acme Corporation Ltd",
            "gst_vat_number": "GST123456",
            "tax_number": "TAX98765",
            "email": "info@acme.com",
            "phone": "555-1234",
            "categories": ["IT", "Hardware"]
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["vendor_code"] == "VEND001"


@pytest.mark.anyio
@patch.object(VendorRepository, "get_by_id", new_callable=AsyncMock)
@patch.object(VendorDocumentRepository, "create", new_callable=AsyncMock)
async def test_upload_compliance_documents(
    mock_doc_create,
    mock_vendor_get,
    authenticate_officer,
    async_client: AsyncClient,
    mock_vendor
):
    mock_vendor_get.return_value = mock_vendor
    mock_doc = VendorDocument(
        document_id=1,
        vendor_id=1,
        document_type="NDA",
        file_name="nda.pdf",
        file_path="/uploads/nda.pdf",
        uploaded_at=datetime.utcnow()
    )
    mock_doc_create.return_value = mock_doc

    response = await async_client.post(
        "/api/v1/vendors/1/documents",
        json={
            "document_type": "NDA",
            "file_name": "nda.pdf",
            "file_path": "/uploads/nda.pdf"
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["file_name"] == "nda.pdf"


# --- 2. BLACKLIST TESTS ---

@pytest.mark.anyio
@patch("src.api.vendors.get_current_user")
@patch.object(VendorRepository, "get_by_id", new_callable=AsyncMock)
@patch.object(VendorRepository, "update", new_callable=AsyncMock)
@patch.object(VendorBlacklistRepository, "create", new_callable=AsyncMock)
async def test_blacklist_vendor(
    mock_blacklist_create,
    mock_vendor_update,
    mock_vendor_get,
    mock_get_user,
    pmanager_jwt,
    mock_proc_manager,
    async_client: AsyncClient,
    mock_vendor
):
    mock_get_user.return_value = mock_proc_manager
    from src.main import app
    from src.auth.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: mock_proc_manager

    mock_vendor_get.return_value = mock_vendor

    headers = {"Authorization": f"Bearer {pmanager_jwt}"}
    response = await async_client.post("/api/v1/vendors/1/blacklist?reason=Delayed Delivery", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["blacklist_status"] is True

    app.dependency_overrides.pop(get_current_user, None)


# --- 3. RFQ INVITATIONS & SUBMISSIONS ---

@pytest.mark.anyio
@patch.object(RFQRepository, "get_by_id", new_callable=AsyncMock)
@patch.object(VendorRepository, "get_by_id", new_callable=AsyncMock)
@patch.object(RFQVendorRepository, "create", new_callable=AsyncMock)
async def test_invite_blacklisted_vendor_block(
    mock_invite_create,
    mock_vendor_get,
    mock_rfq_get,
    authenticate_officer,
    async_client: AsyncClient,
    mock_vendor
):
    mock_rfq = RequestForQuotation(rfq_id=1, rfq_number="RFQ-2026-TEST", title="Hardware RFQ", status="Draft")
    mock_rfq_get.return_value = mock_rfq

    # Set vendor as blacklisted
    mock_vendor.blacklist_status = True
    mock_vendor.status = "Inactive"
    mock_vendor_get.return_value = mock_vendor

    response = await async_client.post("/api/v1/rfq/1/invite?vendor_id=1")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "is blacklisted/inactive" in response.json()["detail"]


@pytest.mark.anyio
@patch.object(RFQRepository, "get_by_id", new_callable=AsyncMock)
@patch.object(VendorRepository, "get_by_id", new_callable=AsyncMock)
async def test_quotation_submission_blacklist_block(
    mock_vendor_get,
    mock_rfq_get,
    authenticate_officer,
    async_client: AsyncClient,
    mock_vendor
):
    mock_rfq = RequestForQuotation(rfq_id=1, rfq_number="RFQ-2026-TEST", title="Hardware RFQ", status="Published")
    mock_rfq_get.return_value = mock_rfq

    # Set vendor as blacklisted
    mock_vendor.blacklist_status = True
    mock_vendor_get.return_value = mock_vendor

    response = await async_client.post(
        "/api/v1/quotations",
        json={
            "rfq_id": 1,
            "vendor_id": 1,
            "currency": "USD",
            "items": [
                {
                    "rfq_item_id": 1,
                    "unit_price": 500.00
                }
            ]
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "is blacklisted/inactive" in response.json()["detail"]


# --- 4. COMPARISON MATRIX & SELECTION ---

@pytest.mark.anyio
@patch.object(QuotationRepository, "list_by_rfq", new_callable=AsyncMock)
@patch.object(QuotationComparisonRepository, "get_by_rfq", new_callable=AsyncMock)
@patch.object(QuotationComparisonRepository, "create", new_callable=AsyncMock)
@patch.object(QuotationComparisonRepository, "get_by_id", new_callable=AsyncMock)
async def test_quotation_comparison(
    mock_comp_get_id,
    mock_comp_create,
    mock_comp_get_rfq,
    mock_quote_list,
    authenticate_officer,
    async_client: AsyncClient
):
    q1 = VendorQuotation(quotation_id=1, quotation_number="QT1", total_amount=Decimal("1200.00"), technical_score=Decimal("80.00"))
    q2 = VendorQuotation(quotation_id=2, quotation_number="QT2", total_amount=Decimal("1000.00"), technical_score=Decimal("95.00"))
    mock_quote_list.return_value = [q1, q2]
    mock_comp_get_rfq.return_value = None

    comp = QuotationComparison(
        comparison_id=1,
        rfq_id=1,
        winner_technical_quotation_id=2, # Higher technical score (95 vs 80)
        winner_commercial_quotation_id=2, # Lower total cost (1000 vs 1200)
        actioned_at=datetime.utcnow()
    )
    mock_comp_create.return_value = comp
    mock_comp_get_id.return_value = comp

    response = await async_client.get("/api/v1/rfq/1/comparison")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["winner_technical_quotation_id"] == 2
    assert response.json()["winner_commercial_quotation_id"] == 2


# --- 5. PURCHASE ORDER GENERATION ---

@pytest.mark.anyio
@patch.object(PRRepository, "get_by_id", new_callable=AsyncMock)
@patch.object(PORepository, "create", new_callable=AsyncMock)
@patch.object(POItemRepository, "create", new_callable=AsyncMock)
@patch.object(PORepository, "get_by_id", new_callable=AsyncMock)
async def test_po_skip_rfq_for_low_value(
    mock_po_get,
    mock_item_create,
    mock_po_create,
    mock_pr_get,
    authenticate_officer,
    override_db,
    async_client: AsyncClient
):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    override_db.execute = AsyncMock(return_value=mock_result)

    from src.models.purchase_requisition import PurchaseRequisition
    pr = PurchaseRequisition(pr_id=1, total_estimated_amount=Decimal("800.00"), items=[])
    mock_pr_get.return_value = pr

    po = PurchaseOrder(
        po_id=1, 
        po_number="PO-1234", 
        vendor_id=1, 
        pr_id=1, 
        total_amount=Decimal("800.00"), 
        tax_amount=Decimal("0.00"),
        discount_amount=Decimal("0.00"),
        grand_total=Decimal("800.00"), 
        status="Draft",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        items=[]
    )
    mock_po_create.return_value = po
    mock_po_get.return_value = po

    response = await async_client.post(
        "/api/v1/purchase-orders",
        json={
            "vendor_id": 1,
            "pr_id": 1,
            "items": [
                {
                    "item_name": "Screws",
                    "quantity": 100,
                    "unit_price": 8.00
                }
            ]
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert Decimal(response.json()["grand_total"]) == Decimal("800.00")


# --- 6. CONTRACTS, SUBSCRIPTIONS & AMC ---

@pytest.mark.anyio
@patch.object(ContractRepository, "get_by_number", new_callable=AsyncMock)
@patch.object(ContractRepository, "create", new_callable=AsyncMock)
@patch.object(SubscriptionContractRepository, "create", new_callable=AsyncMock)
@patch.object(ContractRepository, "get_by_id", new_callable=AsyncMock)
async def test_create_subscription_contract(
    mock_get_id,
    mock_sub_create,
    mock_contract_create,
    mock_get_number,
    authenticate_officer,
    async_client: AsyncClient
):
    mock_get_number.return_value = None
    
    contract = Contract(
        contract_id=1,
        contract_number="CON-SUB-1",
        vendor_id=1,
        title="Slack SaaS Subscription",
        contract_type="subscription",
        status="Active",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_contract_create.return_value = contract
    mock_get_id.return_value = contract

    response = await async_client.post(
        "/api/v1/contracts",
        json={
            "contract_number": "CON-SUB-1",
            "vendor_id": 1,
            "title": "Slack SaaS Subscription",
            "contract_type": "subscription",
            "start_date": str(date.today()),
            "end_date": str(date.today() + timedelta(days=365)),
            "subscription_details": {
                "license_count": 50,
                "billing_frequency": "Annually",
                "unit_price": 96.00,
                "auto_renew": True
            }
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["contract_type"] == "subscription"
