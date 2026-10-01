from __future__ import annotations
import argparse
from pathlib import Path
from .replay import replay
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--root",default=".");a=ap.parse_args()
    print("[QSB-034] MRIYA CAPTURED ROUTE REPLAY",flush=True)
    print("[SOURCE] QSB-032 captured target slots/signatures + known captured slots from this session",flush=True)
    print("[ACTION] paced getBlock replay -> exact QSB-033 anatomy",flush=True)
    print("[NO WAIT] historical caught Mriya transactions are dissected immediately",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    r=replay(Path(a.root))
    wins=sum(not x["failed"] for x in r["routes"]);fails=sum(bool(x["failed"]) for x in r["routes"])
    closed=sum(bool(x.get("closed_anchor_cycle")) for x in r["routes"])
    print("[SUMMARY] routes=%d wins=%d fails=%d closed_anchor_cycles=%d rpc429=%d errors=%d"%(
        len(r["routes"]),wins,fails,closed,r["rpc429"],r["errors"]),flush=True)
if __name__=="__main__":main()
