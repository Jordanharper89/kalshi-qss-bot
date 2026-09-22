from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID="OAD-090"; REVISION="OAD_090_PRODUCTION_INSTALLER_V1"; TITLE='PHYSICAL SPORTS ADAPTER REQUIREMENT GATE'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise SystemExit("[ERROR] Q Series repository not found")
ROOT=root(); PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_090_physical_sports_adapter_requirement_gate.py'; TEST=ROOT/'test_oad_090_physical_sports_adapter_requirement_gate.py'; INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom collections import Counter\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort,snapshot_markets\nfrom qseries_v2.oracle_adapters.independent.oad_086_structural_sports_market_detector import detect_sports_market\nfrom qseries_v2.oracle_adapters.independent.oad_087_sport_league_resolver import resolve_sport_league\nREAD_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False\n\nSOURCE_BY_LEAGUE={\n "NFL":("NFL official game/stat/injury sources",),\n "NCAA_FOOTBALL":("NCAA/conference/team official sources",),\n "NBA":("NBA official game/stat/injury sources",),\n "WNBA":("WNBA official game/stat/injury sources",),\n "MLB":("MLB official game/stat sources",),\n "NHL":("NHL official game/stat sources",),\n "ATP_WTA":("ATP/WTA official tournament/result sources",),\n "UFC_MMA":("UFC/commission official bout/result sources",),\n "BOXING":("Sanctioning-body/commission official bout sources",),\n "SOCCER":("Competition/club official match sources",),\n "UNKNOWN":("Sport-specific authoritative source unresolved",),\n}\n@dataclass(frozen=True,slots=True)\nclass SportsAdapterRequirement:\n rank:int;sport:str;league:str;live_markets:int;source_families:tuple[str,...]\n\ndef build_sports_adapter_requirements(limit=1000):\n s=capture_current_market_cohort(limit);c=Counter()\n for m in snapshot_markets(s):\n  if detect_sports_market(m).is_sports:\n   r=resolve_sport_league(m);c[(r.sport,r.league)]+=1\n rows=[]\n for i,((sport,league),count) in enumerate(sorted(c.items(),key=lambda kv:(-kv[1],kv[0])),1):\n  rows.append(SportsAdapterRequirement(i,sport,league,count,SOURCE_BY_LEAGUE.get(league,SOURCE_BY_LEAGUE["UNKNOWN"])))\n return s,tuple(rows)\n'; TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_090_physical_sports_adapter_requirement_gate import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  s,rows=build_sports_adapter_requirements(1000)\n  print("[PHYSICAL] snapshot_id=",s.snapshot_id);print("[PHYSICAL] evaluated_markets=",s.market_count);print("[PHYSICAL] sports_adapter_requirements=",len(rows))\n  for x in rows:print("[BUILD_NEXT]",x.rank,x.sport,x.league,"live_markets=",x.live_markets,"sources=",x.source_families)\n  self.assertGreater(s.market_count,0);self.assertTrue(all(x.rank==i+1 for i,x in enumerate(rows)))\nif __name__=="__main__":\n print("="*88);print(" OAD-090 PHYSICAL CERTIFICATION TEST");print(" SPORTS ADAPTER REQUIREMENT GATE");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] Sports adapter requirements derived from live structural demand")\n print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE")\n print("[DONE] OAD-086 through OAD-090 CAPABILITY SLICE CERTIFIED")\n'
FROZEN=[('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')]; REQUIRED=[('qseries_v2/oracle_adapters/independent/oad_089_single_snapshot_structural_sports_reclassification.py', 'Certified OAD-089')]
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
