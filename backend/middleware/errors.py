import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError

async def global_exception_handler(request: Request, exc: Exception):
    logging.exception(f"Unhandled error processing request: {request.url}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "about:blank",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected server error occurred. Our team is investigating.",
            "instance": str(request.url),
        }
    )

async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    logging.error(f"Database transaction failure on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "about:blank",
            "title": "Database Error",
            "status": 500,
            "detail": "A database operational error occurred. Transaction rolled back.",
            "instance": str(request.url),
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.warning(f"Validation failure on {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "type": "about:blank",
            "title": "Validation Error",
            "status": 422,
            "detail": "The request body failed parameter constraints.",
            "errors": exc.errors(),
            "instance": str(request.url),
        }
    )
