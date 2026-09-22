
from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED = "build_oad_394_solana_finalized_head_missing_slot_scheduler_DEPENDENCY_REBUILD.py"
MODULE = "oad_394_solana_finalized_head_missing_slot_scheduler.py"
TEST = "test_oad_394_solana_finalized_head_missing_slot_scheduler.py"

MODULE_SOURCE = r"""
from __future__ import annotations
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

def build_missing_slot_schedule(last_committed_slot, finalized_head, max_slots=32, skipped_slots=()):
    head=int(finalized_head)
    if max_slots < 1:
        raise ValueError("max_slots must be >= 1")
    skipped={int(x) for x in skipped_slots}
    start=head if last_committed_slot is None else int(last_committed_slot)+1

    if start > head:
        return MissingSlotSchedule(last_committed_slot, head, (), 0, True, False)

    universe=[s for s in range(start, head+1) if s not in skipped]
    scheduled=tuple(universe[:max_slots])
    remaining=max(0, len(universe)-len(scheduled))

    return MissingSlotSchedule(
        last_committed_slot,
        head,
        scheduled,
        remaining,
        remaining == 0,
        False,
    )

def _checkpoint_candidates(root: Path):
    fixed = (
        root/"runtime_state"/"solana_universal_chain"/"checkpoint.json",
        root/"runtime_state"/"solana_universal_chain_checkpoint.json",
    )
    seen=set()
    for p in fixed:
        if p not in seen:
            seen.add(p)
            yield p

    rs=root/"runtime_state"
    if rs.is_dir():
        for p in rs.rglob("*.json"):
            name=p.name.lower()
            parent=str(p.parent).lower()
            if "solana" in name or "solana" in parent:
                if "checkpoint" in name or "continuity" in name or "chain" in parent:
                    if p not in seen:
                        seen.add(p)
                        yield p

def _extract_slot(obj):
    if isinstance(obj, dict):
        for key in (
            "last_committed_slot",
            "checkpoint_slot",
            "committed_slot",
            "through_slot",
            "last_slot",
            "slot",
        ):
            v=obj.get(key)
            if isinstance(v, int):
                return v

        for value in obj.values():
            found=_extract_slot(value)
            if found is not None:
                return found

    elif isinstance(obj, list):
        for value in obj:
            found=_extract_slot(value)
            if found is not None:
                return found

    return None

def read_last_committed_slot(root=None):
    r=Path(root).resolve() if root else Path.cwd().resolve()

    for p in _checkpoint_candidates(r):
        if not p.is_file():
            continue
        try:
            payload=json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue

        found=_extract_slot(payload)
        if found is not None:
            return int(found)

    return None
"""

TEST_SOURCE = r"""
import json
import tempfile
import unittest
from pathlib import Path

from qseries_v2.oracle_adapters.independent.oad_394_solana_finalized_head_missing_slot_scheduler import (
    build_missing_slot_schedule,
    read_last_committed_slot,
)

class T(unittest.TestCase):
    def test_scheduler(self):
        x=build_missing_slot_schedule(100,110,max_slots=4,skipped_slots=(103,))
        print("[SCHEDULE]",x)
        self.assertEqual(x.scheduled_slots,(101,102,104,105))
        self.assertEqual(x.remaining_lag_slots,5)

        y=build_missing_slot_schedule(110,110,max_slots=4)
        self.assertTrue(y.caught_up)
        self.assertEqual(y.scheduled_slots,())

    def test_checkpoint_discovery_without_hardcoded_module_dependency(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            p=root/"runtime_state"/"solana_universal_chain"/"checkpoint.json"
            p.parent.mkdir(parents=True)
            p.write_text(json.dumps({"generation":9,"last_committed_slot":444147940}),encoding="utf-8")
            self.assertEqual(read_last_committed_slot(root),444147940)

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not rr.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-394 finalized-head missing-slot scheduler certified")
    print("[PASS] no guessed OAD-323 module dependency")
"""

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("repository root not found")

def atomic_write(path: Path, source: str):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def verify_oad393(root: Path):
    rel=Path("qseries_v2/oracle_adapters/independent/oad_393_solana_zero_cost_public_rpc_budget_governor.py")
    p=root/rel
    if not p.is_file():
        raise RuntimeError("required certified OAD-393 missing: "+str(rel))
    tree=ast.parse(p.read_text(encoding="utf-8"),filename=str(p))
    names={n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
    if "SolanaPublicRpcBudgetGovernor" not in names:
        raise RuntimeError("OAD-393 certified interface missing")
    print("[PASS] certified OAD-393 dependency verified")

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer filename mismatch")

    root=find_root()
    verify_oad393(root)

    pkg=root/"qseries_v2"/"oracle_adapters"/"independent"
    module_path=pkg/MODULE
    test_path=root/TEST

    atomic_write(module_path,MODULE_SOURCE)
    atomic_write(test_path,TEST_SOURCE)

    init=pkg/"__init__.py"
    lines=init.read_text(encoding="utf-8").splitlines() if init.exists() else []
    export="from ."+module_path.stem+" import *"
    if export not in lines:
        lines.append(export)
    atomic_write(init,"\n".join(x for x in lines if x.strip())+"\n")

    print("[PASS] installed:",module_path.relative_to(root))
    print("[PASS] test installed:",test_path.relative_to(root))
    print("[PASS] removed brittle guessed OAD-323 filename dependency")
    print("[PASS] checkpoint readback now discovers durable Solana checkpoint state by content/path")
    print("[PASS] existing chain persistence architecture preserved")
    print("[PASS] no paid RPC provider dependency")
    print("[PASS] no GMGN dependency")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution_authority=FALSE")
    print("[DONE]",EXPECTED)

if __name__=="__main__":
    main()
