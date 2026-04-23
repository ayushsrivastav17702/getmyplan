"""Unit tests for the style_mix domain (pure classifier + service orchestration)."""

import pytest
from backend.domains.buy_planning.style_mix import (
    classify_style,
    compute_style_stats,
    StyleMixService,
    StyleMixRepository,
    ValidationError,
    NotFoundError,
)


# ═══════════════════════════════════════════════════════════════════
# 1. Pure classifier — no I/O, no mocks, no async.
# ═══════════════════════════════════════════════════════════════════

class TestClassifyStyle:
    def test_core_when_high_volume_and_always_present(self):
        assert classify_style(avg_weekly_qty=6, weeks_active=30,
                              peak_to_avg_ratio=1.5, week_presence_pct=0.90) == "Core"

    def test_not_core_when_presence_below_80pct(self):
        # Even with avg=6/wk, sporadic presence disqualifies Core
        assert classify_style(avg_weekly_qty=6, weeks_active=10,
                              peak_to_avg_ratio=1.5, week_presence_pct=0.70) != "Core"

    def test_fashion_when_peaky_and_short_lived(self):
        assert classify_style(avg_weekly_qty=3, weeks_active=20,
                              peak_to_avg_ratio=4.0, week_presence_pct=0.60) == "Fashion"

    def test_test_when_too_new(self):
        # < 8 weeks active → Test regardless of peakiness
        assert classify_style(avg_weekly_qty=10, weeks_active=5,
                              peak_to_avg_ratio=2.0, week_presence_pct=0.70) == "Test"

    def test_test_when_very_low_avg(self):
        assert classify_style(avg_weekly_qty=1.5, weeks_active=20,
                              peak_to_avg_ratio=1.5, week_presence_pct=0.60) == "Test"

    def test_default_fashion_for_middle_ground(self):
        # avg=3 (not Core), not peaky (not Fashion rule), active=15 (not Test) → fallback Fashion
        assert classify_style(avg_weekly_qty=3, weeks_active=15,
                              peak_to_avg_ratio=1.5, week_presence_pct=0.60) == "Fashion"


class TestComputeStyleStats:
    def test_empty_weeks_safe(self):
        stats = compute_style_stats([], total_weeks_in_dataset=10)
        assert stats["weeks_active"] == 0
        assert stats["total_qty"] == 0
        assert stats["avg_weekly_qty"] == 0

    def test_basic_math(self):
        stats = compute_style_stats([10, 20, 30], total_weeks_in_dataset=10)
        assert stats["weeks_active"] == 3
        assert stats["total_qty"] == 60
        assert stats["avg_weekly_qty"] == 20.0
        assert stats["peak_to_avg_ratio"] == 1.5  # 30/20
        assert stats["week_presence_pct"] == 30.0  # 3/10

    def test_peak_heavy(self):
        # one 100-week, rest zeros → massive peak_to_avg
        stats = compute_style_stats([100, 5, 5, 5], total_weeks_in_dataset=10)
        assert stats["peak_to_avg_ratio"] > 3


# ═══════════════════════════════════════════════════════════════════
# 2. Service layer orchestration — with fake repo.
# ═══════════════════════════════════════════════════════════════════

class FakeStyleMixRepo:
    def __init__(self):
        self.existing = {}       # style → style_mix
        self.overrides_recorded = []
        self.reverts = []
        self.applied = []
        self.audit_inserts = []

    async def find_one_style(self, style):
        return {"style_mix": self.existing[style]} if style in self.existing else None

    async def apply_manual_override(self, style, mix, user_email, now_iso):
        self.existing[style] = mix
        self.applied.append((style, mix, user_email))

    async def record_override(self, **kw):
        self.overrides_recorded.append(kw)

    async def revert_override(self, style, user_email, now_iso):
        self.reverts.append((style, user_email))


@pytest.fixture
def svc():
    repo = FakeStyleMixRepo()
    repo.existing["KURTA-001"] = "Fashion"
    return StyleMixService(repo), repo


@pytest.mark.asyncio
async def test_override_valid(svc):
    service, repo = svc
    out = await service.override(
        style="KURTA-001", mix="Core", reason="Bestseller",
        user_email="u@x.com", tenant_id="t1",
    )
    assert out == {"success": True, "style": "KURTA-001", "old": "Fashion", "new": "Core"}
    assert repo.existing["KURTA-001"] == "Core"
    assert len(repo.overrides_recorded) == 1
    assert repo.overrides_recorded[0]["old"] == "Fashion"
    assert repo.overrides_recorded[0]["new"] == "Core"


@pytest.mark.asyncio
async def test_override_invalid_mix(svc):
    service, _ = svc
    with pytest.raises(ValidationError):
        await service.override(
            style="KURTA-001", mix="Premium", reason=None,
            user_email="u@x.com", tenant_id="t1",
        )


@pytest.mark.asyncio
async def test_override_nonexistent_style(svc):
    service, _ = svc
    with pytest.raises(NotFoundError):
        await service.override(
            style="DOES-NOT-EXIST", mix="Core", reason=None,
            user_email="u@x.com", tenant_id="t1",
        )


@pytest.mark.asyncio
async def test_revert_override(svc):
    service, repo = svc
    out = await service.revert_override("KURTA-001", "u@x.com")
    assert out["success"] is True
    assert repo.reverts == [("KURTA-001", "u@x.com")]
