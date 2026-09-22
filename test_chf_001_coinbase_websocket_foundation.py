from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_001_foundation import *
ROOT=Path.cwd()
assert WS_URL=="wss://advanced-trade-ws.coinbase.com"
assert PRODUCTS==("BTC-USD","ETH-USD","SOL-USD")
assert WINDOW_SECONDS==(5,15,30,60)
msgs=subscription_messages()
assert msgs[0]["channel"]=="heartbeats"
assert {m["channel"] for m in msgs}=={"heartbeats","market_trades","ticker","level2"}
assert runtime_dir(ROOT).exists()
print("[ENDPOINT]",WS_URL)
print("[PRODUCTS]",PRODUCTS)
print("[CHANNELS]",CHANNELS)
print("[WINDOWS]",WINDOW_SECONDS)
print("[PASS] CHF-001 Coinbase WebSocket foundation certified")
