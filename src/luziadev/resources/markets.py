from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from luziadev.models import MarketListResponse

if TYPE_CHECKING:
    from luziadev.client import Luzia


class MarketsResource:
    def __init__(self, client: Luzia) -> None:
        self._client = client

    async def list(
        self,
        exchange: str,
        *,
        base: Optional[str] = None,
        quote: Optional[str] = None,
        active: Optional[bool] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> MarketListResponse:
        query: dict = {"limit": limit, "offset": offset}
        if base:
            query["base"] = base.upper()
        if quote:
            query["quote"] = quote.upper()
        if active is not None:
            query["active"] = str(active).lower()
        data = await self._client.request(
            f"/v1/markets/{exchange.lower()}",
            query=query,
        )
        return MarketListResponse.from_dict(data)
