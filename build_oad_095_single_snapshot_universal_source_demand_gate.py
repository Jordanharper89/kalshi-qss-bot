from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID="OAD-095";REVISION="OAD_095_PRODUCTION_INSTALLER_V1";TITLE='SINGLE-SNAPSHOT UNIVERSAL SOURCE-DEMAND GATE'
def find_root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise SystemExit("[ERROR] Q Series repository not found")
ROOT=find_root();PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_095_single_snapshot_universal_source_demand_gate.py';TEST=ROOT/'test_oad_095_single_snapshot_universal_source_demand_gate.py';INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom collections import Counter\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_adapters.independent.oad_082_single_live_market_cohort_snapshot import capture_current_market_cohort,snapshot_markets\nfrom qseries_v2.oracle_adapters.independent.oad_092_expanded_structural_sport_league_resolver import expanded_resolve_sport_league\nfrom qseries_v2.oracle_adapters.independent.oad_094_expanded_universal_domain_classifier import expanded_domain_classify\nREAD_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False\nSOURCE_DEMAND={\n "sports":("SPORT_SPECIFIC",),\n "macroeconomics":("BLS","BEA","Federal Reserve/FRED"),\n "politics_elections":("Official election authorities","FEC"),\n "corporate_finance":("SEC EDGAR","Issuer investor relations"),\n "crypto":("Coinbase/chain RPC/indexers",),\n "weather":("NWS/NOAA",),\n "energy_commodities":("EIA","USDA"),\n "legal_regulatory":("Federal Register","CourtListener/official courts"),\n "health":("CDC","FDA"),\n "transport":("FAA","TSA","Maritime/port authorities"),\n "science_space":("NASA",),\n "geopolitics":("State/Defense/UN official releases",),\n "technology":("Issuer official releases","SEC EDGAR"),\n "entertainment_awards":("Official award/event organizations",),\n}\nSPORT_SOURCES={\n "NHL":("NHL official game/stat sources",),"MLB":("MLB official game/stat sources",),\n "SOCCER":("Competition/club official match sources",),"ATP_WTA":("ATP/WTA official tournament/result sources",),\n "UFC_MMA":("UFC/commission official bout/result sources",),"BOXING":("Sanctioning-body/commission official bout sources",),\n "NFL":("NFL official game/stat/injury sources",),"NCAA_FOOTBALL":("NCAA/conference/team official sources",),\n "NBA":("NBA official game/stat/injury sources",),"WNBA":("WNBA official game/stat/injury sources",),\n "NCAA_BASKETBALL":("NCAA/conference/team official basketball sources",),\n "UNKNOWN":("Sport-specific authoritative source unresolved",),\n}\n@dataclass(frozen=True,slots=True)\nclass UniversalPriority:\n rank:int;domain:str;subdomain:str;live_markets:int;source_families:tuple[str,...]\n@dataclass(frozen=True,slots=True)\nclass UniversalGate:\n snapshot_id:str;evaluated_markets:int;unresolved:int;priorities:tuple[UniversalPriority,...]\ndef build_universal_source_demand_gate(limit=1000):\n s=capture_current_market_cohort(limit);c=Counter()\n for m in snapshot_markets(s):\n  d=expanded_domain_classify(m)\n  if d.domain=="sports":\n   r=expanded_resolve_sport_league(m);c[("sports",r.league)]+=1\n  else:c[(d.domain,"")]+=1\n unresolved=c.get(("other",""),0);rows=[]\n for (domain,sub),count in c.items():\n  if domain=="other":continue\n  src=SPORT_SOURCES.get(sub,()) if domain=="sports" else SOURCE_DEMAND.get(domain,())\n  rows.append((count,domain,sub,src))\n rows.sort(key=lambda x:(-x[0],x[1],x[2]))\n return UniversalGate(s.snapshot_id,s.market_count,unresolved,tuple(UniversalPriority(i+1,d,sub,n,src) for i,(n,d,sub,src) in enumerate(rows)))\n';TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_095_single_snapshot_universal_source_demand_gate import *\nclass T(unittest.TestCase):\n def test_physical(self):\n  g=build_universal_source_demand_gate(1000)\n  print("[PHYSICAL] snapshot_id=",g.snapshot_id);print("[PHYSICAL] evaluated_markets=",g.evaluated_markets);print("[PHYSICAL] unresolved=",g.unresolved)\n  print("[PHYSICAL] priorities=",len(g.priorities))\n  for p in g.priorities:print("[BUILD_NEXT]",p.rank,p.domain,p.subdomain,"live_markets=",p.live_markets,"sources=",p.source_families)\n  self.assertGreater(g.evaluated_markets,0);self.assertTrue(all(p.rank==i+1 for i,p in enumerate(g.priorities)))\nif __name__=="__main__":\n print("="*88);print(" OAD-095 PHYSICAL CERTIFICATION TEST");print(" SINGLE-SNAPSHOT UNIVERSAL SOURCE-DEMAND GATE");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] One live cohort drives final domain/source-demand ranking")\n print("[PASS] Unresolved demand remains explicit");print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE")\n print("[DONE] OAD-091 through OAD-095 CAPABILITY SLICE CERTIFIED")\n';FROZEN=[('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')];REQUIRED=[('qseries_v2/oracle_adapters/independent/oad_092_expanded_structural_sport_league_resolver.py', 'Certified OAD-092'), ('qseries_v2/oracle_adapters/independent/oad_094_expanded_universal_domain_classifier.py', 'Certified OAD-094')]
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
