"""
Audit Log domain module.

Endpoints owned:
  GET /overrides/history   manual override history
  GET /audit-log           full buy-planning audit trail
"""

from typing import List, Optional


class AuditLogRepository:
    def __init__(self, db):
        self._db = db

    async def list_overrides(self, entity_type: Optional[str], limit: int) -> List[dict]:
        query: dict = {}
        if entity_type:
            query["entity_type"] = entity_type
        out: list = []
        async for doc in self._db.buy_planning_overrides.find(
            query, {"_id": 0},
        ).sort("created_at", -1).limit(limit):
            out.append(doc)
        return out

    async def list_audit_entries(self, *, tenant_id: str, entity_type: Optional[str],
                                  source: Optional[str], limit: int) -> List[dict]:
        query: dict = {"tenant_id": tenant_id}
        if entity_type:
            query["entity_type"] = entity_type
        if source:
            query["source"] = source
        out: list = []
        async for doc in self._db.buy_planning_audit_log.find(
            query, {"_id": 0},
        ).sort("created_at", -1).limit(limit):
            out.append(doc)
        return out


class AuditLogService:
    def __init__(self, repo: AuditLogRepository):
        self._repo = repo

    async def get_override_history(self, entity_type: Optional[str] = None,
                                    limit: int = 50) -> dict:
        overrides = await self._repo.list_overrides(entity_type, limit)
        return {"overrides": overrides, "total": len(overrides)}

    async def get_audit_log(self, *, tenant_id: str, entity_type: Optional[str] = None,
                             source: Optional[str] = None, limit: int = 100) -> dict:
        entries = await self._repo.list_audit_entries(
            tenant_id=tenant_id, entity_type=entity_type, source=source, limit=limit,
        )
        return {"entries": entries, "total": len(entries)}
