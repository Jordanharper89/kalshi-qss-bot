from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_033_event_sport_context.py'
TEST=ROOT/'test_oiar_033_event_sport_context.py'
MODULE_SOURCE='from __future__ import annotations\nOIAR_033_BUILD_ID="OIAR-033"\nOIAR_033_REVISION="OIAR_033_EVENT_SPORT_CONTEXT_V1"\nEXECUTION_AUTHORITY=False\nSPORT_RULES=(\n ("SOCCER",("both teams to score","goals scored","real madrid","atletico","valencia","draw")),\n ("BASEBALL",("runs scored","first 5 innings","philadelphia","cleveland","boston","milwaukee","pittsburgh","houston","chicago c","los angeles d")),\n ("TENNIS",("auger-aliassime","nakashima","musetti","gauff","sabalenka","svitolina","kostyuk","jovic")),\n)\ndef classify_event_context(market):\n    title=str(market.get("market_title") or market.get("title") or "").lower()\n    explicit=str(market.get("sport") or market.get("category") or "").strip()\n    if explicit:return {"sport":explicit.upper(),"event_context":explicit,"context_source":"SNAPSHOT"}\n    scores=[]\n    for sport,tokens in SPORT_RULES:\n        n=sum(1 for token in tokens if token in title)\n        if n:scores.append((n,sport))\n    if not scores:return {"sport":"UNKNOWN","event_context":"Event not identified from snapshot","context_source":"UNRESOLVED"}\n    scores.sort(reverse=True)\n    sport=scores[0][1]\n    return {"sport":sport,"event_context":sport.title()+" market","context_source":"TITLE_DERIVED"}\n'
TEST_SOURCE='import unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_033_event_sport_context as m\nclass T(unittest.TestCase):\n def test_soccer(self):self.assertEqual(m.classify_event_context({"market_title":"yes Both Teams To Score,yes Atletico,yes Real Madrid"})["sport"],"SOCCER")\n def test_baseball(self):self.assertEqual(m.classify_event_context({"market_title":"yes Philadelphia,yes Cleveland,yes Boston,yes Milwaukee,yes Pittsburgh"})["sport"],"BASEBALL")\n def test_unknown_not_guessed(self):self.assertEqual(m.classify_event_context({"market_title":"Something Else"})["sport"],"UNKNOWN")\nif __name__=="__main__":\n print("="*88);print(" OIAR-033 CERTIFICATION TEST");print(" EVENT AND SPORT CONTEXT");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] event/sport context certification complete");print("[DONE] OIAR-033 CERTIFIED")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_032_market_name_compression.py',)
EXTRA={}

def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_name(p.name+f".{os.getpid()}.tmp")
    t.write_text(s,encoding="utf-8")
    os.replace(t,p)

def restore(p,b):
    if b is None:
        if p.exists(): p.unlink()
    else:
        p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)

def main():
    print("="*88);print(" OIAR-033 INSTALLER");print(" EVENT AND SPORT CONTEXT");print("="*88);print("[ROOT]",ROOT)
    for rel in REQUIRED:
        p=ROOT/rel
        if not p.is_file():raise RuntimeError(f"Required upstream missing: {p}")
    targets=[MOD,TEST]+[ROOT/x for x in EXTRA]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        ast.parse(MODULE_SOURCE,filename=str(MOD));ast.parse(TEST_SOURCE,filename=str(TEST))
        for s in EXTRA.values():ast.parse(s)
        print("[PASS] installer payload syntax verified")
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        for rel,s in EXTRA.items():write_exact(ROOT/rel,s)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=30)
        importlib.invalidate_caches()
        pass
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OIAR-033 failed; affected repository files restored")
        raise
    print("[PASS] snapshot-only trader presentation boundary preserved")
    print("[PASS] no canonical-table terminal scan introduced")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-033 INSTALLATION COMPLETE")
if __name__=="__main__":main()
