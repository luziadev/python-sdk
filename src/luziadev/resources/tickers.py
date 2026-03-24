from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from luziadev.models import Ticker, TickerListResponse

if TYPE_CHECKING:
    from luziadev.client import Luzia


class TickersResource:
    def __init__(self, client: Luzia) -> None:
        self._client = client

    async def get(self, exchange: str, symbol: str) -> Ticker:
        url_symbol = self._client.symbol_to_url(symbol)
        data = await self._client.request(
            f"/v1/ticker/{exchange.lower()}/{url_symbol}"
        )
        return Ticker.from_dict(data)

    async def list(
        self,
        exchange: str,
        *,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> TickerListResponse:
        data = await self._client.request(
            f"/v1/tickers/{exchange.lower()}",
            query={"limit": limit, "offset": offset},
        )
        return TickerListResponse.from_dict(data)

    async def list_filtered(
        self,
        *,
        exchange: Optional[str] = None,
        symbols: Optional[list[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> TickerListResponse:
        query: dict = {"limit": limit, "offset": offset}
        if exchange:
            query["exchange"] = exchange.lower()
        if symbols:
            query["symbols"] = ",".join(
                self._client.symbol_to_url(s) for s in symbols
            )
        data = await self._client.request("/v1/tickers", query=query)
        return TickerListResponse.from_dict(data)
