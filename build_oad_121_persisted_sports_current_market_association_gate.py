from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION="OAD_121_PERSISTED_SPORTS_CURRENT_MARKET_ASSOCIATION_GATE_V1"

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
MODULE=PKG/'oad_121_persisted_sports_current_market_association_gate.py'
TEST=ROOT/'test_oad_121_persisted_sports_current_market_association_gate.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nfrom .oad_118_persisted_authoritative_sports_cohort import load_persisted_authoritative_sports_cohort\nfrom .oad_119_persisted_sports_structured_descriptor import descriptors_from_persisted_sports_rows\nfrom .oad_120_current_market_sports_team_pair_index import fetch_current_market_sports_candidates\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass PersistedSportsAssociationReport:\n    persisted_observations: int\n    structured_descriptors: int\n    current_markets: int\n    observations_with_candidates: int\n    association_candidates: int\n    associations: tuple\n    ready_for_reasoning_evidence_comparison: bool\n    execution_authority: bool=False\n\ndef run_persisted_sports_current_market_association_gate(\n    root=None,\n    market_limit=1000,\n    timeout_seconds=120.0,\n    acquisition_timeout_seconds=20.0,\n    market_timeout_seconds=20.0,\n):\n    cohort=load_persisted_authoritative_sports_cohort(\n        root=root,\n        timeout_seconds=timeout_seconds,\n        acquisition_timeout_seconds=acquisition_timeout_seconds,\n    )\n    descriptors=descriptors_from_persisted_sports_rows(cohort.rows)\n    markets,groups=fetch_current_market_sports_candidates(\n        descriptors,\n        limit=market_limit,\n        timeout_seconds=market_timeout_seconds,\n    )\n    flat=tuple(x for _,xs in groups for x in xs)\n    with_candidates=sum(1 for _,xs in groups if xs)\n    return PersistedSportsAssociationReport(\n        persisted_observations=cohort.cohort_size,\n        structured_descriptors=len(descriptors),\n        current_markets=len(markets),\n        observations_with_candidates=with_candidates,\n        association_candidates=len(flat),\n        associations=flat,\n        ready_for_reasoning_evidence_comparison=bool(flat),\n        execution_authority=False,\n    )\n'
TEST_SOURCE='import unittest\nfrom unittest.mock import patch\nfrom types import SimpleNamespace\nimport qseries_v2.oracle_adapters.independent.oad_121_persisted_sports_current_market_association_gate as m\n\nclass T(unittest.TestCase):\n    def test_candidate_only_gate(self):\n        row=SimpleNamespace(\n            observation_id="o1",\n            source_id="source.independent.mlb:game:1",\n            payload=(("subject","Houston Astros at New York Mets"),("independent_evidence",True)),\n        )\n        cohort=SimpleNamespace(rows=(row,),cohort_size=1)\n        candidate=SimpleNamespace(market_id="KXTEST",candidate_only=True)\n        with patch.object(m,"load_persisted_authoritative_sports_cohort",return_value=cohort), \\\n             patch.object(m,"fetch_current_market_sports_candidates",\n                          return_value=(({"ticker":"KXTEST"},),((SimpleNamespace(observation_id="o1"),(candidate,)),))):\n            r=m.run_persisted_sports_current_market_association_gate(root=".")\n        print("[PERSISTED]",r.persisted_observations)\n        print("[CURRENT_MARKETS]",r.current_markets)\n        print("[ASSOCIATION_CANDIDATES]",r.association_candidates)\n        print("[READY_FOR_REASONING_EVIDENCE_COMPARISON]",r.ready_for_reasoning_evidence_comparison)\n        self.assertEqual(r.association_candidates,1)\n        self.assertTrue(r.ready_for_reasoning_evidence_comparison)\n        self.assertFalse(r.execution_authority)\n\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-121 persisted sports current-market association gate certified")\n    print("[NOTE] associations remain candidate_only; no direction/probability is manufactured")\n'
DEPENDENCIES=['oad_118_persisted_authoritative_sports_cohort.py', 'oad_119_persisted_sports_structured_descriptor.py', 'oad_120_current_market_sports_team_pair_index.py']

def main():
    print("="*112)
    print(" OAD-121 PERSISTED SPORTS CURRENT-MARKET ASSOCIATION GATE INSTALLER")
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
        exp="from .oad_121_persisted_sports_current_market_association_gate import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] existing certified boundaries preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-121 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__":
    main()
