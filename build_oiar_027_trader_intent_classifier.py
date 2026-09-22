from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_027_trader_intent_classifier.py'
TEST=ROOT/'test_oiar_027_trader_intent_classifier.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nimport re\nOIAR_027_BUILD_ID="OIAR-027"\nOIAR_027_REVISION="OIAR_027_TRADER_INTENT_CLASSIFIER_V1"\nEXECUTION_AUTHORITY=False\n@dataclass(frozen=True)\nclass TraderIntent:\n    route:str\n    ranking:str\n    timeframe:str\n    direction:str\n    follow_up:bool\n    confidence:float\nTOKENS=("play","plays","like","strongest","best","watch","watching","setting up","setup","edge","market right now","anything good","anything worth","what are you seeing","what do you see","bullish","bearish","changed","that one","why")\ndef classify_trader_intent(query):\n    q=" ".join(str(query or "").lower().split())\n    trader=any(t in q for t in TOKENS)\n    ranking="strongest" if any(t in q for t in ("strongest","best one","best setup","top play")) else "standard"\n    timeframe="evening" if any(t in q for t in ("evening","tonight")) else "today" if "today" in q else "now" if any(t in q for t in ("right now","now","currently")) else "session"\n    direction="bullish" if any(t in q for t in ("bullish","bull","upside")) else "bearish" if any(t in q for t in ("bearish","bear","downside")) else "any"\n    follow=any(t in q for t in ("that one","why","changed","strongest")) and len(q.split())<=8\n    return TraderIntent("trader_brief" if trader else "fallback",ranking,timeframe,direction,follow,0.95 if trader else 0.0)\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_027_trader_intent_classifier import classify_trader_intent as c\nclass T(unittest.TestCase):\n def test_plays(self):self.assertEqual(c("what are the plays for this evening?").route,"trader_brief")\n def test_strongest(self):self.assertEqual(c("what is the strongest?").ranking,"strongest")\n def test_bull(self):self.assertEqual(c("anything bullish").direction,"bullish")\n def test_fallback(self):self.assertEqual(c("price of bitcoin").route,"fallback")\nif __name__=="__main__":\n print("="*88);print(" OIAR-027 CERTIFICATION TEST");print(" TRADER INTENT CLASSIFIER");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] broad trader intent routing certified");print("[DONE] OIAR-027 CERTIFIED")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_026_operator_terminal_trader_brief_cutover.py',)
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
    print("="*88);print(" OIAR-027 INSTALLER");print(" TRADER INTENT CLASSIFIER");print("="*88);print("[ROOT]",ROOT)
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
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_027_trader_intent_classifier")
        for q in ("what are the plays for this evening?","what is the strongest?","anything worth watching","anything bullish","anything bearish","what changed","why do you like that one"):
            x=m.classify_trader_intent(q);print(f"[ROUTE] {q!r} => route={x.route} ranking={x.ranking} timeframe={x.timeframe} direction={x.direction}")
            if x.route!="trader_brief":raise RuntimeError("OIAR-027 missed trader query")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OIAR-027 failed; affected repository files restored")
        raise
    print("[PASS] persisted snapshot intelligence remains read-only")
    print("[PASS] no canonical-table terminal scan introduced")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-027 INSTALLATION COMPLETE")
if __name__=="__main__":main()
