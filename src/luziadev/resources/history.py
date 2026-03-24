from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from luziadev.models import OHLCVResponse

if TYPE_CHECKING:
    from luziadev.client import Luzia


class HistoryResource:
    def __init__(self, client: Luzia) -> None:
        self._client = client

    async def get(
        self,
        exchange: str,
        symbol: str,
        *,
        interval: Optional[str] = None,
        start: Optional[int] = None,
        end: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> OHLCVResponse:
        url_symbol = self._client.symbol_to_url(symbol)
        query: dict = {
            "interval": interval,
            "start": start,
            "end": end,
            "limit": limit,
        }
        data = await self._client.request(
            f"/v1/history/{exchange.lower()}/{url_symbol}",
            query=query,
        )
        return OHLCVResponse.from_dict(data)
