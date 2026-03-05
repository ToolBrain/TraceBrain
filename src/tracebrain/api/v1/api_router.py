"""Main API router for v1."""

from fastapi import APIRouter

from .ai_features import router as ai_router
from .curriculum import router as curriculum_router
from .episodes import router as episodes_router
from .operations import router as operations_router
from .system import router as system_router
from .traces import router as traces_router

router = APIRouter()

router.include_router(system_router)
router.include_router(traces_router)
router.include_router(episodes_router)
router.include_router(curriculum_router)
router.include_router(operations_router)
router.include_router(ai_router)
