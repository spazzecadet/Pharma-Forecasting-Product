from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class GeographyLevel(str, Enum):
    COUNTRY = "country"
    REGION = "region"
    MARKET_TIER = "market_tier"


class ChannelType(str, Enum):
    RETAIL = "retail"
    HOSPITAL = "hospital"
    SPECIALTY = "specialty"


class PayerSegment(str, Enum):
    COMMERCIAL = "commercial"
    MEDICARE = "medicare"
    MEDICAID = "medicaid"
    CASH = "cash"


class Brand(BaseModel):
    brand_id: str = Field(..., description="Unique brand identifier")
    molecule: str = Field(..., description="Active molecule")
    form: str = Field(..., description="Dosage form")
    strength: str = Field(..., description="Strength/dosage")
    indication: str = Field(..., description="Primary indication")
    launch_date: Optional[datetime] = None
    loe_date: Optional[datetime] = None
    therapeutic_area: Optional[str] = None


class Geography(BaseModel):
    geo_id: str = Field(..., description="Unique geography identifier")
    country: str = Field(..., description="Country name")
    region: Optional[str] = None
    market_tier: Optional[str] = None
    level: GeographyLevel = Field(default=GeographyLevel.COUNTRY)


class Channel(BaseModel):
    channel_id: str = Field(..., description="Unique channel identifier")
    channel_type: ChannelType = Field(..., description="Channel type")
    description: Optional[str] = None


class Payer(BaseModel):
    payer_id: str = Field(..., description="Unique payer identifier")
    payer_name: str = Field(..., description="Payer name")
    segment: PayerSegment = Field(..., description="Payer segment")
    coverage_pct: float = Field(..., ge=0, le=1, description="Coverage percentage")
    formulary_tier: Optional[int] = None
    copay: Optional[float] = None


class DemandFact(BaseModel):
    date: datetime = Field(..., description="Date of observation")
    brand_id: str = Field(..., description="Brand identifier")
    geo_id: str = Field(..., description="Geography identifier")
    channel_id: str = Field(..., description="Channel identifier")
    trx: int = Field(..., ge=0, description="Total prescriptions")
    nrx: int = Field(..., ge=0, description="New prescriptions")
    units: int = Field(..., ge=0, description="Units sold")
    net_sales: float = Field(..., ge=0, description="Net sales amount")


class PricePromoFact(BaseModel):
    date: datetime = Field(..., description="Date of observation")
    brand_id: str = Field(..., description="Brand identifier")
    geo_id: str = Field(..., description="Geography identifier")
    price: float = Field(..., ge=0, description="Unit price")
    discount: float = Field(default=0, ge=0, le=1, description="Discount percentage")
    promo_spend: float = Field(default=0, ge=0, description="Promotional spending")
    grps: float = Field(default=0, ge=0, description="Gross rating points")
    calls: int = Field(default=0, ge=0, description="Sales calls")


class PayerFact(BaseModel):
    date: datetime = Field(..., description="Date of observation")
    brand_id: str = Field(..., description="Brand identifier")
    geo_id: str = Field(..., description="Geography identifier")
    payer_id: str = Field(..., description="Payer identifier")
    coverage_pct: float = Field(..., ge=0, le=1, description="Coverage percentage")
    formulary_tier: Optional[int] = None
    copay: Optional[float] = None


class CompetitorEvent(BaseModel):
    date: datetime = Field(..., description="Event date")
    market: str = Field(..., description="Market/indication")
    event_type: str = Field(..., description="Type of event")
    intensity: float = Field(..., ge=0, le=1, description="Event intensity")
    narrative: Optional[str] = None


class InventorySupply(BaseModel):
    date: datetime = Field(..., description="Date of observation")
    brand_id: str = Field(..., description="Brand identifier")
    geo_id: str = Field(..., description="Geography identifier")
    on_hand: int = Field(..., ge=0, description="Units on hand")
    stockout_flag: bool = Field(default=False, description="Stockout indicator")


class DataSource(BaseModel):
    source_id: str = Field(..., description="Unique source identifier")
    source_name: str = Field(..., description="Source name")
    source_type: str = Field(..., description="Type (API, Database, File)")
    connection_string: Optional[str] = None
    refresh_frequency: str = Field(default="daily", description="How often to refresh")
    last_updated: Optional[datetime] = None
    status: str = Field(default="active", description="Source status")


class DataLineage(BaseModel):
    source_id: str = Field(..., description="Source identifier")
    target_table: str = Field(..., description="Target table name")
    transformation: str = Field(..., description="Transformation description")
    dependencies: List[str] = Field(default_factory=list, description="Dependencies")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
