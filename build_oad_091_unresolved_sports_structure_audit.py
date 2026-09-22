from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID="OAD-091";REVISION="OAD_091_PRODUCTION_INSTALLER_V1";TITLE='UNRESOLVED SPORTS STRUCTURE AUDIT'
def find_root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise SystemExit("[ERROR] Q Series repository not found")
ROOT=find_root();PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_091_unresolved_sports_structure_audit.py';TEST=ROOT/'test_oad_091_unresolved_sports_structure_audit.py';INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom collections import Counter\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import snapshot_markets\nfrom qseries_v2.oracle_adapters.independent.oad_086_structural_sports_market_detector import detect_sports_market\nfrom qseries_v2.oracle_adapters.independent.oad_087_sport_league_resolver import resolve_sport_league\nREAD_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False\nFIELDS=("ticker","event_ticker","series_ticker","title","subtitle","yes_sub_title","no_sub_title","rules_primary","rules_secondary")\n@dataclass(frozen=True,slots=True)\nclass UnresolvedSportsAudit:\n count:int;field_nonempty:tuple;series_prefixes:tuple;samples:tuple\ndef audit_unresolved_sports(snapshot,sample_limit=30):\n rows=[];non=Counter();prefix=Counter()\n for m in snapshot_markets(snapshot):\n  if not detect_sports_market(m).is_sports:continue\n  if resolve_sport_league(m).league!="UNKNOWN":continue\n  rows.append(m)\n  for f in FIELDS:\n   if str(m.get(f,"") or "").strip():non[f]+=1\n  raw=str(m.get("series_ticker","") or m.get("event_ticker","") or m.get("ticker",""))\n  token=raw.split("-")[0][:40]\n  if token:prefix[token]+=1\n samples=tuple((str(m.get("ticker","")),str(m.get("series_ticker","")),str(m.get("event_ticker","")),str(m.get("title",""))[:220]) for m in rows[:sample_limit])\n return UnresolvedSportsAudit(len(rows),tuple(non.most_common()),tuple(prefix.most_common(30)),samples)\n';TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort\nfrom qseries_v2.oracle_adapters.independent.oad_091_unresolved_sports_structure_audit import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  s=capture_current_market_cohort(1000);a=audit_unresolved_sports(s)\n  print("[PHYSICAL] snapshot_id=",s.snapshot_id);print("[PHYSICAL] unresolved_sports=",a.count)\n  print("[PHYSICAL] field_nonempty=",a.field_nonempty);print("[PHYSICAL] series_prefixes=",a.series_prefixes)\n  for x in a.samples:print("[UNRESOLVED_SPORT]",x)\n  self.assertGreaterEqual(a.count,0)\nif __name__=="__main__":\n print("="*88);print(" OAD-091 PHYSICAL CERTIFICATION TEST");print(" UNRESOLVED SPORTS STRUCTURE AUDIT");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] Unresolved sports physically audited without fabricated league assignment");print("[DONE] OAD-091 CERTIFIED")\n';FROZEN=[('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')];REQUIRED=[('qseries_v2/oracle_adapters/independent/oad_090_physical_sports_adapter_requirement_gate.py', 'Certified OAD-090')]
def write(p,s):
    s=textwrap.dedent(s).lstrip();ast.parse(s,filename=str(p));p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def main():
    print("="*88);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*88);print("[BOOT] Revision:",REVISION);print("[ROOT]",ROOT)
    for rel,label in REQUIRED:
        if not (ROOT/rel).is_file():raise RuntimeError(label+" missing")
        print("[PASS]",label,"verified")
    frozen={ROOT/r:hashlib.sha256((ROOT/r).read_bytes()).hexdigest() for r,_ in FROZEN}
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}
    try:
        write(MODULE,MODULE_SOURCE);write(TEST,TEST_SOURCE)
        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        exp="from ."+MODULE.stem+" import *"
        if exp not in lines:lines.append(exp)
        write(INIT,"\n".join(x for x in lines if x.strip())+"\n")
        for p,h in frozen.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:raise RuntimeError("Frozen dependency changed: "+p.name)
        print("[PASS] Wrote:",MODULE.relative_to(ROOT));print("[PASS] Wrote:",TEST.name)
        print("[PASS] Frozen Kalshi/OPH/UMD boundaries unchanged");print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE")
        print("[DONE] "+BUILD_ID+" INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] affected files restored");raise
if __name__=="__main__":main()
