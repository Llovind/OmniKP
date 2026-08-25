"""
routers/harvest.py — Harvester Agent endpoint: Excel file upload and column mapping.

POST /api/v1/domains/{domain_id}/harvest
    Accepts a multipart/form-data Excel upload.
    Returns column mapping report + 5-row preview for human review.
    Does NOT write to the database — human confirmation required.
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from agents.harvester import process_excel
from dependencies import get_validated_domain
from schemas import HarvestResponse

router = APIRouter(
    prefix="/api/v1/domains/{domain_id}",
    tags=["Harvester Agent"],
    dependencies=[Depends(get_validated_domain)],
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB guard


@router.post("/harvest", response_model=HarvestResponse)
async def harvest_excel(
    domain_id: int,
    file: UploadFile = File(..., description="Excel file (.xlsx) with KPI data"),
):
    """
    Harvester Agent: parse an Excel file and map its columns to the OmniKPI schema.

    Column mapping logic:
      - rapidfuzz (WRatio scorer) maps column headers to target schema, threshold = 80%
      - Below 80% confidence: escalates to LLM (OpenRouter) for interpretation
      - Returns mapping report: { source_col: { target, confidence, method } }
      - Returns 5-row data preview using mapped column names

    Human-in-the-loop: this endpoint never writes to the database.
    The UI should show the mapping report to the user for confirmation before ingestion.
    This satisfies Purdue Model / ISA-95 read-only advisory constraints.
    """
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Only Excel files (.xlsx, .xls) are accepted.",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE // (1024*1024)} MB.",
        )

    result = await process_excel(content, domain_id)

    # Normalize column_mapping values to ColumnMappingResult schema
    from schemas import ColumnMappingResult
    normalized_mapping = {
        k: ColumnMappingResult(**v) for k, v in result.get("column_mapping", {}).items()
    }

    return HarvestResponse(
        success=result["success"],
        rows_parsed=result["rows_parsed"],
        column_mapping=normalized_mapping,
        preview=result["preview"],
        error=result.get("error"),
    )
