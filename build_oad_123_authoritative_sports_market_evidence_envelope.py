from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

REVISION='OAD_123_AUTHORITATIVE_SPORTS_MARKET_EVIDENCE_ENVELOPE_V1'

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
MODULE=PKG/'oad_123_authoritative_sports_market_evidence_envelope.py'
TEST=ROOT/'test_oad_123_authoritative_sports_market_evidence_envelope.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\n@dataclass(frozen=True, slots=True)\nclass AuthoritativeSportsMarketEvidence:\n    observation_id: str\n    market_id: str\n    source_id: str\n    sport_family: str\n    subject: str\n    away_team: str\n    home_team: str\n    evidence_type: str\n    association_strength: str\n    independent_evidence: bool\n    candidate_only: bool\n    direction: None=None\n    probability: None=None\n    execution_authority: bool=False\n\ndef build_sports_market_evidence_envelopes(report):\n    descriptors={d.observation_id:d for d in tuple(report.descriptors)}\n    out=[]\n    for a in tuple(report.associations):\n        d=descriptors.get(a.observation_id)\n        if d is None:\n            raise RuntimeError("association references unknown sports observation")\n        if d.independent_evidence is not True:\n            raise RuntimeError("sports evidence is not independent")\n        if a.candidate_only is not True:\n            raise RuntimeError("sports market association must remain candidate-only")\n        out.append(AuthoritativeSportsMarketEvidence(\n            observation_id=d.observation_id,\n            market_id=a.market_id,\n            source_id=d.source_id,\n            sport_family=d.sport_family,\n            subject=d.subject,\n            away_team=d.away_team,\n            home_team=d.home_team,\n            evidence_type=d.evidence_type,\n            association_strength=a.association_strength,\n            independent_evidence=True,\n            candidate_only=True,\n            direction=None,\n            probability=None,\n            execution_authority=False,\n        ))\n    return tuple(out)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_123_authoritative_sports_market_evidence_envelope import build_sports_market_evidence_envelopes\n\nclass T(unittest.TestCase):\n    def test_envelope(self):\n        d=SimpleNamespace(\n            observation_id="o1",source_id="source.independent.mlb:game:1",sport_family="baseball",\n            subject="Houston Astros at New York Mets",away_team="Houston Astros",home_team="New York Mets",\n            evidence_type="official_game_schedule_state",independent_evidence=True)\n        a=SimpleNamespace(observation_id="o1",market_id="KXTEST",association_strength="EXACT_TWO_TEAM_PAIR",candidate_only=True)\n        r=build_sports_market_evidence_envelopes(SimpleNamespace(descriptors=(d,),associations=(a,)))\n        print("[EVIDENCE_ENVELOPES]",len(r))\n        print("[MARKET_ID]",r[0].market_id)\n        print("[SOURCE_ID]",r[0].source_id)\n        self.assertEqual(len(r),1)\n        self.assertTrue(r[0].independent_evidence)\n        self.assertIsNone(r[0].direction)\n        self.assertIsNone(r[0].probability)\n        self.assertFalse(r[0].execution_authority)\n\nif __name__=="__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-123 authoritative sports market evidence envelope certified")\n'
DEPENDENCIES=['oad_122_authoritative_sports_live_end_to_end_evidence_certification.py']

def main():
    print("="*112)
    print(" OAD-123 AUTHORITATIVE SPORTS MARKET EVIDENCE ENVELOPE INSTALLER")
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
        exp="from .oad_123_authoritative_sports_market_evidence_envelope import *"
        if exp not in lines: lines.append(exp)
        write_py(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",MODULE.relative_to(ROOT))
        print("[PASS] test installed:",TEST.relative_to(ROOT))
        print("[PASS] syntax validated")
        print("[PASS] certified OAD-118 through OAD-121 boundaries preserved")
        print("[PASS] candidate_only evidence boundary preserved")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-123 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__":
    main()
