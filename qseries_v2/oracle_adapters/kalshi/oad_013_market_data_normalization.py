from dataclasses import dataclass
from decimal import Decimal
from types import MappingProxyType
from qseries_v2.oracle_adapters.oad_003_canonical_event import build_canonical_source_event

OAD_013_BUILD_ID="OAD-013"
OAD_013_REVISION="OAD_013_KALSHI_ORDERBOOK_TRADE_TICKER_NORMALIZATION_V1"

@dataclass(frozen=True)
class NormalizedKalshiMarketData:
    event_type:str
    market_ticker:str
    sid:int
    seq:int
    source_event_ns:int
    canonical_event_hash:str

def _source_ns(raw,receive_ns):
    msg=raw.get("msg") or {}
    if "ts_ms" in msg: return int(msg["ts_ms"])*1_000_000
    if "ts" in msg and isinstance(msg["ts"],(int,float)): return int(msg["ts"])*1_000_000_000
    return int(receive_ns)

def normalize_kalshi_market_data(raw,oracle_receive_ns):
    typ=str(raw.get("type",""))
    if typ not in ("orderbook_snapshot","orderbook_delta","ticker","trade"):
        raise ValueError("unsupported Kalshi market-data event")
    msg=raw.get("msg") or {}
    ticker=str(msg.get("market_ticker") or msg.get("ticker") or "")
    if not ticker: raise ValueError("market ticker required")
    sid=int(raw.get("sid",0)); seq=int(raw.get("seq",0))
    if sid<0 or seq<0: raise ValueError("non-negative sid/seq required")
    src=_source_ns(raw,oracle_receive_ns)
    if src>int(oracle_receive_ns): src=int(oracle_receive_ns)
    canonical=build_canonical_source_event(
        "kalshi_predictions_universal","kalshi",ticker,typ,src,int(oracle_receive_ns),seq,raw
    )
    return NormalizedKalshiMarketData(typ,ticker,sid,seq,src,canonical.envelope_hash)

def build_oad_013_certification_manifest():
    return MappingProxyType({"build_id":OAD_013_BUILD_ID,"revision":OAD_013_REVISION,
        "events":("orderbook_snapshot","orderbook_delta","ticker","trade"),"fixed_point_safe":True,"execution":False})

def verify_oad_013_kalshi_orderbook_trade_ticker_normalization():
    raw={"type":"orderbook_delta","sid":2,"seq":3,"msg":{"market_ticker":"KXTEST","price_dollars":"0.960","delta_fp":"-54.00","side":"yes","ts_ms":100}}
    x=normalize_kalshi_market_data(raw,100_000_001)
    return x.event_type=="orderbook_delta" and x.market_ticker=="KXTEST" and x.seq==3 and len(x.canonical_event_hash)==64
