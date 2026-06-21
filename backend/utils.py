import logging
from datetime import datetime
from typing import Any, Dict, Optional

from flask import Response, jsonify

logger = logging.getLogger("ecotrack.utils")


def send_response(
    data: Any, status_code: int = 200, headers: Optional[Dict[str, str]] = None
) -> Response:
    """Centralized JSON response wrapper function to standardize API response schemas across all endpoints."""
    response = jsonify(data)
    response.status_code = status_code
    if headers:
        for key, value in headers.items():
            response.headers[key] = value
    return response


def serialize_datetime(obj: Any) -> Any:
    """Recursively serialize datetime objects to ISO format strings within dicts and lists (Item 19)."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    return obj


def safe_session_close(db_session: Any) -> None:
    """Type-safe database session cleanup helper to ensure sessions are removed after requests (Item 14)."""
    try:
        db_session.remove()
    except Exception as err:
        logger.warning(f"Failed to cleanly close database session: {err}")


def register_sqlalchemy_event_logger(app: Any, db: Any) -> None:
    """Registers SQLAlchemy query parameter logging listener in debug mode (Item 6)."""
    if app.debug:
        from sqlalchemy import event
        from sqlalchemy.engine import Engine

        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            app.logger.debug(
                f"[SQLAlchemy] Query: {statement[:200]} | Params: {str(parameters)[:100]}"
            )


class SensitiveDataFilter(logging.Filter):
    """Logging filter to mask password and auth token values in log messages (Action-SEC-158)."""

    def filter(self, record: logging.LogRecord) -> bool:
        import re

        if isinstance(record.msg, str):
            record.msg = re.sub(
                r'(password["\'\s:]+)[^\'",\s]+',
                r"\1[MASKED]",
                record.msg,
                flags=re.IGNORECASE,
            )
            record.msg = re.sub(
                r'(token["\'\s:]+)[^\'",\s]+',
                r"\1[MASKED]",
                record.msg,
                flags=re.IGNORECASE,
            )
            record.msg = re.sub(
                r'(bearer\s+)[^\'",\s]+',
                r"\1[MASKED]",
                record.msg,
                flags=re.IGNORECASE,
            )
        return True
