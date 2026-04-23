"""Unit tests for the promotions domain (service + validation)."""

import pytest
from backend.domains.buy_planning.promotions import (
    PromotionsService, NotFoundError, ValidationError,
)


class FakePromoRepo:
    def __init__(self):
        self._db: list = []
        self.last_today: str = ""

    async def insert(self, doc):
        self._db.append(doc)

    async def list_all(self, tenant_id, status):
        rows = [p for p in self._db if p["tenant_id"] == tenant_id]
        if status:
            rows = [r for r in rows if r.get("status") == status]
        return rows

    async def update(self, *, tenant_id, promo_id, payload, user_email, now_iso):
        for p in self._db:
            if p["tenant_id"] == tenant_id and p["promo_id"] == promo_id:
                p.update(payload)
                p["updated_by"] = user_email
                p["updated_at"] = now_iso
                return 1
        return 0

    async def delete(self, *, tenant_id, promo_id):
        before = len(self._db)
        self._db = [p for p in self._db if not (p["tenant_id"] == tenant_id and p["promo_id"] == promo_id)]
        return before - len(self._db)

    async def list_active_on(self, tenant_id, today_iso):
        self.last_today = today_iso
        return [
            p for p in self._db
            if p["tenant_id"] == tenant_id
            and p.get("status") == "active"
            and p.get("start_date", "") <= today_iso <= p.get("end_date", "")
        ]


@pytest.mark.asyncio
async def test_create_valid_promo():
    svc = PromotionsService(FakePromoRepo())
    out = await svc.create(
        tenant_id="t1",
        payload={"name": "BOGO", "lift_factor": 2.0, "start_date": "2026-02-01", "end_date": "2026-02-28"},
        user_email="u@x.com",
    )
    assert out["success"] is True
    assert out["promo_id"].startswith("PROMO-")


@pytest.mark.asyncio
async def test_create_rejects_low_lift():
    svc = PromotionsService(FakePromoRepo())
    with pytest.raises(ValidationError):
        await svc.create(tenant_id="t1", payload={"lift_factor": 0.3}, user_email="u@x.com")


@pytest.mark.asyncio
async def test_create_rejects_high_lift():
    svc = PromotionsService(FakePromoRepo())
    with pytest.raises(ValidationError):
        await svc.create(tenant_id="t1", payload={"lift_factor": 6.0}, user_email="u@x.com")


@pytest.mark.asyncio
async def test_update_not_found():
    svc = PromotionsService(FakePromoRepo())
    with pytest.raises(NotFoundError):
        await svc.update(tenant_id="t1", promo_id="GHOST", payload={"lift_factor": 2.0}, user_email="u@x.com")


@pytest.mark.asyncio
async def test_update_happy_path():
    repo = FakePromoRepo()
    svc = PromotionsService(repo)
    await svc.create(tenant_id="t1", payload={"name": "X", "lift_factor": 1.5}, user_email="u@x.com")
    pid = repo._db[0]["promo_id"]
    out = await svc.update(tenant_id="t1", promo_id=pid, payload={"name": "X2", "lift_factor": 2.0}, user_email="u@x.com")
    assert out["success"] is True
    assert repo._db[0]["name"] == "X2"


@pytest.mark.asyncio
async def test_delete_not_found():
    svc = PromotionsService(FakePromoRepo())
    with pytest.raises(NotFoundError):
        await svc.delete(tenant_id="t1", promo_id="GHOST")


@pytest.mark.asyncio
async def test_list_filters_by_status():
    repo = FakePromoRepo()
    svc = PromotionsService(repo)
    await svc.create(tenant_id="t1", payload={"name": "A", "lift_factor": 1.5}, user_email="u@x.com")
    # Create and then "archive" it by direct mutation to simulate another status
    repo._db.append({"tenant_id": "t1", "promo_id": "OLD", "status": "archived", "name": "OLD"})
    active = await svc.list_all("t1", status="active")
    archived = await svc.list_all("t1", status="archived")
    assert active["total"] == 1
    assert archived["total"] == 1


@pytest.mark.asyncio
async def test_get_active_lifts_uses_today():
    repo = FakePromoRepo()
    svc = PromotionsService(repo)
    out = await svc.get_active_lifts("t1")
    # Today's iso date was passed to repo
    assert len(repo.last_today) == 10  # YYYY-MM-DD
    assert out["total"] == 0
