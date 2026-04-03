"""
Onboarding Models — Marketplace, Store, Category Taxonomy, and Onboarding Status.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime, timezone
from enum import Enum


class Currency(str, Enum):
    INR = "INR"
    USD = "USD"
    GBP = "GBP"
    EUR = "EUR"
    AED = "AED"
    SGD = "SGD"
    CAD = "CAD"


class MarketplaceType(str, Enum):
    MARKETPLACE = "marketplace"
    WEBSITE = "website"
    SOCIAL_COMMERCE = "social_commerce"


class StoreType(str, Enum):
    PHYSICAL = "physical"
    WAREHOUSE = "warehouse"
    DARK_STORE = "dark_store"


class Marketplace(BaseModel):
    marketplace_id: Optional[str] = Field(None, max_length=50)
    name: str = Field(..., max_length=100, min_length=2)
    type: MarketplaceType = MarketplaceType.MARKETPLACE
    currency: Currency = Currency.INR
    tax_rate: float = Field(18.0, ge=0, le=100)
    commission_percentage: float = Field(0.0, ge=0, le=50)
    settlement_period_days: int = Field(7, ge=1, le=90)
    shipping_provider: Optional[str] = None
    api_config: Optional[Dict] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @validator('marketplace_id', pre=True, always=True)
    def generate_marketplace_id(cls, v, values):
        if not v and 'name' in values:
            return values['name'].lower().replace(' ', '_').replace('-', '_')
        return v


class StoreMapping(BaseModel):
    store_code: str = Field(..., max_length=50, min_length=1)
    store_name: str = Field(..., max_length=200, min_length=1)
    type: StoreType = StoreType.PHYSICAL
    address: Optional[str] = None
    city: str = Field(..., max_length=100)
    state: str = Field(..., max_length=100)
    pincode: str = Field(..., max_length=10, min_length=3)
    marketplaces: List[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CategoryNode(BaseModel):
    category_id: Optional[str] = Field(None, max_length=50)
    name: str = Field(..., max_length=100, min_length=1)
    level: int = Field(1, ge=1, le=10)
    parent_id: Optional[str] = None
    description: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @validator('category_id', pre=True, always=True)
    def generate_category_id(cls, v, values):
        if not v and 'name' in values:
            return values['name'].lower().replace(' ', '_').replace('-', '_')
        return v
