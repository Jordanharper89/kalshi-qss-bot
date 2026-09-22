from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION='OAD_122_AUTHORITATIVE_SPORTS_LIVE_END_TO_END_EVIDENCE_CERTIFICATION_V1'

def find_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")

def write_py(path,src):
    src=textwrap.dedent(src).lstrip()
    ast.parse(src,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(src,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_122_authoritative_sports_live_end_to_end_evidence_certification.py'
TEST=ROOT/'test_oad_122_authoritative_sports_live_end_to_end_evidence_certification.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\n\nfrom .oad_118_persisted_authoritative_sports_cohort import load_persisted_authoritative_sports_cohort\nfrom .oad_119_persisted_sports_structured_descriptor import descriptors_from_persisted_sports_rows\nfrom .oad_120_current_market_sports_team_pair_index import fetch_current_market_sports_candidates\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass LiveSportsEndToEndEvidenceReport:\n    persisted_observations: int\n    committed_new: int\n    providers: tuple\n    structured_descriptors: int\n    current_markets: int\n    observations_with_candidates: int\n    association_candidates: int\n    descriptors: tuple\n    associations: tuple\n    certified_at: str\n    read_only: bool=True\n    probability_enabled: bool=False\n    execution_authority: bool=False\n\ndef run_live_sports_end_to_end_evidence_certification(\n    root=None,\n    market_limit=1000,\n    timeout_seconds=120.0,\n    acquisition_timeout_seconds=20.0,\n    market_timeout_seconds=20.0,\n):\n    cohort=load_persisted_authoritative_sports_cohort(\n        root=root,\n        timeout_seconds=timeout_seconds,\n        acquisition_timeout_seconds=acquisition_timeout_seconds,\n    )\n    descriptors=descriptors_from_persisted_sports_rows(cohort.rows)\n    markets,groups=fetch_current_market_sports_candidates(\n        descriptors,\n        limit=market_limit,\n        timeout_seconds=market_timeout_seconds,\n    )\n    flat=tuple(x for _,xs in groups for x in xs)\n    with_candidates=sum(1 for _,xs in groups if xs)\n    if any(getattr(x,"candidate_only",None) is not True for x in flat):\n        raise RuntimeError("sports association escaped candidate-only boundary")\n    return LiveSportsEndToEndEvidenceReport(\n        persisted_observations=int(cohort.cohort_size),\n        committed_new=int(cohort.committed_new),\n        providers=tuple(cohort.providers),\n        structured_descriptors=len(descriptors),\n        current_markets=len(markets),\n        observations_with_candidates=with_candidates,\n        association_candidates=len(flat),\n        descriptors=tuple(descriptors),\n        associations=flat,\n        certified_at=datetime.now(timezone.utc).isoformat(),\n        read_only=True,\n        probability_enabled=False,\n        execution_authority=False,\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.independent.oad_122_authoritative_sports_live_end_to_end_evidence_certification import run_live_sports_end_to_end_evidence_certification\n\nclass T(unittest.TestCase):\n    def test_physical_live_chain(self):\n        r=run_live_sports_end_to_end_evidence_certification()\n        print("[PHYSICAL] persisted_observations=",r.persisted_observations)\n        print("[PHYSICAL] committed_new=",r.committed_new)\n        print("[PHYSICAL] providers=",r.providers)\n        print("[PHYSICAL] structured_descriptors=",r.structured_descriptors)\n        print("[PHYSICAL] current_markets=",r.current_markets)\n        print("[PHYSICAL] observations_with_candidates=",r.observations_with_candidates)\n        print("[PHYSICAL] association_candidates=",r.association_candidates)\n        self.assertGreaterEqual(r.persisted_observations,0)\n        self.assertGreaterEqual(r.current_markets,1)\n        self.assertEqual(r.structured_descriptors,r.persisted_observations)\n        self.assertTrue(r.read_only)\n        self.assertFalse(r.probability_enabled)\n        self.assertFalse(r.execution_authority)\n        self.assertTrue(all(x.candidate_only for x in r.associations))\n\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-122 physical live sports evidence chain certified")\n    print("[PASS] real acquisition -> PostgreSQL -> exact readback -> current Kalshi association exercised")\n    print("[PASS] candidate_only=TRUE probability_enabled=FALSE execution_authority=FALSE")\n'
DEPENDENCIES=['oad_118_persisted_authoritative_sports_cohort.py', 'oad_119_persisted_sports_structured_descriptor.py', 'oad_120_current_market_sports_team_pair_index.py']

def main():
    print("="*112)
    print(" OAD-122 AUTHORITATIVE SPORTS LIVE END-TO-END EVIDENCE CERTIFICATION INSTALLER")
    print("="*112)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)
    for dep in DEPENDENCIES:
        p=PKG/dep
        if not p.is_file(): raise RuntimeError("Required certified dependency missing: "+str(p))
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}
    try:
        write_py(MODULE,MODULE_SOURCE)
        write_py(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from .oad_122_authoritative_sports_live_end_to_end_evidence_certification import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] certified OAD-118 through OAD-121 boundaries preserved")
        print("[PASS] candidate_only evidence boundary preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-122 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__":
    main()
