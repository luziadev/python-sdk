import pytest

from luziadev.websocket import LuziaWebSocket


def test_initial_state():
    ws = LuziaWebSocket(url="wss://api.luzia.dev/v1/ws")
    assert ws.state == "disconnected"
    assert ws.subscriptions == frozenset()


def test_on_off_listeners():
    ws = LuziaWebSocket(url="wss://api.luzia.dev/v1/ws")
    events = []

    def handler(data):
        events.append(data)

    ws.on("ticker", handler)
    ws._emit("ticker", {"type": "ticker", "data": {"last": 100}})
    assert len(events) == 1

    ws.off("ticker", handler)
    ws._emit("ticker", {"type": "ticker", "data": {"last": 200}})
    assert len(events) == 1  # No new events after unsubscribing


def test_on_returns_self():
    ws = LuziaWebSocket(url="wss://api.luzia.dev/v1/ws")
    result = ws.on("ticker", lambda data: None)
    assert result is ws


def test_subscribe_tracks_channels():
    ws = LuziaWebSocket(url="wss://api.luzia.dev/v1/ws")
    ws.subscribe(["ticker:binance:BTC-USDT", "ticker:binance:ETH-USDT"])
    assert ws.subscriptions == frozenset(["ticker:binance:BTC-USDT", "ticker:binance:ETH-USDT"])


def test_unsubscribe_removes_channels():
    ws = LuziaWebSocket(url="wss://api.luzia.dev/v1/ws")
    ws.subscribe(["ticker:binance:BTC-USDT", "ticker:binance:ETH-USDT"])
    ws.unsubscribe(["ticker:binance:BTC-USDT"])
    assert ws.subscriptions == frozenset(["ticker:binance:ETH-USDT"])


def test_subscribe_empty_list():
    ws = LuziaWebSocket(url="wss://api.luzia.dev/v1/ws")
    ws.subscribe([])
    assert ws.subscriptions == frozenset()


def test_multiple_listeners_same_event():
    ws = LuziaWebSocket(url="wss://api.luzia.dev/v1/ws")
    results = []

    ws.on("connected", lambda d: results.append("a"))
    ws.on("connected", lambda d: results.append("b"))

    ws._emit("connected", {"type": "connected"})
    assert len(results) == 2


def test_emit_unknown_event_no_error():
    ws = LuziaWebSocket(url="wss://api.luzia.dev/v1/ws")
    ws._emit("nonexistent", {"data": "test"})  # Should not raise


def test_disconnect_sets_state():
    ws = LuziaWebSocket(url="wss://api.luzia.dev/v1/ws")
    events = []
    ws.on("disconnected", lambda d: events.append(d))
    ws.disconnect()
    assert ws.state == "disconnected"
    assert len(events) == 1
    assert events[0]["code"] == 1000


@pytest.mark.asyncio
async def test_connect_without_websockets_raises():
    ws = LuziaWebSocket(url="wss://api.luzia.dev/v1/ws")
    # This test validates the import error path.
    # If websockets IS installed, it will try to connect and fail on the URL.
    # Either way the test validates the connect() path.
    with pytest.raises(Exception):
        await ws.connect()
