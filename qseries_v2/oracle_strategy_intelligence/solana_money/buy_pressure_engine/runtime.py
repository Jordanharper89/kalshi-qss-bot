from __future__ import annotations
import argparse,time
from pathlib import Path
from .tape import ArtifactTapeReader
from .watchdog import ProducerWatchdog
from .engine import EventDrivenBuyPressureEngine

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");ap.add_argument("--tick",type=float,default=.05)
    a=ap.parse_args();root=Path(a.root).resolve()
    reader=ArtifactTapeReader(root);watch=ProducerWatchdog(root);engine=EventDrivenBuyPressureEngine(root)
    watch.start();last_print=0.0
    print("[QSB-024] EVENT-DRIVEN PUMP BUY_PRESSURE MONEY ENGINE",flush=True)
    print("[SUBSYSTEM] qseries_v2/oracle_strategy_intelligence/solana_money/buy_pressure_engine",flush=True)
    print("[EVALUATION] every NEW exact Pump.fun/PumpSwap trade; artifact check every %.3fs"%a.tick,flush=True)
    print("[HOLD] dynamic exits; hard ceiling 90s",flush=True)
    print("[SOURCE] killable producer processes with hard deadlines; parent money loop cannot block",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    try:
        while True:
            events,tape=reader.poll();buys=[];sells=[]
            for e in events:
                b,c=engine.on_event(e);buys.extend(b);sells.extend(c)
            sells.extend(engine.heartbeat())
            for p in buys:
                print("[BUY] family=%s token=%s market=%s entry=%.12g score=%.3f"%(
                    p["family"],p["token"],p["market"],p["entry_price"],p["signal"]["adaptive_score"]),flush=True)
            for t in sells:
                print("[SELL] family=%s token=%s reason=%s age=%.2fs pnl=$%.6f"%(
                    t["family"],t["token"],t["exit_reason"],t["closed_unix"]-t["opened_unix"],t["net_pnl_usdc"]),flush=True)
            now=time.monotonic()
            if now-last_print>=1.0:
                s=engine.status();w=watch.snapshot();L=s["learning"]
                print("[TAPE] files=%d changed=%d new_events=%d emitted=%d"%(
                    tape["artifact_files_present"],tape["artifact_files_changed"],tape["new_events"],tape["rows_emitted_total"]),flush=True)
                print("[WATCHDOG] PUMP_FUN=%s PUMP_SWAP=%s"%(w["PUMP_FUN"],w["PUMP_SWAP"]),flush=True)
                print("[MONEY] events=%d evaluations=%d open=%d closed=%d wins=%d losses=%d NET=$%.4f milestone=%s"%(
                    s["events_processed"],s["evaluations"],s["open"],s["closed"],s["wins"],s["losses"],s["net_pnl_usdc"],s["milestone"]),flush=True)
                print("[LEARNING] sample=%d win_rate=%s gate=%.3f hold=%.1fs promoted=%s demoted=%s"%(
                    L["sample"],L["win_rate"],L["admission_score"],L["max_hold_seconds"],L["promoted"],L["demoted"]),flush=True)
                last_print=now
            time.sleep(max(.01,a.tick))
    finally:
        watch.close()

if __name__=="__main__":main()
