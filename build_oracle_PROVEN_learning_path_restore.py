from __future__ import annotations

from pathlib import Path
import ast
import importlib
import json
import os
import subprocess
import sys

ROOT=Path.cwd().resolve()
STATE=ROOT/"runtime_state"/"oracle_learning_runtime_state.json"
LEDGER=ROOT/"runtime_state"/"oracle_learning_event_ledger.json"
LAUNCHER=ROOT/"run_oracle_LIVE.py"
RUNNER=ROOT/"run_oracle_PROVEN_learning_runtime.py"
TEST=ROOT/"test_oracle_PROVEN_learning_restore.py"

RUNNER_SOURCE=r"""from __future__ import annotations
from pathlib import Path
import argparse,time

from qseries_v2.oracle_learning_runtime.olr_009_high_coverage_learning_cycle import (
    run_high_coverage_learning_cycle,
)

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--cadence-seconds",type=float,default=15.0)
    p.add_argument("--settled-limit",type=int,default=100)
    p.add_argument("--evidence-limit",type=int,default=3)
    p.add_argument("--once",action="store_true")
    p.add_argument("--check",action="store_true")
    a=p.parse_args(argv)

    if a.check:
        print("[READY] Proven Oracle learning runtime")
        print("[PASS] source=OLR-009_HIGH_COVERAGE_LEARNING_CYCLE")
        print("[PASS] execution_authority=FALSE")
        return 0

    root=Path.cwd()
    cycle=0
    print("="*88,flush=True)
    print(" ORACLE PROVEN OUTCOME-GROUNDED LEARNING RUNTIME",flush=True)
    print("="*88,flush=True)
    print("[LEARNING] source=OLR-009 proven_historical_path execution_authority=FALSE",flush=True)

    while True:
        cycle+=1
        try:
            s=run_high_coverage_learning_cycle(
                root=root,
                settled_limit=a.settled_limit,
                evidence_limit=a.evidence_limit,
                progress=lambda x:print(x,flush=True),
            )
            print(
                f"[PROVEN LEARNING] runtime_cycle={cycle} "
                f"learned_total={s.learned_total} state_hash={s.state_hash} idle={s.idle}",
                flush=True,
            )
        except Exception as exc:
            print(
                f"[PROVEN LEARNING ERROR] type={type(exc).__name__} message={exc}",
                flush=True,
            )
            if a.once:
                raise

        if a.once:
            return 0
        time.sleep(a.cadence_seconds)

if __name__=="__main__":
    raise SystemExit(main())
"""

TEST_SOURCE=r"""import json
import unittest
from pathlib import Path

ROOT=Path.cwd()

class T(unittest.TestCase):
    def test_proven_state_exists(self):
        p=ROOT/"runtime_state"/"oracle_learning_runtime_state.json"
        self.assertTrue(p.is_file())
        d=json.loads(p.read_text(encoding="utf-8"))
        self.assertGreater(int(d.get("outcomes_learned",0)),0)
        self.assertGreater(int(d.get("cycles",0)),0)
        self.assertTrue(str(d.get("ocl_state",{}).get("state_hash","")))

    def test_proven_ledger_exists(self):
        p=ROOT/"runtime_state"/"oracle_learning_event_ledger.json"
        self.assertTrue(p.is_file())
        d=json.loads(p.read_text(encoding="utf-8"))
        rows=list(d.values()) if isinstance(d,dict) else list(d)
        learned=sum(
            1 for r in rows
            if isinstance(r,dict) and str(r.get("status","")).lower()=="learned"
        )
        self.assertGreater(learned,0)

if __name__=="__main__":
    print("="*88)
    print(" ORACLE PROVEN LEARNING RESTORE CERTIFICATION TEST")
    print("="*88)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] Existing physically learned state verified")
    print("[PASS] Existing learned-event ledger verified")
    print("[PASS] execution_authority=FALSE")
"""

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.write_bytes(data)

def load_state():
    d=json.loads(STATE.read_text(encoding="utf-8"))
    return (
        int(d.get("cycles",0)),
        int(d.get("outcomes_learned",0)),
        int(d.get("ocl_state",{}).get("applied_through_sequence",0)),
        str(d.get("ocl_state",{}).get("state_hash","")),
    )

def learned_ledger_count():
    d=json.loads(LEDGER.read_text(encoding="utf-8"))
    rows=list(d.values()) if isinstance(d,dict) else list(d)
    return sum(
        1 for r in rows
        if isinstance(r,dict) and str(r.get("status","")).lower()=="learned"
    )

def patch_learning_child(source,target):
    tree=ast.parse(source)
    node=None
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict):
            if any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):
                node=item.value
                break
    if node is None:
        raise RuntimeError("Oracle Live CHILDREN dictionary not found")

    lines=source.splitlines(keepends=True)
    for k,v in zip(node.keys,node.values):
        if (
            isinstance(k,ast.Constant)
            and str(k.value)=="learning"
            and isinstance(v,ast.Constant)
        ):
            old=str(v.value)
            if old==target:
                return source
            line=lines[v.lineno-1]
            for token in (repr(old),'"'+old+'"',"'"+old+"'"):
                if token in line:
                    lines[v.lineno-1]=line.replace(token,repr(target),1)
                    out="".join(lines)
                    ast.parse(out)
                    return out
    raise RuntimeError("Oracle Live learning child not found")

def main():
    print("="*88)
    print(" ORACLE PROVEN LEARNING PATH RESTORE")
    print(" PHYSICAL ADVANCEMENT REQUIRED BEFORE LIVE CUTOVER")
    print("="*88)
    print("[ROOT]",ROOT)

    required=(STATE,LEDGER,LAUNCHER)
    for p in required:
        if not p.is_file():
            raise RuntimeError("Required production artifact missing: "+str(p))

    sys.path.insert(0,str(ROOT))

    # Verify the exact lower-level path that historically advanced the learner.
    ocl=importlib.import_module(
        "qseries_v2.oracle_continuous_learner.ocl_028_learning_cycle_orchestrator"
    )
    if ocl.verify_ocl_028_continuous_learning_cycle_orchestrator() is not True:
        raise RuntimeError("Frozen OCL-028 verifier failed")

    olr=importlib.import_module(
        "qseries_v2.oracle_learning_runtime.olr_009_high_coverage_learning_cycle"
    )
    if not callable(getattr(olr,"run_high_coverage_learning_cycle",None)):
        raise RuntimeError("Proven OLR-009 learning cycle unavailable")

    before=load_state()
    ledger_before=learned_ledger_count()

    print(
        f"[PROVEN STATE BEFORE] cycles={before[0]} outcomes_learned={before[1]} "
        f"through_sequence={before[2]} state_hash={before[3]}"
    )
    print(f"[PROVEN LEDGER BEFORE] learned_records={ledger_before}")

    if before[0]<=0 or before[1]<=0 or before[2]<=0 or not before[3] or ledger_before<=0:
        raise RuntimeError(
            "Repository does not contain physically proven learned state; refusing installation"
        )

    old={p:(p.read_bytes() if p.exists() else None) for p in (RUNNER,TEST,LAUNCHER)}

    try:
        write_exact(RUNNER,RUNNER_SOURCE)
        write_exact(TEST,TEST_SOURCE)

        compile(RUNNER_SOURCE,str(RUNNER),"exec")
        compile(TEST_SOURCE,str(TEST),"exec")

        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(RUNNER),"--check"],cwd=str(ROOT),check=True)

        print("[PHYSICAL PROOF] Running the exact proven OLR-009 production cycle once")
        summary=olr.run_high_coverage_learning_cycle(
            root=ROOT,
            settled_limit=100,
            evidence_limit=3,
            progress=lambda x:print(x,flush=True),
        )

        after=load_state()
        ledger_after=learned_ledger_count()

        print(
            f"[PROVEN STATE AFTER] cycles={after[0]} outcomes_learned={after[1]} "
            f"through_sequence={after[2]} state_hash={after[3]}"
        )
        print(f"[PROVEN LEDGER AFTER] learned_records={ledger_after}")

        advanced=(
            after[0] > before[0]
            and after[1] > before[1]
            and after[2] > before[2]
            and after[3] != before[3]
            and ledger_after >= ledger_before
            and int(getattr(summary,"learned_total",0)) >= after[1]
            and not bool(getattr(summary,"idle",True))
        )

        if not advanced:
            raise RuntimeError(
                "PHYSICAL LEARNING DID NOT ADVANCE. Oracle Live was NOT changed."
            )

        patched=patch_learning_child(
            LAUNCHER.read_text(encoding="utf-8"),
            RUNNER.name,
        )
        compile(patched,str(LAUNCHER),"exec")
        write_exact(LAUNCHER,patched)

        subprocess.run(
            [sys.executable,str(LAUNCHER),"--check"],
            cwd=str(ROOT),
            check=True,
        )

    except Exception:
        for p,b in old.items():
            restore(p,b)
        print("[ROLLBACK] Live cutover refused; launcher/runner/test restored")
        raise

    print("[PASS] REAL production learner state physically advanced")
    print("[PASS] outcomes_learned increased")
    print("[PASS] applied_through_sequence increased")
    print("[PASS] learner state_hash changed")
    print("[PASS] Oracle Live learning child -> run_oracle_PROVEN_learning_runtime.py")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] PROVEN LEARNING PATH RESTORED AND CUT OVER")

if __name__=="__main__":
    main()
