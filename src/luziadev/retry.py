from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional, TypeVar

from luziadev.errors import LuziaError, is_retryable_error

T = TypeVar("T")


@dataclass
class RetryOptions:
    max_retries: int = 3
    initial_delay_ms: int = 1000
    max_delay_ms: int = 30000
    backoff_multiplier: float = 2.0
    jitter: bool = True


@dataclass
class RetryContext:
    attempt: int
    max_retries: int
    error: Optional[BaseException] = None


OnRetryCallback = Callable[[RetryContext], None]


def calculate_retry_delay(
    attempt: int,
    options: RetryOptions,
    error: Optional[LuziaError] = None,
) -> float:
    if error and isinstance(error, LuziaError) and error.retry_after is not None:
        return (error.retry_after * 1000) + 100

    delay = options.initial_delay_ms * (options.backoff_multiplier ** attempt)
    delay = min(delay, options.max_delay_ms)

    if options.jitter:
        delay *= 0.5 + random.random()

    return delay


async def with_retry(
    fn: Callable[[], Awaitable[T]],
    options: Optional[RetryOptions] = None,
    on_retry: Optional[OnRetryCallback] = None,
) -> T:
    opts = options or RetryOptions()
    last_error: Optional[BaseException] = None

    for attempt in range(opts.max_retries + 1):
        try:
            return await fn()
        except Exception as error:
            last_error = error

            if attempt >= opts.max_retries or not is_retryable_error(error):
                raise

            if on_retry:
                ctx = RetryContext(
                    attempt=attempt,
                    max_retries=opts.max_retries,
                    error=error,
                )
                on_retry(ctx)

            luzia_err = error if isinstance(error, LuziaError) else None
            delay_ms = calculate_retry_delay(attempt, opts, luzia_err)
            await asyncio.sleep(delay_ms / 1000)

    raise last_error  # type: ignore[misc]
