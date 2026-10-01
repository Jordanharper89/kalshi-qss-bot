from __future__ import annotations
import argparse,time
from collections import deque
from pathlib import Path
from .profile import TARGET_WALLET,TARGET_EVIDENCE
from .profiler import RateSafeTargetProfiler
from .live_edges import LiveEdgeCapture
from .scanner import scan_cycles
from .ledger import OpportunityLedger

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");ap.add_argument("--profile-target",action="store_true")
    ap.add_argument("--profile-limit",type=int,default=100);ap.add_argument("--capture-seconds",type=float,default=.65)
    a=ap.parse_args();root=Path(a.root).resolve()
    profiler=RateSafeTargetProfiler(root,a.profile_limit);live=LiveEdgeCapture()
    ledger=OpportunityLedger(root/"runtime_state/qseries/qsb030_mriya_live_atomic_arb/opportunities.json")
    if a.profile_target:profiler.start()
    window=deque(maxlen=5000);cycle=0
    print("[QSB-030C] MRIYA LIVE ATOMIC ARBITRAGE ENGINE",flush=True)
    print("[TARGET]",TARGET_WALLET,flush=True);print("[OBSERVED]",TARGET_EVIDENCE,flush=True)
    print("[LIVE] shared multi-DEX WebSocket -> bounded tx hydration -> observed-direction swap edges",flush=True)
    print("[TRUTH] no synthetic reciprocal edges; capture age<=0.75s; chain age<=3s; route spread<=0.75s",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    try:
        while True:
            cycle+=1;edges,ls=live.capture(seconds=max(.15,a.capture_seconds))
            now=time.time()
            for e in edges:window.append(e)
            while window and now-float(window[0]["t"])>2.0:window.popleft()
            routes,ss=scan_cycles(list(window),now)
            new=0
            for o in routes[:50]:
                if ledger.record(o):
                    new+=1;print("[ARB] hops=%d net_bps=%.2f motif=%.2f venues=%s"%(o["hops"],o["net_bps"],o["motif_match"],o["venues"]),flush=True)
            ledger.save()
            print("[LIVE] cycle=%d raw=%d sigs=%d hydrated=%d new_edges=%d fresh_edges=%d chain_stale=%d venues=%s rpc429=%d pending=%d"%(
                cycle,ls["raw_rows"],ls["new_signatures"],ls["hydrated"],ls["edges"],ss["fresh_edges"],ss["chain_stale_rejected"],ss["venues"],ls["rate_limits"],ls["pending"]),flush=True)
            print("[SCAN] opportunities=%d new=%d"%(len(routes),new),flush=True)
            if a.profile_target:print("[PROFILE]",profiler.snapshot(),flush=True)
    finally:
        profiler.close()
if __name__=="__main__":main()
