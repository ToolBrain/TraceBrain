"""
TraceBrain TraceStore REST API Settings Router (v1)

This router manages application settings.

Features:
- GET /api/v1/settings: Retrieve current settings
- POST /api/v1/settings: Update and persist settings
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal

from tracebrain.constants import SETTINGS_FILE

router = APIRouter(
    prefix="/settings",
    tags=["Settings"]
)

# Pydantic Models
class AppearanceSettings(BaseModel):
    theme: Literal["light", "dark"] = "light"

class RefreshSettings(BaseModel):
    autoRefresh: bool = False
    refreshInterval: int = 30

class LLMSettings(BaseModel):
    model: str

class ChatLLMSettings(BaseModel):
    model: str

class Settings(BaseModel):
    appearance: AppearanceSettings
    refresh: RefreshSettings
    llm: LLMSettings
    chatLLM: ChatLLMSettings
    
    class Config:
        json_schema_extra = {
            "example": {
                "appearance": {
                    "theme": "dark"
                },
                "refresh": {
                    "autoRefresh": True,
                    "refreshInterval": 160
                },
                "llm": {
                    "model": "gpt-4"
                },
                "chatLLM": {
                    "model": "gpt-4"
                }
            }
        }

# API Endpoints
@router.get("/")
async def get_settings() -> Settings:
    """Load settings from the settings file."""
    try:
        return Settings.model_validate_json(SETTINGS_FILE.read_text())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def save_settings(settings: Settings):
    """Save the settings object to the settings file."""
    try:
        SETTINGS_FILE.write_text(settings.model_dump_json(indent=2))
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))