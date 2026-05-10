from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from luziadev.models import Token, TokenListResponse

if TYPE_CHECKING:
    from luziadev.client import Luzia


class TokensResource:
    """List and look up canonical assets and on-chain tokens."""

    def __init__(self, client: Luzia) -> None:
        self._client = client

    async def list(
        self,
        *,
        search: Optional[str] = None,
        chain_id: Optional[str] = None,
        has_chain: Optional[bool] = None,
        page: int = 1,
        limit: int = 20,
    ) -> TokenListResponse:
        """List tokens with optional filtering and pagination.

        Args:
            search: Case-insensitive search across symbol, name, and id.
            chain_id: Filter by chain id (e.g. ``"ethereum"``).
            has_chain: ``True`` returns on-chain tokens only, ``False`` returns
                chainless canonical tokens only. Omit for both.
            page: Page number, 1-based.
            limit: Items per page, max 100.

        Example:
            >>> page = await luzia.tokens.list(search="USDC")
            >>> for t in page.data:
            ...     print(t.id, t.chain_id)
        """
        query: dict = {"page": page, "limit": limit}
        if search is not None:
            query["search"] = search
        if chain_id is not None:
            query["chainId"] = chain_id
        if has_chain is not None:
            query["hasChain"] = "true" if has_chain else "false"
        data = await self._client.request("/v1/tokens", query=query)
        return TokenListResponse.from_dict(data)

    async def get(self, token_id: str) -> Token:
        """Look up a single token by composite id (e.g. ``"crypto:USDC"``)."""
        # The colon needs URL-encoding when embedded in a path segment
        from urllib.parse import quote

        data = await self._client.request(f"/v1/tokens/{quote(token_id, safe='')}")
        return Token.from_dict(data.get("data", {}))
