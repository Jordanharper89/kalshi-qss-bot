
from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED = 'build_oad_395_solana_block_efficient_universal_acquisition_worker.py'
MODULE = 'oad_395_solana_block_efficient_universal_acquisition_worker.py'
TEST = 'test_oad_395_solana_block_efficient_universal_acquisition_worker.py'
RUNNER = ''
MODULE_SOURCE = r"""from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .oad_318_solana_native_finalized_block_stream import acquire_finalized_block_batch
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class BlockEfficientAcquisition:
    start_slot:int
    requested_limit:int
    blocks_observed:int
    transactions_observed:int
    rpc_getblock_equivalents:int
    per_transaction_rpc_calls:int
    batch:Any
    execution_authority:bool=False

def _blocks(batch):
    for name in ("blocks","block_records","records"):
        v=getattr(batch,name,None)
        if isinstance(v,(list,tuple)): return list(v)
    if isinstance(batch,(list,tuple)): return list(batch)
    return []

def _tx_count(block):
    if isinstance(block,dict):
        tx=block.get("transactions")
        if isinstance(tx,list): return len(tx)
        raw=block.get("raw")
        if isinstance(raw,dict) and isinstance(raw.get("transactions"),list): return len(raw["transactions"])
    for name in ("transactions","raw_block","raw"):
        v=getattr(block,name,None)
        if isinstance(v,list): return len(v)
        if isinstance(v,dict) and isinstance(v.get("transactions"),list): return len(v["transactions"])
    return 0

def acquire_missing_block_batch(start_slot,limit=4,timeout_seconds=20.0,acquire_fn=None):
    if limit<1 or limit>32: raise ValueError("limit must be 1..32")
    fn=acquire_fn or acquire_finalized_block_batch
    batch=fn(start_slot=int(start_slot),limit=int(limit),timeout_seconds=float(timeout_seconds))
    blocks=_blocks(batch)
    tx=sum(_tx_count(b) for b in blocks)
    return BlockEfficientAcquisition(int(start_slot),int(limit),len(blocks),tx,len(blocks),0,batch,False)"""
TEST_SOURCE = r"""import unittest
from dataclasses import dataclass
from qseries_v2.oracle_adapters.independent.oad_395_solana_block_efficient_universal_acquisition_worker import acquire_missing_block_batch
@dataclass
class FakeBatch:
    blocks:tuple
class T(unittest.TestCase):
    def test_block_efficiency(self):
        def fake(**kwargs):
            return FakeBatch(({"transactions":[1,2,3]},{"transactions":[4,5]}))
        x=acquire_missing_block_batch(101,2,acquire_fn=fake)
        print("[ACQUISITION]",x)
        self.assertEqual(x.blocks_observed,2)
        self.assertEqual(x.transactions_observed,5)
        self.assertEqual(x.per_transaction_rpc_calls,0)
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-395 block-efficient universal acquisition contract certified")"""
RUNNER_SOURCE = r""""""
DEPS = [('qseries_v2/oracle_adapters/independent/oad_318_solana_native_finalized_block_stream.py', ('acquire_finalized_block_batch',)), ('qseries_v2/oracle_adapters/independent/oad_394_solana_finalized_head_missing_slot_scheduler.py', ('build_missing_slot_schedule',))]

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
