from __future__ import annotations
import argparse,time,json
from pathlib import Path
from .failure_memory import FAILURE_AUDIT
from .tape import ArtifactTapeReader
from .watchdog import Watchdog
from .engine import ProfitEngine
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");ap.add_argument("--poll",type=float,default=.05)
    a=ap.parse_args();root=Path(a.root).resolve();reader=ArtifactTapeReader(root);watch=Watchdog(root);engine=ProfitEngine(root)
    watch.start();last=0
    print("[QSB-026] LOSS-AWARE BUY_PRESSURE PROFIT ENGINE",flush=True)
    print("[FAILURE MEMORY]",json.dumps(FAILURE_AUDIT,sort_keys=True),flush=True)
    print("[RULE] no WSOL/USDC identity guesses; no re-buy after a loss; stale exits do not train; hard max hold=90s",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    try:
        while True:
            events,t=reader.poll();buys=[];sells=[]
            if events:
                b,c=engine.on_batch(events);buys+=b;sells+=c
            sells+=engine.heartbeat()
            for p in buys:print("[BUY] token=%s family=%s quality=%.3f entry=%.12g"%(p["token"],p["family"],p["signal"]["quality_score"],p["entry_price"]),flush=True)
            for x in sells:print("[SELL] token=%s reason=%s valid=%s pnl=$%.6f age=%.2fs"%(x["token"],x["exit_reason"],x["evidence_valid"],x["net_pnl_usdc"],x["closed_unix"]-x["opened_unix"]),flush=True)
            now=time.monotonic()
            if now-last>=1:
                s=engine.stats();print("[TAPE]",t,flush=True);print("[WATCHDOG]",watch.snapshot(),flush=True)
                print("[MONEY] events={events} batches={batches} open={open} valid_closed={closed_valid} aborts={data_gap_aborts} wins={wins} losses={losses} NET=${net_pnl_usdc:.4f} milestone={milestone}".format(**s),flush=True)
                print("[REJECTS]",s["rejects"],flush=True)
                print("[PERSISTENCE]",engine.persistence_modes,flush=True)
                L=s["learning"];print("[LEARNING] sample=%d wr=%s quality_floor=%.3f hard_hold=%.0fs promoted=%s demoted=%s"%(L["sample"],L["win_rate"],L["quality_floor"],L["hard_max_hold_seconds"],L["promoted"],L["demoted"]),flush=True)
                last=now
            time.sleep(max(.01,a.poll))
    finally:watch.close()
if __name__=="__main__":main()
