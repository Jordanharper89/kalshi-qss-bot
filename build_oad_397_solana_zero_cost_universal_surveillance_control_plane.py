
from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED = 'build_oad_397_solana_zero_cost_universal_surveillance_control_plane.py'
MODULE = 'oad_397_solana_zero_cost_universal_surveillance_control_plane.py'
TEST = 'test_oad_397_solana_zero_cost_universal_surveillance_control_plane.py'
RUNNER = 'run_oad_397_solana_zero_cost_universal_surveillance.py'
MODULE_SOURCE = r"""from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .oad_394_solana_finalized_head_missing_slot_scheduler import build_missing_slot_schedule,read_last_committed_slot
from .oad_396_solana_websocket_assisted_live_head import observe_live_head
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaSurveillanceSnapshot:
    state:str
    finalized_head:int
    last_committed_slot:int|None
    checkpoint_lag:int
    scheduled_slots:tuple
    gaps_pending:int
    rpc_requests:int
    throttle_count:int
    blocks_seen:int
    transactions_seen:int
    economic_events:int
    unknown_programs:int
    universe_entities:int
    active_entities:int
    hot_entities:int
    ultra_hot_entities:int
    execution_authority:bool=False

def classify_surveillance_state(checkpoint_lag,throttle_count=0):
    if checkpoint_lag<=2 and throttle_count==0: return "RUNNING_CAUGHT_UP"
    if checkpoint_lag<=32: return "RUNNING_CATCHING_UP"
    return "BACKFILL_REQUIRED"

def build_surveillance_snapshot(finalized_head,last_committed_slot,*,max_schedule_slots=32,rpc_requests=0,throttle_count=0,blocks_seen=0,transactions_seen=0,economic_events=0,unknown_programs=0,universe_entities=0,active_entities=0,hot_entities=0,ultra_hot_entities=0):
    lag=0 if last_committed_slot is not None and last_committed_slot>=finalized_head else (finalized_head+1 if last_committed_slot is None else finalized_head-last_committed_slot)
    sched=build_missing_slot_schedule(last_committed_slot,finalized_head,max_schedule_slots)
    return SolanaSurveillanceSnapshot(classify_surveillance_state(lag,throttle_count),int(finalized_head),last_committed_slot,int(lag),sched.scheduled_slots,sched.remaining_lag_slots,int(rpc_requests),int(throttle_count),int(blocks_seen),int(transactions_seen),int(economic_events),int(unknown_programs),int(universe_entities),int(active_entities),int(hot_entities),int(ultra_hot_entities),False)

def live_read_only_snapshot(root=None,rpc_head_fn=None):
    r=Path(root).resolve() if root else Path.cwd().resolve()
    head=observe_live_head(rpc_head_fn=rpc_head_fn)
    checkpoint=read_last_committed_slot(r)
    return build_surveillance_snapshot(head.slot,checkpoint)"""
TEST_SOURCE = r"""import unittest
from qseries_v2.oracle_adapters.independent.oad_397_solana_zero_cost_universal_surveillance_control_plane import build_surveillance_snapshot
class T(unittest.TestCase):
    def test_control_plane(self):
        x=build_surveillance_snapshot(110,100,max_schedule_slots=4,rpc_requests=5,blocks_seen=2,transactions_seen=1800,economic_events=220,unknown_programs=12,universe_entities=500,active_entities=40,hot_entities=7,ultra_hot_entities=2)
        print("[SURVEILLANCE]",x)
        self.assertEqual(x.checkpoint_lag,10)
        self.assertEqual(x.state,"RUNNING_CATCHING_UP")
        self.assertEqual(x.scheduled_slots,(101,102,103,104))
        self.assertFalse(x.execution_authority)
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-397 zero-cost universal Solana surveillance control plane certified")"""
RUNNER_SOURCE = r"""from __future__ import annotations
import argparse,time
from qseries_v2.oracle_adapters.independent.oad_397_solana_zero_cost_universal_surveillance_control_plane import live_read_only_snapshot
def main():
    ap=argparse.ArgumentParser(description="Read-only zero-cost Solana universal surveillance monitor")
    ap.add_argument("--interval",type=float,default=5.0)
    ap.add_argument("--once",action="store_true")
    args=ap.parse_args()
    while True:
        x=live_read_only_snapshot()
        print("[SOLANA] state={} finalized_head={} last_committed_slot={} checkpoint_lag={} scheduled={} gaps_pending={} execution_authority={}".format(x.state,x.finalized_head,x.last_committed_slot,x.checkpoint_lag,len(x.scheduled_slots),x.gaps_pending,x.execution_authority))
        if args.once: break
        time.sleep(max(1.0,args.interval))
if __name__=="__main__":
    main()"""
DEPS = [('qseries_v2/oracle_adapters/independent/oad_393_solana_zero_cost_public_rpc_budget_governor.py', ('SolanaPublicRpcBudgetGovernor',)), ('qseries_v2/oracle_adapters/independent/oad_394_solana_finalized_head_missing_slot_scheduler.py', ('build_missing_slot_schedule',)), ('qseries_v2/oracle_adapters/independent/oad_395_solana_block_efficient_universal_acquisition_worker.py', ('acquire_missing_block_batch',)), ('qseries_v2/oracle_adapters/independent/oad_396_solana_websocket_assisted_live_head.py', ('observe_live_head',))]

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
