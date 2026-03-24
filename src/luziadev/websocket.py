from __future__ import annotations

import asyncio
import json
import random
from typing import Any, Callable, Literal, Optional

WSConnectionState = Literal["disconnected", "connecting", "connected", "reconnecting"]

WSEventType = Literal[
    "connected",
    "ticker",
    "subscribed",
    "unsubscribed",
    "error",
    "disconnected",
    "reconnecting",
]


class LuziaWebSocket:
    """WebSocket client for real-time Luzia ticker streaming."""

    def __init__(
        self,
        url: str,
        *,
        headers: Optional[dict[str, str]] = None,
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 10,
        reconnect_delay_ms: int = 1000,
        max_reconnect_delay_ms: int = 30000,
        heartbeat_interval_ms: int = 30000,
    ) -> None:
        self._url = url
        self._headers = headers or {}
        self._auto_reconnect = auto_reconnect
        self._max_reconnect_attempts = max_reconnect_attempts
        self._reconnect_delay_ms = reconnect_delay_ms
        self._max_reconnect_delay_ms = max_reconnect_delay_ms
        self._heartbeat_interval_ms = heartbeat_interval_ms

        self._state: WSConnectionState = "disconnected"
        self._subscriptions: set[str] = set()
        self._listeners: dict[str, set[Callable]] = {}
        self._ws: Any = None
        self._recv_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._reconnect_attempt = 0

    @property
    def state(self) -> WSConnectionState:
        return self._state

    @property
    def subscriptions(self) -> frozenset[str]:
        return frozenset(self._subscriptions)

    def on(self, event: str, callback: Callable) -> LuziaWebSocket:
        if event not in self._listeners:
            self._listeners[event] = set()
        self._listeners[event].add(callback)
        return self

    def off(self, event: str, callback: Callable) -> LuziaWebSocket:
        if event in self._listeners:
            self._listeners[event].discard(callback)
        return self

    def _emit(self, event: str, data: Any = None) -> None:
        for callback in self._listeners.get(event, set()):
            try:
                result = callback(data)
                if asyncio.iscoroutine(result):
                    asyncio.ensure_future(result)
            except Exception:
                pass

    async def connect(self) -> LuziaWebSocket:
        try:
            import websockets
        except ImportError:
            raise ImportError(
                "websockets is required for WebSocket support. "
                "Install it with: pip install luziadev[websocket]"
            )

        self._state = "connecting"
        try:
            self._ws = await websockets.connect(
                self._url,
                additional_headers=self._headers,
            )
        except Exception as exc:
            self._state = "disconnected"
            self._emit("error", {"type": "error", "code": "network", "message": str(exc)})
            raise

        self._reconnect_attempt = 0
        self._recv_task = asyncio.create_task(self._recv_loop())

        if self._heartbeat_interval_ms > 0:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        return self

    def disconnect(self) -> None:
        self._auto_reconnect = False
        self._cleanup()
        self._state = "disconnected"
        self._emit("disconnected", {"code": 1000, "reason": "client disconnect"})

    def subscribe(self, channels: list[str]) -> None:
        if not channels:
            return
        self._subscriptions.update(channels)
        if self._ws and self._state == "connected":
            self._send({"type": "subscribe", "channels": channels})

    def unsubscribe(self, channels: list[str]) -> None:
        if not channels:
            return
        self._subscriptions -= set(channels)
        if self._ws and self._state == "connected":
            self._send({"type": "unsubscribe", "channels": channels})

    def ping(self) -> None:
        if self._ws and self._state == "connected":
            self._send({"type": "ping"})

    def _send(self, data: dict) -> None:
        if self._ws:
            asyncio.ensure_future(self._ws.send(json.dumps(data)))

    def _cleanup(self) -> None:
        if self._recv_task and not self._recv_task.done():
            self._recv_task.cancel()
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
        if self._ws:
            asyncio.ensure_future(self._ws.close())
            self._ws = None

    async def _recv_loop(self) -> None:
        try:
            async for raw_message in self._ws:
                try:
                    message = json.loads(raw_message)
                except json.JSONDecodeError:
                    continue

                msg_type = message.get("type")

                if msg_type == "connected":
                    self._state = "connected"
                    self._emit("connected", message)
                    if self._subscriptions:
                        self._send({"type": "subscribe", "channels": list(self._subscriptions)})
                elif msg_type == "ticker":
                    self._emit("ticker", message)
                elif msg_type == "subscribed":
                    self._emit("subscribed", message)
                elif msg_type == "unsubscribed":
                    self._emit("unsubscribed", message)
                elif msg_type == "error":
                    self._emit("error", message)
                elif msg_type == "pong":
                    self._emit("pong", message)

        except asyncio.CancelledError:
            return
        except Exception:
            pass

        if self._auto_reconnect:
            await self._reconnect()
        else:
            self._state = "disconnected"
            self._emit("disconnected", {"code": 1006, "reason": "connection lost"})

    async def _heartbeat_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self._heartbeat_interval_ms / 1000)
                if self._state == "connected":
                    self.ping()
        except asyncio.CancelledError:
            pass

    async def _reconnect(self) -> None:
        max_attempts = self._max_reconnect_attempts
        if max_attempts > 0 and self._reconnect_attempt >= max_attempts:
            self._state = "disconnected"
            self._emit("disconnected", {"code": 1006, "reason": "max reconnect attempts reached"})
            return

        self._state = "reconnecting"
        self._reconnect_attempt += 1

        delay = self._reconnect_delay_ms * (2 ** (self._reconnect_attempt - 1))
        delay = min(delay, self._max_reconnect_delay_ms)
        delay *= 0.5 + random.random()

        self._emit("reconnecting", {
            "attempt": self._reconnect_attempt,
            "delayMs": delay,
        })

        await asyncio.sleep(delay / 1000)

        try:
            import websockets

            self._ws = await websockets.connect(
                self._url,
                additional_headers=self._headers,
            )

            self._recv_task = asyncio.create_task(self._recv_loop())

            if self._heartbeat_interval_ms > 0:
                if self._heartbeat_task and not self._heartbeat_task.done():
                    self._heartbeat_task.cancel()
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        except Exception:
            await self._reconnect()
