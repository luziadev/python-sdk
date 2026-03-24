import pytest
import httpx
import respx

from luziadev import Luzia, Exchange, Ticker, Market, OHLCVCandle


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
    "timestamp": "2024-01-01T00:00:00.000Z",
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
    "timestamp": "2024-01-01T00:00:00.000Z",
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
async def test_history_get():
    respx.get("https://api.luzia.dev/v1/history/binance/BTC-USDT").mock(
        return_value=httpx.Response(200, json={
            "exchange": "binance",
            "symbol": "BTC/USDT",
            "interval": "1h",
            "candles": [MOCK_CANDLE],
            "count": 1,
            "start": "2024-01-01T00:00:00.000Z",
            "end": "2024-01-01T01:00:00.000Z",
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
