"""Health check and diagnostics schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DatabaseHealth(BaseModel):
    connected: bool = Field(..., description="Whether the database responded to ping")
    engine: str = Field(..., description="Database engine type: postgresql or sqlite")
    latency_ms: Optional[float] = Field(None, description="Database ping roundtrip in milliseconds")
    error: Optional[str] = Field(None, description="Safe error message if connection failed")


class ModelHealth(BaseModel):
    loaded: bool = Field(..., description="Whether a trained model binary is loaded")
    version: str = Field(..., description="Model version or fallback indicator")
    status: str = Field(..., description="Status: 'trained' or 'not_trained'")


class AppInfo(BaseModel):
    name: str
    version: str
    environment: str


class HealthResponse(BaseModel):
    status: str = Field(..., description="System overall status: ok or degraded")
    timestamp: datetime = Field(..., description="Timestamp of health check")
    app: AppInfo
    database: DatabaseHealth
    model: ModelHealth
