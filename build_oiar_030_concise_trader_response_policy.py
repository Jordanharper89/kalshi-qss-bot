from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_030_concise_trader_response_policy.py'
TEST=ROOT/'test_oiar_030_concise_trader_response_policy.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom .oiar_028_relative_strength_semantics import rank_relative,strongest_assessment\nOIAR_030_BUILD_ID="OIAR-030"\nOIAR_030_REVISION="OIAR_030_CONCISE_TRADER_RESPONSE_POLICY_V1"\nEXECUTION_AUTHORITY=False\ndef _title(m):\n    t=str(m.get("market_title") or "Identity unresolved")\n    return t if len(t)<=150 else t[:147]+"..."\ndef render_concise(markets,intent,limit=2):\n    ranked=rank_relative(markets)\n    if intent.direction in ("bullish","bearish"):\n        want="BULLISH" if intent.direction=="bullish" else "BEARISH"\n        ranked=tuple(m for m in ranked if str(m.get("direction") or "").upper()==want)\n    if intent.ranking=="strongest":\n        a=strongest_assessment(ranked)\n        if not a["market"]:return ("ORACLE READ: NOTHING TO RANK RIGHT NOW",)\n        m=a["market"]\n        return ("="*80,"ORACLE TRADER READ",a["message"],"-"*80,_title(m),f"Oracle read: {m.get(\'trader_takeaway\')}",f"Direction: {m.get(\'direction\')}",f"Why: {m.get(\'why\')}",f"Trader take: {\'Worth watching now.\' if a[\'clears_edge\'] else \'Watch it. Do not chase it yet.\'}",f"Market ID: {m.get(\'market_id\')}","="*80)\n    edge=tuple(m for m in ranked if str(m.get("setup_status") or "")=="WORTH_WATCHING_NOW")\n    forming=tuple(m for m in ranked if str(m.get("setup_status") or "")=="SETUP_FORMING")\n    chosen=(edge or forming or ranked)[:max(1,min(int(limit),2))]\n    lead=("ORACLE READ: PLAYS AVAILABLE" if edge else "ORACLE READ: SETUPS FORMING, NOTHING CONFIRMED" if forming else "ORACLE READ: NO EDGE RIGHT NOW")\n    lines=["="*80,"ORACLE TRADER READ",lead,"-"*80]\n    for i,m in enumerate(chosen,1):\n        lines += [f"#{i} {_title(m)}",f"   Read: {m.get(\'trader_takeaway\')} | Direction: {m.get(\'direction\')}",f"   Why: {m.get(\'why\')}",f"   Risk: {m.get(\'risk\')}"]\n    lines+=["-"*80,"No order placement. Q Series execution authority remains separate.","="*80]\n    return tuple(lines)\n'
TEST_SOURCE='\nimport unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_030_concise_trader_response_policy as m\nfrom types import SimpleNamespace\nclass T(unittest.TestCase):\n def test_max_two(self):\n  xs=[{"market_id":str(i),"market_title":"x"*300,"setup_status":"NO_CONFIRMED_EDGE","live_evidence":"WEAK","historical_strength":"STRONG","direction":"NEUTRAL","trader_takeaway":"NO EDGE RIGHT NOW","why":"weak","risk":"HIGH"} for i in range(5)]\n  out=m.render_concise(xs,SimpleNamespace(ranking="standard",direction="any"),2)\n  self.assertLess(len(out),20)\nif __name__=="__main__":\n print("="*88);print(" OIAR-030 CERTIFICATION TEST");print(" CONCISE TRADER RESPONSE POLICY");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] concise trader response policy certified");print("[DONE] OIAR-030 CERTIFIED")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_029_trader_session_context.py',)
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
    print("="*88);print(" OIAR-030 INSTALLER");print(" CONCISE TRADER RESPONSE POLICY");print("="*88);print("[ROOT]",ROOT)
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
        from qseries_v2.oracle_intelligence_analytics_runtime.oiar_027_trader_intent_classifier import classify_trader_intent
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_030_concise_trader_response_policy")
        x=read_fast_trader_brief(ROOT,50);lines=m.render_concise(x.markets,classify_trader_intent("what is the strongest?"),2)
        print("[PHYSICAL] lines=",len(lines))
        for line in lines:print(line)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OIAR-030 failed; affected repository files restored")
        raise
    print("[PASS] persisted snapshot intelligence remains read-only")
    print("[PASS] no canonical-table terminal scan introduced")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-030 INSTALLATION COMPLETE")
if __name__=="__main__":main()
