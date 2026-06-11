from flask import jsonify, Response
from typing import Any, Dict, Optional

def send_response(data: Any, status_code: int = 200, headers: Optional[Dict[str, str]] = None) -> Response:
    """Centralized JSON response wrapper function to standardize API response schemas across all endpoints."""
    response = jsonify(data)
    response.status_code = status_code
    if headers:
        for key, value in headers.items():
            response.headers[key] = value
    return response
