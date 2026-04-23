"""Unit tests for the audit_log domain (service orchestration over fake repo)."""

import pytest
from backend.domains.buy_planning.audit_log import AuditLogService


class FakeAuditRepo:
    def __init__(self):
        self.overrides = [
            {"entity_type": "store", "entity_id": "S1", "created_at": "2026-02-18T10:00:00"},
            {"entity_type": "style", "entity_id": "KUR-1", "created_at": "2026-02-17T09:00:00"},
        ]
        self.audit_entries = [
            {"tenant_id": "t1", "entity_type": "store", "source": "auto", "action": "classify"},
            {"tenant_id": "t1", "entity_type": "store", "source": "manual", "action": "override"},
            {"tenant_id": "t1", "entity_type": "style", "source": "auto", "action": "classify"},
        ]
        self.last_override_query = None
        self.last_audit_query = None

    async def list_overrides(self, entity_type, limit):
        self.last_override_query = (entity_type, limit)
        if entity_type:
            return [o for o in self.overrides if o["entity_type"] == entity_type][:limit]
        return self.overrides[:limit]

    async def list_audit_entries(self, *, tenant_id, entity_type, source, limit):
        self.last_audit_query = {"tenant_id": tenant_id, "entity_type": entity_type, "source": source, "limit": limit}
        rows = [e for e in self.audit_entries if e.get("tenant_id") == tenant_id]
        if entity_type:
            rows = [r for r in rows if r["entity_type"] == entity_type]
        if source:
            rows = [r for r in rows if r["source"] == source]
        return rows[:limit]


@pytest.mark.asyncio
async def test_get_override_history_default_limit():
    repo = FakeAuditRepo()
    svc = AuditLogService(repo)
    out = await svc.get_override_history()
    assert out["total"] == 2
    assert repo.last_override_query == (None, 50)


@pytest.mark.asyncio
async def test_get_override_history_filtered_by_entity_type():
    repo = FakeAuditRepo()
    svc = AuditLogService(repo)
    out = await svc.get_override_history(entity_type="store", limit=10)
    assert out["total"] == 1
    assert out["overrides"][0]["entity_id"] == "S1"


@pytest.mark.asyncio
async def test_get_audit_log_filters_by_source():
    repo = FakeAuditRepo()
    svc = AuditLogService(repo)
    out = await svc.get_audit_log(tenant_id="t1", source="manual")
    assert out["total"] == 1
    assert out["entries"][0]["action"] == "override"


@pytest.mark.asyncio
async def test_get_audit_log_respects_tenant_boundary():
    repo = FakeAuditRepo()
    repo.audit_entries.append({"tenant_id": "OTHER_TENANT", "entity_type": "store", "source": "auto"})
    svc = AuditLogService(repo)
    out = await svc.get_audit_log(tenant_id="t1")
    # 3 original t1 rows — cross-tenant leak would inflate count
    assert out["total"] == 3
