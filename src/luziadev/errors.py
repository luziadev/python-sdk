from __future__ import annotations

from typing import Literal, Optional

import httpx

from luziadev.models import RateLimitInfo

ErrorCode = Literal[
    "auth",
    "not_found",
    "validation",
    "rate_limit",
    "timeout",
    "network",
    "server",
    "unknown",
]


class LuziaError(Exception):
    """Base exception for all Luzia SDK errors."""

    def __init__(
        self,
        message: str,
        *,
        status: Optional[int] = None,
        code: ErrorCode = "unknown",
        correlation_id: Optional[str] = None,
        rate_limit_info: Optional[RateLimitInfo] = None,
        retry_after: Optional[int] = None,
        details: Optional[dict] = None,
        timeout_ms: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.correlation_id = correlation_id
        self.rate_limit_info = rate_limit_info
        self.retry_after = retry_after
        self.details = details
        self.timeout_ms = timeout_ms


def is_luzia_error(error: BaseException) -> bool:
    return isinstance(error, LuziaError)


def is_retryable_error(error: BaseException) -> bool:
    if isinstance(error, LuziaError):
        return error.code in ("rate_limit", "network", "timeout", "server")
    return False


def is_retryable_status(status: int) -> bool:
    return status in (408, 429, 500, 502, 503, 504)


def parse_rate_limit_headers(headers: httpx.Headers) -> Optional[RateLimitInfo]:
    limit = headers.get("x-ratelimit-limit")
    remaining = headers.get("x-ratelimit-remaining")
    reset = headers.get("x-ratelimit-reset")

    if limit is None or remaining is None or reset is None:
        return None

    daily_limit = headers.get("x-ratelimit-daily-limit")
    daily_remaining = headers.get("x-ratelimit-daily-remaining")
    daily_reset = headers.get("x-ratelimit-daily-reset")

    return RateLimitInfo(
        limit=int(limit),
        remaining=int(remaining),
        reset=int(reset),
        daily_limit=int(daily_limit) if daily_limit else None,
        daily_remaining=int(daily_remaining) if daily_remaining else None,
        daily_reset=int(daily_reset) if daily_reset else None,
    )


def _status_to_error_code(status: int) -> ErrorCode:
    if status == 400:
        return "validation"
    if status == 401:
        return "auth"
    if status == 404:
        return "not_found"
    if status == 429:
        return "rate_limit"
    if status >= 500:
        return "server"
    return "unknown"


async def create_error_from_response(
    response: httpx.Response,
    rate_limit_info: Optional[RateLimitInfo] = None,
) -> LuziaError:
    code = _status_to_error_code(response.status_code)

    correlation_id = None
    message = f"HTTP {response.status_code}"
    details = None
    retry_after = None

    try:
        body = response.json()
        message = body.get("message", message)
        correlation_id = body.get("correlationId")
        details = body.get("details")
    except Exception:
        pass

    if code == "rate_limit":
        retry_after_header = response.headers.get("retry-after")
        if retry_after_header:
            try:
                retry_after = int(retry_after_header)
            except ValueError:
                pass

    return LuziaError(
        message,
        status=response.status_code,
        code=code,
        correlation_id=correlation_id,
        rate_limit_info=rate_limit_info,
        retry_after=retry_after,
        details=details,
    )
