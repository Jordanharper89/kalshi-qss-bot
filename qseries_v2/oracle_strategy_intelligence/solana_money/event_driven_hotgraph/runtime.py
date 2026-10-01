from __future__ import annotations
import json,time
from pathlib import Path
from .core import HotGraph,read_changed,ANCHORS

def _short(x):
    return ANCHORS.get(x,x[:10])

def main():
    root=Path.cwd();g=HotGraph();state={}
    print("[QSB-047] EVENT-DRIVEN IN-MEMORY ARBITRAGE HOTGRAPH",flush=True)
    print("[HOT_PATH] local file-change -> ingest -> affected 2-leg/3-leg graph recompute; ZERO quote/RPC calls",flush=True)
    print("[SOURCE] existing Phase-8 strict/balanced live economics producer",flush=True)
    print("[MODE] READ_ONLY=True execution_authority=FALSE",flush=True)
    quiet=0
    try:
        while True:
            rows,files=read_changed(root,state)
            if rows:
                now=time.time()
                n,changed=g.ingest(rows,now)
                routes,micros=g.scan_changed(changed,now)
                print("[TICK] new=%d edges=%d files=%d recompute_us=%.1f routes=%d"%(
                    n,len(g.edges),len(files),micros,len(routes)),flush=True)
                for i,r in enumerate(routes[:8],1):
                    print("[ARB_TRIGGER %d] legs=%d path=%s venues=%s gross_bps=%+.2f skew_ms=%.1f"%(
                        i,r["legs"]," -> ".join(_short(x) for x in r["path"]),
                        " -> ".join(r["families"]),r["gross_bps"],r["skew_seconds"]*1000.0),flush=True)
                quiet=0
            else:
                quiet+=1
                if quiet%500==0:
                    print("[HEARTBEAT] edges=%d waiting_for_live_economic_update"%len(g.edges),flush=True)
            time.sleep(.01)
    except KeyboardInterrupt:
        print("[STOP]",flush=True)

if __name__=="__main__":main()
