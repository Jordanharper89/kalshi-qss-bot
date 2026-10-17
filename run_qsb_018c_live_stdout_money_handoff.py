
from __future__ import annotations
import json, subprocess, sys, threading, queue, time
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_018c_live_stdout_money_handoff import (
    parse_fast_entries, parse_fresh_money, qualifies_existing_qsb015_entry
)

ROOT=Path.cwd()
QSB015=ROOT/"run_qsb_015_first_seconds_launch_impulse.py"
STATE=ROOT/"runtime_state"/"solana_opportunities"
LEDGER=STATE/"qsb_018c_live_money_handoff.jsonl"

def _gmgn_matches(token):
    hits=[]
    root=ROOT/"runtime_state"
    if not root.exists():
        return hits
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in (".json",".jsonl"):
            continue
        s=str(p).lower()
        if not any(x in s for x in ("gmgn","wallet","trader")):
            continue
        try:
            txt=p.read_text(encoding="utf-8",errors="ignore")
        except Exception:
            continue
        if token in txt:
            hits.append(str(p.relative_to(ROOT)))
    return hits[:10]

def _write(row):
    STATE.mkdir(parents=True,exist_ok=True)
    with LEDGER.open("a",encoding="utf-8") as f:
        f.write(json.dumps(row,sort_keys=True)+"\n")

def main():
    if not QSB015.is_file():
        raise SystemExit("[FAIL] missing QSB-015 runtime")

    proc=subprocess.Popen(
        [sys.executable,str(QSB015)],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    print("[QSB-018C] ONE SOLANA MONEY RUNTIME")
    print("[QSB-018C] LIVE QSB-015 STDOUT HANDOFF + GMGN TOKEN MATCH")
    print("[QSB-018C] PAPER ONLY / execution_authority=FALSE")

    try:
        assert proc.stdout is not None
        for raw in proc.stdout:
            line=raw.rstrip()
            print(line)

            money=parse_fresh_money(line)
            if money is not None:
                print("[QSB-018C MONEY]",json.dumps(money,sort_keys=True))

            entries=parse_fast_entries(line)
            for e in entries:
                if not qualifies_existing_qsb015_entry(e):
                    continue
                gmgn=_gmgn_matches(e.token)
                row={
                    "event":"QSB015_FAST_ENTRY_HANDOFF",
                    "family":e.family,
                    "token":e.token,
                    "score":e.score,
                    "liquidity_usd":e.liquidity_usd,
                    "gmgn_matching_sources":gmgn,
                    "gmgn_match_count":len(gmgn),
                    "paper_only":True,
                    "execution_authority":False,
                }
                _write(row)
                print("[LIVE HANDOFF]",json.dumps(row,sort_keys=True))
                if gmgn:
                    print("[GMGN MATCH] token=",e.token," sources=",len(gmgn))
                else:
                    print("[GMGN PENDING] token=",e.token," QSB-015 entry remains active; wallet enrichment does not block it")

        rc=proc.wait()
        raise SystemExit("[FAIL] QSB-015 child exited rc="+str(rc))
    finally:
        if proc.poll() is None:
            proc.terminate()
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait()

if __name__=="__main__":
    main()
