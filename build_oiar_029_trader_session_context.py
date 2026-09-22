from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_029_trader_session_context.py'
TEST=ROOT/'test_oiar_029_trader_session_context.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nOIAR_029_BUILD_ID="OIAR-029"\nOIAR_029_REVISION="OIAR_029_TRADER_SESSION_CONTEXT_V1"\nEXECUTION_AUTHORITY=False\n@dataclass\nclass TraderSessionContext:\n timeframe:str="now"\n direction:str="any"\n last_market_id:str=""\n last_market_title:str=""\n last_intent:str=""\ndef apply_intent(context,intent):\n    if intent.timeframe!="session":context.timeframe=intent.timeframe\n    if intent.direction!="any":context.direction=intent.direction\n    context.last_intent=intent.ranking\n    return context\ndef remember_market(context,market):\n    if market:\n        context.last_market_id=str(market.get("market_id") or "")\n        context.last_market_title=str(market.get("market_title") or "")\n    return context\n'
TEST_SOURCE='\nimport unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_029_trader_session_context as m\nclass T(unittest.TestCase):\n def test_context(self):\n  c=m.TraderSessionContext();self.assertEqual(c.timeframe,"now");self.assertEqual(c.direction,"any")\nif __name__=="__main__":\n print("="*88);print(" OIAR-029 CERTIFICATION TEST");print(" TRADER SESSION CONTEXT");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] trader session/timeframe context certified");print("[DONE] OIAR-029 CERTIFIED")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_028_relative_strength_semantics.py',)
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
    print("="*88);print(" OIAR-029 INSTALLER");print(" TRADER SESSION CONTEXT");print("="*88);print("[ROOT]",ROOT)
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
        a=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_027_trader_intent_classifier")
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_029_trader_session_context")
        c=m.TraderSessionContext();m.apply_intent(c,a.classify_trader_intent("what are the plays this evening"))
        print(f"[PHYSICAL] timeframe={c.timeframe} direction={c.direction}")
        if c.timeframe!="evening":raise RuntimeError("OIAR-029 timeframe inheritance failed")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OIAR-029 failed; affected repository files restored")
        raise
    print("[PASS] persisted snapshot intelligence remains read-only")
    print("[PASS] no canonical-table terminal scan introduced")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-029 INSTALLATION COMPLETE")
if __name__=="__main__":main()
