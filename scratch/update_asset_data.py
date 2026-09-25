import asyncio
import os
import sys

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from src.database.session import async_session
from src.models.assets import AssetCategory

categories = {
    "Hardware": "Laptop, Desktop, Monitor, Mobile, Tablet, Printer, Other Peripherals",
    "Network": "Router, Switch, Firewall, Access Point, Network Equipment",
    "Server & Storage": "Server, NAS, Storage, Backup",
    "Software": "Operating System, Application, Database, Development Software",
    "Software Licenses": "Subscription, Enterprise License, User License",
    "Cloud": "VM, Storage, Database, Cloud Service, SaaS",
    "Security": "Security Device, Certificate, Security Key, Security Software",
    "Communication": "IP Phone, Headset, Webcam, Conference Equipment",
    "Office": "Desk, Chair, Projector, UPS",
    "Vehicle": "Car, Bike, Other"
}

async def update_assets():
    async with async_session() as session:
        # Delete existing data from asset tables
        print("Truncating asset tables...")
        # We use cascade to delete dependencies or delete in order.
        # SQLite doesn't support TRUNCATE, so we use DELETE.
        # Ensure we delete dependent tables first if foreign keys are enforced without cascade
        await session.execute(text("DELETE FROM asset_incidents"))
        await session.execute(text("DELETE FROM asset_documents"))
        await session.execute(text("DELETE FROM asset_history"))
        await session.execute(text("DELETE FROM asset_assignments"))
        await session.execute(text("DELETE FROM assets"))
        await session.execute(text("DELETE FROM asset_categories"))
        
        print("Seeding new categories...")
        for cat_name, desc in categories.items():
            cat = AssetCategory(category_name=cat_name, description=desc)
            session.add(cat)
            
        await session.commit()
        print("Successfully updated asset data.")

if __name__ == "__main__":
    asyncio.run(update_assets())
