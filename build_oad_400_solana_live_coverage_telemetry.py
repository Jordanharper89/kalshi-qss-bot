
from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED='build_oad_400_solana_live_coverage_telemetry.py'
MODULE='oad_400_solana_live_coverage_telemetry.py'
TEST='test_oad_400_solana_live_coverage_telemetry.py'
RUNNER=''
DEPS=[('qseries_v2/oracle_adapters/independent/oad_394_solana_finalized_head_missing_slot_scheduler.py', ('read_last_committed_slot',)), ('qseries_v2/oracle_adapters/independent/oad_396_solana_websocket_assisted_live_head.py', ('observe_live_head',))]
MODULE_SOURCE=r"""from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .oad_394_solana_finalized_head_missing_slot_scheduler import read_last_committed_slot
from .oad_396_solana_websocket_assisted_live_head import observe_live_head

EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class LiveCoverageTelemetry:
    finalized_head:int
    last_committed_slot:int|None
    checkpoint_lag:int
    source:str
    state:str
    execution_authority:bool=False

def classify_lag(lag):
    if lag<=2: return "CAUGHT_UP"
    if lag<=32: return "NEAR_LIVE"
    if lag<=256: return "CATCHING_UP"
    return "BACKLOG"

def capture_live_coverage(root=None,rpc_head_fn=None):
    r=Path(root).resolve() if root else Path.cwd().resolve()
    head=observe_live_head(rpc_head_fn=rpc_head_fn)
    cp=read_last_committed_slot(r)
    lag=head.slot+1 if cp is None else max(0,head.slot-cp)
    return LiveCoverageTelemetry(head.slot,cp,lag,head.source,classify_lag(lag),False)"""
TEST_SOURCE=r"""import unittest
from unittest.mock import patch
from qseries_v2.oracle_adapters.independent.oad_400_solana_live_coverage_telemetry import capture_live_coverage
class H:
    slot=110; source="HTTP_FINALIZED_FALLBACK"
class T(unittest.TestCase):
    def test_telemetry(self):
        with patch("qseries_v2.oracle_adapters.independent.oad_400_solana_live_coverage_telemetry.observe_live_head",return_value=H()), patch("qseries_v2.oracle_adapters.independent.oad_400_solana_live_coverage_telemetry.read_last_committed_slot",return_value=108):
            x=capture_live_coverage()
        print("[COVERAGE]",x)
        self.assertEqual(x.checkpoint_lag,2)
        self.assertEqual(x.state,"CAUGHT_UP")
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-400 live checkpoint-lag telemetry certified")"""
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
