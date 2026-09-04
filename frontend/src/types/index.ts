export interface Permission {
  permission_id: number;
  permission_name: string;
  description?: string;
  module: string;
}

export interface Role {
  role_id: number;
  role_name: string;
  description?: string;
  status: boolean;
  permissions?: Permission[];
}

export interface User {
  user_id: number;
  employee_code: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  department_id?: number;
  designation_id?: number;
  status: string;
  roles: Role[];
}

export interface Department {
  department_id: number;
  department_name: string;
  department_code: string;
  description?: string;
  status: boolean;
}

export interface CostCenter {
  cost_center_id: number;
  cost_center_name: string;
  department_id?: number;
  budget_limit: number;
  status: boolean;
}

export interface BudgetCode {
  budget_code_id: number;
  budget_code: string;
  description?: string;
  department_id?: number;
  cost_center_id?: number;
  annual_budget: number;
  available_budget: number;
  fiscal_year: string;
  status: string;
}

export interface PRItem {
  item_id: number;
  item_description: string;
  category: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  required_by_date: string;
}

export interface PurchaseRequisition {
  pr_id: number;
  pr_number: string;
  requestor_id?: number;
  requestor_name?: string;
  title: string;
  description?: string;
  justification: string;
  department_id: number;
  cost_centre_id?: number;
  budget_code_id?: number;
  total_estimated_amount: number;
  currency: string;
  priority: string;
  status: string;
  requested_by: number;
  created_at: string;
  updated_at: string;
  items?: PRItem[];
}

export interface ApprovalStep {
  step_id: number;
  workflow_id: number;
  sequence_number: number;
  approver_id: number;
  role_name?: string;
  status: string;
  actioned_at?: string;
}

export interface ApprovalWorkflow {
  workflow_id: number;
  entity_type: string;
  entity_id: number;
  current_step_sequence: number;
  status: string;
  created_at: string;
  requestor_id?: number;
  requester_id?: number;
  requestor_name?: string;
  workflow_step?: string;
  title?: string;
  justification?: string;
  past_approvers?: string[];
  pending_approvers?: string[];
  steps?: ApprovalStep[];
  can_approve?: boolean;
}

export interface Vendor {
  vendor_id: number;
  vendor_code: string;
  company_name: string;
  contact_name: string;
  email: string;
  phone?: string;
  address?: string;
  tax_identifier?: string;
  compliance_status: string;
  status: string;
  scoreCard?: number;
}

export interface RFQItem {
  rfq_item_id: number;
  item_description: string;
  quantity: number;
}

export interface RFQ {
  rfq_id: number;
  rfq_number: string;
  pr_id: number;
  title: string;
  description?: string;
  submission_deadline: string;
  status: string;
  created_at: string;
  items?: RFQItem[];
}

export interface QuotationItem {
  quotation_item_id?: number;
  quotation_id?: number;
  rfq_item_id: number;
  unit_price: number;
  tax_amount?: number;
  discount_amount?: number;
  total_price?: number;
}

export interface Quotation {
  quotation_id: number;
  rfq_id: number;
  vendor_id: number;
  quotation_number: string;
  total_amount: number;
  currency: string;
  lead_time_days?: number;
  status: string;
  is_selected?: boolean;
  submitted_at: string;
  items?: QuotationItem[];
}

export interface POItem {
  po_item_id: number;
  item_description: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface PurchaseOrder {
  po_id: number;
  po_number: string;
  pr_id: number;
  vendor_id: number;
  total_amount: number;
  currency: string;
  status: string;
  created_at: string;
  items?: POItem[];
}

export interface Contract {
  contract_id: number;
  contract_number: string;
  vendor_id: number;
  title: string;
  description?: string;
  start_date: string;
  end_date: string;
  total_value: number;
  currency: string;
  status: string;
  created_at: string;
}

export interface Delivery {
  delivery_id: number;
  po_id: number;
  delivery_number: string;
  delivered_date: string;
  received_by: number;
  status: string;
}

export interface GRNItem {
  grn_item_id: number;
  po_item_id: number;
  received_quantity: number;
  accepted_quantity: number;
  rejected_quantity: number;
  rejection_reason?: string;
}

export interface GRN {
  grn_id: number;
  grn_number: string;
  po_id: number;
  delivery_id?: number;
  received_date: string;
  status: string;
  items?: GRNItem[];
}

export interface Asset {
  asset_id: number;
  asset_code: string;
  asset_name: string;
  category: string;
  serial_number?: string;
  cost: number;
  purchase_date: string;
  location?: string;
  status: string;
  assigned_to_id?: number;
  assigned_to_name?: string;
}

export interface Invoice {
  invoice_id: number;
  invoice_number: string;
  vendor_id: number;
  vendor_name?: string;
  po_id?: number;
  invoice_date: string;
  due_date: string;
  grand_total: number;
  amount?: number;
  currency: string;
  status: string;
  matching_status: string;
}

export interface Payment {
  payment_id: number;
  invoice_id: number;
  payment_number: string;
  amount: number;
  currency: string;
  payment_date: string;
  payment_method: string;
  transaction_reference?: string;
  status: string;
}

export interface AuditLog {
  audit_log_id: number;
  timestamp: string;
  user_email: string;
  action: string;
  module: string;
  entity_id?: string;
  ip_address?: string;
}

export interface Notification {
  notification_id: number;
  user_id: number;
  title: string;
  message: string;
  notification_type: string;
  status: string;
  created_at: string;
}

export interface SystemSetting {
  setting_id: number;
  key: string;
  value: string;
  description?: string;
  category: string;
}

export interface SearchResult {
  index_id: number;
  entity_type: string;
  entity_id: string;
  title: string;
  content: string;
  meta_data?: string;
  updated_at: string;
}

export interface Receipt {
  receipt_id: number;
  expense_report_id: number;
  merchant_name?: string;
  receipt_date?: string;
  receipt_number?: string;
  category?: string;
  ocr_amount: number;
  verified_amount: number;
  tax: number;
  currency: string;
  ocr_confidence?: number;
  image_path: string;
  file_name: string;
  created_at: string;
}

export interface ExpenseReport {
  expense_report_id: number;
  employee_id: number;
  purpose: string;
  justification?: string;
  department_id?: number;
  cost_center_id?: number;
  project_code?: string;
  status: string;
  currency: string;
  total_amount: number;
  duplicate_flag?: boolean;
  policy_flags?: string;
  created_at: string;
  updated_at: string;
  receipts?: Receipt[];
}

export type CurrentUser = User;

export interface Report {
  report_id: number;
  name: string;
  report_type: string;
  file_type: string;
  file_path?: string;
  status: string;
  created_at: string;
}

