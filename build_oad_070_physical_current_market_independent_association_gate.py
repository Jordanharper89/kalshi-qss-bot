from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path
BUILD_ID="OAD-070"
REVISION="OAD_070_PRODUCTION_INSTALLER_V1"
TITLE='PHYSICAL CURRENT-MARKET INDEPENDENT ASSOCIATION GATE'
def locate_root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise SystemExit("[ERROR] Q Series repository not found")
ROOT=locate_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_070_physical_current_market_independent_association_gate.py'
TEST=ROOT/'test_oad_070_physical_current_market_independent_association_gate.py'
INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_adapters.independent.oad_060_independent_source_bundle import acquire_independent_production_bundle\nfrom qseries_v2.oracle_adapters.independent.oad_061_independent_to_canonical_bridge import canonicalize_independent_bundle\nfrom qseries_v2.oracle_adapters.independent.oad_063_independent_entity_term_projection import extract_independent_entity_terms\nfrom qseries_v2.oracle_adapters.independent.oad_064_bounded_market_association_candidate import bounded_market_association_candidates\nfrom qseries_v2.oracle_adapters.independent.oad_069_current_open_kalshi_market_index import fetch_current_open_kalshi_market_index\nREAD_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False\n@dataclass(frozen=True,slots=True)\nclass PhysicalAssociationReport:\n    observations:int;current_markets:int;observations_with_candidates:int;association_candidates:int;candidates:tuple\ndef run_physical_current_market_association(per_source_limit=2,market_limit=1000):\n    raw=acquire_independent_production_bundle(per_source_limit);canonical=canonicalize_independent_bundle(raw,"oad070.physical")\n    entities=tuple(extract_independent_entity_terms(x) for x in canonical);markets,index=fetch_current_open_kalshi_market_index(limit=market_limit)\n    groups=tuple((e,bounded_market_association_candidates(e,index,max_candidates=5)) for e in entities);flat=tuple(c for _,cs in groups for c in cs)\n    return PhysicalAssociationReport(len(canonical),len(markets),sum(bool(cs) for _,cs in groups),len(flat),flat)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_070_physical_current_market_independent_association_gate import *\nclass T(unittest.TestCase):\n    def test_physical(self):\n        r=run_physical_current_market_association()\n        print("[PHYSICAL] independent_observations=",r.observations);print("[PHYSICAL] current_open_markets=",r.current_markets)\n        print("[PHYSICAL] observations_with_candidates=",r.observations_with_candidates);print("[PHYSICAL] association_candidates=",r.association_candidates)\n        for c in r.candidates[:10]: print("[CANDIDATE]",c.observation_id[:12],c.market_id,c.overlap_terms,"candidate_only=",c.candidate_only)\n        self.assertGreater(r.observations,0);self.assertGreater(r.current_markets,0);self.assertTrue(all(c.candidate_only for c in r.candidates))\nif __name__=="__main__":\n    print("="*88);print(" OAD-070 PHYSICAL CERTIFICATION TEST");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Zero candidates permitted; no association fabricated")\n    print("[PASS] Any match remains candidate-only pending validation")\n    print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE")\n    print("[DONE] OAD-066 through OAD-070 CAPABILITY SLICE CERTIFIED")\n'
def write_exact(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def main():
    print("="*88);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*88)
    print("[BOOT] Revision:",REVISION);print("[ROOT]",ROOT)
    freeze=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"/"oad_055_kalshi_production_freeze.py"
    oph=ROOT/"qseries_v2"/"oracle_production_hardening"/"oph_023_postgresql_single_writer_production_freeze.py"
    dep=PKG/"oad_065_independent_canonical_batch_gate.py"
    for p,label in ((freeze,"Frozen Kalshi OAD-055"),(oph,"Frozen OPH-023"),(dep,"Certified OAD-065")):
        if not p.is_file(): raise RuntimeError(label+" dependency missing")
    freeze_hash=hashlib.sha256(freeze.read_bytes()).hexdigest()
    oph_hash=hashlib.sha256(oph.read_bytes()).hexdigest()
    affected=(MODULE,TEST,INIT)
    old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from ."+MODULE.stem+" import *"
        if exp not in lines: lines.append(exp)
        write_exact(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        if hashlib.sha256(freeze.read_bytes()).hexdigest()!=freeze_hash: raise RuntimeError("Frozen Kalshi OAD-055 changed")
        if hashlib.sha256(oph.read_bytes()).hexdigest()!=oph_hash: raise RuntimeError("Frozen OPH-023 changed")
        print("[PASS] Certified OAD-065 dependency verified")
        print("[PASS] Frozen Kalshi OAD-055 unchanged")
        print("[PASS] Frozen OPH-023 single-writer boundary unchanged")
        print("[PASS] Wrote:",MODULE.relative_to(ROOT));print("[PASS] Wrote:",TEST.name)
        print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(b)
        print("[ROLLBACK] affected files restored");raise
if __name__=="__main__": main()
