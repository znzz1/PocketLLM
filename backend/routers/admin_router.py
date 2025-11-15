"""Admin API router."""
from fastapi import APIRouter, Depends
from typing import Annotated
from schemas.auth import TokenPayload
from schemas.admin import SystemMetrics, CacheFlushResponse, ModelConfig
from utils.dependencies import get_current_admin
import utils.dependencies as deps

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/metrics", response_model=SystemMetrics)
async def get_metrics(
    current_admin: Annotated[TokenPayload, Depends(get_current_admin)]
):
    """
    Get system metrics (admin only).
    """
    deps.monitoring_service.increment_request_count()

    cache_stats = deps.cache_manager.get_stats()
    active_sessions = len(deps.session_service.sessions)

    return deps.monitoring_service.get_system_metrics(cache_stats, active_sessions)


@router.post("/cache/flush", response_model=CacheFlushResponse)
async def flush_cache(
    current_admin: Annotated[TokenPayload, Depends(get_current_admin)]
):
    """
    Flush all cache entries (admin only).
    """
    deps.monitoring_service.increment_request_count()
    entries_flushed = deps.cache_manager.flush()

    return CacheFlushResponse(
        success=True,
        message="Cache flushed successfully",
        entries_flushed=entries_flushed
    )


@router.get("/model/info", response_model=ModelConfig)
async def get_model_info(
    current_admin: Annotated[TokenPayload, Depends(get_current_admin)]
):
    """
    Get LLM model configuration (admin only).
    """
    deps.monitoring_service.increment_request_count()
    info = deps.inference_service.llm_engine.get_model_info()

    return ModelConfig(
        model_path=info["model_path"],
        n_ctx=info["n_ctx"],
        n_threads=info["n_threads"],
        n_gpu_layers=info["n_gpu_layers"],
        temperature=info["temperature"],
        top_p=info["top_p"],
        max_tokens=info["max_tokens"]
    )


@router.get("/cache/stats")
async def get_cache_stats(
    current_admin: Annotated[TokenPayload, Depends(get_current_admin)]
):
    """
    Get cache statistics (admin only).
    """
    deps.monitoring_service.increment_request_count()
    return deps.cache_manager.get_stats()


@router.get("/sessions/count")
async def get_session_count(
    current_admin: Annotated[TokenPayload, Depends(get_current_admin)]
):
    """
    Get total session count (admin only).
    """
    deps.monitoring_service.increment_request_count()
    return {
        "total_sessions": len(deps.session_service.sessions),
        "total_users": len(deps.session_service.user_sessions)
    }
