import asyncio
from src.database.dependency import get_db_session
from sqlalchemy import select
from src.models.assets import AssetCategory

SUB_CATEGORIES = {
    "Hardware": ["Laptop", "Desktop", "Monitor", "Mobile", "Tablet", "Printer", "Other Peripherals"],
    "Network": ["Router", "Switch", "Firewall", "Access Point", "Network Equipment"],
    "Server & Storage": ["Server", "NAS", "Storage", "Backup"],
    "Software": ["Operating System", "Application", "Database", "Development Software"],
    "Software Licenses": ["Subscription", "Enterprise License", "User License"],
    "Cloud": ["VM", "Cloud Service", "SaaS"],
    "Security": ["Security Device", "Certificate", "Security Key", "Security Software"],
    "Communication": ["IP Phone", "Headset", "Webcam", "Conference Equipment"],
    "Office": ["Desk", "Chair", "Projector", "UPS"],
    "Vehicle": ["Car", "Bike", "Other"]
}

async def main():
    async for db in get_db_session():
        # Get existing categories
        res = await db.execute(select(AssetCategory))
        existing = {c.category_name for c in res.scalars()}
        
        added = 0
        for main, subs in SUB_CATEGORIES.items():
            for sub in subs:
                if sub not in existing:
                    new_cat = AssetCategory(category_name=sub, description=f"{sub} under {main}")
                    db.add(new_cat)
                    existing.add(sub)
                    added += 1
        
        if added > 0:
            await db.commit()
            print(f"Added {added} subcategories!")
        else:
            print("All subcategories already exist.")
        break

asyncio.run(main())
