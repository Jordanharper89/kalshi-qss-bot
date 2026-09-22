from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID="OAD-087"; REVISION="OAD_087_PRODUCTION_INSTALLER_V1"; TITLE='SPORT / LEAGUE RESOLVER'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise SystemExit("[ERROR] Q Series repository not found")
ROOT=root(); PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_087_sport_league_resolver.py'; TEST=ROOT/'test_oad_087_sport_league_resolver.py'; INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nimport re\nfrom qseries_v2.oracle_adapters.independent.oad_086_structural_sports_market_detector import detect_sports_market\nREAD_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False\n\n@dataclass(frozen=True,slots=True)\nclass SportLeagueResolution:\n ticker:str; sport:str; league:str; evidence:tuple[str,...]\n\nRULES=(\n ("american_football","NFL",("NFL","touchdown","passing yards","rushing yards")),\n ("american_football","NCAA_FOOTBALL",("NCAAF","college football")),\n ("basketball","NBA",("NBA","rebounds","assists","three pointers")),\n ("basketball","WNBA",("WNBA",)),\n ("baseball","MLB",("MLB","home runs","strikeouts","runs","innings")),\n ("ice_hockey","NHL",("NHL","goals","shots on goal")),\n ("tennis","ATP_WTA",("ATP","WTA","sets","aces","break points")),\n ("combat_sports","UFC_MMA",("UFC","MMA","submission","knockout","round")),\n ("boxing","BOXING",("boxing","bout","knockout")),\n ("soccer","SOCCER",("both teams to score","champions league","premier league","la liga","bundesliga","serie a","ligue 1","mls","goals")),\n)\ndef _text(m):return " ".join(str(m.get(k,"") or "") for k in ("ticker","event_ticker","series_ticker","title","subtitle","rules_primary","rules_secondary"))\ndef resolve_sport_league(m):\n d=detect_sports_market(m); text=_text(m); low=text.lower(); upper=text.upper()\n if not d.is_sports:return SportLeagueResolution(d.ticker,"non_sports","NONE",())\n hits=[]\n for sport,league,terms in RULES:\n  found=tuple(x for x in terms if (x in upper if x.isupper() else x.lower() in low))\n  if found:hits.append((len(found),sport,league,found))\n if not hits:return SportLeagueResolution(d.ticker,"sports_unresolved","UNKNOWN",d.signals)\n hits.sort(key=lambda x:(-x[0],x[1],x[2]));_,sport,league,found=hits[0]\n return SportLeagueResolution(d.ticker,sport,league,tuple(found))\n'; TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_087_sport_league_resolver import *\nclass T(unittest.TestCase):\n def test_soccer(self):\n  x=resolve_sport_league({"title":"1st Half: Both Teams To Score","rules_primary":"soccer goals"})\n  self.assertEqual(x.sport,"soccer")\n def test_baseball(self):\n  x=resolve_sport_league({"title":"Will the player hit 2 home runs?","series_ticker":"MLB"})\n  self.assertEqual(x.league,"MLB")\nif __name__=="__main__":\n print("="*88);print(" OAD-087 CERTIFICATION TEST");print(" SPORT / LEAGUE RESOLVER");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] Sport and league resolution certified");print("[DONE] OAD-087 CERTIFIED")\n'
FROZEN=[('qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py', 'Frozen Kalshi OAD-055'), ('qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py', 'Frozen OPH-023'), ('qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py', 'Frozen UMD-098'), ('qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py', 'Frozen UMD-109')]; REQUIRED=[('qseries_v2/oracle_adapters/independent/oad_086_structural_sports_market_detector.py', 'Certified OAD-086')]
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
