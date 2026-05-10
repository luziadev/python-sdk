from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Optional

from luziadev.models import MarketListResponse

if TYPE_CHECKING:
    from luziadev.client import Luzia


# Valid market types.
# - "stock" covers tokenized equities (Kraken xStocks).
# - "dex" covers decentralized-exchange pools (Uniswap V3/V4, Raydium, ...).
MarketType = Literal["spot", "futures", "margin", "stock", "dex"]


def _has_mixed_case(value: str) -> bool:
    """Return True if the string contains both upper and lower case letters."""
    return any(c.isupper() for c in value) and any(c.islower() for c in value)


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
        type: Optional[MarketType] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> MarketListResponse:
        """List markets for a specific exchange.

        Args:
            exchange: Exchange identifier (e.g. ``"binance"``, ``"kraken"``).
            base: Filter by base currency (``"BTC"``, ``"AAPLx"``).
                Mixed-case values (xStock tickers) are preserved as-typed.
            quote: Filter by quote currency (``"USDT"``, ``"USD"``).
            active: Filter by active status.
            type: Filter by market type. Pass ``"stock"`` to retrieve
                tokenized equities (Kraken xStocks).
            limit: Page size.
            offset: Page offset.

        Example:
            >>> # Get tokenized stocks on Kraken
            >>> resp = await luzia.markets.list("kraken", type="stock")
            >>> for m in resp.markets:
            ...     print(m.symbol)
        """
        query: dict = {"limit": limit, "offset": offset}
        if base:
            # Preserve case for mixed-case bases (xStock tickers like "AAPLx").
            query["base"] = base if _has_mixed_case(base) else base.upper()
        if quote:
            query["quote"] = quote if _has_mixed_case(quote) else quote.upper()
        if active is not None:
            query["active"] = str(active).lower()
        if type is not None:
            query["type"] = type
        data = await self._client.request(
            f"/v1/markets/{exchange.lower()}",
            query=query,
        )
        return MarketListResponse.from_dict(data)
