with open("src/api/approvals_inbox.py", "r") as f:
    content = f.read()

import re
old_block_pattern = r"(# Fetch pending Asset Incidents where user is explicitly the approver\n.*?)(try:\n.*?from src.models.assets import AssetIncident, Asset.*?)(if conditions:\n\s+stmt = stmt.where\(or_\(\*conditions\)\)\n\s+result = await db.execute\(stmt\)\n\s+for incident, asset, reporter in result.all\(\):)(.*?)(except Exception as e:\n\s+logger.error\(f\"Error fetching pending Asset Incidents: \{e\}\", exc_info=True\))"

new_block = """# Fetch pending Asset Incidents where user is explicitly the approver
    try:
        from src.models.assets import AssetIncident, Asset
        from sqlalchemy import or_
        from sqlalchemy.orm import selectinload
        
        stmt = (
            select(AssetIncident, Asset, UserModel)
            .options(selectinload(UserModel.roles))
            .join(Asset, AssetIncident.asset_id == Asset.asset_id)
            .join(UserModel, AssetIncident.reporter_id == UserModel.user_id)
            .where(
                AssetIncident.reporter_id != current_user.user_id,
                AssetIncident.status != "Draft"
            )
        )
        
        conditions = []
        if has_manager:
            conditions.append(UserModel.manager_id == current_user.user_id)
            
        if has_admin or has_it:
            conditions.append(AssetIncident.status.in_(["Pending Fulfillment", "Closed", "In Progress", "Resolved"]))
            
        if conditions:
            stmt = stmt.where(or_(*conditions))
            result = await db.execute(stmt)
            for incident, asset, reporter in result.all():"""

def replacement(match):
    return new_block + match.group(4) + match.group(5)

content = re.sub(old_block_pattern, replacement, content, flags=re.DOTALL)

with open("src/api/approvals_inbox.py", "w") as f:
    f.write(content)
