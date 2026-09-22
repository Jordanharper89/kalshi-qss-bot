from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION="OAD_113_AUTHORITATIVE_SPORTS_SINGLE_WRITER_BINDING_V1"

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")

def write_py(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_113_authoritative_sports_single_writer_binding.py'
TEST=ROOT/'test_oad_113_authoritative_sports_single_writer_binding.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\n\nfrom .oad_066_independent_single_writer_ingress_binding import (\n    submit_independent_canonical_batch,\n    await_independent_commit,\n    verify_oad_066_independent_single_writer_ingress_binding,\n)\nfrom .oad_112_authoritative_sports_canonical_batch_gate import AuthoritativeSportsCanonicalBatch\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\ndef submit_authoritative_sports_batch(batch: AuthoritativeSportsCanonicalBatch, root=None):\n    if not isinstance(batch, AuthoritativeSportsCanonicalBatch):\n        raise TypeError("AuthoritativeSportsCanonicalBatch required")\n    if not batch.ready_for_existing_single_writer:\n        raise RuntimeError("sports canonical batch is not ready for existing single writer")\n    if batch.execution_authority is not False:\n        raise RuntimeError("execution authority must remain false")\n    return submit_independent_canonical_batch(batch.canonical_observations,root)\n\ndef await_authoritative_sports_commit(request_id, root=None, timeout_seconds=120.0):\n    return await_independent_commit(request_id,root,timeout_seconds)\n\ndef verify_existing_single_writer_boundary():\n    return (\n        verify_oad_066_independent_single_writer_ingress_binding() is True\n        and READ_ONLY\n        and not EXECUTION_AUTHORITY\n        and not PROBABILITY_ENABLED\n    )\n'
TEST_SOURCE='import unittest\nfrom unittest.mock import patch\nfrom types import SimpleNamespace\n\nfrom qseries_v2.oracle_adapters.independent.oad_107_authoritative_sports_source_foundation import build_observation\nfrom qseries_v2.oracle_adapters.independent.oad_112_authoritative_sports_canonical_batch_gate import build_authoritative_sports_canonical_batch\nfrom qseries_v2.oracle_adapters.independent.oad_113_authoritative_sports_single_writer_binding import submit_authoritative_sports_batch\n\nclass T(unittest.TestCase):\n    def test_exact_existing_writer_reuse(self):\n        o=build_observation(\n            source_id="mlb:game:2",provider="statsapi.mlb.com",sport_family="baseball",\n            observation_type="official_game_schedule_state",subject="A at B",\n            observed_at="2026-08-28T12:00:00+00:00",\n            source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",payload={"gamePk":2})\n        batch=build_authoritative_sports_canonical_batch((o,),"oad113-test")\n        with patch("qseries_v2.oracle_adapters.independent.oad_113_authoritative_sports_single_writer_binding.submit_independent_canonical_batch",\n                   return_value=SimpleNamespace(request_id="req-1",observation_count=1)) as p:\n            sub=submit_authoritative_sports_batch(batch)\n        print("[REQUEST_ID]",sub.request_id)\n        print("[OBSERVATION_COUNT]",sub.observation_count)\n        p.assert_called_once()\n        self.assertEqual(sub.observation_count,1)\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-113 existing PostgreSQL single-writer binding certified")\n'
DEPENDENCIES=['oad_066_independent_single_writer_ingress_binding.py', 'oad_112_authoritative_sports_canonical_batch_gate.py']

def main():
    print("="*112)
    print(" OAD-113 AUTHORITATIVE SPORTS SINGLE-WRITER BINDING INSTALLER")
    print("="*112)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)
    for dep in DEPENDENCIES:
        p=PKG/dep
        if not p.is_file():
            raise RuntimeError("Required certified dependency missing: "+str(p))
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}
    try:
        write_py(MODULE,MODULE_SOURCE)
        write_py(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from .oad_113_authoritative_sports_single_writer_binding import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] existing certified architecture reused")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-113 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__":
    main()
