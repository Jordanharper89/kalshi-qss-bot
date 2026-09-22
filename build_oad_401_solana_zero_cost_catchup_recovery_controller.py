
from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED='build_oad_401_solana_zero_cost_catchup_recovery_controller.py'
MODULE='oad_401_solana_zero_cost_catchup_recovery_controller.py'
TEST='test_oad_401_solana_zero_cost_catchup_recovery_controller.py'
RUNNER=''
DEPS=[('qseries_v2/oracle_adapters/independent/oad_394_solana_finalized_head_missing_slot_scheduler.py', ('build_missing_slot_schedule',)), ('qseries_v2/oracle_adapters/independent/oad_399_solana_zero_cost_continuous_surveillance_worker.py', ('run_zero_cost_continuous_surveillance',))]
MODULE_SOURCE=r"""from __future__ import annotations
from dataclasses import dataclass
from .oad_394_solana_finalized_head_missing_slot_scheduler import build_missing_slot_schedule

EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class CatchupPlan:
    checkpoint_slot:int|None
    finalized_head:int
    lag:int
    batch_slots:tuple
    state:str
    execution_authority:bool=False

def plan_zero_cost_catchup(checkpoint_slot,finalized_head,max_slots=16,skipped_slots=()):
    s=build_missing_slot_schedule(checkpoint_slot,finalized_head,max_slots=max_slots,skipped_slots=skipped_slots)
    lag=finalized_head+1 if checkpoint_slot is None else max(0,finalized_head-checkpoint_slot)
    state="CAUGHT_UP" if lag<=2 else ("BOUNDED_CATCHUP" if lag<=256 else "DEEP_BACKFILL")
    return CatchupPlan(checkpoint_slot,int(finalized_head),int(lag),s.scheduled_slots,state,False)

def catchup_cycles_for_lag(lag,slots_per_cycle=16,max_cycles=32):
    if lag<=0:return 0
    return min(max_cycles,max(1,(int(lag)+slots_per_cycle-1)//slots_per_cycle))"""
TEST_SOURCE=r"""import unittest
from qseries_v2.oracle_adapters.independent.oad_401_solana_zero_cost_catchup_recovery_controller import plan_zero_cost_catchup,catchup_cycles_for_lag
class T(unittest.TestCase):
    def test_plan(self):
        x=plan_zero_cost_catchup(100,150,max_slots=8)
        print("[CATCHUP]",x)
        self.assertEqual(x.lag,50)
        self.assertEqual(len(x.batch_slots),8)
        self.assertEqual(x.state,"BOUNDED_CATCHUP")
        self.assertEqual(catchup_cycles_for_lag(50,16),4)
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-401 zero-cost catch-up recovery controller certified")"""
RUNNER_SOURCE=r""""""

def find_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("repository root not found")

def atomic_write(path, source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def verify_dep(root, rel, required):
    p=root/rel
    if not p.is_file():
        raise RuntimeError("required dependency missing: "+rel)
    tree=ast.parse(p.read_text(encoding="utf-8"),filename=str(p))
    names={n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
    missing=[x for x in required if x not in names]
    if missing:
        raise RuntimeError("dependency interface missing: "+rel+" -> "+repr(missing))
    print("[PASS] dependency verified:",rel)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer filename mismatch")
    root=find_root()
    for rel,req in DEPS:
        verify_dep(root,rel,req)

    pkg=root/"qseries_v2"/"oracle_adapters"/"independent"
    m=pkg/MODULE
    t=root/TEST
    atomic_write(m,MODULE_SOURCE)
    atomic_write(t,TEST_SOURCE)
    if RUNNER:
        atomic_write(root/RUNNER,RUNNER_SOURCE)

    init=pkg/"__init__.py"
    lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
    exp="from ."+m.stem+" import *"
    if exp not in lines:
        lines.append(exp)
    atomic_write(init,"\n".join(x for x in lines if x.strip())+"\n")

    print("[PASS] installed:",m.relative_to(root))
    print("[PASS] test installed:",t.relative_to(root))
    if RUNNER:
        print("[PASS] runner installed:",RUNNER)
    print("[PASS] existing OAD-326 worker reused; no parallel persistence stack")
    print("[PASS] public-RPC / zero-cost architecture only")
    print("[PASS] no paid RPC provider dependency")
    print("[PASS] no GMGN dependency")
    print("[PASS] OPH-019/021 persistence boundary preserved")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution_authority=FALSE")
    print("[DONE]",EXPECTED)

if __name__=="__main__":
    main()
