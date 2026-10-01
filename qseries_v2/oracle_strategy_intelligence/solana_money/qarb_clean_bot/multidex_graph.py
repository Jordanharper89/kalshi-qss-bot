
from dataclasses import dataclass
from time import perf_counter_ns

VENUES=("PUMPSWAP","METEORA_DLMM","RAYDIUM_CPMM","RAYDIUM_CLMM","ORCA_WHIRLPOOL","METEORA_DAMM_V2")
MAX_AGE_MS=750.0

@dataclass
class VenueQuote:
    venue:str
    token:str
    input_mint:str
    output_mint:str
    amount_in:int
    amount_out:int
    observed_ns:int
    pool:str

def fresh(q,now_ns=None):
    now=perf_counter_ns() if now_ns is None else int(now_ns)
    return (now-q.observed_ns)/1e6 <= MAX_AGE_MS

def best_two_leg(quotes,start_mint,end_mint,now_ns=None):
    now=perf_counter_ns() if now_ns is None else int(now_ns)
    buys=[q for q in quotes if q.input_mint==start_mint and fresh(q,now)]
    sells=[q for q in quotes if q.output_mint==end_mint and fresh(q,now)]
    best=None
    for a in buys:
        for b in sells:
            if a.venue==b.venue or a.token!=b.token:
                continue
            if a.output_mint!=b.input_mint:
                continue
            if a.amount_out!=b.amount_in:
                continue
            net=b.amount_out-a.amount_in
            bps=net/a.amount_in*10000.0 if a.amount_in>0 else -1e18
            row={
                "buy_venue":a.venue,"sell_venue":b.venue,"token":a.token,
                "start":a.amount_in,"end":b.amount_out,"net":net,"bps":bps,
                "age_ms":max((now-a.observed_ns)/1e6,(now-b.observed_ns)/1e6),
                "execution_authority":False,
            }
            if best is None or row["net"]>best["net"]:
                best=row
    return best

def route_pairs():
    return tuple((a,b) for a in VENUES for b in VENUES if a!=b)
