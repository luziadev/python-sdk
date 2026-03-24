import pytest

from luziadev.errors import LuziaError
from luziadev.retry import (
    RetryOptions,
    RetryContext,
    calculate_retry_delay,
    with_retry,
)


def test_calculate_retry_delay_exponential():
    opts = RetryOptions(
        initial_delay_ms=1000,
        backoff_multiplier=2.0,
        max_delay_ms=30000,
        jitter=False,
    )
    assert calculate_retry_delay(0, opts) == 1000
    assert calculate_retry_delay(1, opts) == 2000
    assert calculate_retry_delay(2, opts) == 4000
    assert calculate_retry_delay(3, opts) == 8000


def test_calculate_retry_delay_max_cap():
    opts = RetryOptions(
        initial_delay_ms=1000,
        backoff_multiplier=2.0,
        max_delay_ms=5000,
        jitter=False,
    )
    assert calculate_retry_delay(10, opts) == 5000


def test_calculate_retry_delay_respects_retry_after():
    opts = RetryOptions(jitter=False)
    error = LuziaError("rate limited", code="rate_limit", retry_after=60)
    delay = calculate_retry_delay(0, opts, error)
    assert delay == 60100  # 60s * 1000 + 100ms buffer


def test_calculate_retry_delay_with_jitter():
    opts = RetryOptions(initial_delay_ms=1000, jitter=True)
    delays = [calculate_retry_delay(0, opts) for _ in range(100)]
    assert min(delays) >= 500
    assert max(delays) <= 1500
    assert len(set(delays)) > 1  # Not all the same


@pytest.mark.asyncio
async def test_with_retry_success_first_attempt():
    call_count = 0

    async def fn():
        nonlocal call_count
        call_count += 1
        return "ok"

    result = await with_retry(fn)
    assert result == "ok"
    assert call_count == 1


@pytest.mark.asyncio
async def test_with_retry_retries_on_retryable_error():
    call_count = 0

    async def fn():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise LuziaError("server error", code="server", status=500)
        return "ok"

    opts = RetryOptions(max_retries=3, initial_delay_ms=10, jitter=False)
    result = await with_retry(fn, opts)
    assert result == "ok"
    assert call_count == 3


@pytest.mark.asyncio
async def test_with_retry_gives_up_after_max():
    call_count = 0

    async def fn():
        nonlocal call_count
        call_count += 1
        raise LuziaError("server error", code="server", status=500)

    opts = RetryOptions(max_retries=2, initial_delay_ms=10, jitter=False)
    with pytest.raises(LuziaError) as exc_info:
        await with_retry(fn, opts)
    assert exc_info.value.code == "server"
    assert call_count == 3  # initial + 2 retries


@pytest.mark.asyncio
async def test_with_retry_no_retry_on_auth_error():
    call_count = 0

    async def fn():
        nonlocal call_count
        call_count += 1
        raise LuziaError("unauthorized", code="auth", status=401)

    opts = RetryOptions(max_retries=3, initial_delay_ms=10)
    with pytest.raises(LuziaError) as exc_info:
        await with_retry(fn, opts)
    assert exc_info.value.code == "auth"
    assert call_count == 1


@pytest.mark.asyncio
async def test_with_retry_calls_on_retry_callback():
    contexts: list[RetryContext] = []

    async def fn():
        if len(contexts) < 2:
            raise LuziaError("timeout", code="timeout")
        return "ok"

    def on_retry(ctx: RetryContext):
        contexts.append(ctx)

    opts = RetryOptions(max_retries=3, initial_delay_ms=10, jitter=False)
    result = await with_retry(fn, opts, on_retry=on_retry)
    assert result == "ok"
    assert len(contexts) == 2
    assert contexts[0].attempt == 0
    assert contexts[1].attempt == 1
