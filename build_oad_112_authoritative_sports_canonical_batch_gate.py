from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION="OAD_112_AUTHORITATIVE_SPORTS_CANONICAL_BATCH_GATE_V1"

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
MODULE=PKG/'oad_112_authoritative_sports_canonical_batch_gate.py'
TEST=ROOT/'test_oad_112_authoritative_sports_canonical_batch_gate.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom uuid import uuid4\n\nfrom .oad_110_authoritative_sports_canonical_bridge import canonicalize_authoritative_sports_observation\nfrom .oad_062_independent_canonical_provenance_validation import validate_independent_canonical\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass AuthoritativeSportsCanonicalBatch:\n    canonical_observations: tuple\n    provenance_validated: int\n    ready_for_existing_single_writer: bool\n    acquisition_batch_id: str\n    execution_authority: bool=False\n\ndef build_authoritative_sports_canonical_batch(observations, acquisition_batch_id=None):\n    items=tuple(observations)\n    if not items:\n        raise ValueError("non-empty authoritative sports observation batch required")\n    batch_id=str(acquisition_batch_id or ("oad112-"+uuid4().hex))\n    canonical=tuple(canonicalize_authoritative_sports_observation(x,batch_id) for x in items)\n    validations=tuple(validate_independent_canonical(x) for x in canonical)\n    valid=sum(1 for x in validations if x.valid)\n    ready=bool(canonical) and valid==len(canonical)\n    return AuthoritativeSportsCanonicalBatch(\n        canonical_observations=canonical,\n        provenance_validated=valid,\n        ready_for_existing_single_writer=ready,\n        acquisition_batch_id=batch_id,\n        execution_authority=False,\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_107_authoritative_sports_source_foundation import build_observation\nfrom qseries_v2.oracle_adapters.independent.oad_112_authoritative_sports_canonical_batch_gate import build_authoritative_sports_canonical_batch\n\nclass T(unittest.TestCase):\n    def test_batch(self):\n        o=build_observation(\n            source_id="mlb:game:1",provider="statsapi.mlb.com",sport_family="baseball",\n            observation_type="official_game_schedule_state",subject="Houston Astros at New York Mets",\n            observed_at="2026-08-28T12:00:00+00:00",\n            source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",\n            payload={"gamePk":1},\n        )\n        r=build_authoritative_sports_canonical_batch((o,),"oad112-test")\n        print("[CANONICAL]",len(r.canonical_observations))\n        print("[PROVENANCE_VALIDATED]",r.provenance_validated)\n        self.assertTrue(r.ready_for_existing_single_writer)\n        self.assertEqual(r.provenance_validated,1)\n        self.assertFalse(r.execution_authority)\n\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-112 authoritative sports canonical batch gate certified")\n'
DEPENDENCIES=['oad_110_authoritative_sports_canonical_bridge.py', 'oad_062_independent_canonical_provenance_validation.py']

def main():
    print("="*112)
    print(" OAD-112 AUTHORITATIVE SPORTS CANONICAL BATCH GATE INSTALLER")
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
        exp="from .oad_112_authoritative_sports_canonical_batch_gate import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] existing certified architecture reused")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-112 INSTALLATION COMPLETE")
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
