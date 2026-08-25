"""
schemas.py — Pydantic response models for OmniKPI / PlantIntel API.
"""
from pydantic import BaseModel
from typing import Optional


# ─── Domain ───────────────────────────────────────────────────────────────────

class DomainInfo(BaseModel):
    domain_id: int
    domain_name: str
    domain_code: str

    model_config = {"from_attributes": True}


# ─── Location ─────────────────────────────────────────────────────────────────

class LocationNode(BaseModel):
    location_id: int
    location_name: str
    location_type: str
    parent_location_id: Optional[int]
    domain_id: int
    children: list["LocationNode"] = []

    model_config = {"from_attributes": True}

LocationNode.model_rebuild()


# ─── KPI ──────────────────────────────────────────────────────────────────────

class KPIInfo(BaseModel):
    kpi_id: int
    kpi_name: str
    kpi_archetype: str
    unit: Optional[str]
    target_threshold: Optional[float]
    higher_is_better: bool
    source_standard: Optional[str]
    formula_description: Optional[str]

    model_config = {"from_attributes": True}


# ─── Heatmap ──────────────────────────────────────────────────────────────────

class HeatmapCell(BaseModel):
    kpi_id: int
    kpi_name: str
    kpi_archetype: str
    actual_value: float
    target_value: Optional[float]
    z_score: Optional[float]
    is_anomaly: bool
    status: str          # GREEN | YELLOW | RED
    unit: str
    higher_is_better: bool


class LocationSummary(BaseModel):
    total: int
    red: int
    yellow: int
    green: int


class HeatmapLocation(BaseModel):
    location_id: int
    location_name: str
    location_type: str
    parent_location_id: Optional[int]
    kpis: list[HeatmapCell]
    summary: LocationSummary


class HeatmapResponse(BaseModel):
    domain_id: int
    domain_name: str
    date: str
    locations: list[HeatmapLocation]


# ─── History ──────────────────────────────────────────────────────────────────

class HistoryPoint(BaseModel):
    date: str
    actual_value: float
    z_score: Optional[float]
    is_anomaly: bool
    status: str


class HistoryResponse(BaseModel):
    domain_id: int
    kpi_id: int
    kpi_name: str
    location_id: int
    location_name: str
    unit: str
    target_threshold: Optional[float]
    higher_is_better: bool
    history: list[HistoryPoint]


# ─── Anomaly ──────────────────────────────────────────────────────────────────

class AnomalyItem(BaseModel):
    kpi_id: int
    kpi_name: str
    kpi_archetype: str
    location_id: int
    location_name: str
    actual_value: float
    target_value: Optional[float]
    z_score: float
    status: str
    unit: str
    anomaly_reason: Optional[str]
    date: str


class AnomalyResponse(BaseModel):
    domain_id: int
    date: str
    total_anomalies: int
    anomalies: list[AnomalyItem]


# ─── RCA ──────────────────────────────────────────────────────────────────────

class RCARequest(BaseModel):
    kpi_id: int
    location_id: int


class RCAResponse(BaseModel):
    kpi_name: str
    location_name: str
    actual_value: float
    z_score: Optional[float]
    root_cause: str
    confidence_score: int         # Derived from Z-score — NOT LLM-generated
    confidence_basis: str
    prescriptive_action: str
    estimated_impact: str
    shift_logs_retrieved: int
    llm_model: str


# ─── Harvester ────────────────────────────────────────────────────────────────

class ColumnMappingResult(BaseModel):
    target: Optional[str]
    confidence: float
    method: str          # "fuzzy" | "llm" | "none"


class HarvestResponse(BaseModel):
    success: bool
    rows_parsed: int
    column_mapping: dict[str, ColumnMappingResult]
    preview: list[dict]
    error: Optional[str] = None
