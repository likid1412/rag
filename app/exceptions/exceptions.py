"""custom exceptions"""

# pylint: disable=too-few-public-methods

import traceback
from loguru import logger
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.types import ASGIApp


class InvalidResponseFromUpStream(HTTPException):
    """Invalid response from upstream service"""

    def __init__(
        self,
        detail: str = "",
    ) -> None:
        detail = f"Invalid response from upstream service: {detail}"
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, detail)


class InternalProcessError(HTTPException):
    """
    Internal Process Error

    Indicate error when processing data, but not call rpc
    """

    def __init__(
        self,
        detail: str = "",
    ) -> None:
        detail = f"Internal Process Error: {detail}"
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, detail)


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):
    """Exception Handling Middleware"""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ):
        try:
            response = await call_next(request)
            return response
        except (TypeError, ValueError) as e:
            logger.error(f"BAD_REQUEST, e: {e}, {traceback.format_exc()}")
            return JSONResponse({"detail": str(e)}, status.HTTP_400_BAD_REQUEST)
        except (InvalidResponseFromUpStream, InternalProcessError) as e:
            logger.error(
                f"INTERNAL_SERVER_ERROR, e: {e}, {traceback.format_exc()}"
            )
            return JSONResponse(
                {"detail": str(e)}, status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except HTTPException as e:
            logger.error(f"HTTPException, e: {e}, {traceback.format_exc()}")
            return JSONResponse({"detail": str(e)}, e.status_code)
        except Exception as e:
            logger.error(
                f"INTERNAL_SERVER_ERROR, e: {e}, {traceback.format_exc()}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            ) from e
