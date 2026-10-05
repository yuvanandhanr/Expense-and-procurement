from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ExecutiveReportFilterRequest(BaseModel):
    scope: str = Field("all", description="'all', 'employee', 'department'")
    employee_id: Optional[int] = None
    department_id: Optional[int] = None
    expense_category: Optional[str] = Field("all", description="'all' or specific category")
    time_horizon: str = Field("5_YEAR_ARCHIVE", description="'5_YEAR_ARCHIVE', 'YTD', 'MTD', 'CUSTOM'")
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    status: Optional[str] = Field("Approved", description="'Approved', 'All', 'Pending'")


class DocumentMetadata(BaseModel):
    subject_entity: str
    entity_identifier: str
    prepared_by: str
    report_date: str
    reporting_period: str
    document_id: str
    classification: str


class ExecutiveSummary(BaseModel):
    core_takeaway: str
    risk_score_outlook: str


class FinancialMetricItem(BaseModel):
    metric: str
    current_period: float
    prior_period: float
    yoy_variance_pct: float
    status: str


class IncomeExpenseBreakdown(BaseModel):
    primary_revenue_streams: List[Dict[str, Any]]
    cost_structure_analysis: Dict[str, float]
    category_distribution: List[Dict[str, Any]]


class BalanceSheetSnapshot(BaseModel):
    total_assets: float
    current_assets: float
    non_current_assets: float
    total_liabilities: float
    current_liabilities: float
    long_term_obligations: float
    total_equity: float


class PredictiveInsights(BaseModel):
    trend_analysis: str
    ai_forecast_model: str
    anomaly_risk_detection: str


class SignOffVerification(BaseModel):
    prepared_by_name: str
    prepared_by_title: str
    approved_by_name: str
    approved_by_title: str


class ExecutiveReportResponse(BaseModel):
    company_name: str
    tagline: str
    document_metadata: DocumentMetadata
    executive_summary: ExecutiveSummary
    key_financial_metrics: List[FinancialMetricItem]
    income_expense_breakdown: IncomeExpenseBreakdown
    balance_sheet_snapshot: BalanceSheetSnapshot
    predictive_insights: PredictiveInsights
    sign_off: SignOffVerification
    raw_transaction_sample: List[Dict[str, Any]]
