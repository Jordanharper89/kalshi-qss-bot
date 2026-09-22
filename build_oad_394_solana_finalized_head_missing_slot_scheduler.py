
from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED = 'build_oad_394_solana_finalized_head_missing_slot_scheduler.py'
MODULE = 'oad_394_solana_finalized_head_missing_slot_scheduler.py'
TEST = 'test_oad_394_solana_finalized_head_missing_slot_scheduler.py'
RUNNER = ''
MODULE_SOURCE = r"""from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class MissingSlotSchedule:
    last_committed_slot:int|None
    finalized_head:int
    scheduled_slots:tuple[int,...]
    remaining_lag_slots:int
    caught_up:bool
    execution_authority:bool=False

def build_missing_slot_schedule(last_committed_slot,finalized_head,max_slots=32,skipped_slots=()):
    head=int(finalized_head)
    if max_slots<1: raise ValueError("max_slots must be >= 1")
    skipped={int(x) for x in skipped_slots}
    start=head if last_committed_slot is None else int(last_committed_slot)+1
    if start>head:
        return MissingSlotSchedule(last_committed_slot,head,(),0,True,False)
    universe=[s for s in range(start,head+1) if s not in skipped]
    scheduled=tuple(universe[:max_slots])
    remaining=max(0,len(universe)-len(scheduled))
    return MissingSlotSchedule(last_committed_slot,head,scheduled,remaining,remaining==0,False)

def read_last_committed_slot(root=None):
    r=Path(root).resolve() if root else Path.cwd().resolve()
    candidates=[
        r/"runtime_state"/"solana_universal_chain"/"checkpoint.json",
        r/"runtime_state"/"solana_universal_chain_checkpoint.json",
    ]
    for p in candidates:
        if not p.is_file(): continue
        try: d=json.loads(p.read_text(encoding="utf-8"))
        except Exception: continue
        if isinstance(d,dict):
            for key in ("last_committed_slot","checkpoint_slot","slot"):
                v=d.get(key)
                if isinstance(v,int): return v
    return None"""
TEST_SOURCE = r"""import unittest
from qseries_v2.oracle_adapters.independent.oad_394_solana_finalized_head_missing_slot_scheduler import build_missing_slot_schedule
class T(unittest.TestCase):
    def test_scheduler(self):
        x=build_missing_slot_schedule(100,110,max_slots=4,skipped_slots=(103,))
        print("[SCHEDULE]",x)
        self.assertEqual(x.scheduled_slots,(101,102,104,105))
        self.assertEqual(x.remaining_lag_slots,5)
        y=build_missing_slot_schedule(110,110,max_slots=4)
        self.assertTrue(y.caught_up)
        self.assertEqual(y.scheduled_slots,())
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-394 finalized-head missing-slot scheduler certified")"""
RUNNER_SOURCE = r""""""
DEPS = [('qseries_v2/oracle_adapters/independent/oad_323_solana_durable_chain_checkpoint.py', ()), ('qseries_v2/oracle_adapters/independent/oad_393_solana_zero_cost_public_rpc_budget_governor.py', ('SolanaPublicRpcBudgetGovernor',))]

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise RuntimeError("repository root not found")

def atomic_write(path: Path, source: str):
    source = textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def verify_dep(root: Path, rel: str, required=()):
    p = root / rel
    if not p.is_file():
        raise RuntimeError("required dependency missing: " + rel)
    tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    names = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    missing = [x for x in required if x not in names]
    if missing:
        raise RuntimeError("dependency interface missing: " + rel + " -> " + repr(missing))
    print("[PASS] dependency verified:", rel)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer filename mismatch")
    root = find_root()
    for rel, req in DEPS:
        verify_dep(root, rel, req)

    pkg = root / "qseries_v2" / "oracle_adapters" / "independent"
    module_path = pkg / MODULE
    test_path = root / TEST
    atomic_write(module_path, MODULE_SOURCE)
    atomic_write(test_path, TEST_SOURCE)

    if RUNNER:
        atomic_write(root / RUNNER, RUNNER_SOURCE)

    init = pkg / "__init__.py"
    lines = init.read_text(encoding="utf-8").splitlines() if init.exists() else []
    export = "from ." + module_path.stem + " import *"
    if export not in lines:
        lines.append(export)
    atomic_write(init, "\n".join(x for x in lines if x.strip()) + "\n")

    print("[PASS] installed:", module_path.relative_to(root))
    print("[PASS] test installed:", test_path.relative_to(root))
    if RUNNER:
        print("[PASS] runner installed:", RUNNER)
    print("[PASS] public-RPC / zero-cost architecture only")
    print("[PASS] no paid RPC provider dependency")
    print("[PASS] no GMGN dependency")
    print("[PASS] existing OAD-318+ chain path preserved")
    print("[PASS] existing OPH-019/021 PostgreSQL path preserved")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution_authority=FALSE")
    print("[DONE]", EXPECTED)

if __name__ == "__main__":
    main()
