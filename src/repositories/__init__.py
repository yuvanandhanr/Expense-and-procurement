from src.repositories.base import BaseRepository
from src.repositories.auth import (
    UserRepository,
    RoleRepository,
    PermissionRepository,
    UserRoleRepository,
    SessionRepository,
    LoginHistoryRepository,
    RefreshTokenRepository,
)
from src.repositories.organization import (
    DepartmentRepository,
    DesignationRepository,
    CostCenterRepository,
    BudgetCodeRepository,
    OrgSettingsRepository,
)
from src.repositories.purchase_requisition import (
    PRRepository,
    PRItemRepository,
)
from src.repositories.approval import (
    ApprovalMatrixRepository,
    ApprovalWorkflowRepository,
    ApprovalStepRepository,
    WorkflowHistoryRepository,
    ApprovalHistoryRepository,
    CommentRepository,
)
from src.repositories.budget import (
    BudgetAllocationRepository,
    BudgetReservationRepository,
)
from src.repositories.attachment import (
    PRAttachmentRepository,
)
from src.repositories.vendor import (
    VendorRepository,
    VendorContactRepository,
    VendorDocumentRepository,
    VendorCategoryRepository,
    VendorPerformanceRepository,
    VendorBlacklistRepository,
)
from src.repositories.rfq import (
    RFQRepository,
    RFQItemRepository,
    RFQVendorRepository,
)
from src.repositories.quotation import (
    QuotationRepository,
    QuotationItemRepository,
    QuotationComparisonRepository,
)
from src.repositories.purchase_order import (
    PORepository,
    POItemRepository,
    POApprovalRepository,
)
from src.repositories.contract import (
    ContractRepository,
    ContractDocumentRepository,
    SubscriptionContractRepository,
    AMCContractRepository,
    RateContractRepository,
)
from src.repositories.delivery import (
    DeliveryRepository,
    DeliveryItemRepository,
)
from src.repositories.inspection import (
    InspectionRepository,
    InspectionItemRepository,
)
from src.repositories.grn import (
    GRNRepository,
    GRNItemRepository,
)
from src.repositories.assets import (
    AssetCategoryRepository,
    AssetRepository,
    AssetAssignmentRepository,
    AssetHistoryRepository,
    AssetDocumentRepository,
)
from src.repositories.invoice import (
    InvoiceRepository,
    InvoiceItemRepository,
    InvoiceDocumentRepository,
    InvoiceApprovalRepository,
)
from src.repositories.matching import (
    ThreeWayMatchingRepository,
)
from src.repositories.payments import (
    PaymentRequestRepository,
    PaymentApprovalRepository,
)
from src.repositories.procurement import (
    ProcurementClosureRepository,
)
from src.repositories.platform_services import (
    NotificationTemplateRepository,
    NotificationRepository,
    NotificationPreferenceRepository,
    AuditLogRepository,
    ActivityLogRepository,
    ReportRepository,
    ScheduledReportRepository,
    DashboardWidgetRepository,
    SavedFilterRepository,
    SearchIndexRepository,
    AttachmentRepository,
    AttachmentVersionRepository,
    JobRepository,
    JobHistoryRepository,
    SystemHealthRepository,
    SystemMetricRepository,
    SystemSettingRepository,
    EmailTemplateRepository,
    EmailQueueRepository,
    CacheMetadataRepository,
)

__all__ = [
    "BaseRepository",
    "UserRepository",
    "RoleRepository",
    "PermissionRepository",
    "UserRoleRepository",
    "SessionRepository",
    "LoginHistoryRepository",
    "RefreshTokenRepository",
    "DepartmentRepository",
    "DesignationRepository",
    "CostCenterRepository",
    "BudgetCodeRepository",
    "OrgSettingsRepository",
    "PRRepository",
    "PRItemRepository",
    "ApprovalMatrixRepository",
    "ApprovalWorkflowRepository",
    "ApprovalStepRepository",
    "WorkflowHistoryRepository",
    "ApprovalHistoryRepository",
    "CommentRepository",
    "BudgetAllocationRepository",
    "BudgetReservationRepository",
    "PRAttachmentRepository",
    "VendorRepository",
    "VendorContactRepository",
    "VendorDocumentRepository",
    "VendorCategoryRepository",
    "VendorPerformanceRepository",
    "VendorBlacklistRepository",
    "RFQRepository",
    "RFQItemRepository",
    "RFQVendorRepository",
    "QuotationRepository",
    "QuotationItemRepository",
    "QuotationComparisonRepository",
    "PORepository",
    "POItemRepository",
    "POApprovalRepository",
    "ContractRepository",
    "ContractDocumentRepository",
    "SubscriptionContractRepository",
    "AMCContractRepository",
    "RateContractRepository",
    "DeliveryRepository",
    "DeliveryItemRepository",
    "InspectionRepository",
    "InspectionItemRepository",
    "GRNRepository",
    "GRNItemRepository",
    "AssetCategoryRepository",
    "AssetRepository",
    "AssetAssignmentRepository",
    "AssetHistoryRepository",
    "AssetDocumentRepository",
    "InvoiceRepository",
    "InvoiceItemRepository",
    "InvoiceDocumentRepository",
    "InvoiceApprovalRepository",
    "ThreeWayMatchingRepository",
    "PaymentRequestRepository",
    "PaymentApprovalRepository",
    "ProcurementClosureRepository",
    "NotificationTemplateRepository",
    "NotificationRepository",
    "NotificationPreferenceRepository",
    "AuditLogRepository",
    "ActivityLogRepository",
    "ReportRepository",
    "ScheduledReportRepository",
    "DashboardWidgetRepository",
    "SavedFilterRepository",
    "SearchIndexRepository",
    "AttachmentRepository",
    "AttachmentVersionRepository",
    "JobRepository",
    "JobHistoryRepository",
    "SystemHealthRepository",
    "SystemMetricRepository",
    "SystemSettingRepository",
    "EmailTemplateRepository",
    "EmailQueueRepository",
    "CacheMetadataRepository",
]
