"""Unified API v1 router mounting all v1 endpoint routers."""

from fastapi import APIRouter

from app.api.v1.endpoints import analyze, analytics, health

api_v1_router = APIRouter()

# Mount endpoints
api_v1_router.include_router(health.router, tags=["Health & Diagnostics"])
api_v1_router.include_router(analyze.router, tags=["Job Risk Analysis"])
api_v1_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics & Insights"])

