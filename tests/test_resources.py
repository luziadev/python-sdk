import pytest
import httpx
import respx

from luziadev import (
    Exchange,
    FiatCurrency,
    Luzia,
    Market,
    OHLCVCandle,
    Ticker,
    Token,
)


MOCK_EXCHANGE = {
    "id": "binance",
    "name": "Binance",
    "status": "operational",
    "websiteUrl": "https://binance.com",
}

MOCK_TICKER = {
    "symbol": "BTC/USDT",
    "exchange": "binance",
    "last": 43250.50,
    "bid": 43250.00,
    "ask": 43251.00,
    "high": 44000.00,
    "low": 42000.00,
    "open": 42500.00,
    "close": 43250.50,
    "volume": 12345.678,
    "quoteVolume": 534123456.78,
    "change": 750.50,
    "changePercent": 1.76,
    "timestamp": 1704067200000,
}

MOCK_MARKET = {
    "symbol": "BTC/USDT",
    "exchange": "binance",
    "base": "BTC",
    "baseId": "BTC",
    "quote": "USDT",
    "quoteId": "USDT",
    "active": True,
    "precision": {"amount": 8, "price": 2},
    "limits": {"amount": {"min": 0.00001, "max": 1000}},
}

MOCK_CANDLE = {
    "timestamp": 1704067200000,
    "open": 43000.0,
    "high": 43500.0,
    "low": 42800.0,
    "close": 43250.0,
    "volume": 123.45,
    "quoteVolume": 5345678.9,
    "trades": 342,
}


@respx.mock
@pytest.mark.asyncio
async def test_exchanges_list():
    respx.get("https://api.luzia.dev/v1/exchanges").mock(
        return_value=httpx.Response(200, json={"exchanges": [MOCK_EXCHANGE]})
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        exchanges = await client.exchanges.list()
        assert len(exchanges) == 1
        ex = exchanges[0]
        assert isinstance(ex, Exchange)
        assert ex.id == "binance"
        assert ex.name == "Binance"
        assert ex.status == "operational"
        assert ex.website_url == "https://binance.com"


@respx.mock
@pytest.mark.asyncio
async def test_tickers_get():
    respx.get("https://api.luzia.dev/v1/ticker/binance/BTC-USDT").mock(
        return_value=httpx.Response(200, json=MOCK_TICKER)
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        ticker = await client.tickers.get("binance", "BTC/USDT")
        assert isinstance(ticker, Ticker)
        assert ticker.symbol == "BTC/USDT"
        assert ticker.exchange == "binance"
        assert ticker.last == 43250.50
        assert ticker.quote_volume == 534123456.78
        assert ticker.change_percent == 1.76


@respx.mock
@pytest.mark.asyncio
async def test_tickers_list():
    respx.get("https://api.luzia.dev/v1/tickers/binance").mock(
        return_value=httpx.Response(200, json={
            "tickers": [MOCK_TICKER],
            "total": 1,
            "limit": 20,
            "offset": 0,
        })
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        result = await client.tickers.list("binance", limit=20)
        assert len(result.tickers) == 1
        assert result.total == 1
        assert result.limit == 20


@respx.mock
@pytest.mark.asyncio
async def test_tickers_list_filtered():
    route = respx.get("https://api.luzia.dev/v1/tickers").mock(
        return_value=httpx.Response(200, json={
            "tickers": [MOCK_TICKER],
            "total": 1,
            "limit": 20,
            "offset": 0,
        })
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        result = await client.tickers.list_filtered(
            exchange="binance",
            symbols=["BTC/USDT", "ETH/USDT"],
        )
        assert len(result.tickers) == 1

    request = route.calls[0].request
    assert "exchange=binance" in str(request.url)
    assert "symbols=BTC-USDT%2CETH-USDT" in str(request.url)


@respx.mock
@pytest.mark.asyncio
async def test_markets_list():
    respx.get("https://api.luzia.dev/v1/markets/binance").mock(
        return_value=httpx.Response(200, json={
            "markets": [MOCK_MARKET],
            "total": 1,
            "limit": 100,
            "offset": 0,
        })
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        result = await client.markets.list("binance", quote="USDT")
        assert len(result.markets) == 1
        market = result.markets[0]
        assert isinstance(market, Market)
        assert market.symbol == "BTC/USDT"
        assert market.base_id == "BTC"
        assert market.quote_id == "USDT"
        assert market.active is True
        assert market.precision == {"amount": 8, "price": 2}


@respx.mock
@pytest.mark.asyncio
async def test_markets_list_xstocks():
    """xStock markets carry type='stock' and the type filter is passed through."""
    route = respx.get("https://api.luzia.dev/v1/markets/kraken").mock(
        return_value=httpx.Response(200, json={
            "markets": [{
                "symbol": "AAPLx/USD",
                "exchange": "kraken",
                "base": "AAPLx",
                "quote": "USD",
                "baseId": "AAPLx",
                "quoteId": "ZUSD",
                "active": True,
                "type": "stock",
                "precision": {"amount": 8, "price": 2},
                "limits": {"amount": {"min": 0.0001, "max": 0}, "price": {"min": 0, "max": 0}},
            }],
            "total": 1,
            "limit": 100,
            "offset": 0,
        })
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        result = await client.markets.list("kraken", type="stock", base="AAPLx")

    assert len(result.markets) == 1
    market = result.markets[0]
    assert market.symbol == "AAPLx/USD"
    assert market.base == "AAPLx"
    assert market.type == "stock"
    # Mixed-case base must NOT be uppercased — Kraken stores "AAPLx", not "AAPLX".
    request_url = str(route.calls[0].request.url)
    assert "base=AAPLx" in request_url
    assert "type=stock" in request_url


MOCK_DEX_EXCHANGE = {
    "id": "raydium-solana",
    "name": "Raydium (Solana)",
    "status": "operational",
    "websiteUrl": "https://raydium.io",
    "type": "dex",
    "chainId": "solana",
    "dexId": "raydium",
}

MOCK_DEX_MARKET = {
    "symbol": "TSLAx/USDC",
    "exchange": "raydium-solana",
    "base": "TSLAx",
    "quote": "USDC",
    "active": True,
    "type": "dex",
    "chainId": "solana",
    "poolAddress": "6UmmUiYoBjSrhakAobJw8BvkmJtDVxaeBtbt7rxWo1mg",
    "poolType": "clmm",
    "baseToken": {
        "address": "XsbEhLAtcf6HdfpFZ5xEMdqW8nfAvcsP5bdudRLJzJp",
        "symbol": "TSLAx",
        "decimals": 8,
        "chainId": "solana",
    },
    "quoteToken": {
        "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
        "symbol": "USDC",
        "decimals": 6,
        "chainId": "solana",
    },
}


@respx.mock
@pytest.mark.asyncio
async def test_exchanges_list_dex_filter():
    """Passing type='dex' forwards the query parameter and parses DEX fields."""
    route = respx.get("https://api.luzia.dev/v1/exchanges").mock(
        return_value=httpx.Response(200, json={"exchanges": [MOCK_DEX_EXCHANGE]})
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        exchanges = await client.exchanges.list(type="dex")

    assert len(exchanges) == 1
    ex = exchanges[0]
    assert isinstance(ex, Exchange)
    assert ex.id == "raydium-solana"
    assert ex.type == "dex"
    assert ex.chain_id == "solana"
    assert ex.dex_id == "raydium"

    request_url = str(route.calls[0].request.url)
    assert "type=dex" in request_url


@respx.mock
@pytest.mark.asyncio
async def test_markets_list_dex():
    """DEX markets expose pool/chain metadata and parsed Token objects."""
    respx.get("https://api.luzia.dev/v1/markets/raydium-solana").mock(
        return_value=httpx.Response(200, json={
            "markets": [MOCK_DEX_MARKET],
            "total": 1,
            "limit": 100,
            "offset": 0,
        })
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        result = await client.markets.list("raydium-solana")

    assert len(result.markets) == 1
    market = result.markets[0]
    assert isinstance(market, Market)
    assert market.symbol == "TSLAx/USDC"
    assert market.type == "dex"
    assert market.chain_id == "solana"
    assert market.pool_address == "6UmmUiYoBjSrhakAobJw8BvkmJtDVxaeBtbt7rxWo1mg"
    assert market.pool_type == "clmm"

    assert isinstance(market.base_token, Token)
    assert market.base_token.symbol == "TSLAx"
    assert market.base_token.decimals == 8
    assert market.base_token.chain_id == "solana"

    assert isinstance(market.quote_token, Token)
    assert market.quote_token.address == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    assert market.quote_token.symbol == "USDC"


@respx.mock
@pytest.mark.asyncio
async def test_history_get():
    respx.get("https://api.luzia.dev/v1/history/binance/BTC-USDT").mock(
        return_value=httpx.Response(200, json={
            "exchange": "binance",
            "symbol": "BTC/USDT",
            "interval": "1h",
            "candles": [MOCK_CANDLE],
            "count": 1,
            "start": 1704067200000,
            "end": 1704070800000,
        })
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        result = await client.history.get(
            "binance", "BTC/USDT",
            interval="1h",
            limit=24,
        )
        assert result.exchange == "binance"
        assert result.interval == "1h"
        assert len(result.candles) == 1
        candle = result.candles[0]
        assert isinstance(candle, OHLCVCandle)
        assert candle.open == 43000.0
        assert candle.trades == 342
        assert candle.quote_volume == 5345678.9


MOCK_TOKEN = {
    "id": "crypto:USDC",
    "symbol": "USDC",
    "name": "USD Coin",
    "decimals": 6,
    "address": None,
    "chainId": None,
    "totalSupply": None,
    "logoUrl": None,
    "tags": ["stablecoin"],
    "canonicalId": None,
}

MOCK_FIAT = {
    "code": "USD",
    "name": "United States Dollar",
    "symbol": "$",
    "enabled": True,
}


@respx.mock
@pytest.mark.asyncio
async def test_tokens_list():
    """tokens.list parses data + pagination and forwards filter query params."""
    route = respx.get("https://api.luzia.dev/v1/tokens").mock(
        return_value=httpx.Response(200, json={
            "data": [MOCK_TOKEN],
            "pagination": {"total": 1, "page": 1, "limit": 20, "pages": 1},
        })
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        result = await client.tokens.list(
            search="USDC", chain_id="solana", has_chain=True, page=1, limit=20
        )

    assert len(result.data) == 1
    token = result.data[0]
    assert isinstance(token, Token)
    assert token.id == "crypto:USDC"
    assert token.symbol == "USDC"
    assert token.tags == ("stablecoin",)
    assert result.pagination.total == 1

    request_url = str(route.calls[0].request.url)
    assert "search=USDC" in request_url
    assert "chainId=solana" in request_url
    assert "hasChain=true" in request_url
    assert "limit=20" in request_url


@respx.mock
@pytest.mark.asyncio
async def test_tokens_get():
    """tokens.get URL-encodes the composite id and unwraps the data envelope."""
    route = respx.get(url__startswith="https://api.luzia.dev/v1/tokens/").mock(
        return_value=httpx.Response(200, json={"data": MOCK_TOKEN})
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        token = await client.tokens.get("crypto:USDC")

    assert isinstance(token, Token)
    assert token.id == "crypto:USDC"
    assert token.decimals == 6
    # The colon must be percent-encoded in the path segment.
    assert "crypto%3AUSDC" in str(route.calls[0].request.url)


@respx.mock
@pytest.mark.asyncio
async def test_fiat_currencies_list():
    """fiat_currencies.list parses data + pagination and maps the enabled filter."""
    route = respx.get("https://api.luzia.dev/v1/fiat-currencies").mock(
        return_value=httpx.Response(200, json={
            "data": [MOCK_FIAT],
            "pagination": {"total": 38, "page": 1, "limit": 50, "pages": 1},
        })
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        result = await client.fiat_currencies.list(search="dollar", enabled="all")

    assert len(result.data) == 1
    currency = result.data[0]
    assert isinstance(currency, FiatCurrency)
    assert currency.code == "USD"
    assert currency.name == "United States Dollar"
    assert result.pagination.total == 38

    request_url = str(route.calls[0].request.url)
    assert "search=dollar" in request_url
    assert "enabled=all" in request_url


@respx.mock
@pytest.mark.asyncio
async def test_fiat_currencies_get():
    """fiat_currencies.get upper-cases the ISO code and unwraps the data envelope."""
    route = respx.get("https://api.luzia.dev/v1/fiat-currencies/USD").mock(
        return_value=httpx.Response(200, json={"data": MOCK_FIAT})
    )

    async with Luzia("lz_test_key_12345678901234567890") as client:
        currency = await client.fiat_currencies.get("usd")

    assert isinstance(currency, FiatCurrency)
    assert currency.code == "USD"
    assert currency.symbol == "$"
    assert "/v1/fiat-currencies/USD" in str(route.calls[0].request.url)
