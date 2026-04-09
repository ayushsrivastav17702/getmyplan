"""
Seed 210 days of realistic historical data for AI Demand Planning.
Generates daily_sales, store_inventory, warehouse_inventory, sku_ean_master,
style_master, store_master, and warehouse_master — all seeded into V1
uploaded_files collection for immediate use by AI demand module.
"""
import asyncio
import random
import math
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os

random.seed(42)

# ── Configuration ────────────────────────────────────────────────
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = "test_database"

START_DATE = datetime(2024, 4, 1)
END_DATE = datetime(2026, 4, 28)  # ~25 months
NUM_DAYS = (END_DATE - START_DATE).days  # ~758

SKUS = [
    {"ean": "TSHIRT-BLK-M",     "style": "TSHIRT-BLK",    "size": "M",   "mrp": 999},
    {"ean": "TSHIRT-BLK-L",     "style": "TSHIRT-BLK",    "size": "L",   "mrp": 999},
    {"ean": "HOODIE-GRY-M",     "style": "HOODIE-GRY",    "size": "M",   "mrp": 2499},
    {"ean": "HOODIE-GRY-L",     "style": "HOODIE-GRY",    "size": "L",   "mrp": 2499},
    {"ean": "CAP-BLK-ONE",      "style": "CAP-BLK",       "size": "ONE", "mrp": 599},
    {"ean": "SOCKS-WHT-3PK",    "style": "SOCKS-WHT",     "size": "3PK", "mrp": 399},
    {"ean": "JOGGER-BLK-M",     "style": "JOGGER-BLK",    "size": "M",   "mrp": 1999},
    {"ean": "SNEAKER-WHT-9",    "style": "SNEAKER-WHT",   "size": "9",   "mrp": 4999},
    {"ean": "BACKPACK-BLK",     "style": "BACKPACK",       "size": "ONE", "mrp": 2999},
    {"ean": "WATER-BOTTLE-500", "style": "WATER-BOTTLE",   "size": "500", "mrp": 799},
]

STYLES = [
    {"style_code": "TSHIRT-BLK",   "season": "SS25", "category": "Tops",        "subcategory": "T-Shirts", "gender": "Unisex", "brand": "GetMyPlan Originals", "segment": "Casual", "fashion_grade": "A", "family": "Upper Wear", "description": "Classic Black T-Shirt", "master_category": "Apparel", "image_url": "", "vendor": "VendorA", "attribute1": "", "attribute2": "", "attribute3": "", "attribute4": "", "attribute5": "", "attribute6": "", "attribute7": "", "attribute8": "", "attribute9": ""},
    {"style_code": "HOODIE-GRY",   "season": "AW25", "category": "Tops",        "subcategory": "Hoodies",  "gender": "Unisex", "brand": "GetMyPlan Originals", "segment": "Casual", "fashion_grade": "A", "family": "Upper Wear", "description": "Grey Hoodie",          "master_category": "Apparel", "image_url": "", "vendor": "VendorA", "attribute1": "", "attribute2": "", "attribute3": "", "attribute4": "", "attribute5": "", "attribute6": "", "attribute7": "", "attribute8": "", "attribute9": ""},
    {"style_code": "CAP-BLK",      "season": "SS25", "category": "Accessories",  "subcategory": "Caps",     "gender": "Unisex", "brand": "GetMyPlan Originals", "segment": "Casual", "fashion_grade": "B", "family": "Head Wear", "description": "Black Cap",             "master_category": "Accessories", "image_url": "", "vendor": "VendorB", "attribute1": "", "attribute2": "", "attribute3": "", "attribute4": "", "attribute5": "", "attribute6": "", "attribute7": "", "attribute8": "", "attribute9": ""},
    {"style_code": "SOCKS-WHT",    "season": "SS25", "category": "Accessories",  "subcategory": "Socks",    "gender": "Unisex", "brand": "GetMyPlan Originals", "segment": "Essentials", "fashion_grade": "C", "family": "Foot Wear", "description": "White Socks 3-Pack",   "master_category": "Accessories", "image_url": "", "vendor": "VendorC", "attribute1": "", "attribute2": "", "attribute3": "", "attribute4": "", "attribute5": "", "attribute6": "", "attribute7": "", "attribute8": "", "attribute9": ""},
    {"style_code": "JOGGER-BLK",   "season": "AW25", "category": "Bottoms",     "subcategory": "Joggers",  "gender": "Unisex", "brand": "GetMyPlan Originals", "segment": "Athleisure", "fashion_grade": "A", "family": "Lower Wear", "description": "Black Jogger Pants",   "master_category": "Apparel", "image_url": "", "vendor": "VendorA", "attribute1": "", "attribute2": "", "attribute3": "", "attribute4": "", "attribute5": "", "attribute6": "", "attribute7": "", "attribute8": "", "attribute9": ""},
    {"style_code": "SNEAKER-WHT",  "season": "SS25", "category": "Footwear",    "subcategory": "Sneakers", "gender": "Unisex", "brand": "GetMyPlan Originals", "segment": "Sport", "fashion_grade": "A", "family": "Foot Wear", "description": "White Sneaker",         "master_category": "Footwear", "image_url": "", "vendor": "VendorD", "attribute1": "", "attribute2": "", "attribute3": "", "attribute4": "", "attribute5": "", "attribute6": "", "attribute7": "", "attribute8": "", "attribute9": ""},
    {"style_code": "BACKPACK",     "season": "SS25", "category": "Accessories",  "subcategory": "Bags",     "gender": "Unisex", "brand": "GetMyPlan Originals", "segment": "Travel", "fashion_grade": "B", "family": "Carry", "description": "Black Backpack",        "master_category": "Accessories", "image_url": "", "vendor": "VendorE", "attribute1": "", "attribute2": "", "attribute3": "", "attribute4": "", "attribute5": "", "attribute6": "", "attribute7": "", "attribute8": "", "attribute9": ""},
    {"style_code": "WATER-BOTTLE", "season": "SS25", "category": "Accessories",  "subcategory": "Bottles",  "gender": "Unisex", "brand": "GetMyPlan Originals", "segment": "Lifestyle", "fashion_grade": "C", "family": "Drinkware", "description": "Water Bottle 500ml",   "master_category": "Accessories", "image_url": "", "vendor": "VendorE", "attribute1": "", "attribute2": "", "attribute3": "", "attribute4": "", "attribute5": "", "attribute6": "", "attribute7": "", "attribute8": "", "attribute9": ""},
]

STORES = [
    {"channel": "Retail",  "store": "Main Store",   "store_code": "MAIN-01",   "city": "Mumbai",    "region": "West",  "etl_new": "No", "area": "500sqft", "class": "A", "cluster": "Metro", "is_online": "No", "open_date": "2020-01-01"},
    {"channel": "Retail",  "store": "South Store",  "store_code": "SOUTH-02",  "city": "Chennai",   "region": "South", "etl_new": "No", "area": "350sqft", "class": "B", "cluster": "Metro", "is_online": "No", "open_date": "2021-06-15"},
    {"channel": "Retail",  "store": "West Store",   "store_code": "WEST-03",   "city": "Pune",      "region": "West",  "etl_new": "No", "area": "300sqft", "class": "B", "cluster": "Tier1", "is_online": "No", "open_date": "2022-03-01"},
    {"channel": "Online",  "store": "Online Store",  "store_code": "ONLINE-01", "city": "Bangalore", "region": "South", "etl_new": "No", "area": "N/A",     "class": "A", "cluster": "Online", "is_online": "Yes", "open_date": "2019-01-01"},
    {"channel": "Retail",  "store": "Popup Store",   "store_code": "POPUP-01",  "city": "Delhi",     "region": "North", "etl_new": "Yes", "area": "150sqft", "class": "C", "cluster": "Tier1", "is_online": "No", "open_date": "2025-09-01"},
]

WAREHOUSES = [
    {"warehouse": "WH-CENTRAL", "online_fulfillment_flag": "Yes", "outwards": "Yes", "inwards": "Yes", "iwht_group": "Central"},
    {"warehouse": "WH-SOUTH",   "online_fulfillment_flag": "No",  "outwards": "Yes", "inwards": "Yes", "iwht_group": "Regional"},
]

# Base daily demand per SKU (units per store per day)
BASE_DEMAND = {
    "TSHIRT-BLK-M": 8, "TSHIRT-BLK-L": 6, "HOODIE-GRY-M": 4, "HOODIE-GRY-L": 3,
    "CAP-BLK-ONE": 5, "SOCKS-WHT-3PK": 12, "JOGGER-BLK-M": 3, "SNEAKER-WHT-9": 2,
    "BACKPACK-BLK": 2, "WATER-BOTTLE-500": 7,
}

# Store multipliers (ONLINE sells 2x, POPUP sells 0.5x)
STORE_MULT = {"MAIN-01": 1.0, "SOUTH-02": 0.8, "WEST-03": 0.7, "ONLINE-01": 2.0, "POPUP-01": 0.4}

# Channel mapping for sales
STORE_CHANNEL = {"MAIN-01": "offline", "SOUTH-02": "offline", "WEST-03": "offline", "ONLINE-01": "online", "POPUP-01": "offline"}


def generate_daily_sales():
    """Generate 210 days of daily sales with realistic patterns."""
    rows = []
    for day_offset in range(NUM_DAYS):
        dt = START_DATE + timedelta(days=day_offset)
        day_str = dt.strftime("%Y-%m-%d")
        dow = dt.weekday()  # 0=Mon, 6=Sun

        # Weekend multiplier: Sat=1.4, Sun=1.5, Fri=1.2
        weekend_mult = {4: 1.2, 5: 1.4, 6: 1.5}.get(dow, 1.0)

        # Monthly growth: 5% per month from start
        months_elapsed = day_offset / 30.0
        growth_mult = 1.0 + 0.05 * months_elapsed

        # Light seasonality: Oct-Dec (festive) higher, Jan-Feb dip
        month = dt.month
        season_mult = {10: 1.25, 11: 1.35, 12: 1.45, 1: 0.75, 2: 0.80, 3: 0.95, 4: 1.05}.get(month, 1.0)

        for sku_info in SKUS:
            ean = sku_info["ean"]
            mrp = sku_info["mrp"]
            base = BASE_DEMAND[ean]

            for store_info in STORES:
                store_code = store_info["store_code"]
                store_mult = STORE_MULT[store_code]
                channel = STORE_CHANNEL[store_code]

                # ~80% chance of sale on any given day (some zero-sale days)
                if random.random() < 0.18:
                    continue

                # Calculate quantity
                raw_qty = base * store_mult * weekend_mult * growth_mult * season_mult
                noise = random.uniform(0.80, 1.20)  # ±20%
                qty = max(1, round(raw_qty * noise))

                # Revenue: qty * MRP with slight discount variation (5-15%)
                discount_pct = random.uniform(0.05, 0.15)
                discount_val = round(mrp * qty * discount_pct, 2)
                revenue = round(mrp * qty - discount_val, 2)

                rows.append({
                    "channel": channel,
                    "store_code": store_code,
                    "sku": ean,
                    "day": day_str,
                    "online": 1 if channel == "online" else 0,
                    "quantity": qty,
                    "discount_value": discount_val,
                    "revenue": revenue,
                })
    return rows


def generate_store_inventory(sales_data):
    """Generate store inventory based on cumulative sales.
    Start with initial stock, replenish periodically, deplete via sales."""
    # Build daily sales per (sku, store)
    daily_map = {}
    for r in sales_data:
        key = (r["sku"], r["store_code"], r["day"])
        daily_map[key] = daily_map.get(key, 0) + r["quantity"]

    rows = []
    for sku_info in SKUS:
        ean = sku_info["ean"]
        for store_info in STORES:
            sc = store_info["store_code"]
            ch = store_info["channel"]
            # Initial stock: 30-50 days of supply
            base = BASE_DEMAND[ean] * STORE_MULT[sc]
            stock = round(base * random.uniform(30, 50))

            for day_offset in range(NUM_DAYS):
                dt = START_DATE + timedelta(days=day_offset)
                day_str = dt.strftime("%Y-%m-%d")

                # Deplete by today's sales
                sold = daily_map.get((ean, sc, day_str), 0)
                stock = max(0, stock - sold)

                # Replenish every 14 days (simulating restock cycle)
                if day_offset > 0 and day_offset % 14 == 0:
                    replenish = round(base * random.uniform(15, 25))
                    stock += replenish

                rows.append({
                    "channel": ch,
                    "store_code": sc,
                    "ean": ean,
                    "day": day_str,
                    "quantity": stock,
                })
    return rows


def generate_warehouse_inventory(sales_data):
    """Generate warehouse inventory snapshots (one per day per SKU per warehouse)."""
    # Total daily demand across all stores per SKU
    daily_demand = {}
    for r in sales_data:
        key = (r["sku"], r["day"])
        daily_demand[key] = daily_demand.get(key, 0) + r["quantity"]

    rows = []
    for sku_info in SKUS:
        ean = sku_info["ean"]
        total_base = sum(BASE_DEMAND[ean] * STORE_MULT[s["store_code"]] for s in STORES)

        for wh in WAREHOUSES:
            wh_code = wh["warehouse"]
            # Central warehouse holds more
            mult = 1.0 if wh_code == "WH-CENTRAL" else 0.4
            stock = round(total_base * mult * random.uniform(60, 90))

            for day_offset in range(NUM_DAYS):
                dt = START_DATE + timedelta(days=day_offset)
                day_str = dt.strftime("%Y-%m-%d")

                # Deplete by proportion of daily demand
                sold = daily_demand.get((ean, day_str), 0)
                stock = max(0, stock - round(sold * mult * 0.5))

                # Large replenishment every 30 days
                if day_offset > 0 and day_offset % 30 == 0:
                    stock += round(total_base * mult * random.uniform(40, 60))

                rows.append({
                    "sku": ean,
                    "warehouse": wh_code,
                    "quantity": stock,
                    "day": day_str,
                })
    return rows


async def seed():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    print("Generating daily sales...")
    sales = generate_daily_sales()
    print(f"  Generated {len(sales)} daily sales rows")

    print("Generating store inventory...")
    store_inv = generate_store_inventory(sales)
    print(f"  Generated {len(store_inv)} store inventory rows")

    print("Generating warehouse inventory...")
    wh_inv = generate_warehouse_inventory(sales)
    print(f"  Generated {len(wh_inv)} warehouse inventory rows")

    # Date range info
    days = sorted(set(r["day"] for r in sales))
    print(f"  Date range: {days[0]} to {days[-1]} ({len(days)} unique days)")

    # Replace V1 uploaded_files
    print("\nSeeding V1 uploaded_files...")

    async def upsert(file_type, data, columns):
        await db.uploaded_files.update_one(
            {"file_type": file_type},
            {"$set": {
                "file_type": file_type,
                "data": data,
                "columns": columns,
                "rows": len(data),
                "uploaded_at": datetime.utcnow().isoformat(),
                "validation": {"status": "valid", "errors": 0},
            }},
            upsert=True,
        )
        print(f"  {file_type}: {len(data)} rows")

    await upsert("daily_sales", sales, list(sales[0].keys()))
    await upsert("store_inventory", store_inv, list(store_inv[0].keys()))
    await upsert("warehouse_inventory", wh_inv, list(wh_inv[0].keys()))
    await upsert("sku_ean_master", SKUS, list(SKUS[0].keys()))
    await upsert("style_master", STYLES, list(STYLES[0].keys()))
    await upsert("store_master", STORES, list(STORES[0].keys()))
    await upsert("warehouse_master", WAREHOUSES, list(WAREHOUSES[0].keys()))

    # Verify
    print("\nVerification:")
    count = await db.uploaded_files.count_documents({})
    print(f"  Total uploaded_files docs: {count}")
    for ft in ["daily_sales", "store_inventory", "warehouse_inventory", "sku_ean_master", "style_master", "store_master", "warehouse_master"]:
        doc = await db.uploaded_files.find_one({"file_type": ft}, {"rows": 1, "_id": 0})
        print(f"  {ft}: {doc.get('rows', 0) if doc else 0} rows")

    client.close()
    print("\nDone! 210 days of data seeded successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
