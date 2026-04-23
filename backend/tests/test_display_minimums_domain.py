"""Unit tests for the extracted display_minimums domain module."""

import pytest
from backend.domains.buy_planning.display_minimums import (
    DisplayMinimumsRepository,
    DisplayMinimumsService,
    NotFoundError,
)


class FakeCollection:
    """In-memory stand-in for a Motor collection — just enough for these tests."""

    def __init__(self):
        self.docs: list = []

    def find(self, filt, projection=None):
        results = [d for d in self.docs if all(d.get(k) == v for k, v in filt.items())]
        async def gen():
            for d in results:
                out = {k: v for k, v in d.items() if k != "_id"} if projection and projection.get("_id") == 0 else d
                yield out
        return gen()

    async def update_one(self, filt, update, upsert=False):
        for d in self.docs:
            if all(d.get(k) == v for k, v in filt.items()):
                d.update(update["$set"])
                return
        if upsert:
            self.docs.append({**filt, **update["$set"]})

    async def delete_one(self, filt):
        class Result: deleted_count = 0
        for i, d in enumerate(self.docs):
            if all(d.get(k) == v for k, v in filt.items()):
                self.docs.pop(i)
                Result.deleted_count = 1
                return Result()
        return Result()


class FakeDB:
    def __init__(self):
        self._collections: dict = {}

    def __getitem__(self, name):
        return self._collections.setdefault(name, FakeCollection())


@pytest.fixture
def svc():
    return DisplayMinimumsService(DisplayMinimumsRepository(FakeDB()))


@pytest.mark.asyncio
async def test_set_then_list(svc):
    out = await svc.set_config(
        category="Tops", store_wedge="A", min_facings=3, display_units_per_facing=2,
    )
    assert out == {
        "success": True, "category": "Tops", "store_wedge": "A",
        "total_display_min_units": 6,
    }
    listed = await svc.list_configs()
    assert listed["total"] == 1
    assert listed["configs"][0]["total_display_min_units"] == 6


@pytest.mark.asyncio
async def test_update_same_key_overwrites(svc):
    await svc.set_config(category="Tops", store_wedge="A", min_facings=3, display_units_per_facing=2)
    await svc.set_config(category="Tops", store_wedge="A", min_facings=5, display_units_per_facing=2)
    listed = await svc.list_configs()
    assert listed["total"] == 1
    assert listed["configs"][0]["total_display_min_units"] == 10


@pytest.mark.asyncio
async def test_delete_missing_raises(svc):
    with pytest.raises(NotFoundError):
        await svc.delete_config(category="X", store_wedge="A")


@pytest.mark.asyncio
async def test_delete_existing(svc):
    await svc.set_config(category="Tops", store_wedge="A", min_facings=3, display_units_per_facing=2)
    out = await svc.delete_config(category="Tops", store_wedge="A")
    assert out["success"] is True
    listed = await svc.list_configs()
    assert listed["total"] == 0


@pytest.mark.asyncio
async def test_invalid_wedge_rejected(svc):
    with pytest.raises(ValueError, match="invalid store_wedge"):
        await svc.set_config(category="Tops", store_wedge="Z", min_facings=1, display_units_per_facing=1)


@pytest.mark.asyncio
async def test_negative_values_rejected(svc):
    with pytest.raises(ValueError):
        await svc.set_config(category="Tops", store_wedge="A", min_facings=-1, display_units_per_facing=1)
