from dataclasses import dataclass
from .ois_031_low_latency_event_intake import CanonicalMarketEvent

OIS_032_BUILD_ID="OIS-032"
OIS_032_REVISION="OIS_032_MARKET_EVENT_CLASSIFICATION_V1"

EVENT_CLASSES=(
    "TRADE","BOOK_ADD","BOOK_REMOVE","BOOK_SIZE_CHANGE","BEST_PRICE_CHANGE",
    "SPREAD_CHANGE","LIQUIDITY_ARRIVAL","LIQUIDITY_WITHDRAWAL","ABNORMAL_SIZE",
    "TRADE_BURST","PRICE_JUMP","MARKET_STATUS_CHANGE","NEW_LISTING",
    "SETTLEMENT","CROSS_MARKET_DIVERGENCE","OPPORTUNITY_TRIGGER","OTHER"
)

@dataclass(frozen=True)
class ClassifiedMarketEvent:
    event_hash:str
    event_class:str
    urgency:str

def classify_market_event(event):
    if not isinstance(event,CanonicalMarketEvent):
        raise ValueError("canonical market event required")
    x=event.event_type.strip().lower()
    mapping={
        "trade":"TRADE","book_add":"BOOK_ADD","book_remove":"BOOK_REMOVE",
        "book_size_change":"BOOK_SIZE_CHANGE","best_price_change":"BEST_PRICE_CHANGE",
        "spread_change":"SPREAD_CHANGE","liquidity_arrival":"LIQUIDITY_ARRIVAL",
        "liquidity_withdrawal":"LIQUIDITY_WITHDRAWAL","abnormal_size":"ABNORMAL_SIZE",
        "trade_burst":"TRADE_BURST","price_jump":"PRICE_JUMP","market_status":"MARKET_STATUS_CHANGE",
        "new_listing":"NEW_LISTING","settlement":"SETTLEMENT",
        "cross_market_divergence":"CROSS_MARKET_DIVERGENCE","opportunity_trigger":"OPPORTUNITY_TRIGGER",
    }
    cls=mapping.get(x,"OTHER")
    urgency="INTERRUPT" if cls in ("PRICE_JUMP","TRADE_BURST","LIQUIDITY_WITHDRAWAL","CROSS_MARKET_DIVERGENCE","OPPORTUNITY_TRIGGER","NEW_LISTING") else "NORMAL"
    return ClassifiedMarketEvent(event.event_hash,cls,urgency)

def verify_ois_032_market_event_classification():
    from .ois_031_low_latency_event_intake import build_canonical_market_event
    e=build_canonical_market_event("k","a","m","price_jump",1,2,1,"a"*64)
    c=classify_market_event(e)
    return c.event_class=="PRICE_JUMP" and c.urgency=="INTERRUPT"
