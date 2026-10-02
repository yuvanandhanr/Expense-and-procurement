import asyncio
import os
import sys
from datetime import datetime
from decimal import Decimal
import uuid

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from src.core.config import settings
from src.models.vendor import Vendor
from src.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from src.models.assets import Asset, AssetCategory
from src.models.delivery import Delivery, DeliveryItem

RAW_DATA = """PR-001	Yuvan Sourcing Vendor	Q3 Server Upgrades	₹150000.00	High	Approved	8/5/2026	
PR-005	Yuvan Sourcing Vendor	Developer Laptops	₹12500.00	Medium	Approved	8/5/2026	
PR-00001	Yuvan Sourcing Vendor	Kaggle Order PO-00001	₹23672.88	Medium	Approved	10/17/2023	
PR-00002	Yuvan Sourcing Vendor	Kaggle Order PO-00002	₹59333.88	Medium	Approved	4/25/2022	
PR-00003	Yuvan Sourcing Vendor	Kaggle Order PO-00003	₹86914.10	Medium	Approved	1/26/2022	
PR-00004	Yuvan Sourcing Vendor	Kaggle Order PO-00004	₹134198.40	Medium	Approved	10/9/2022	
PR-00005	Yuvan Sourcing Vendor	Kaggle Order PO-00005	₹75602.60	Medium	Approved	9/8/2022	
PR-00006	Yuvan Sourcing Vendor	Kaggle Order PO-00006	₹79245.45	Medium	Approved	8/17/2022	
PR-00007	Yuvan Sourcing Vendor	Kaggle Order PO-00007	₹91130.38	Medium	Approved	5/23/2022	
PR-00008	Yuvan Sourcing Vendor	Kaggle Order PO-00008	₹40401.42	Medium	Approved	4/15/2022	
PR-00009	Yuvan Sourcing Vendor	Kaggle Order PO-00009	₹74153.84	Medium	Approved	11/24/2023	
PR-00010	Yuvan Sourcing Vendor	Kaggle Order PO-00010	₹13144.77	Medium	Approved	7/13/2023	
PR-00011	Yuvan Sourcing Vendor	Kaggle Order PO-00011	₹392450.00	Medium	Approved	3/31/2022	
PR-00012	Yuvan Sourcing Vendor	Kaggle Order PO-00012	₹444800.00	Medium	Approved	8/28/2023	
PR-00013	Yuvan Sourcing Vendor	Kaggle Order PO-00013	₹433700.00	Medium	Approved	3/9/2023	
PR-00014	Yuvan Sourcing Vendor	Kaggle Order PO-00014	₹91500.00	Medium	Approved	2/2/2022	
PR-00015	Yuvan Sourcing Vendor	Kaggle Order PO-00015	₹272500.00	Medium	Approved	1/31/2022	
PR-00016	Yuvan Sourcing Vendor	Kaggle Order PO-00016	₹77050.00	Medium	Approved	4/6/2022	
PR-00017	Yuvan Sourcing Vendor	Kaggle Order PO-00017	₹72186.42	Medium	Approved	8/12/2022	
PR-00018	Yuvan Sourcing Vendor	Kaggle Order PO-00018	₹47413.08	Medium	Approved	8/27/2022	
PR-00019	Yuvan Sourcing Vendor	Kaggle Order PO-00019	₹169409.61	Medium	Approved	6/2/2023	
PR-00020	Yuvan Sourcing Vendor	Kaggle Order PO-00020	₹8233.20	Medium	Approved	9/9/2023	
PR-00021	Yuvan Sourcing Vendor	Kaggle Order PO-00021	₹35636.90	Medium	Approved	1/28/2022	
PR-00022	Yuvan Sourcing Vendor	Kaggle Order PO-00022	₹34453.26	Medium	Approved	7/29/2023	
PR-00023	Yuvan Sourcing Vendor	Kaggle Order PO-00023	₹66248.91	Medium	Approved	7/23/2022	
PR-00024	Yuvan Sourcing Vendor	Kaggle Order PO-00024	₹28504.29	Medium	Approved	10/28/2023	
PR-00025	Yuvan Sourcing Vendor	Kaggle Order PO-00025	₹33334.50	Medium	Approved	12/20/2023	
PR-00026	Yuvan Sourcing Vendor	Kaggle Order PO-00026	₹28476.05	Medium	Approved	7/13/2023	
PR-00027	Yuvan Sourcing Vendor	Kaggle Order PO-00027	₹66861.00	Medium	Approved	3/6/2023	
PR-00028	Yuvan Sourcing Vendor	Kaggle Order PO-00028	₹7451.55	Medium	Approved	8/14/2022	
PR-00029	Yuvan Sourcing Vendor	Kaggle Order PO-00029	₹114178.90	Medium	Approved	4/5/2023	
PR-00030	Yuvan Sourcing Vendor	Kaggle Order PO-00030	₹80952.75	Medium	Approved	8/27/2023	
PR-00031	Yuvan Sourcing Vendor	Kaggle Order PO-00031	₹5900.60	Medium	Approved	10/12/2022	
PR-00032	Yuvan Sourcing Vendor	Kaggle Order PO-00032	₹21767.76	Medium	Approved	1/7/2022	
PR-00033	Yuvan Sourcing Vendor	Kaggle Order PO-00033	₹51546.43	Medium	Approved	6/13/2022	
PR-00034	Yuvan Sourcing Vendor	Kaggle Order PO-00034	₹67560.77	Medium	Approved	12/16/2023	
PR-00035	Yuvan Sourcing Vendor	Kaggle Order PO-00035	₹3293.69	Medium	Approved	3/9/2023	
PR-00036	Yuvan Sourcing Vendor	Kaggle Order PO-00036	₹26494.46	Medium	Approved	12/15/2022	
PR-00037	Yuvan Sourcing Vendor	Kaggle Order PO-00037	₹79333.38	Medium	Approved	10/12/2022	
PR-00038	Yuvan Sourcing Vendor	Kaggle Order PO-00038	₹91696.26	Medium	Approved	6/9/2022	
PR-00039	Yuvan Sourcing Vendor	Kaggle Order PO-00039	₹131586.02	Medium	Approved	8/9/2022	
PR-00040	Yuvan Sourcing Vendor	Kaggle Order PO-00040	₹24250.72	Medium	Approved	12/11/2022	
PR-00041	Yuvan Sourcing Vendor	Kaggle Order PO-00041	₹20126.96	Medium	Approved	4/15/2022	
PR-00042	Yuvan Sourcing Vendor	Kaggle Order PO-00042	₹45438.40	Medium	Approved	4/5/2022	
PR-00043	Yuvan Sourcing Vendor	Kaggle Order PO-00043	₹112091.85	Medium	Approved	1/25/2023	
PR-00044	Yuvan Sourcing Vendor	Kaggle Order PO-00044	₹75746.10	Medium	Approved	4/10/2022	
PR-00045	Yuvan Sourcing Vendor	Kaggle Order PO-00045	₹72705.43	Medium	Approved	1/3/2023	
PR-00046	Yuvan Sourcing Vendor	Kaggle Order PO-00046	₹21637.75	Medium	Approved	12/19/2022	
PR-00047	Yuvan Sourcing Vendor	Kaggle Order PO-00047	₹110933.12	Medium	Approved	9/11/2023	
PR-00048	Yuvan Sourcing Vendor	Kaggle Order PO-00048	₹2738.94	Medium	Approved	9/28/2022	
PR-00049	Yuvan Sourcing Vendor	Kaggle Order PO-00049	₹52807.08	Medium	Approved	2/14/2022	
PR-00050	Yuvan Sourcing Vendor	Kaggle Order PO-00050	₹11923.20	Medium	Approved	4/16/2023	
PR-00051	Yuvan Sourcing Vendor	Kaggle Order PO-00051	₹22717.92	Medium	Approved	7/4/2023	
PR-00052	Yuvan Sourcing Vendor	Kaggle Order PO-00052	₹12845.88	Medium	Approved	5/8/2022	
PR-00053	Yuvan Sourcing Vendor	Kaggle Order PO-00053	₹141360.97	Medium	Approved	1/23/2023	
PR-00054	Yuvan Sourcing Vendor	Kaggle Order PO-00054	₹127788.80	Medium	Approved	3/22/2022	
PR-00055	Yuvan Sourcing Vendor	Kaggle Order PO-00055	₹89727.21	Medium	Approved	7/20/2023	
PR-00056	Yuvan Sourcing Vendor	Kaggle Order PO-00056	₹88928.14	Medium	Approved	10/28/2022	
PR-00057	Yuvan Sourcing Vendor	Kaggle Order PO-00057	₹76264.74	Medium	Approved	10/6/2023	
PR-00058	Yuvan Sourcing Vendor	Kaggle Order PO-00058	₹47305.16	Medium	Approved	9/26/2023	
PR-00059	Yuvan Sourcing Vendor	Kaggle Order PO-00059	₹145610.68	Medium	Approved	1/6/2023	
PR-00060	Yuvan Sourcing Vendor	Kaggle Order PO-00060	₹62417.08	Medium	Approved	8/15/2023	
PR-00061	Yuvan Sourcing Vendor	Kaggle Order PO-00061	₹69314.64	Medium	Approved	7/16/2022	
PR-00062	Yuvan Sourcing Vendor	Kaggle Order PO-00062	₹865.90	Medium	Approved	12/23/2023	
PR-00063	Yuvan Sourcing Vendor	Kaggle Order PO-00063	₹87451.40	Medium	Approved	3/13/2022	
PR-00064	Yuvan Sourcing Vendor	Kaggle Order PO-00064	₹3013.20	Medium	Approved	2/16/2022	
PR-00065	Yuvan Sourcing Vendor	Kaggle Order PO-00065	₹134875.11	Medium	Approved	11/9/2023	
PR-00066	Yuvan Sourcing Vendor	Kaggle Order PO-00066	₹26005.87	Medium	Approved	8/22/2022	
PR-00067	Yuvan Sourcing Vendor	Kaggle Order PO-00067	₹67496.00	Medium	Approved	10/24/2022	
PR-00068	Yuvan Sourcing Vendor	Kaggle Order PO-00068	₹6135.65	Medium	Approved	3/23/2022	
PR-00069	Yuvan Sourcing Vendor	Kaggle Order PO-00069	₹3902.22	Medium	Approved	8/27/2022	
PR-00070	Yuvan Sourcing Vendor	Kaggle Order PO-00070	₹28721.70	Medium	Approved	4/14/2022	
PR-00071	Yuvan Sourcing Vendor	Kaggle Order PO-00071	₹49973.00	Medium	Approved	1/25/2023	
PR-00072	Yuvan Sourcing Vendor	Kaggle Order PO-00072	₹98819.16	Medium	Approved	10/12/2022	
PR-00073	Yuvan Sourcing Vendor	Kaggle Order PO-00073	₹47928.84	Medium	Approved	4/10/2023	
PR-00074	Yuvan Sourcing Vendor	Kaggle Order PO-00074	₹53268.75	Medium	Approved	10/13/2023	
PR-00075	Yuvan Sourcing Vendor	Kaggle Order PO-00075	₹99574.11	Medium	Approved	1/9/2023	
PR-00076	Yuvan Sourcing Vendor	Kaggle Order PO-00076	₹9045.15	Medium	Approved	6/16/2022	
PR-00077	Yuvan Sourcing Vendor	Kaggle Order PO-00077	₹139060.80	Medium	Approved	1/15/2023	
PR-00078	Yuvan Sourcing Vendor	Kaggle Order PO-00078	₹14944.35	Medium	Approved	12/30/2022	
PR-00079	Yuvan Sourcing Vendor	Kaggle Order PO-00079	₹55802.56	Medium	Approved	8/3/2022	
PR-00080	Yuvan Sourcing Vendor	Kaggle Order PO-00080	₹159181.05	Medium	Approved	11/18/2023	
PR-00081	Yuvan Sourcing Vendor	Kaggle Order PO-00081	₹52552.44	Medium	Approved	10/1/2022	
PR-00082	Yuvan Sourcing Vendor	Kaggle Order PO-00082	₹46926.00	Medium	Approved	12/20/2023	
PR-00083	Yuvan Sourcing Vendor	Kaggle Order PO-00083	₹6163.92	Medium	Approved	12/1/2023	
PR-00084	Yuvan Sourcing Vendor	Kaggle Order PO-00084	₹9853.20	Medium	Approved	10/26/2023	
PR-00085	Yuvan Sourcing Vendor	Kaggle Order PO-00085	₹31388.80	Medium	Approved	3/15/2022	
PR-00086	Yuvan Sourcing Vendor	Kaggle Order PO-00086	₹93047.85	Medium	Approved	9/16/2023	
PR-00087	Yuvan Sourcing Vendor	Kaggle Order PO-00087	₹89839.55	Medium	Approved	10/13/2023	
PR-00088	Yuvan Sourcing Vendor	Kaggle Order PO-00088	₹93635.49	Medium	Approved	6/25/2022	
PR-00089	Yuvan Sourcing Vendor	Kaggle Order PO-00089	₹19919.75	Medium	Approved	7/1/2023	
PR-00090	Yuvan Sourcing Vendor	Kaggle Order PO-00090	₹108813.60	Medium	Approved	9/8/2022	
PR-00091	Yuvan Sourcing Vendor	Kaggle Order PO-00091	₹148099.49	Medium	Approved	6/17/2022	
PR-00092	Yuvan Sourcing Vendor	Kaggle Order PO-00092	₹48154.50	Medium	Approved	4/19/2023	
PR-00093	Yuvan Sourcing Vendor	Kaggle Order PO-00093	₹72791.46	Medium	Approved	1/24/2023	
PR-00094	Yuvan Sourcing Vendor	Kaggle Order PO-00094	₹72988.20	Medium	Approved	10/4/2022	
PR-00095	Yuvan Sourcing Vendor	Kaggle Order PO-00095	₹174302.10	Medium	Approved	10/18/2023	
PR-00096	Yuvan Sourcing Vendor	Kaggle Order PO-00096	₹123783.00	Medium	Approved	12/6/2023"""

async def seed_orders():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        # Get or create vendor
        vendor_code = "V-YUVAN"
        vendor_name = "Yuvan Sourcing Vendor"
        result = await session.execute(select(Vendor).where(Vendor.vendor_code == vendor_code))
        vendor = result.scalar_one_or_none()
        
        if not vendor:
            vendor = Vendor(
                vendor_code=vendor_code,
                vendor_name=vendor_name,
                status="Active"
            )
            session.add(vendor)
            await session.flush()

        # Get or create an Asset Category
        result = await session.execute(select(AssetCategory).where(AssetCategory.category_name == "General Equipment"))
        category = result.scalar_one_or_none()
        if not category:
            category = AssetCategory(
                category_name="General Equipment",
                description="Default category for generated orders"
            )
            session.add(category)
            await session.flush()

        lines = RAW_DATA.strip().split("\n")
        
        for idx, line in enumerate(lines):
            parts = line.split("\t")
            if len(parts) < 7:
                continue
            
            pr_num = parts[0].strip()
            title = parts[2].strip()
            cost_str = parts[3].strip().replace("₹", "").replace(",", "")
            date_str = parts[6].strip()
            
            try:
                cost = Decimal(cost_str)
                created_date = datetime.strptime(date_str, "%m/%d/%Y")
            except Exception as e:
                print(f"Error parsing line {line}: {e}")
                continue

            # Create Purchase Order
            po_number = f"PO-{pr_num}"
            po = PurchaseOrder(
                po_number=po_number,
                vendor_id=vendor.vendor_id,
                total_amount=cost,
                grand_total=cost,
                status="Completed",
                created_at=created_date,
                updated_at=created_date
            )
            session.add(po)
            await session.flush()

            # Create PO Item
            po_item = PurchaseOrderItem(
                po_id=po.po_id,
                item_name=title,
                quantity=1,
                unit_price=cost,
                total_price=cost
            )
            session.add(po_item)
            await session.flush()

            # Create Delivery
            delivery = Delivery(
                po_id=po.po_id,
                vendor_id=vendor.vendor_id,
                delivery_number=f"DEL-{pr_num}",
                status="Delivered",
                delivery_date=created_date,
                created_at=created_date
            )
            session.add(delivery)
            await session.flush()

            # Create Delivery Item
            delivery_item = DeliveryItem(
                delivery_id=delivery.delivery_id,
                po_item_id=po_item.po_item_id,
                item_name=title,
                quantity_shipped=1
            )
            session.add(delivery_item)
            await session.flush()

            # Create Asset
            asset = Asset(
                asset_number=f"AST-{uuid.uuid4().hex[:8].upper()}",
                asset_tag=f"TAG-{pr_num}",
                category_id=category.category_id,
                po_id=po.po_id,
                vendor_id=vendor.vendor_id,
                status="Available",
                purchase_date=created_date.date(),
                created_at=created_date
            )
            session.add(asset)

        await session.commit()
        print("Successfully seeded fulfilled orders, deliveries, and assets.")

if __name__ == "__main__":
    asyncio.run(seed_orders())
