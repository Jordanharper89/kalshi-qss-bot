from pathlib import Path
import py_compile

ROOT = Path.cwd()
DEP = ROOT / "run_qsb_013_solana_universal_champion_challenger.py"
if not DEP.is_file():
    raise SystemExit("[FAIL] missing dependency: " + str(DEP))

PKG = ROOT / "qseries_v2/oracle_strategy_intelligence/solana_money"
PKG.mkdir(parents=True, exist_ok=True)
(PKG / "__init__.py").touch(exist_ok=True)

MODULE = PKG / "qsb_020c_universal_buy_pressure_forward_supervisor.py"
TEST = ROOT / "test_qsb_020c_universal_buy_pressure_forward_supervisor.py"
RUN = ROOT / "run_qsb_020c_universal_buy_pressure_forward_supervisor.py"

module = r"""
from __future__ import annotations
import json, os, subprocess, sys
from pathlib import Path

READ_ONLY=True
EXECUTION_AUTHORITY=False
PAPER_ONLY=True
REVISION="QSB_020C_UNIVERSAL_BUY_PRESSURE_FORWARD_SUPERVISOR_V1"
TARGET="BUY_PRESSURE_ACCELERATION"

def parse_leader(line: str):
    if not line.startswith("[LEADERS]"):
        return None
    try:
        rows=json.loads(line.split("]",1)[1].strip())
    except Exception:
        return None
    if not isinstance(rows,list):
        return None
    for r in rows:
        if isinstance(r,dict) and r.get("strategy")==TARGET:
            return {
                "closed": int(r.get("closed") or 0),
                "wins": int(r.get("wins") or 0),
                "losses": int(r.get("losses") or 0),
                "net": float(r.get("net") if r.get("net") is not None else r.get("net_pnl_usdc") or 0.0),
                "win_rate": r.get("win_rate"),
            }
    return None

def delta(current, baseline):
    return {
        "closed": max(0,current["closed"]-baseline["closed"]),
        "wins": max(0,current["wins"]-baseline["wins"]),
        "losses": max(0,current["losses"]-baseline["losses"]),
        "net": current["net"]-baseline["net"],
    }

def milestone(d):
    return d["wins"] >= 10 and d["net"] > 0.0

def child_env():
    e=os.environ.copy()
    e["PYTHONUNBUFFERED"]="1"
    return e

def start_child(script: Path, cwd: Path):
    return subprocess.Popen(
        [sys.executable,"-u",str(script)],
        cwd=str(cwd),
        env=child_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
"""

test = r"""
import json,tempfile,time,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qsb_020c_universal_buy_pressure_forward_supervisor import (
    parse_leader,delta,milestone,start_child,EXECUTION_AUTHORITY,PAPER_ONLY
)

class T(unittest.TestCase):
    def test_exact_leader_parse(self):
        line='[LEADERS] '+json.dumps([
            {"strategy":"BUY_PRESSURE_ACCELERATION","closed":7,"wins":5,"losses":2,"net":2.8746,"win_rate":5/7}
        ])
        x=parse_leader(line)
        self.assertIsNotNone(x)
        self.assertEqual(x["wins"],5)
        self.assertAlmostEqual(x["net"],2.8746)

    def test_forward_delta_gate(self):
        b={"closed":7,"wins":5,"losses":2,"net":2.87}
        c={"closed":20,"wins":15,"losses":5,"net":8.10}
        d=delta(c,b)
        self.assertEqual(d["wins"],10)
        self.assertGreater(d["net"],0)
        self.assertTrue(milestone(d))
        self.assertFalse(EXECUTION_AUTHORITY)
        self.assertTrue(PAPER_ONLY)

    def test_unbuffered_physical_child(self):
        with tempfile.TemporaryDirectory() as td:
            td=Path(td)
            s=td/"child.py"
            s.write_text(
                "import json,time\n"
                "print('[WATCHING] markets=224 tokens=109 rows=650',flush=True)\n"
                "print('[LEADERS] '+json.dumps([{'strategy':'BUY_PRESSURE_ACCELERATION','closed':7,'wins':5,'losses':2,'net':2.87}]),flush=True)\n"
                "time.sleep(1)\n",
                encoding="utf-8"
            )
            p=start_child(s,td)
            seen_watch=False
            seen_leader=False
            try:
                self.assertIsNotNone(p.stdout)
                deadline=time.monotonic()+15
                while time.monotonic()<deadline and not (seen_watch and seen_leader):
                    line=p.stdout.readline()
                    if not line:
                        if p.poll() is not None:
                            break
                        continue
                    line=line.strip()
                    if line.startswith("[WATCHING]"):
                        seen_watch=True
                    if parse_leader(line):
                        seen_leader=True
                self.assertTrue(seen_watch)
                self.assertTrue(seen_leader)
            finally:
                if p.poll() is None:
                    p.terminate(); p.wait(timeout=5)

if __name__=="__main__":
    unittest.main(verbosity=2)
"""

runtime = r"""
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
"""

MODULE.write_text(module,encoding="utf-8")
TEST.write_text(test,encoding="utf-8")
RUN.write_text(runtime,encoding="utf-8")

for p in (MODULE,TEST,RUN):
    py_compile.compile(str(p),doraise=True)

print("[PASS] dependency:",DEP.relative_to(ROOT))
print("[PASS] installed:",MODULE.relative_to(ROOT))
print("[PASS] test:",TEST.relative_to(ROOT))
print("[PASS] runtime:",RUN.relative_to(ROOT))
print("[PASS] QSB-020C direct universal runtime supervision installed")
print("[PASS] no runtime_state directory discovery/scanning")
print("[PASS] baseline prevents historical 5 wins from counting toward forward 10")
print("[PASS] PAPER_ONLY=True execution_authority=FALSE")
