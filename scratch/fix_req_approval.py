import re

with open("src/services/approval_service.py", "r") as f:
    content = f.read()

# We need to replace the logic block inside get_pending_approvals_for_user loop
old_block_pattern = r"(\s+)(if can_approve:\n\s+wf_hist = history_by_wf\.get.*?can_approve\n\s+\}\))"

new_block = r"""\1wf_hist = history_by_wf.get(workflow.workflow_id, [])
\1user_was_past_approver = any(h.performed_by == user.user_id for h in wf_hist)
\1is_manager_of_requestor = requestor and requestor.manager_id == user.user_id
\1
\1should_include = can_approve or user_was_past_approver or is_manager_of_requestor
\1
\1# Check strict visibility rules for Admin/CEO/CFO claims
\1requestor_roles = [r.role_name for r in getattr(requestor, "roles", [])] if requestor else []
\1if any(r in ["Admin", "CEO", "CFO", "SuperAdmin"] for r in requestor_roles):
\1    if not can_approve and not user_was_past_approver:
\1        should_include = False
\1
\1if should_include:
\1    past_approvers_list = []
\1    for h in wf_hist:
\1        if h.action == "Approve" and h.performed_by in users_by_id:
\1            u = users_by_id[h.performed_by]
\1            step = next((s for s in wf_steps if s.step_id == h.step_id), None)
\1            role_name = roles_by_id.get(step.approver_role_id, "Approver") if step else "Approver"
\1            past_approvers_list.append(f"{role_name} ({u.first_name} {u.last_name})")
\1
\1    pending_approvers = []
\1    for s in pending_steps:
\1        role_name = roles_by_id.get(s.approver_role_id, "Approver")
\1        pending_approvers.append(role_name)
\1
\1    current_step_sequence = active_step.step_number if active_step else (max(s.step_number for s in wf_steps) if wf_steps else 0)
\1    steps_to_return = [active_step] if active_step else wf_steps
\1
\1    pending_workflows.append({
\1        "workflow_id": workflow.workflow_id,
\1        "entity_type": "PurchaseRequisition",
\1        "entity_id": pr.pr_id,
\1        "current_step_sequence": current_step_sequence,
\1        "status": workflow.status,
\1        "created_at": workflow.created_at,
\1        "updated_at": workflow.updated_at,
\1        "requestor_id": pr.requestor_id,
\1        "requestor_name": f"{requestor.first_name} {requestor.last_name}" if requestor else "Employee",
\1        "requestor_designation": requestor.designation if requestor and hasattr(requestor, 'designation') and requestor.designation else "",
\1        "title": pr.title,
\1        "justification": pr.justification,
\1        "total_amount": pr.total_estimated_amount,
\1        "amount": pr.total_estimated_amount,
\1        "past_approvers": past_approvers_list,
\1        "pending_approvers": pending_approvers,
\1        "steps": steps_to_return,
\1        "can_approve": can_approve
\1    })"""

new_content = re.sub(old_block_pattern, new_block, content, flags=re.DOTALL)
with open("src/services/approval_service.py", "w") as f:
    f.write(new_content)
