"""
Inventory domain module.

Endpoints owned:
  POST /inventory/bulk          bulk upsert inventory records (up to 100k)
  GET  /inventory               list (filter by store_code / sku)
  GET  /inventory/summary       rollup (total_soh, unique_stores, etc.)
  GET  /inventory/sync-status   last sync info
"""

from datetime import datetime, timezone
from typing import List, Optional


MAX_BULK_RECORDS = 100000


class ValidationError(Exception):
    """Raised on empty payload or oversize bulk upload."""


# ═════════════════════════════════════════════════════════════════
# Repository — pure Mongo.
# ═════════════════════════════════════════════════════════════════

class InventoryRepository:
    def __init__(self, db):
        self._db = db

    async def upsert_record(self, *, tenant_id: str, store_code: str, sku: str,
                             date: str, soh: int, in_transit: int, open_po_qty: int,
                             source: str, user_email: str, now_iso: str):
        return await self._db.store_inventory.update_one(
            {"tenant_id": tenant_id, "store_code": store_code, "sku": sku, "date": date},
            {"$set": {
                "tenant_id": tenant_id, "store_code": store_code, "sku": sku, "date": date,
                "soh": soh, "in_transit": in_transit, "open_po_qty": open_po_qty,
                "source": source, "updated_at": now_iso, "uploaded_by": user_email,
            }},
            upsert=True,
        )

    async def insert_sync_log(self, entry: dict):
        await self._db.inventory_sync_log.insert_one(entry)

    async def list_records(self, *, tenant_id: str, store_code: Optional[str],
                           sku: Optional[str], limit: int) -> List[dict]:
        query: dict = {"tenant_id": tenant_id}
        if store_code:
            query["store_code"] = store_code
        if sku:
            query["sku"] = sku
        out: list = []
        async for doc in self._db.store_inventory.find(query, {"_id": 0}).sort("date", -1).limit(limit):
            out.append(doc)
        return out

    async def count(self, tenant_id: str) -> int:
        return await self._db.store_inventory.count_documents({"tenant_id": tenant_id})

    async def summary_aggregation(self, tenant_id: str) -> Optional[dict]:
        pipeline = [
            {"$match": {"tenant_id": tenant_id}},
            {"$group": {
                "_id": None,
                "total_soh": {"$sum": "$soh"},
                "total_in_transit": {"$sum": "$in_transit"},
                "total_open_po": {"$sum": "$open_po_qty"},
                "unique_stores": {"$addToSet": "$store_code"},
                "unique_skus": {"$addToSet": "$sku"},
            }},
        ]
        result = await self._db.store_inventory.aggregate(pipeline).to_list(1)
        return result[0] if result else None

    async def last_sync(self, tenant_id: str) -> Optional[dict]:
        return await self._db.inventory_sync_log.find_one(
            {"tenant_id": tenant_id}, {"_id": 0}, sort=[("synced_at", -1)],
        )


# ═════════════════════════════════════════════════════════════════
# Service — orchestration.
# ═════════════════════════════════════════════════════════════════

class InventoryService:
    def __init__(self, repo: InventoryRepository):
        self._repo = repo

    async def bulk_upload(self, *, tenant_id: str, records: list, source: str,
                           user_email: str) -> dict:
        if not records:
            raise ValidationError("No records provided")
        if len(records) > MAX_BULK_RECORDS:
            raise ValidationError(f"Maximum {MAX_BULK_RECORDS:,} records per request")

        inserted = 0
        updated = 0
        failed = 0
        errors: list = []
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        for rec in records:
            now_iso = datetime.now(timezone.utc).isoformat()
            try:
                result = await self._repo.upsert_record(
                    tenant_id=tenant_id,
                    store_code=rec.get("store_code", rec.get("store_id", "")),
                    sku=rec.get("sku", rec.get("sku_id", "")),
                    date=rec.get("date", today),
                    soh=rec.get("soh", 0),
                    in_transit=rec.get("in_transit", 0),
                    open_po_qty=rec.get("open_po_qty", 0),
                    source=source, user_email=user_email, now_iso=now_iso,
                )
                if result.upserted_id:
                    inserted += 1
                elif result.modified_count > 0:
                    updated += 1
            except Exception as e:
                failed += 1
                if len(errors) < 10:
                    errors.append(f"{rec}: {str(e)}")

        await self._repo.insert_sync_log({
            "tenant_id": tenant_id,
            "synced_at": datetime.now(timezone.utc).isoformat(),
            "synced_by": user_email, "source": source,
            "total": len(records), "inserted": inserted,
            "updated": updated, "failed": failed,
        })
        return {
            "success": failed == 0, "total": len(records),
            "inserted": inserted, "updated": updated, "failed": failed, "errors": errors,
        }

    async def list_records(self, *, tenant_id: str, store_code: Optional[str] = None,
                            sku: Optional[str] = None, limit: int = 200) -> dict:
        records = await self._repo.list_records(
            tenant_id=tenant_id, store_code=store_code, sku=sku, limit=limit,
        )
        return {"records": records, "total": len(records)}

    async def summary(self, tenant_id: str) -> dict:
        total = await self._repo.count(tenant_id)
        agg = await self._repo.summary_aggregation(tenant_id)
        if agg:
            return {
                "total_records": total,
                "total_soh": agg.get("total_soh", 0),
                "total_in_transit": agg.get("total_in_transit", 0),
                "total_open_po": agg.get("total_open_po", 0),
                "unique_stores": len(agg.get("unique_stores", [])),
                "unique_skus": len(agg.get("unique_skus", [])),
            }
        return {
            "total_records": 0, "total_soh": 0, "total_in_transit": 0,
            "total_open_po": 0, "unique_stores": 0, "unique_skus": 0,
        }

    async def sync_status(self, tenant_id: str) -> dict:
        last = await self._repo.last_sync(tenant_id)
        return {"last_sync": last}
