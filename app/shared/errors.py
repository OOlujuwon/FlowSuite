from fastapi import Request
from fastapi.responses import JSONResponse


class FlowSuiteError(Exception):
    """Base application error."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


async def flowsuite_error_handler(
    request: Request,
    exc: FlowSuiteError,
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
        },
    )