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
