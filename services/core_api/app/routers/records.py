from fastapi import APIRouter, Depends, Query

from trinetra_core.records import mock_enricher
from ..auth import current_user

router = APIRouter(prefix="/api/v1/records", tags=["records"])

_enricher = mock_enricher()


@router.get("/plate/{plate}")
async def plate_dossier(plate: str, user=Depends(current_user)):
    """VAHAN vehicle record + CCTNS watchlist hit + SARTHI DL for a plate."""
    return await _enricher.lookup_plate(plate)


@router.get("/person")
async def person_dossier(name: str = Query(...), user=Depends(current_user)):
    """CCTNS person record + NAFIS fingerprint match."""
    return await _enricher.enrich_person(name)
