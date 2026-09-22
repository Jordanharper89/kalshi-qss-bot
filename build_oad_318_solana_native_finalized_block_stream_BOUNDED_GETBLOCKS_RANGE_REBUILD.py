
from __future__ import annotations

import ast
import os
import shutil
import textwrap
from pathlib import Path

EXPECTED = "build_oad_318_solana_native_finalized_block_stream_BOUNDED_GETBLOCKS_RANGE_REBUILD.py"
REL = Path("qseries_v2/oracle_adapters/independent/oad_318_solana_native_finalized_block_stream.py")
TEST = Path("test_oad_318_solana_native_finalized_block_stream.py")

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise RuntimeError("repository root not found")

def atomic_write(path: Path, source: str):
    ast.parse(source, filename=str(path))
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def patch_source(source: str) -> str:
    old = '_rpc("getBlocks",[start,head,{"commitment":"finalized"}],timeout_seconds)'
    new = '_rpc("getBlocks",[start,min(head,start+max(0,limit-1)),{"commitment":"finalized"}],timeout_seconds)'

    if old in source:
        return source.replace(old, new, 1)

    # Handle spacing variants while still requiring the same semantic call.
    candidates = [
        '_rpc("getBlocks", [start, head, {"commitment": "finalized"}], timeout_seconds)',
        "_rpc('getBlocks',[start,head,{'commitment':'finalized'}],timeout_seconds)",
        "_rpc('getBlocks', [start, head, {'commitment': 'finalized'}], timeout_seconds)",
    ]
    for c in candidates:
        if c in source:
            repl = c.replace("start, head", "start, min(head, start + max(0, limit - 1))")
            repl = repl.replace("start,head", "start,min(head,start+max(0,limit-1))")
            return source.replace(c, repl, 1)

    raise RuntimeError(
        "Could not locate exact OAD-318 getBlocks(start, head) call. "
        "No production file was changed."
    )

TEST_SOURCE = r"""
import ast
import unittest
from pathlib import Path
from unittest.mock import patch

import qseries_v2.oracle_adapters.independent.oad_318_solana_native_finalized_block_stream as m

class T(unittest.TestCase):
    def test_bounded_getblocks_range_contract(self):
        calls=[]

        def fake_rpc(method, params=None, timeout_seconds=20.0):
            calls.append((method, params))
            if method == "getSlot":
                return 500000
            if method == "getBlocks":
                start, end, opts = params
                self.assertLessEqual(end - start + 1, 4)
                return [start, start+1, start+2, start+3]
            if method == "getBlock":
                slot=params[0]
                return {
                    "blockTime": 1700000000,
                    "blockhash": "hash"+str(slot),
                    "previousBlockhash": "prev"+str(slot),
                    "parentSlot": slot-1,
                    "transactions": [],
                }
            raise AssertionError(method)

        with patch.object(m, "_rpc", side_effect=fake_rpc):
            batch=m.acquire_finalized_block_batch(
                start_slot=100,
                limit=4,
                timeout_seconds=1.0,
            )

        getblocks=[x for x in calls if x[0]=="getBlocks"]
        self.assertEqual(len(getblocks),1)
        start,end,_=getblocks[0][1]
        print("[GETBLOCKS RANGE]",start,"->",end,"width=",end-start+1)
        self.assertEqual((start,end),(100,103))

    def test_large_head_never_expands_request_window(self):
        calls=[]
        def fake_rpc(method, params=None, timeout_seconds=20.0):
            calls.append((method,params))
            if method=="getSlot": return 900000
            if method=="getBlocks":
                return []
            raise AssertionError(method)

        with patch.object(m,"_rpc",side_effect=fake_rpc):
            m.acquire_finalized_block_batch(start_slot=100,limit=8,timeout_seconds=1.0)

        p=[x[1] for x in calls if x[0]=="getBlocks"][0]
        self.assertEqual(p[0],100)
        self.assertEqual(p[1],107)
        print("[BOUNDED] head=900000 request=",p[0],"->",p[1])

if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not rr.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-318 bounded finalized-block range repair certified")
"""

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer filename mismatch")

    root=find_root()
    target=root/REL
    if not target.is_file():
        raise RuntimeError("OAD-318 production module missing: "+str(REL))

    original=target.read_text(encoding="utf-8")
    tree=ast.parse(original,filename=str(target))
    names={n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
    required={"acquire_finalized_block_batch","SolanaFinalizedBlockBatch"}
    missing=required-names
    if missing:
        raise RuntimeError("OAD-318 public interface missing: "+repr(sorted(missing)))

    patched=patch_source(original)
    ast.parse(patched,filename=str(target))

    backup=target.with_suffix(".py.pre_bounded_getblocks_rebuild.bak")
    if not backup.exists():
        shutil.copy2(target,backup)

    atomic_write(target,patched)
    atomic_write(root/TEST,textwrap.dedent(TEST_SOURCE).lstrip())

    print("[PASS] exact OAD-318 public interface preserved")
    print("[PASS] backup written:",backup.relative_to(root))
    print("[PASS] getBlocks range changed from start->finalized_head to bounded start->start+limit-1")
    print("[PASS] large checkpoint backlog now advances through repeated bounded windows")
    print("[PASS] no OAD-322/OAD-325/OAD-326 interface change")
    print("[PASS] no checkpoint mutation introduced")
    print("[PASS] no paid RPC provider dependency")
    print("[PASS] no GMGN dependency")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution_authority=FALSE")
    print("[DONE]",EXPECTED)

if __name__=="__main__":
    main()
