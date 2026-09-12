"""Engine error type; api.py turns it into the contract ErrorResponse. OWNER: engine (P2)."""

from typing import Any

from tastespace_contracts.errors import ERROR_STATUS


class TasteSpaceError(Exception):
    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        assert code in ERROR_STATUS, code
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details

    @property
    def status(self) -> int:
        return ERROR_STATUS[self.code]
