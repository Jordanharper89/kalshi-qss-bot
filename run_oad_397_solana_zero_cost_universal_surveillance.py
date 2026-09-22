from __future__ import annotations
import argparse,time
from qseries_v2.oracle_adapters.independent.oad_397_solana_zero_cost_universal_surveillance_control_plane import live_read_only_snapshot
def main():
    ap=argparse.ArgumentParser(description="Read-only zero-cost Solana universal surveillance monitor")
    ap.add_argument("--interval",type=float,default=5.0)
    ap.add_argument("--once",action="store_true")
    args=ap.parse_args()
    while True:
        x=live_read_only_snapshot()
        print("[SOLANA] state={} finalized_head={} last_committed_slot={} checkpoint_lag={} scheduled={} gaps_pending={} execution_authority={}".format(x.state,x.finalized_head,x.last_committed_slot,x.checkpoint_lag,len(x.scheduled_slots),x.gaps_pending,x.execution_authority))
        if args.once: break
        time.sleep(max(1.0,args.interval))
if __name__=="__main__":
    main()