from __future__ import annotations

from typing import Any, Optional

import httpx

from luziadev._utils import filter_none
from luziadev.errors import (
    LuziaError,
    create_error_from_response,
    parse_rate_limit_headers,
)
from luziadev.models import RateLimitInfo
from luziadev.resources.exchanges import ExchangesResource
from luziadev.resources.history import HistoryResource
from luziadev.resources.markets import MarketsResource
from luziadev.resources.tickers import TickersResource
from luziadev.retry import RetryOptions, with_retry


class Luzia:
    """Official Python client for the Luzia cryptocurrency pricing API."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://api.luzia.dev",
        timeout: int = 30,
        retry: Optional[RetryOptions] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key is required")

        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._retry_options = retry
        self._rate_limit_info: Optional[RateLimitInfo] = None

        self._http_client = http_client or httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        self._owns_client = http_client is None

        self.exchanges = ExchangesResource(self)
        self.tickers = TickersResource(self)
        self.markets = MarketsResource(self)
        self.history = HistoryResource(self)

    @property
    def rate_limit_info(self) -> Optional[RateLimitInfo]:
        return self._rate_limit_info

    @staticmethod
    def symbol_to_url(symbol: str) -> str:
        return symbol.replace("/", "-")

    @staticmethod
    def symbol_from_url(symbol: str) -> str:
        return symbol.replace("-", "/")

    def create_websocket(
        self,
        *,
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 10,
        reconnect_delay_ms: int = 1000,
        max_reconnect_delay_ms: int = 30000,
        heartbeat_interval_ms: int = 30000,
    ) -> "LuziaWebSocket":
        from luziadev.websocket import LuziaWebSocket

        ws_url = self._base_url.replace("https://", "wss://").replace(
            "http://", "ws://"
        )

        return LuziaWebSocket(
            url=f"{ws_url}/v1/ws",
            headers={"Authorization": f"Bearer {self._api_key}"},
            auto_reconnect=auto_reconnect,
            max_reconnect_attempts=max_reconnect_attempts,
            reconnect_delay_ms=reconnect_delay_ms,
            max_reconnect_delay_ms=max_reconnect_delay_ms,
            heartbeat_interval_ms=heartbeat_interval_ms,
        )

    async def request(
        self,
        path: str,
        *,
        query: Optional[dict] = None,
        retry: Optional[RetryOptions] = None,
    ) -> dict[str, Any]:
        opts = retry or self._retry_options

        async def do_request() -> dict[str, Any]:
            try:
                params = filter_none(query) if query else None
                response = await self._http_client.get(path, params=params)
            except httpx.TimeoutException as exc:
                raise LuziaError(
                    f"Request timed out after {self._timeout}s",
                    code="timeout",
                    timeout_ms=self._timeout * 1000,
                ) from exc
            except httpx.ConnectError as exc:
                raise LuziaError(
                    f"Failed to connect to {self._base_url}",
                    code="network",
                ) from exc

            rate_limit = parse_rate_limit_headers(response.headers)
            if rate_limit:
                self._rate_limit_info = rate_limit

            if response.status_code >= 400:
                raise await create_error_from_response(response, rate_limit)

            return response.json()

        if opts:
            return await with_retry(do_request, opts)
        return await do_request()

    async def close(self) -> None:
        if self._owns_client:
            await self._http_client.aclose()

    async def __aenter__(self) -> Luzia:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
