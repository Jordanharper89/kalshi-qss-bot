from __future__ import annotations
import argparse,asyncio,time
from pathlib import Path
from .acquire import capture_activity,SlotBatchAcquirer
from .scanner import observed_cycles
from .ledger import Ledger

def slots_from_rows(rows):
    out=[]
    for r in rows:
        try:s=int(r.get("slot") or 0)
        except Exception:continue
        if s>0:out.append(s)
    return sorted(set(out),reverse=True)

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");ap.add_argument("--cycles",type=int,default=0)
    ap.add_argument("--capture-seconds",type=float,default=.70);ap.add_argument("--max-slots-per-cycle",type=int,default=2)
    a=ap.parse_args();root=Path(a.root).resolve();acq=SlotBatchAcquirer()
    ledger=Ledger(root/"runtime_state/qseries/qsb032_public_rpc_slot_batched_mriya_arb/ledger.json")
    print("[QSB-032] PUBLIC-RPC SLOT-BATCHED MRIYA ARB OBSERVER",flush=True)
    print("[HOT PATH] USLS-046B activity -> unique slots -> one getBlock per slot; NO getTransaction fanout",flush=True)
    print("[RATE] >=0.45s between getBlock calls; bounded slots per cycle",flush=True)
    print("[TRUTH] observed block execution patterns only; NOT relabeled as live executable quotes",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    cycle=0
    while True:
        cycle+=1
        try:ret=asyncio.run(capture_activity(a.capture_seconds,1800)) or {}
        except Exception as e:
            print("[CAPTURE_ERROR]",type(e).__name__,str(e),flush=True);time.sleep(1);continue
        rows=list(ret.get("rows") or []);slots=[s for s in slots_from_rows(rows) if s not in acq.seen_slots][:max(1,a.max_slots_per_cycle)]
        total_edges=0;total_cycles=0;target_count=0
        for slot in slots:
            block,limited=acq.fetch_block(slot)
            if limited:
                print("[RPC429] slot=%d preserved_for_retry=True"%slot,flush=True)
                break
            if not isinstance(block,dict):
                print("[BLOCK_MISS] slot=%d"%slot,flush=True);continue
            acq.seen_slots.add(slot)
            es,targets,meta=acq.process_block(slot,block,time.time());total_edges+=len(es);target_count+=len(targets)
            cs=observed_cycles(es);total_cycles+=len(cs)
            for o in cs[:50]:
                if ledger.add_cycle(o,slot):
                    print("[OBSERVED_ARB] slot=%d hops=%d net_bps=%.2f venues=%s"%(
                        slot,o["hops"],o["net_bps"],o["venues"]),flush=True)
            if targets:
                ledger.add_targets(targets)
                for t in targets:
                    print("[TARGET_TX] slot=%d executor=%s venues=%s failed=%s"%(
                        slot,t["executor_present"],t["tracked_venues"],t["failed"]),flush=True)
        ledger.save()
        print("[CYCLE] n=%d raw=%d unique_slots=%d fetched_now=%d edges=%d observed_cycles=%d target_tx=%d rpc=%s"%(
            cycle,len(rows),len(slots_from_rows(rows)),len(slots),total_edges,total_cycles,target_count,acq.snapshot()),flush=True)
        if a.cycles and cycle>=a.cycles:return

if __name__=="__main__":main()
