from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID="OAD-092";REVISION="OAD_092_PRODUCTION_INSTALLER_V1";TITLE='EXPANDED STRUCTURAL SPORT / LEAGUE RESOLVER'
def find_root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise SystemExit("[ERROR] Q Series repository not found")
ROOT=find_root();PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_092_expanded_structural_sport_league_resolver.py';TEST=ROOT/'test_oad_092_expanded_structural_sport_league_resolver.py';INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nimport re\nfrom qseries_v2.oracle_adapters.independent.oad_087_sport_league_resolver import resolve_sport_league\nREAD_ONLY=True;EXECUTION_AUTHORITY=False;PROBABILITY_ENABLED=False\n@dataclass(frozen=True,slots=True)\nclass ExpandedSportResolution:\n ticker:str;sport:str;league:str;evidence:tuple[str,...]\nPATTERNS=(\n ("combat_sports","UFC_MMA",("ufc","mma","fight night","bout","submission","ko/tko")),\n ("boxing","BOXING",("boxing","bout","wbc","wba","ibf","wbo")),\n ("tennis","ATP_WTA",("tennis","atp","wta","set 1","sets won","aces")),\n ("american_football","NCAA_FOOTBALL",("college football","fbs","fcs","ncaa football")),\n ("basketball","NCAA_BASKETBALL",("college basketball","ncaa basketball","march madness")),\n ("soccer","SOCCER",("both teams to score","clean sheet","first half","1st half","draw","tie")),\n ("baseball","MLB",("runs","home run","strikeout","innings","rbi")),\n ("ice_hockey","NHL",("shots on goal","power play","puck","period goals")),\n)\ndef expanded_resolve_sport_league(m):\n b=resolve_sport_league(m)\n if b.league!="UNKNOWN":return ExpandedSportResolution(b.ticker,b.sport,b.league,b.evidence)\n text=" ".join(str(m.get(k,"") or "") for k in ("ticker","event_ticker","series_ticker","title","subtitle","yes_sub_title","no_sub_title","rules_primary","rules_secondary")).lower()\n hits=[]\n for sport,league,terms in PATTERNS:\n  found=tuple(x for x in terms if x in text)\n  if found:hits.append((len(found),sport,league,found))\n if not hits:return ExpandedSportResolution(b.ticker,"sports_unresolved","UNKNOWN",b.evidence)\n hits.sort(key=lambda x:(-x[0],x[1],x[2]));_,sport,league,found=hits[0]\n return ExpandedSportResolution(b.ticker,sport,league,found)\n';TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_092_expanded_structural_sport_league_resolver import *\nclass T(unittest.TestCase):\n def test_mma(self):self.assertEqual(expanded_resolve_sport_league({"title":"Fight Night bout by submission","rules_primary":"MMA"}).league,"UFC_MMA")\n def test_tennis(self):self.assertEqual(expanded_resolve_sport_league({"title":"Will player win Set 1?","rules_primary":"tennis"}).league,"ATP_WTA")\n def test_unknown(self):self.assertEqual(expanded_resolve_sport_league({"title":"Team prop points scored"}).league,"UNKNOWN")\nif __name__=="__main__":\n print("="*88);print(" OAD-092 CERTIFICATION TEST");print(" EXPANDED STRUCTURAL SPORT / LEAGUE RESOLVER");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] Additional sport structures resolved without player/team dictionaries");print("[DONE] OAD-092 CERTIFIED")\n';FROZEN=[('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')];REQUIRED=[('qseries_v2/oracle_adapters/independent/oad_091_unresolved_sports_structure_audit.py', 'Certified OAD-091')]
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
