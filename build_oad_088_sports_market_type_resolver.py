from __future__ import annotations
import ast,hashlib,os,textwrap
from pathlib import Path
BUILD_ID="OAD-088"; REVISION="OAD_088_PRODUCTION_INSTALLER_V1"; TITLE='SPORTS MARKET-TYPE RESOLVER'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise SystemExit("[ERROR] Q Series repository not found")
ROOT=root(); PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/'oad_088_sports_market_type_resolver.py'; TEST=ROOT/'test_oad_088_sports_market_type_resolver.py'; INIT=PKG/"__init__.py"
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom qseries_v2.oracle_adapters.independent.oad_086_structural_sports_market_detector import detect_sports_market\nREAD_ONLY=True; EXECUTION_AUTHORITY=False; PROBABILITY_ENABLED=False\n\n@dataclass(frozen=True,slots=True)\nclass SportsMarketType:\n ticker:str; market_type:str; signals:tuple[str,...]\n\nRULES=(\n ("both_teams_to_score",("both teams to score",)),\n ("spread",("wins by over","spread")),\n ("total",("over ","under ","total points","total runs","total goals")),\n ("player_prop",("home runs","strikeouts","rebounds","assists","yards","touchdown","points scored")),\n ("team_prop",("team total","goals scored","runs scored")),\n ("match_winner",("moneyline"," to win","wins the match","wins the game")),\n ("tournament_advancement",("round of 16","quarterfinal","semifinal","advance","qualify")),\n)\ndef resolve_sports_market_type(m):\n d=detect_sports_market(m)\n if not d.is_sports:return SportsMarketType(d.ticker,"non_sports",())\n text=" ".join(str(m.get(k,"") or "") for k in ("title","subtitle","yes_sub_title","no_sub_title","rules_primary","rules_secondary")).lower()\n hits=[]\n for typ,terms in RULES:\n  found=tuple(x for x in terms if x in text)\n  if found:hits.append((len(found),typ,found))\n if not hits:return SportsMarketType(d.ticker,"sports_other",d.signals)\n hits.sort(key=lambda x:(-x[0],x[1]));_,typ,found=hits[0]\n return SportsMarketType(d.ticker,typ,found)\n'; TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_088_sports_market_type_resolver import *\nclass T(unittest.TestCase):\n def test_btts(self):self.assertEqual(resolve_sports_market_type({"title":"1st Half: Both Teams To Score"}).market_type,"both_teams_to_score")\n def test_spread(self):self.assertEqual(resolve_sports_market_type({"title":"Indiana wins by over 1.5 points"}).market_type,"spread")\nif __name__=="__main__":\n print("="*88);print(" OAD-088 CERTIFICATION TEST");print(" SPORTS MARKET-TYPE RESOLVER");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] Sports market-type resolution certified");print("[DONE] OAD-088 CERTIFIED")\n'
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
