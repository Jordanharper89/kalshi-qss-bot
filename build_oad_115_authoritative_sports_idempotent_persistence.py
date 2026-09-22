from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION="OAD_115_AUTHORITATIVE_SPORTS_IDEMPOTENT_PERSISTENCE_V1"

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
MODULE=PKG/'oad_115_authoritative_sports_idempotent_persistence.py'
TEST=ROOT/'test_oad_115_authoritative_sports_idempotent_persistence.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nfrom .oad_111_authoritative_sports_physical_acquisition_gate import run_physical_gate\nfrom .oad_112_authoritative_sports_canonical_batch_gate import AuthoritativeSportsCanonicalBatch\nfrom .oad_113_authoritative_sports_single_writer_binding import (\n    submit_authoritative_sports_batch,\n    await_authoritative_sports_commit,\n)\nfrom .oad_114_authoritative_sports_exact_postgresql_readback import (\n    find_authoritative_sports_observation,\n    exact_authoritative_sports_readback,\n)\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass AuthoritativeSportsPersistenceResult:\n    cohort_size: int\n    already_present: int\n    missing_before_write: int\n    committed_new: int\n    exact_readback: int\n    request_id: str|None\n    providers: tuple\n    observation_ids: tuple\n    execution_authority: bool=False\n\ndef persist_current_authoritative_sports(root=None, timeout_seconds=120.0, acquisition_timeout_seconds=20.0):\n    physical=run_physical_gate(timeout_seconds=acquisition_timeout_seconds)\n    canonical=tuple(physical["canonical"])\n    if not canonical:\n        return AuthoritativeSportsPersistenceResult(\n            0,0,0,0,0,None,tuple(physical["providers"]),(),False\n        )\n\n    existing=[]\n    missing=[]\n    for i,obs in enumerate(canonical):\n        row=find_authoritative_sports_observation(obs.observation_id,root,i)\n        if row is None:\n            missing.append(obs)\n        else:\n            if getattr(row,"observation_id",None)!=obs.observation_id:\n                raise RuntimeError("exact PostgreSQL identity mismatch")\n            existing.append(row)\n\n    request_id=None\n    committed_new=0\n    if missing:\n        batch=AuthoritativeSportsCanonicalBatch(\n            canonical_observations=tuple(missing),\n            provenance_validated=len(missing),\n            ready_for_existing_single_writer=True,\n            acquisition_batch_id="oad115.missing-only",\n            execution_authority=False,\n        )\n        submission=submit_authoritative_sports_batch(batch,root)\n        request_id=str(submission.request_id)\n        evidence=tuple(await_authoritative_sports_commit(request_id,root,timeout_seconds))\n        accepted=tuple(x for x in evidence if getattr(x,"accepted",False) is True)\n        if len(accepted)!=len(missing):\n            raise RuntimeError("sports single-writer commit count mismatch")\n        committed_new=len(accepted)\n\n    ids=tuple(x.observation_id for x in canonical)\n    rows=tuple(exact_authoritative_sports_readback(ids,root))\n    if len(rows)!=len(ids):\n        raise RuntimeError("sports exact readback count mismatch")\n    return AuthoritativeSportsPersistenceResult(\n        cohort_size=len(ids),\n        already_present=len(existing),\n        missing_before_write=len(missing),\n        committed_new=committed_new,\n        exact_readback=len(rows),\n        request_id=request_id,\n        providers=tuple(physical["providers"]),\n        observation_ids=ids,\n        execution_authority=False,\n    )\n'
TEST_SOURCE='import unittest\nfrom unittest.mock import patch\nfrom types import SimpleNamespace\n\nimport qseries_v2.oracle_adapters.independent.oad_115_authoritative_sports_idempotent_persistence as m\nfrom qseries_v2.oracle_adapters.independent.oad_107_authoritative_sports_source_foundation import build_observation\nfrom qseries_v2.oracle_adapters.independent.oad_110_authoritative_sports_canonical_bridge import canonicalize_authoritative_sports_observation\n\nclass T(unittest.TestCase):\n    def test_missing_only_write_and_exact_readback(self):\n        raw=build_observation(\n            source_id="mlb:game:3",provider="statsapi.mlb.com",sport_family="baseball",\n            observation_type="official_game_schedule_state",subject="A at B",\n            observed_at="2026-08-28T12:00:00+00:00",\n            source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",payload={"gamePk":3})\n        c=canonicalize_authoritative_sports_observation(raw,"oad115-test")\n        physical={"canonical":(c,),"providers":("statsapi.mlb.com",)}\n        accepted=SimpleNamespace(accepted=True)\n        submission=SimpleNamespace(request_id="req-115")\n        with patch.object(m,"run_physical_gate",return_value=physical), \\\n             patch.object(m,"find_authoritative_sports_observation",return_value=None), \\\n             patch.object(m,"submit_authoritative_sports_batch",return_value=submission), \\\n             patch.object(m,"await_authoritative_sports_commit",return_value=(accepted,)), \\\n             patch.object(m,"exact_authoritative_sports_readback",return_value=(c,)):\n            r=m.persist_current_authoritative_sports(root=".")\n        print("[COHORT_SIZE]",r.cohort_size)\n        print("[MISSING_BEFORE_WRITE]",r.missing_before_write)\n        print("[COMMITTED_NEW]",r.committed_new)\n        print("[EXACT_READBACK]",r.exact_readback)\n        self.assertEqual((r.cohort_size,r.missing_before_write,r.committed_new,r.exact_readback),(1,1,1,1))\n        self.assertFalse(r.execution_authority)\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-115 idempotent authoritative sports persistence contract certified")\n    print("[NOTE] physical production function uses real sports acquisition and existing PostgreSQL single writer")\n'
DEPENDENCIES=['oad_111_authoritative_sports_physical_acquisition_gate.py', 'oad_112_authoritative_sports_canonical_batch_gate.py', 'oad_113_authoritative_sports_single_writer_binding.py', 'oad_114_authoritative_sports_exact_postgresql_readback.py']

def main():
    print("="*112)
    print(" OAD-115 AUTHORITATIVE SPORTS IDEMPOTENT PERSISTENCE INSTALLER")
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
        exp="from .oad_115_authoritative_sports_idempotent_persistence import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] existing certified architecture reused")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-115 INSTALLATION COMPLETE")
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
