from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Optional, Union

from luziadev.models import FiatCurrency, FiatCurrencyListResponse

if TYPE_CHECKING:
    from luziadev.client import Luzia


# Filter for the ``enabled`` query parameter.
EnabledFilter = Union[bool, Literal["all"]]


class FiatCurrenciesResource:
    """List and look up ISO 4217 fiat currencies referenced by markets."""

    def __init__(self, client: Luzia) -> None:
        self._client = client

    async def list(
        self,
        *,
        search: Optional[str] = None,
        enabled: EnabledFilter = True,
        page: int = 1,
        limit: int = 50,
    ) -> FiatCurrencyListResponse:
        """List fiat currencies.

        Args:
            search: Case-insensitive search across code and name.
            enabled: ``True`` returns enabled only (default), ``False`` disabled
                only, ``"all"`` for both.
            page: Page number, 1-based.
            limit: Items per page, max 200.

        Example:
            >>> page = await luzia.fiat_currencies.list(search="EUR")
        """
        query: dict = {"page": page, "limit": limit}
        if search is not None:
            query["search"] = search
        if enabled == "all":
            query["enabled"] = "all"
        else:
            query["enabled"] = "true" if enabled else "false"
        data = await self._client.request("/v1/fiat-currencies", query=query)
        return FiatCurrencyListResponse.from_dict(data)

    async def get(self, code: str) -> FiatCurrency:
        """Look up a single fiat currency by ISO 4217 code (e.g. ``"USD"``)."""
        data = await self._client.request(f"/v1/fiat-currencies/{code.upper()}")
        return FiatCurrency.from_dict(data.get("data", {}))
