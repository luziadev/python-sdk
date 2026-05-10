from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Exchange:
    id: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    website_url: Optional[str] = None
    # Exchange kind: "cex" for centralized exchanges, "dex" for decentralized
    # exchanges (Uniswap V3/V4, Raydium, ...). May be ``None`` on legacy responses.
    type: Optional[str] = None
    # Blockchain identifier hosting this DEX (e.g. ``"solana"``, ``"ethereum"``).
    # ``None`` for CEX exchanges.
    chain_id: Optional[str] = None
    # DexScreener ``dexId`` value identifying the underlying protocol
    # (e.g. ``"raydium"``, ``"uniswapv3"``, ``"uniswapv4"``). ``None`` for CEX.
    dex_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> Exchange:
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            status=data.get("status"),
            website_url=data.get("websiteUrl"),
            type=data.get("type"),
            chain_id=data.get("chainId"),
            dex_id=data.get("dexId"),
        )


@dataclass(frozen=True)
class Ticker:
    symbol: str = ""
    exchange: str = ""
    last: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None
    quote_volume: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    timestamp: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> Ticker:
        return cls(
            symbol=data.get("symbol", ""),
            exchange=data.get("exchange", ""),
            last=data.get("last"),
            bid=data.get("bid"),
            ask=data.get("ask"),
            high=data.get("high"),
            low=data.get("low"),
            open=data.get("open"),
            close=data.get("close"),
            volume=data.get("volume"),
            quote_volume=data.get("quoteVolume"),
            change=data.get("change"),
            change_percent=data.get("changePercent"),
            timestamp=data.get("timestamp"),
        )


@dataclass(frozen=True)
class Token:
    """On-chain token referenced by a DEX market."""

    address: str = ""
    symbol: str = ""
    decimals: int = 0
    chain_id: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> Token:
        return cls(
            address=data.get("address", ""),
            symbol=data.get("symbol", ""),
            decimals=int(data.get("decimals", 0)),
            chain_id=data.get("chainId", ""),
        )


@dataclass(frozen=True)
class Market:
    symbol: str = ""
    exchange: str = ""
    base: str = ""
    base_id: str = ""
    quote: str = ""
    quote_id: str = ""
    active: bool = True
    # Market classification: "spot" | "futures" | "margin" | "stock" | "dex".
    # "stock" indicates a tokenized equity (e.g. Kraken xStocks like AAPLx/USD).
    # "dex" indicates an on-chain DEX pool (Uniswap, Raydium, ...).
    # `None` is treated as "spot" for back-compat.
    type: Optional[str] = None
    precision: Optional[dict] = None
    limits: Optional[dict] = None
    # DEX-only fields. `None` for CEX markets.
    chain_id: Optional[str] = None
    pool_address: Optional[str] = None
    pool_type: Optional[str] = None
    base_token: Optional[Token] = None
    quote_token: Optional[Token] = None

    @classmethod
    def from_dict(cls, data: dict) -> Market:
        base_token_raw = data.get("baseToken")
        quote_token_raw = data.get("quoteToken")
        return cls(
            symbol=data.get("symbol", ""),
            exchange=data.get("exchange", ""),
            base=data.get("base", ""),
            base_id=data.get("baseId", ""),
            quote=data.get("quote", ""),
            quote_id=data.get("quoteId", ""),
            active=data.get("active", True),
            type=data.get("type"),
            precision=data.get("precision"),
            limits=data.get("limits"),
            chain_id=data.get("chainId"),
            pool_address=data.get("poolAddress"),
            pool_type=data.get("poolType"),
            base_token=Token.from_dict(base_token_raw) if base_token_raw else None,
            quote_token=Token.from_dict(quote_token_raw) if quote_token_raw else None,
        )


@dataclass(frozen=True)
class OHLCVCandle:
    timestamp: Optional[str] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None
    quote_volume: Optional[float] = None
    trades: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> OHLCVCandle:
        return cls(
            timestamp=data.get("timestamp"),
            open=data.get("open"),
            high=data.get("high"),
            low=data.get("low"),
            close=data.get("close"),
            volume=data.get("volume"),
            quote_volume=data.get("quoteVolume"),
            trades=data.get("trades"),
        )


@dataclass(frozen=True)
class RateLimitInfo:
    limit: int = 0
    remaining: int = 0
    reset: int = 0
    daily_limit: Optional[int] = None
    daily_remaining: Optional[int] = None
    daily_reset: Optional[int] = None


@dataclass
class TickerListResponse:
    tickers: list[Ticker]
    total: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> TickerListResponse:
        return cls(
            tickers=[Ticker.from_dict(t) for t in data.get("tickers", [])],
            total=data.get("total"),
            limit=data.get("limit"),
            offset=data.get("offset"),
        )


@dataclass
class MarketListResponse:
    markets: list[Market]
    total: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> MarketListResponse:
        return cls(
            markets=[Market.from_dict(m) for m in data.get("markets", [])],
            total=data.get("total"),
            limit=data.get("limit"),
            offset=data.get("offset"),
        )


@dataclass
class OHLCVResponse:
    exchange: Optional[str] = None
    symbol: Optional[str] = None
    interval: Optional[str] = None
    candles: list[OHLCVCandle] | None = None
    count: Optional[int] = None
    start: Optional[str] = None
    end: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> OHLCVResponse:
        candles_raw = data.get("candles")
        return cls(
            exchange=data.get("exchange"),
            symbol=data.get("symbol"),
            interval=data.get("interval"),
            candles=[OHLCVCandle.from_dict(c) for c in candles_raw] if candles_raw else [],
            count=data.get("count"),
            start=data.get("start"),
            end=data.get("end"),
        )
