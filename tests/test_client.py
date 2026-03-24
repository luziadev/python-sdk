import pytest
import httpx
import respx

from luziadev import Luzia, LuziaError


def test_requires_api_key():
    with pytest.raises(ValueError, match="api_key is required"):
        Luzia("")


def test_symbol_to_url():
    assert Luzia.symbol_to_url("BTC/USDT") == "BTC-USDT"
    assert Luzia.symbol_to_url("ETH/BTC") == "ETH-BTC"


def test_symbol_from_url():
    assert Luzia.symbol_from_url("BTC-USDT") == "BTC/USDT"
    assert Luzia.symbol_from_url("ETH-BTC") == "ETH/BTC"


def test_rate_limit_info_initially_none():
    client = Luzia("lz_test_key_12345678901234567890")
    assert client.rate_limit_info is None


@respx.mock
@pytest.mark.asyncio
async def test_auth_header_sent():
    route = respx.get("https://api.luzia.dev/v1/exchanges").mock(
        return_value=httpx.Response(200, json={"exchanges": []})
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        await client.exchanges.list()

    assert route.called
    request = route.calls[0].request
    assert request.headers["authorization"] == "Bearer lz_test_key_12345678901234567890"


@respx.mock
@pytest.mark.asyncio
async def test_rate_limit_parsed_from_headers():
    respx.get("https://api.luzia.dev/v1/exchanges").mock(
        return_value=httpx.Response(
            200,
            json={"exchanges": []},
            headers={
                "x-ratelimit-limit": "100",
                "x-ratelimit-remaining": "95",
                "x-ratelimit-reset": "1704067260",
            },
        )
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        await client.exchanges.list()
        info = client.rate_limit_info
        assert info is not None
        assert info.limit == 100
        assert info.remaining == 95
        assert info.reset == 1704067260


@respx.mock
@pytest.mark.asyncio
async def test_401_raises_auth_error():
    respx.get("https://api.luzia.dev/v1/exchanges").mock(
        return_value=httpx.Response(
            401,
            json={"error": "Unauthorized", "message": "Invalid API key"},
        )
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        with pytest.raises(LuziaError) as exc_info:
            await client.exchanges.list()
        assert exc_info.value.code == "auth"
        assert exc_info.value.status == 401


@respx.mock
@pytest.mark.asyncio
async def test_404_raises_not_found_error():
    respx.get("https://api.luzia.dev/v1/ticker/binance/BTC-USDT").mock(
        return_value=httpx.Response(
            404,
            json={"error": "Not Found", "message": "Symbol not found"},
        )
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        with pytest.raises(LuziaError) as exc_info:
            await client.tickers.get("binance", "BTC/USDT")
        assert exc_info.value.code == "not_found"


@respx.mock
@pytest.mark.asyncio
async def test_429_raises_rate_limit_error():
    respx.get("https://api.luzia.dev/v1/exchanges").mock(
        return_value=httpx.Response(
            429,
            json={"error": "Too Many Requests", "message": "Rate limit exceeded"},
            headers={
                "retry-after": "30",
                "x-ratelimit-limit": "100",
                "x-ratelimit-remaining": "0",
                "x-ratelimit-reset": "1704067260",
            },
        )
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        with pytest.raises(LuziaError) as exc_info:
            await client.exchanges.list()
        assert exc_info.value.code == "rate_limit"
        assert exc_info.value.retry_after == 30


@respx.mock
@pytest.mark.asyncio
async def test_custom_base_url():
    route = respx.get("https://custom.api.dev/v1/exchanges").mock(
        return_value=httpx.Response(200, json={"exchanges": []})
    )

    async with Luzia("lz_test_key_12345678901234567890", base_url="https://custom.api.dev") as client:
        await client.exchanges.list()

    assert route.called


@pytest.mark.asyncio
async def test_context_manager():
    client = Luzia("lz_test_key_12345678901234567890")
    async with client:
        assert client is not None
    # Client should be closed after context exit
