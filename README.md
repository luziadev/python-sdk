# luziadev

Official Python SDK for the [Luzia](https://luzia.dev) cryptocurrency pricing API.

## Installation

```bash
pip install luziadev
```

For WebSocket support:

```bash
pip install luziadev[websocket]
```

## Quick Start

```python
import asyncio
from luziadev import Luzia

async def main():
    async with Luzia("lz_your_api_key") as client:
        # Get a single ticker
        ticker = await client.tickers.get("binance", "BTC/USDT")
        print(f"BTC/USDT: ${ticker.last}")

        # List all exchanges
        exchanges = await client.exchanges.list()
        for exchange in exchanges:
            print(f"{exchange.name} ({exchange.status})")

        # Get multiple tickers
        result = await client.tickers.list_filtered(
            exchange="binance",
            symbols=["BTC/USDT", "ETH/USDT"],
        )
        for t in result.tickers:
            print(f"{t.symbol}: ${t.last}")

        # Get OHLCV candles
        ohlcv = await client.history.get(
            "binance", "BTC/USDT",
            interval="1h",
            limit=24,
        )
        for candle in ohlcv.candles:
            print(f"{candle.timestamp}: O={candle.open} H={candle.high} L={candle.low} C={candle.close}")

        # List markets
        markets = await client.markets.list("binance", quote="USDT", limit=10)
        for market in markets.markets:
            print(f"{market.symbol} (active={market.active})")

asyncio.run(main())
```

## WebSocket Streaming

```python
import asyncio
from luziadev import Luzia

async def main():
    client = Luzia("lz_your_api_key")
    ws = client.create_websocket()

    ws.on("connected", lambda data: print(f"Connected! Max subs: {data['limits']['maxSubscriptions']}"))
    ws.on("ticker", lambda data: print(f"{data['data']['symbol']}: ${data['data']['last']}"))
    ws.on("error", lambda data: print(f"Error: {data['message']}"))
    ws.on("reconnecting", lambda data: print(f"Reconnecting (attempt {data['attempt']})..."))

    await ws.connect()

    ws.subscribe(["ticker:binance:BTC-USDT", "ticker:binance:ETH-USDT"])

    # Keep running
    try:
        await asyncio.sleep(3600)
    finally:
        ws.disconnect()
        await client.close()

asyncio.run(main())
```

## Error Handling

```python
from luziadev import Luzia, LuziaError

async with Luzia("lz_your_api_key") as client:
    try:
        ticker = await client.tickers.get("binance", "BTC/USDT")
    except LuziaError as e:
        match e.code:
            case "rate_limit":
                print(f"Rate limited. Retry after {e.retry_after}s")
            case "auth":
                print("Invalid API key")
            case "not_found":
                print("Symbol not found")
            case "timeout":
                print(f"Timed out after {e.timeout_ms}ms")
            case _:
                print(f"Error [{e.code}]: {e}")
```

## Retry Configuration

```python
from luziadev import Luzia, RetryOptions

client = Luzia(
    "lz_your_api_key",
    retry=RetryOptions(
        max_retries=5,
        initial_delay_ms=500,
        max_delay_ms=10000,
        backoff_multiplier=2.0,
        jitter=True,
    ),
)
```

## Rate Limit Info

```python
ticker = await client.tickers.get("binance", "BTC/USDT")

info = client.rate_limit_info
if info:
    print(f"Remaining: {info.remaining}/{info.limit}")
    print(f"Resets at: {info.reset}")
```

## Development

### Setup

```bash
cd packages/python-sdk
uv sync --extra dev --extra websocket
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_client.py

# Run a specific test
uv run pytest tests/test_client.py::test_auth_header_sent
```

### Publishing to PyPI

1. Build the package:

```bash
uv build
```

This creates `dist/luziadev-X.Y.Z.tar.gz` (sdist) and `dist/luziadev-X.Y.Z-py3-none-any.whl` (wheel).

2. Upload to Test PyPI (optional, to verify first):

```bash
uv publish --index-url https://test.pypi.org/legacy/
```

3. Upload to PyPI:

```bash
uv publish
```

You will be prompted for your PyPI credentials. To use an API token instead, pass `--token pypi-YOUR_TOKEN`.

### Versioning

Update the version in two places before publishing:

- `pyproject.toml` → `version`
- `src/luziadev/__init__.py` → `__version__`

## Requirements

- Python 3.10+
- `httpx` (installed automatically)
- `websockets` (optional, for WebSocket support)

## License

MIT
