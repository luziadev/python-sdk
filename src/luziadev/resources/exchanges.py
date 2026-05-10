from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Optional

from luziadev.models import Exchange

if TYPE_CHECKING:
    from luziadev.client import Luzia


# Exchange kind filter. "cex" returns centralized exchanges only,
# "dex" returns decentralized exchanges only (Uniswap V3/V4, Raydium, ...).
ExchangeType = Literal["cex", "dex"]


class ExchangesResource:
    def __init__(self, client: Luzia) -> None:
        self._client = client

    async def list(
        self,
        *,
        type: Optional[ExchangeType] = None,
    ) -> list[Exchange]:
        """List supported exchanges, optionally filtered by kind.

        Args:
            type: Filter by ``"cex"`` or ``"dex"``. Omit for all.

        Example:
            >>> # Only DEX exchanges (Uniswap, Raydium, ...)
            >>> dexes = await luzia.exchanges.list(type="dex")
        """
        query: dict = {}
        if type is not None:
            query["type"] = type
        data = await self._client.request("/v1/exchanges", query=query or None)
        return [Exchange.from_dict(e) for e in data.get("exchanges", [])]
