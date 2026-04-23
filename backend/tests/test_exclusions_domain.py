"""Unit tests for the exclusions domain (service over fake repo)."""

import pytest
from backend.domains.buy_planning.exclusions import (
    ExclusionsService, NotFoundError,
)


class FakeExclusionsRepo:
    def __init__(self):
        self._store: list = []
        self.last_upsert: dict = {}

    async def upsert(self, **kw):
        self.last_upsert = kw
        # De-dup on (tenant, store, sku)
        key = (kw["tenant_id"], kw["store_code"], kw["sku"])
        self._store = [s for s in self._store if (s["tenant_id"], s["store_code"], s["sku"]) != key]
        self._store.append(kw)

    async def delete(self, *, tenant_id, store_code, sku):
        before = len(self._store)
        self._store = [
            s for s in self._store
            if not (s["tenant_id"] == tenant_id and s["store_code"] == store_code and s["sku"] == sku)
        ]
        return before - len(self._store)

    async def list_all(self, tenant_id):
        return [s for s in self._store if s["tenant_id"] == tenant_id]


@pytest.mark.asyncio
async def test_add_then_list():
    svc = ExclusionsService(FakeExclusionsRepo())
    out = await svc.add(
        tenant_id="t1", store_code="S1", sku="SKU1",
        reason="bad seller", expires_at=None, user_email="u@x.com",
    )
    assert out == {"success": True, "store_code": "S1", "sku": "SKU1"}
    listed = await svc.list_all("t1")
    assert listed["total"] == 1
    assert listed["exclusions"][0]["sku"] == "SKU1"


@pytest.mark.asyncio
async def test_remove_raises_when_missing():
    svc = ExclusionsService(FakeExclusionsRepo())
    with pytest.raises(NotFoundError):
        await svc.remove(tenant_id="t1", store_code="S1", sku="GHOST")


@pytest.mark.asyncio
async def test_remove_after_add():
    svc = ExclusionsService(FakeExclusionsRepo())
    await svc.add(tenant_id="t1", store_code="S1", sku="SKU1",
                  reason=None, expires_at=None, user_email="u@x.com")
    out = await svc.remove(tenant_id="t1", store_code="S1", sku="SKU1")
    assert out["deleted"] is True
    listed = await svc.list_all("t1")
    assert listed["total"] == 0


@pytest.mark.asyncio
async def test_tenant_isolation():
    svc = ExclusionsService(FakeExclusionsRepo())
    await svc.add(tenant_id="t1", store_code="S1", sku="SKU1",
                  reason=None, expires_at=None, user_email="u@x.com")
    await svc.add(tenant_id="t2", store_code="S1", sku="SKU1",
                  reason=None, expires_at=None, user_email="u@x.com")
    t1_list = await svc.list_all("t1")
    assert t1_list["total"] == 1
