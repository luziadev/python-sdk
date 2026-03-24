from __future__ import annotations

from typing import TYPE_CHECKING

from luziadev.models import Exchange

if TYPE_CHECKING:
    from luziadev.client import Luzia


class ExchangesResource:
    def __init__(self, client: Luzia) -> None:
        self._client = client

    async def list(self) -> list[Exchange]:
        data = await self._client.request("/v1/exchanges")
        return [Exchange.from_dict(e) for e in data.get("exchanges", [])]
