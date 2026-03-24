import httpx
import pytest

from luziadev.errors import (
    LuziaError,
    create_error_from_response,
    is_luzia_error,
    is_retryable_error,
    is_retryable_status,
    parse_rate_limit_headers,
)
from luziadev.models import RateLimitInfo


def test_luzia_error_creation():
    error = LuziaError(
        "Something went wrong",
        status=500,
        code="server",
        correlation_id="abc-123",
        details={"key": "value"},
    )
    assert str(error) == "Something went wrong"
    assert error.status == 500
    assert error.code == "server"
    assert error.correlation_id == "abc-123"
    assert error.details == {"key": "value"}
    assert error.retry_after is None
    assert error.timeout_ms is None


def test_is_luzia_error():
    assert is_luzia_error(LuziaError("test"))
    assert not is_luzia_error(ValueError("test"))
    assert not is_luzia_error(Exception("test"))


def test_is_retryable_error():
    assert is_retryable_error(LuziaError("test", code="rate_limit"))
    assert is_retryable_error(LuziaError("test", code="network"))
    assert is_retryable_error(LuziaError("test", code="timeout"))
    assert is_retryable_error(LuziaError("test", code="server"))
    assert not is_retryable_error(LuziaError("test", code="auth"))
    assert not is_retryable_error(LuziaError("test", code="not_found"))
    assert not is_retryable_error(LuziaError("test", code="validation"))
    assert not is_retryable_error(ValueError("test"))


def test_is_retryable_status():
    assert is_retryable_status(408)
    assert is_retryable_status(429)
    assert is_retryable_status(500)
    assert is_retryable_status(502)
    assert is_retryable_status(503)
    assert is_retryable_status(504)
    assert not is_retryable_status(200)
    assert not is_retryable_status(400)
    assert not is_retryable_status(401)
    assert not is_retryable_status(404)


def test_parse_rate_limit_headers_complete():
    headers = httpx.Headers({
        "x-ratelimit-limit": "100",
        "x-ratelimit-remaining": "95",
        "x-ratelimit-reset": "1704067260",
        "x-ratelimit-daily-limit": "5000",
        "x-ratelimit-daily-remaining": "4900",
        "x-ratelimit-daily-reset": "1704096000",
    })
    info = parse_rate_limit_headers(headers)
    assert info is not None
    assert info.limit == 100
    assert info.remaining == 95
    assert info.reset == 1704067260
    assert info.daily_limit == 5000
    assert info.daily_remaining == 4900
    assert info.daily_reset == 1704096000


def test_parse_rate_limit_headers_minimal():
    headers = httpx.Headers({
        "x-ratelimit-limit": "1000",
        "x-ratelimit-remaining": "999",
        "x-ratelimit-reset": "1704067260",
    })
    info = parse_rate_limit_headers(headers)
    assert info is not None
    assert info.limit == 1000
    assert info.daily_limit is None


def test_parse_rate_limit_headers_missing():
    headers = httpx.Headers({})
    info = parse_rate_limit_headers(headers)
    assert info is None


@pytest.mark.asyncio
async def test_create_error_from_response_401():
    response = httpx.Response(
        401,
        json={"error": "Unauthorized", "message": "Invalid API key", "correlationId": "req-123"},
        request=httpx.Request("GET", "https://api.luzia.dev/v1/exchanges"),
    )
    error = await create_error_from_response(response)
    assert error.code == "auth"
    assert error.status == 401
    assert error.correlation_id == "req-123"
    assert "Invalid API key" in str(error)


@pytest.mark.asyncio
async def test_create_error_from_response_429_with_retry_after():
    rate_limit = RateLimitInfo(limit=100, remaining=0, reset=1704067260)
    response = httpx.Response(
        429,
        json={"error": "Too Many Requests", "message": "Rate limit exceeded"},
        headers={"retry-after": "30"},
        request=httpx.Request("GET", "https://api.luzia.dev/v1/exchanges"),
    )
    error = await create_error_from_response(response, rate_limit)
    assert error.code == "rate_limit"
    assert error.retry_after == 30
    assert error.rate_limit_info == rate_limit


@pytest.mark.asyncio
async def test_create_error_from_response_500():
    response = httpx.Response(
        500,
        json={"error": "Internal Server Error", "message": "Unexpected error"},
        request=httpx.Request("GET", "https://api.luzia.dev/v1/exchanges"),
    )
    error = await create_error_from_response(response)
    assert error.code == "server"
    assert error.status == 500
