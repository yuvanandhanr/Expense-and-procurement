with open("/Users/a.chaitnasree/Expense-and-procurement/frontend/src/pages/MyAssets.tsx", "r") as f:
    content = f.read()

# Replace report incident submit
old_submit = """      await api.post("/asset-incidents", {
        asset_id: selectedAsset.asset_id,
        description: incidentDescription,
        incident_type: incidentType,
        image_url: imageUrl || null
      });"""

new_submit = """      await api.post("/asset-incidents", {
        asset_id: selectedAsset.asset_id,
        description: incidentDescription,
        incident_type: incidentType,
        image_url: imageUrl || null,
        is_draft: isDraft
      });"""
content = content.replace(old_submit, new_submit)

content = content.replace(
    'const submitIncident = async (e: React.FormEvent) => {', 
    'const submitIncident = async (e: React.FormEvent, isDraft = false) => {'
)
content = content.replace(
    'onSubmit={submitIncident}',
    'onSubmit={(e) => submitIncident(e, false)}'
)
content = content.replace(
    '<Button type="submit" disabled={isSubmitting || !incidentDescription}>Submit Report</Button>',
    '<Button type="button" disabled={isSubmitting || !incidentDescription} variant="outline" onClick={(e) => submitIncident(e as any, true)}>Save Draft</Button>\n            <Button type="submit" disabled={isSubmitting || !incidentDescription}>Submit Report</Button>'
)

with open("/Users/a.chaitnasree/Expense-and-procurement/frontend/src/pages/MyAssets.tsx", "w") as f:
    f.write(content)
