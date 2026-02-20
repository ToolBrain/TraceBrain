"""
TraceBrain TraceStore REST API Settings Router (v1)

This router manages global application settings.

Features:
- GET /api/v1/settings: Retrieve current settings
- POST /api/v1/settings: Update and persist settings
"""
from typing import Any, Dict
from fastapi import APIRouter, HTTPException

from ..endpoints import store

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
)

# API Endpoints
@router.get("")
async def get_settings() -> Dict[str, Any]:
    """Load settings from the database."""
    try:
        return store.get_settings()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("")
async def save_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Save the settings object to the database."""
    try:
        return store.update_settings(settings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))