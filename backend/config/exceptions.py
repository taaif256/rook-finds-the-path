"""One error shape for the whole API.

Every error response, from any endpoint, looks like::

    {"status": "error", "message": "Invalid request.", "errors": {"start": ["..."]}}

``errors`` maps request fields to messages using dotted paths for nested input
(``grid.rows``, ``start.row``, ``barriers.2.col``). It is empty for errors that
are not about a specific field (wrong method, malformed JSON, ...).
"""

from __future__ import annotations

from typing import Any

from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

VALIDATION_MESSAGE = "Invalid request."
NON_FIELD_KEY = "non_field_errors"


def flatten_errors(detail: Any) -> dict[str, list[str]]:
    """Flatten DRF's nested validation errors into ``{"dotted.path": ["message", ...]}``."""
    flat: dict[str, list[str]] = {}
    _collect(detail, "", flat)
    return flat


def _collect(detail: Any, path: str, out: dict[str, list[str]]) -> None:
    if isinstance(detail, dict):
        for key, value in detail.items():
            # A nested serializer's own error belongs to the nested field itself.
            child = path if key == NON_FIELD_KEY and path else f"{path}.{key}" if path else str(key)
            _collect(value, child, out)
    elif isinstance(detail, (list, tuple)):
        if all(not isinstance(item, (dict, list, tuple)) for item in detail):
            if detail:
                out.setdefault(path or NON_FIELD_KEY, []).extend(str(item) for item in detail)
        else:  # a list of per-item errors (e.g. one entry per barrier)
            for index, item in enumerate(detail):
                _collect(item, f"{path}.{index}" if path else str(index), out)
    else:
        out.setdefault(path or NON_FIELD_KEY, []).append(str(detail))


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """DRF's handler, with the response body reshaped into the error envelope."""
    response = drf_exception_handler(exc, context)
    if response is None:
        return None  # not an API error; let Django deal with it

    if isinstance(exc, exceptions.ValidationError):
        message, errors = VALIDATION_MESSAGE, flatten_errors(exc.detail)
    else:
        detail = response.data.get("detail", "") if isinstance(response.data, dict) else ""
        message, errors = str(detail), {}

    response.data = {"status": "error", "message": message, "errors": errors}
    return response
