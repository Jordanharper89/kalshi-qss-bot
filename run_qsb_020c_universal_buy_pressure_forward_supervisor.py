
from __future__ import annotations
import json,subprocess
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_020c_universal_buy_pressure_forward_supervisor import (
    parse_leader,delta,milestone,start_child
)

ROOT=Path.cwd()
CHILD=ROOT/"run_qsb_013_solana_universal_champion_challenger.py"
STATE=ROOT/"runtime_state/qseries/qsb020c_buy_pressure"
BASELINE=STATE/"baseline.json"
STATUS=STATE/"status.json"

def _load(path):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception:return None

def _atomic(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,sort_keys=True),encoding="utf-8")
    tmp.replace(path)

def main():
    if not CHILD.is_file():
        raise SystemExit("[FAIL] missing QSB-013 runtime")

    STATE.mkdir(parents=True,exist_ok=True)
    baseline=_load(BASELINE)
    proc=start_child(CHILD,ROOT)

    print("[QSB-020C] UNIVERSAL BUY_PRESSURE FORWARD SUPERVISOR",flush=True)
    print("[QSB-020C] DIRECT CHILD: QSB-013 UNIVERSAL BURST RUNTIME",flush=True)
    print("[QSB-020C] NO DIRECTORY SCANNER / COUNTS ONLY NEW BUY_PRESSURE RESULTS",flush=True)
    print("[QSB-020C] PAPER ONLY / execution_authority=FALSE",flush=True)

    try:
        assert proc.stdout is not None
        for raw in iter(proc.stdout.readline,""):
            line=raw.rstrip()
            if not line:
                continue

            if (
                line.startswith("[BURST]") or
                line.startswith("[BURST FAMILIES]") or
                line.startswith("[WATCHING]") or
                line.startswith("[ARENA]") or
                line.startswith("[MODE]")
            ):
                print(line,flush=True)

            leader=parse_leader(line)
            if leader is None:
                continue

            if baseline is None:
                baseline=dict(leader)
                _atomic(BASELINE,baseline)
                print("[BASELINE] "+json.dumps(baseline,sort_keys=True),flush=True)

            d=delta(leader,baseline)
            status={
                "revision":"QSB_020C_UNIVERSAL_BUY_PRESSURE_FORWARD_SUPERVISOR_V1",
                "strategy":"BUY_PRESSURE_ACCELERATION",
                "baseline":baseline,
                "current":leader,
                "forward":d,
                "milestone_reached":milestone(d),
                "paper_only":True,
                "execution_authority":False,
            }
            _atomic(STATUS,status)

            print(
                "[BUY_PRESSURE FORWARD] closed={closed} wins={wins} losses={losses} NET=${net:.4f} milestone={m}".format(
                    closed=d["closed"],wins=d["wins"],losses=d["losses"],net=d["net"],m=milestone(d)
                ),
                flush=True
            )

            if milestone(d):
                print("[PASS] 10 NEW BUY_PRESSURE WINS + POSITIVE FORWARD NET",flush=True)

        rc=proc.wait()
        raise SystemExit("[FAIL] QSB-013 child exited rc="+str(rc))
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill();proc.wait()

if __name__=="__main__":
    main()
