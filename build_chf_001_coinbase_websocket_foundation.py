from pathlib import Path
import py_compile

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_coinbase_high_frequency"
PKG.mkdir(parents=True,exist_ok=True)
(PKG/"__init__.py").write_text('REVISION="CHF-001"\n',encoding="utf-8")

BODY=r"""
from dataclasses import dataclass
from pathlib import Path

REVISION="CHF-001"
WS_URL="wss://advanced-trade-ws.coinbase.com"
PRODUCTS=("BTC-USD","ETH-USD","SOL-USD")
CHANNELS=("heartbeats","market_trades","ticker","level2")
WINDOW_SECONDS=(5,15,30,60)

@dataclass(frozen=True)
class CHFConfig:
    ws_url:str=WS_URL
    products:tuple=PRODUCTS
    channels:tuple=CHANNELS
    windows:tuple=WINDOW_SECONDS
    reconnect_min_s:float=1.0
    reconnect_max_s:float=30.0
    recv_timeout_s:float=10.0

def subscription_messages(cfg=CHFConfig()):
    out=[{"type":"subscribe","channel":"heartbeats"}]
    for ch in ("market_trades","ticker","level2"):
        out.append({"type":"subscribe","product_ids":list(cfg.products),"channel":ch})
    return out

def runtime_dir(root:Path):
    p=root/"runtime"/"coinbase_hf"
    p.mkdir(parents=True,exist_ok=True)
    return p
"""
TEST=r"""
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
"""
mod=PKG/"chf_001_foundation.py"
tst=ROOT/"test_chf_001_coinbase_websocket_foundation.py"
mod.write_text(BODY.lstrip(),encoding="utf-8")
tst.write_text(TEST.lstrip(),encoding="utf-8")
py_compile.compile(str(mod),doraise=True); py_compile.compile(str(tst),doraise=True)
print("[PASS] wrote",mod)
print("[PASS] wrote",tst)
print("[PASS] execution_authority=FALSE")
