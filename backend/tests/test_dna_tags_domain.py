"""Unit tests for the dna_tags domain (pure classifiers + service)."""

import pytest
from backend.domains.buy_planning.dna_tags import (
    classify_flow_rank,
    classify_lifecycle,
    compute_expected_weeks,
    parse_sale_date_safely,
    DnaTagsService,
    NotFoundError,
)


# ═══════════════════════════════════════════════════════════════════
# 1. Pure classifiers.
# ═══════════════════════════════════════════════════════════════════

class TestClassifyFlowRank:
    def test_hero_top_80pct(self):
        assert classify_flow_rank(0.50) == 1
        assert classify_flow_rank(0.80) == 1

    def test_core_next_15pct(self):
        assert classify_flow_rank(0.85) == 2
        assert classify_flow_rank(0.95) == 2

    def test_fill_in_bottom_5pct(self):
        assert classify_flow_rank(0.96) == 3
        assert classify_flow_rank(1.00) == 3


class TestClassifyLifecycle:
    def test_launch_when_new(self):
        assert classify_lifecycle(age_weeks=2, recency_days=0) == "Launch"
        assert classify_lifecycle(age_weeks=4, recency_days=0) == "Launch"

    def test_peak_when_middle_age(self):
        assert classify_lifecycle(age_weeks=6, recency_days=3) == "Peak"
        assert classify_lifecycle(age_weeks=12, recency_days=5) == "Peak"

    def test_decline_when_gap_14_to_30_days(self):
        assert classify_lifecycle(age_weeks=8, recency_days=20) == "Decline"

    def test_exit_when_no_sale_30d_plus(self):
        assert classify_lifecycle(age_weeks=20, recency_days=45) == "Exit"

    def test_decline_when_old_but_selling(self):
        # >12 weeks old, recent sale → Decline (mature product)
        assert classify_lifecycle(age_weeks=20, recency_days=5) == "Decline"


class TestComputeExpectedWeeks:
    def test_exit_returns_zero(self):
        assert compute_expected_weeks(age_weeks=30, lifecycle="Exit") == 0

    def test_cap_at_52_weeks(self):
        assert compute_expected_weeks(age_weeks=1, lifecycle="Launch") == 51

    def test_minimum_4_weeks(self):
        assert compute_expected_weeks(age_weeks=60, lifecycle="Decline") == 4


class TestParseSaleDateSafely:
    def test_valid_string(self):
        dt = parse_sale_date_safely("2026-01-15")
        assert dt is not None
        assert dt.year == 2026

    def test_none(self):
        assert parse_sale_date_safely(None) is None
        assert parse_sale_date_safely("") is None

    def test_invalid_format(self):
        assert parse_sale_date_safely("not-a-date") is None


# ═══════════════════════════════════════════════════════════════════
# 2. Service layer.
# ═══════════════════════════════════════════════════════════════════

class FakeDnaRepo:
    def __init__(self):
        self.tagged_skus: list = []
        self.tagged_styles: list = []
        self.style_sales: list = []
        self.tag_list: list = []
        self.tag_sku_should_miss = False

    async def tag_sku(self, sku, update):
        if self.tag_sku_should_miss:
            return 0
        self.tagged_skus.append((sku, update))
        return 1

    async def tag_style(self, style, update):
        self.tagged_styles.append((style, update))
        return 3  # pretend 3 SKUs matched

    async def aggregate_style_sales(self, tenant_id):
        return list(self.style_sales)

    async def list_dna_tags(self, tenant_id):
        return list(self.tag_list)


@pytest.fixture
def svc():
    return DnaTagsService(FakeDnaRepo()), None


@pytest.mark.asyncio
async def test_tag_sku_success(svc):
    service, _ = svc
    out = await service.tag_sku(sku="SKU1", flow_rank=1, lifecycle_stage="Peak")
    assert out == {"success": True, "sku": "SKU1"}


@pytest.mark.asyncio
async def test_tag_sku_not_found():
    repo = FakeDnaRepo()
    repo.tag_sku_should_miss = True
    service = DnaTagsService(repo)
    with pytest.raises(NotFoundError):
        await service.tag_sku(sku="GHOST", flow_rank=1)


@pytest.mark.asyncio
async def test_tag_style_bulk_returns_count(svc):
    service, _ = svc
    out = await service.tag_style_bulk(style="STYLE1", flow_rank=2)
    assert out == {"success": True, "style": "STYLE1", "skus_updated": 3}


@pytest.mark.asyncio
async def test_auto_tag_no_sales_short_circuits(svc):
    service, _ = svc
    out = await service.auto_tag("t1")
    assert out["tagged"] == 0
    assert "No sales data" in out["message"]


@pytest.mark.asyncio
async def test_auto_tag_classifies_hero_vs_fill_in():
    repo = FakeDnaRepo()
    repo.style_sales = [
        {"_id": "HERO", "first_sale": "2025-10-01", "last_sale": "2026-02-15",
         "total_revenue": 800},
        {"_id": "CORE", "first_sale": "2025-12-01", "last_sale": "2026-02-10",
         "total_revenue": 150},
        {"_id": "FILL", "first_sale": "2026-01-15", "last_sale": "2026-02-01",
         "total_revenue": 50},
    ]
    svc = DnaTagsService(repo)
    out = await svc.auto_tag("t1")
    assert out["success"] is True
    assert out["styles_processed"] == 3
    # Expect 3 tag_style calls, each with its flow_rank
    ranks = [update["flow_rank"] for (_, update) in repo.tagged_styles]
    assert 1 in ranks and 2 in ranks and 3 in ranks


@pytest.mark.asyncio
async def test_list_tags_wraps_repo(svc):
    service, _ = svc
    service._repo.tag_list = [{"style": "X", "flow_rank": 1}]
    out = await service.list_tags("t1")
    assert out["total"] == 1
    assert out["styles"][0]["style"] == "X"
