"""Curriculum endpoints for v1."""

from __future__ import annotations

from typing import List
import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response

from ...core.curator import CurriculumCurator
from ...db.base import CurriculumTask
from .common import store
from .schemas.api_models import CurriculumTaskOut, GenerateCurriculumRequest

router = APIRouter(prefix="/curriculum", tags=["Curriculum"])


@router.post("/generate")
def generate_curriculum(request: GenerateCurriculumRequest):
    """Generate curriculum tasks from failed traces."""
    try:
        curator = CurriculumCurator(store)
        provided_error_types = request.error_types or []
        valid_error_types = [
            value for value in provided_error_types if value in curator.VALID_ERROR_TYPES
        ]
        invalid_error_types = [
            value for value in provided_error_types if value not in curator.VALID_ERROR_TYPES
        ]
        created = curator.generate_curriculum(
            error_types=valid_error_types or None,
            limit=request.limit,
        )
        response = {"status": "success", "tasks_generated": created}
        if invalid_error_types:
            response["warning"] = {
                "message": "Some error_types were not recognized and were ignored.",
                "invalid_error_types": invalid_error_types,
            }
        return response
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate curriculum: {str(exc)}")


@router.get("", response_model=List[CurriculumTaskOut])
def list_curriculum_tasks():
    """List all curriculum tasks ordered by creation time."""
    session = store.get_session()
    try:
        return (
            session.query(CurriculumTask)
            .order_by(CurriculumTask.created_at.desc())
            .all()
        )
    finally:
        session.close()


@router.get("/export")
def export_curriculum(
    format: str = Query("json", description="Export format: 'json' or 'jsonl'"),
):
    """Export pending curriculum tasks for training ingestion."""
    format_value = format.lower().strip()
    if format_value not in {"json", "jsonl"}:
        raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'jsonl'.")
    try:
        tasks = store.get_pending_curriculum(limit=100)

        export_data = []
        for task in tasks:
            export_data.append(
                {
                    "id": task["id"],
                    "role": "user",
                    "content": task["instruction"],
                    "metadata": {
                        "difficulty": task["priority"],
                        "focus": "auto_curriculum",
                        "reasoning": task["context"],
                    },
                }
            )

        if format_value == "jsonl":
            jsonl_content = "\n".join(json.dumps(item) for item in export_data)
            return Response(content=jsonl_content, media_type="application/x-jsonlines")

        return export_data
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
