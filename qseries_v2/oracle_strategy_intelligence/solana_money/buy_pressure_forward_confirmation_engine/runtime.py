from __future__ import annotations
import argparse,time
from pathlib import Path
from .tape import ArtifactTapeReader
from .lifecycle import BirthIndex
from .watchdog import Watchdog
from .engine import ForwardConfirmedEngine

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");ap.add_argument("--poll",type=float,default=.05)
    a=ap.parse_args();root=Path(a.root).resolve();reader=ArtifactTapeReader(root);birth=BirthIndex(root)
    watch=Watchdog(root);engine=ForwardConfirmedEngine(root);watch.start();last=0
    print("[QSB-027] FORWARD-CONFIRMED BUY_PRESSURE ENGINE",flush=True)
    print("[ENTRY] pressure burst creates CANDIDATE only; a later artifact generation must provide fresh post-signal confirmation",flush=True)
    print("[FRESHNESS] signal<=2.0s old; confirmation<=2.0s old; candidate expires after 5.0s",flush=True)
    print("[CHASE] confirmation must continue +0.5% to +6.0%; >6% is rejected as late chase",flush=True)
    print("[LEARNING] all candidates, including rejected ones, get 1/3/5/10/20/30/60/90s forward outcomes",flush=True)
    print("[EXIT] profit-lock after >=7% MFE; hard max hold=90s",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    try:
        while True:
            events,t=reader.poll();birth.refresh();buys=[];sells=[]
            if events:
                b,c=engine.on_batch(events,t["generation"],birth);buys+=b;sells+=c
            sells+=engine.heartbeat()
            for p in buys:
                print("[BUY] token=%s family=%s signal_age=%.3fs confirm_move=%.3f%% entry=%.12g"%(
                    p["token"],p["family"],p["signal"]["entry_signal_age_seconds"],p["signal"]["confirmation_move"]*100,p["entry_price"]),flush=True)
            for x in sells:
                print("[SELL] token=%s reason=%s pnl=$%.6f mfe=%.3f%% age=%.2fs"%(
                    x["token"],x["exit_reason"],x["net_pnl_usdc"],x["mfe"]*100,x["closed_unix"]-x["opened_unix"]),flush=True)
            now=time.monotonic()
            if now-last>=1:
                s=engine.stats();print("[TAPE]",t,flush=True);print("[WATCHDOG]",watch.snapshot(),flush=True)
                print("[CANDIDATES] formed={candidates_formed} active={candidates_active} confirmed_entries={confirmed_entries} shadow10={shadow_10s_samples} shadow10_success={shadow_10s_success_rate}".format(**s),flush=True)
                print("[MONEY] open={open} closed={closed_valid} wins={wins} losses={losses} NET=${net_pnl_usdc:.4f} aborts={data_gap_aborts}".format(**s),flush=True)
                print("[REJECTS]",s["rejects"],flush=True);print("[PERSISTENCE]",s["persistence"],flush=True);last=now
            time.sleep(max(.01,a.poll))
    finally:watch.close()
if __name__=="__main__":main()
