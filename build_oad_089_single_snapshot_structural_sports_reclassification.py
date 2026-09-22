from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID="OAD-089"; REVISION="OAD_089_PRODUCTION_INSTALLER_V1"; TITLE='SINGLE-SNAPSHOT STRUCTURAL SPORTS RECLASSIFICATION'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise SystemExit("[ERROR] Q Series repository not found")
ROOT=root(); PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_089_single_snapshot_structural_sports_reclassification.py'; TEST=ROOT/'test_oad_089_single_snapshot_structural_sports_reclassification.py'; INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom collections import Counter\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import snapshot_markets\nfrom qseries_v2.oracle_adapters.independent.oad_083_deep_unresolved_market_classification import deep_classify_market\nfrom qseries_v2.oracle_adapters.independent.oad_086_structural_sports_market_detector import detect_sports_market\nfrom qseries_v2.oracle_adapters.independent.oad_087_sport_league_resolver import resolve_sport_league\nfrom qseries_v2.oracle_adapters.independent.oad_088_sports_market_type_resolver import resolve_sports_market_type\nREAD_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False\n\n@dataclass(frozen=True,slots=True)\nclass SportsReclassificationResult:\n market_count:int; baseline_sports:int; structural_sports:int; rescued_from_other:int; unresolved:int; sport_counts:tuple; market_type_counts:tuple\n\ndef reclassify_snapshot_with_structural_sports(snapshot):\n markets=snapshot_markets(snapshot); baseline=0; structural=0; rescued=0; unresolved=0\n sports=Counter(); types=Counter()\n for m in markets:\n  b=deep_classify_market(m); d=detect_sports_market(m)\n  if b.topic=="sports":baseline+=1\n  if d.is_sports:\n   structural+=1\n   if b.topic=="other":rescued+=1\n   r=resolve_sport_league(m);t=resolve_sports_market_type(m);sports[(r.sport,r.league)]+=1;types[t.market_type]+=1\n  elif b.topic=="other":unresolved+=1\n return SportsReclassificationResult(len(markets),baseline,structural,rescued,unresolved,tuple(sports.most_common()),tuple(types.most_common()))\n'; TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort\nfrom qseries_v2.oracle_adapters.independent.oad_089_single_snapshot_structural_sports_reclassification import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  s=capture_current_market_cohort(1000);r=reclassify_snapshot_with_structural_sports(s)\n  print("[PHYSICAL] snapshot_id=",s.snapshot_id);print("[PHYSICAL] market_count=",r.market_count)\n  print("[PHYSICAL] baseline_sports=",r.baseline_sports);print("[PHYSICAL] structural_sports=",r.structural_sports)\n  print("[PHYSICAL] rescued_from_other=",r.rescued_from_other);print("[PHYSICAL] unresolved=",r.unresolved)\n  print("[PHYSICAL] sport_counts=",r.sport_counts);print("[PHYSICAL] market_type_counts=",r.market_type_counts)\n  self.assertEqual(r.market_count,s.market_count);self.assertGreaterEqual(r.structural_sports,r.rescued_from_other)\nif __name__=="__main__":\n print("="*88);print(" OAD-089 PHYSICAL CERTIFICATION TEST");print(" SINGLE-SNAPSHOT STRUCTURAL SPORTS RECLASSIFICATION");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] Structural sports rescue measured on one immutable live cohort");print("[DONE] OAD-089 CERTIFIED")\n'
FROZEN=[('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')]; REQUIRED=[('qseries_v2/oracle_adapters/independent/oad_082_single_live_market_cohort_snapshot.py', 'Certified OAD-082'), ('qseries_v2/oracle_adapters/independent/oad_087_sport_league_resolver.py', 'Certified OAD-087'), ('qseries_v2/oracle_adapters/independent/oad_088_sports_market_type_resolver.py', 'Certified OAD-088')]
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    print("="*88);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*88)
    print("[BOOT] Revision:",REVISION);print("[ROOT]",ROOT)
    for rel,label in REQUIRED:
        if not (ROOT/rel).is_file(): raise RuntimeError(label+" missing")
        print("[PASS]",label,"verified")
    frozen={ROOT/rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() for rel,_ in FROZEN}
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}
    try:
        write(MODULE,MODULE_SOURCE); write(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from ."+MODULE.stem+" import *"
        if exp not in lines: lines.append(exp)
        write(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h: raise RuntimeError("Frozen dependency changed: "+p.name)
        print("[PASS] Wrote:",MODULE.relative_to(ROOT));print("[PASS] Wrote:",TEST.name)
        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored");raise
if __name__=="__main__":main()
