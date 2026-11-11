# hedgehood-maker-py

**Hedgehood maker SDKs:** [Python](https://github.com/0xHedgeHood/hedgehood-maker-py) · [TypeScript](https://github.com/0xHedgeHood/hedgehood-maker-ts) · [Go + CLI](https://github.com/0xHedgeHood/hedgehood-maker-go) · [maker guide, test vectors](https://github.com/0xHedgeHood/sdks)

`hedgehood-maker`: Python SDK for market makers on the Hedgehood options RFQ gateway. Earn upfront users write covered
calls and cash-secured puts on Robinhood Chain stock tokens; makers buy them with **firm EIP-712 quotes they sign
themselves**, and the user fills the winning quote on chain through `RfqSettler`. The gateway never holds your funds or
keys and cannot change a quote. There is no last look.

> **Testnet only** (Robinhood Chain testnet, chainId 46630). The contracts (`OptionsCore`, `RfqSettler`) are not yet
> audited; mainnet addresses follow the launch. Nothing in this repository is a security review. The protocol
> reference (going live, funding, fees, timing, scorecard, wire format) is the
> [maker guide](https://github.com/0xHedgeHood/sdks/blob/main/docs/MAKER_GUIDE.md).

- `MakerClient`: login, your pricer per request within the 2-second window (sync or async), quote building and signing
  (fresh nonce, current epoch, all-or-nothing), the gateway's checks locally, events, reconnect with backoff.
- `eip712`: `quote_digest`, `sign_quote`, `series_id`, byte-equal to `RfqSettler.quoteDigest` (tests pin the
  [golden vectors](https://github.com/0xHedgeHood/sdks/blob/main/vectors/goldens.json) shared with the Solidity,
  gateway, Go and TypeScript implementations).
- `settler`: unsigned transactions for `setSigner`, `approve`, `deposit`, `withdraw`, `increaseEpoch`,
  `invalidateNonces`, `linkMaker`, `OptionsCore.setOperator` and `redeemLong`. The SDK never signs or sends a
  transaction; you review and send each one.
- `rpc.Reader`: read-only `eth_call`s (epoch, signer delegation, balances, allowances, fees) and `can_sell`, which tells
  you whether you hold a long before quoting an early close.
- `fees`: the settler's fee (12.5 % of the premium, capped at 1 % of the notional) and pro-rata math.

## Install

```
pip install hedgehood-maker      # or: pip install "git+https://github.com/0xHedgeHood/hedgehood-maker-py"
```

Python 3.10+, dependencies `eth-account` and `websockets`.

## Quickstart

1. Print the setup transactions, review them and send them yourself:

   ```
   python examples/onboard.py --maker 0xYourMaker --signer 0xYourHotKey --signer-days 7 --deposit 1000 --rpc
   ```

2. Quote:

   ```python
   import asyncio, os
   from hedgehood_maker import MAKER_BUYS, RFQ, TESTNET, Decline, MakerClient
   from hedgehood_maker.fees import notional

   def price(rfq: RFQ):
       if rfq.side != MAKER_BUYS:
           return Decline("no_inventory")             # closes: see examples/simple_maker.py --sell
       return notional(rfq.amount, rfq.series.strike) * 40 // 10_000   # premium, USDG raw, fee excluded

   client = MakerClient(
       TESTNET.gateway_ws,
       os.environ["HEDGEHOOD_SIGNER_KEY"],              # the maker key or its delegated hot key
       price,
       maker="0xYourMaker",                             # omit when the key is the maker itself
       chain_id=TESTNET.chain_id, settler=TESTNET.settler,
       on_event=lambda f: print(f.type, f.raw),         # won, lost, fill, rejected, ...
   )
   asyncio.run(client.run())
   ```

   The pricer may be sync (run in a thread) or async. It returns a premium (int), a `Quote` from
   `client.build_quote(...)`, or a decline. [`examples/simple_maker.py`](examples/simple_maker.py) is fuller:
   Black-Scholes or fixed bps, fee-aware, and with `--sell` it quotes early closes only for longs it holds:

   ```
   export HEDGEHOOD_SIGNER_KEY=...
   python examples/simple_maker.py --mode vol --vol 0.6 --spot TSLA=390 --edge 0.05 --sell --external self
   ```

## Testnet

| | |
|---|---|
| Chain | Robinhood Chain testnet, chainId 46630, RPC `https://rpc.testnet.chain.robinhood.com` |
| Gateway (makers) | `wss://testnet-rfq.hedgehood.io/v1/maker/ws` |
| RfqSettler | `0xda43b0933031e41D5B367E1807536FcF4ebdEE7e` |
| OptionsCore | `0xde5ce903254E9597822D5456a82a25640285B8B4` |
| Quote token (test USDG, 6 decimals) | `0x850DE815d41F6983Aaf09247f9a465c0aefff04C` |
| Scorecard | `https://testnet-rfq.hedgehood.io/v1/makers` |

## Development

```
pip install -e ".[dev]" && ruff check . && pytest                                    # offline
HEDGEHOOD_LIVE_RPC=https://rpc.testnet.chain.robinhood.com pytest tests/test_live.py  # opt-in, read-only
HEDGEHOOD_VECTORS=/path/to/sdks/vectors/goldens.json pytest tests/test_vectors.py    # the shared vectors (CI does this)
```

## License

MIT, see [LICENSE](LICENSE).
