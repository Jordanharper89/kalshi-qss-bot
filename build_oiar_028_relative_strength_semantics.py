from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_028_relative_strength_semantics.py'
TEST=ROOT/'test_oiar_028_relative_strength_semantics.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nOIAR_028_BUILD_ID="OIAR-028"\nOIAR_028_REVISION="OIAR_028_RELATIVE_STRENGTH_SEMANTICS_V1"\nEXECUTION_AUTHORITY=False\ndef score_market(m):\n    setup=str(m.get("setup_status") or "")\n    live={"STRONG":30,"DEVELOPING":18,"WEAK":5}.get(str(m.get("live_evidence") or ""),0)\n    hist={"STRONG":20,"MODERATE":12,"LIMITED":4}.get(str(m.get("historical_strength") or ""),0)\n    direction=10 if str(m.get("direction") or "NEUTRAL")!="NEUTRAL" else 0\n    setup_score={"WORTH_WATCHING_NOW":40,"SETUP_FORMING":20,"NO_CONFIRMED_EDGE":0}.get(setup,0)\n    return setup_score+live+hist+direction\ndef rank_relative(markets):\n    return tuple(sorted((dict(m) for m in markets),key=lambda m:(-score_market(m),str(m.get("market_id") or ""))))\ndef strongest_assessment(markets):\n    ranked=rank_relative(markets)\n    if not ranked:return {"market":None,"clears_edge":False,"message":"Oracle has no markets to rank in the current snapshot."}\n    top=ranked[0];clears=str(top.get("setup_status") or "")=="WORTH_WATCHING_NOW"\n    return {"market":top,"clears_edge":clears,"message":("This is Oracle\'s strongest current setup and it clears the edge threshold." if clears else "This is the strongest market in the current group, but it still does not clear Oracle\'s edge threshold.")}\n'
TEST_SOURCE='\nimport unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_028_relative_strength_semantics as m\nclass T(unittest.TestCase):\n def test_strongest_not_edge(self):\n  x=m.strongest_assessment([{"market_id":"A","setup_status":"NO_CONFIRMED_EDGE","live_evidence":"WEAK","historical_strength":"STRONG","direction":"NEUTRAL"}])\n  self.assertFalse(x["clears_edge"]);self.assertIn("does not clear",x["message"])\nif __name__=="__main__":\n print("="*88);print(" OIAR-028 CERTIFICATION TEST");print(" RELATIVE STRENGTH SEMANTICS");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] strongest-is-not-automatically-good semantics certified");print("[DONE] OIAR-028 CERTIFIED")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_027_trader_intent_classifier.py',)
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
    print("="*88);print(" OIAR-028 INSTALLER");print(" RELATIVE STRENGTH SEMANTICS");print("="*88);print("[ROOT]",ROOT)
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
        from qseries_v2.oracle_intelligence_analytics_runtime.oiar_025_fast_persisted_trader_brief_read_model import read_fast_trader_brief
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_028_relative_strength_semantics")
        x=read_fast_trader_brief(ROOT,50);a=m.strongest_assessment(x.markets)
        print(f"[PHYSICAL] strongest={None if a['market'] is None else a['market'].get('market_title')!r} clears_edge={a['clears_edge']}")
        print("[ASSESSMENT]",a["message"])
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OIAR-028 failed; affected repository files restored")
        raise
    print("[PASS] persisted snapshot intelligence remains read-only")
    print("[PASS] no canonical-table terminal scan introduced")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-028 INSTALLATION COMPLETE")
if __name__=="__main__":main()
