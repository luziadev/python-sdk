# Changelog

All notable changes to `luziadev` (the Luzia Python SDK) will be documented in
this file. Versions prior to 1.3.0 predate this changelog.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-05-21

Aligns the SDK with the Luzia 1.3.0 API.

### Added

- **`tokens` resource:** `tokens.list(...)` and `tokens.get(id)` for canonical
  assets and on-chain tokens (`/v1/tokens`, `/v1/tokens/:id`)
- **`fiat_currencies` resource:** `fiat_currencies.list(...)` and
  `fiat_currencies.get(code)` for ISO 4217 fiat currencies referenced by markets
  (`/v1/fiat-currencies`, `/v1/fiat-currencies/:code`)
- **DEX support:** `exchanges.list(type="cex"|"dex")` filter; DEX metadata on
  `Exchange` (`type`, `chain_id`, `dex_id`) and `Market` (`type="dex"`,
  `chain_id`, `pool_address`, `pool_type`, `base_token`, `quote_token`)
- **Tokenized equities (xStocks):** `markets.list(type="stock")` with mixed-case
  base/quote handling for tickers such as `AAPLx`
- New models: `Token`, `FiatCurrency`, `Pagination`, `TokenListResponse`,
  `FiatCurrencyListResponse`

### Fixed

- Exported `TokensResource` and `FiatCurrenciesResource` from
  `luziadev.resources` (they were wired into the client but missing from the
  subpackage's `__all__`)
- REST timestamp fields are now correctly typed as `int` (Unix milliseconds):
  `Ticker.timestamp`, `OHLCVCandle.timestamp`, `OHLCVResponse.start` / `end`.
  WebSocket message timestamps remain RFC 3339 strings.
