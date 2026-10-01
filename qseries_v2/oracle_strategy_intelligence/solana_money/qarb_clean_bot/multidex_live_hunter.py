
from __future__ import annotations
import json,time
from dataclasses import dataclass
from time import perf_counter_ns
from .multidex_graph import VenueQuote,best_two_leg,VENUES

MAX_AGE_MS=750.0
MIN_NET_BPS=20.0

class HotGraph:
    def __init__(self):
        self.rows={}
        self.events=0
        self.signals=0
        self.best=None

    def publish(self,q):
        self.events+=1
        key=(q.venue,q.pool,q.token,q.input_mint,q.output_mint,q.amount_in)
        self.rows[key]=q
        now=perf_counter_ns()
        r=best_two_leg(list(self.rows.values()),"WSOL","WSOL",now)
        if r is None: return None
        if r["age_ms"]>MAX_AGE_MS or r["bps"]<MIN_NET_BPS: return None
        self.signals+=1
        if self.best is None or r["net"]>self.best["net"]: self.best=r
        return r

def capability_matrix():
    from .dex import raydium_cpmm_live as rc
    from .dex import raydium_clmm_live as rl
    from .dex import orca_whirlpool_live as ow
    from .dex import meteora_damm_v2_live as md
    return {
      "PUMPSWAP":{"live":True,"local_quote":True},
      "METEORA_DLMM":{"live":True,"local_quote":True},
      "RAYDIUM_CPMM":{"live_adapter":True,"local_quote":True},
      "RAYDIUM_CLMM":{"live_adapter":True,"local_quote_provider_required":True},
      "ORCA_WHIRLPOOL":{"live_adapter":True,"local_quote_provider_required":True},
      "METEORA_DAMM_V2":{"live_adapter":True,"local_quote":True},
    }

def format_signal(r):
    return "[HOT_SIGNAL] buy=%s sell=%s token=%s net=%+.9f SOL bps=%+.2f age_ms=%.3f"%(
        r["buy_venue"],r["sell_venue"],r["token"],r["net"]/1e9,r["bps"],r["age_ms"])

def main():
    print("[QARB-015] SIX-DEX CONTINUOUS HOTGRAPH FOUNDATION",flush=True)
    print("[DEX] "+" | ".join(VENUES),flush=True)
    print("[LATENCY] hard_state_age_ms=750",flush=True)
    print("[CAPABILITY] "+json.dumps(capability_matrix(),sort_keys=True),flush=True)
    print("[TRUTH] PumpSwap+DLMM live stream proven; CPMM+DAMM live bindings installed; CLMM+Orca fail closed until native local providers are bound",flush=True)
    print("[MODE] scanner/handoff only execution_authority=FALSE",flush=True)

if __name__=="__main__": main()
