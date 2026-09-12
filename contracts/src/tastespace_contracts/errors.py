"""The single error shape every API route returns on failure."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

ErrorCode = Literal["validation_error", "not_found", "not_ready", "grok_unavailable", "grok_failed", "internal"]

ERROR_STATUS: dict[str, int] = {
    "validation_error": 422,
    "not_found": 404,
    "not_ready": 503,         # build artifact / data missing or invalid
    "grok_unavailable": 503,  # XAI_API_KEY or GROK_MODEL not configured
    "grok_failed": 502,       # xAI call failed at runtime
    "internal": 500,
}

_CFG = ConfigDict(extra="forbid", json_schema_serialization_defaults_required=True)


class ErrorBody(BaseModel):
    model_config = _CFG
    code: ErrorCode
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    model_config = _CFG
    error: ErrorBody
