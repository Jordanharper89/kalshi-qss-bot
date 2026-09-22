from dataclasses import dataclass
from types import MappingProxyType
from .oad_013_market_data_normalization import normalize_kalshi_market_data
from .oad_014_sequence_integrity import evaluate_sequence_integrity

OAD_027_BUILD_ID="OAD-027"
OAD_027_REVISION="OAD_027_CONTINUOUS_REAL_MARKET_EVENT_INTAKE_PUMP_V1"

@dataclass(frozen=True)
class PumpResult:
    accepted:int
    rejected:int
    resync_required:int
    latest_seq_by_sid:tuple[tuple[int,int],...]

def pump_market_messages(messages,oracle_receive_ns):
    seqs={}
    accepted=rejected=resync=0
    for raw in messages:
        typ=str(raw.get("type",""))
        if typ not in ("orderbook_snapshot","orderbook_delta","ticker","trade"):
            continue
        event=normalize_kalshi_market_data(raw,int(oracle_receive_ns))
        prev=seqs.get(event.sid)
        d=evaluate_sequence_integrity(event.sid,prev,event.seq,event.event_type)
        if d.accept:
            accepted+=1
            seqs[event.sid]=event.seq
        else:
            rejected+=1
            if d.resync_required: resync+=1
    return PumpResult(accepted,rejected,resync,tuple(sorted(seqs.items())))

def verify_oad_027_continuous_real_market_event_intake_pump():
    msgs=(
        {"type":"orderbook_snapshot","sid":1,"seq":10,"msg":{"market_ticker":"A"}},
        {"type":"orderbook_delta","sid":1,"seq":11,"msg":{"market_ticker":"A"}},
        {"type":"orderbook_delta","sid":1,"seq":13,"msg":{"market_ticker":"A"}},
    )
    x=pump_market_messages(msgs,100)
    return x.accepted==2 and x.rejected==1 and x.resync_required==1
