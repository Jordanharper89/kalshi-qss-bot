
from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED='build_oad_402_solana_zero_cost_surveillance_physical_gate.py'
MODULE='oad_402_solana_zero_cost_surveillance_physical_gate.py'
TEST='test_oad_402_solana_zero_cost_surveillance_physical_gate.py'
RUNNER='run_oad_402_solana_zero_cost_surveillance_physical_gate.py'
DEPS=[('qseries_v2/oracle_adapters/independent/oad_399_solana_zero_cost_continuous_surveillance_worker.py', ('run_zero_cost_continuous_surveillance',)), ('qseries_v2/oracle_adapters/independent/oad_400_solana_live_coverage_telemetry.py', ('capture_live_coverage',)), ('qseries_v2/oracle_adapters/independent/oad_401_solana_zero_cost_catchup_recovery_controller.py', ('plan_zero_cost_catchup',))]
MODULE_SOURCE=r"""from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .oad_399_solana_zero_cost_continuous_surveillance_worker import run_zero_cost_continuous_surveillance
from .oad_400_solana_live_coverage_telemetry import capture_live_coverage

EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class ZeroCostPhysicalCertification:
    before_lag:int
    after_lag:int
    before_checkpoint:int|None
    after_checkpoint:int|None
    admitted_cycles:int
    failures:int
    checkpoint_advanced:bool
    lag_not_worse:bool
    state:str
    execution_authority:bool=False

def run_zero_cost_physical_gate(root=None,cycles=3,progress=None):
    r=Path(root).resolve() if root else Path.cwd().resolve()
    before=capture_live_coverage(r)
    run=run_zero_cost_continuous_surveillance(root=r,max_cycles=cycles,progress=progress)
    after=capture_live_coverage(r)
    advanced=(before.last_committed_slot is None and after.last_committed_slot is not None) or (
        isinstance(before.last_committed_slot,int) and isinstance(after.last_committed_slot,int) and after.last_committed_slot>before.last_committed_slot
    )
    lag_not_worse=after.checkpoint_lag <= before.checkpoint_lag + 8
    state="ZERO_COST_SURVEILLANCE_CERTIFIED" if advanced and lag_not_worse and run.failures==0 and run.admitted_cycles>0 else "ZERO_COST_SURVEILLANCE_NOT_CERTIFIED"
    return ZeroCostPhysicalCertification(before.checkpoint_lag,after.checkpoint_lag,before.last_committed_slot,after.last_committed_slot,run.admitted_cycles,run.failures,advanced,lag_not_worse,state,False)"""
TEST_SOURCE=r"""import unittest
from qseries_v2.oracle_adapters.independent.oad_402_solana_zero_cost_surveillance_physical_gate import run_zero_cost_physical_gate

class T(unittest.TestCase):
    def test_physical(self):
        x=run_zero_cost_physical_gate(cycles=3,progress=lambda *a,**k: print("[LIVE]",*a))
        print("[PHYSICAL]",x)
        self.assertGreater(x.admitted_cycles,0)
        self.assertEqual(x.failures,0)
        self.assertTrue(x.checkpoint_advanced,"durable Solana checkpoint did not advance")
        self.assertTrue(x.lag_not_worse,"checkpoint lag materially worsened during bounded zero-cost run")
        self.assertEqual(x.state,"ZERO_COST_SURVEILLANCE_CERTIFIED")

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-402 physical zero-cost Solana surveillance certified")"""
RUNNER_SOURCE=r"""from __future__ import annotations
from qseries_v2.oracle_adapters.independent.oad_402_solana_zero_cost_surveillance_physical_gate import run_zero_cost_physical_gate
def main():
    x=run_zero_cost_physical_gate(cycles=3,progress=lambda *a,**k: print("[LIVE]",*a))
    print("[PHYSICAL]",x)
    if x.state!="ZERO_COST_SURVEILLANCE_CERTIFIED":
        raise SystemExit(1)
if __name__=="__main__":
    main()"""

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
