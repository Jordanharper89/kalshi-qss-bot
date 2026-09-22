from dataclasses import dataclass
from types import MappingProxyType

OAD_014_BUILD_ID="OAD-014"
OAD_014_REVISION="OAD_014_KALSHI_SEQUENCE_INTEGRITY_GAP_DETECTION_RESYNC_V1"

@dataclass(frozen=True)
class SequenceIntegrityDecision:
    sid:int
    previous_seq:int|None
    current_seq:int
    status:str
    accept:bool
    resync_required:bool
    reason:str

def evaluate_sequence_integrity(sid,previous_seq,current_seq,event_type):
    sid=int(sid); cur=int(current_seq)
    if sid<0 or cur<0: raise ValueError("non-negative sid/sequence required")
    if event_type=="orderbook_snapshot":
        return SequenceIntegrityDecision(sid,previous_seq,cur,"SNAPSHOT_BASELINE",True,False,"snapshot")
    if previous_seq is None:
        return SequenceIntegrityDecision(sid,None,cur,"NO_BASELINE",False,True,"missing_snapshot_or_baseline")
    prev=int(previous_seq)
    if cur==prev+1:
        return SequenceIntegrityDecision(sid,prev,cur,"IN_ORDER",True,False,"contiguous")
    if cur<=prev:
        return SequenceIntegrityDecision(sid,prev,cur,"STALE_OR_DUPLICATE",False,False,"non_advancing_sequence")
    return SequenceIntegrityDecision(sid,prev,cur,"GAP",False,True,"sequence_gap")

def build_orderbook_resync_command(command_id,sid,market_tickers):
    tickers=tuple(market_tickers)
    if int(command_id)<1 or int(sid)<0 or not tickers:
        raise ValueError("valid command id, sid, market_tickers required")
    return {"id":int(command_id),"cmd":"update_subscription",
            "params":{"sid":int(sid),"market_tickers":list(tickers),"action":"get_snapshot"}}

def build_oad_014_certification_manifest():
    return MappingProxyType({"build_id":OAD_014_BUILD_ID,"revision":OAD_014_REVISION,
        "sequence_gap_detection":True,"snapshot_resync_action":"get_snapshot","execution":False})

def verify_oad_014_kalshi_sequence_integrity_gap_detection_resync():
    good=evaluate_sequence_integrity(2,2,3,"orderbook_delta")
    gap=evaluate_sequence_integrity(2,3,5,"orderbook_delta")
    cmd=build_orderbook_resync_command(9,2,("A",))
    return good.accept and not good.resync_required and gap.resync_required and cmd["params"]["action"]=="get_snapshot"
