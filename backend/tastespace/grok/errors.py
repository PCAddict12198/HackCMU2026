"""Readable messages for xAI provider failures (xai_sdk raises gRPC errors with code() / details())."""


def provider_error_message(exc: Exception) -> str:
    try:
        code = exc.code() if callable(getattr(exc, "code", None)) else None  # type: ignore[attr-defined]
        detail = exc.details() if callable(getattr(exc, "details", None)) else None  # type: ignore[attr-defined]
    except Exception:
        code = detail = None
    if detail:
        return f"{getattr(code, 'name', None) or type(exc).__name__}: {detail}"[:300]
    return f"{type(exc).__name__}: {exc}"[:300]
