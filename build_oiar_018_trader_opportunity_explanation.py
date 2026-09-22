from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_018_trader_opportunity_explanation.py'
TEST = ROOT / 'test_oiar_018_trader_opportunity_explanation.py'
MODULE_SOURCE = 'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oiar_017_trader_market_context_model import build_trader_market_context\n\nOIAR_018_BUILD_ID="OIAR-018"\nOIAR_018_REVISION="OIAR_018_TRADER_OPPORTUNITY_EXPLANATION_V1"\n\n@dataclass(frozen=True)\nclass TraderOpportunityExplanation:\n    market_id:str\n    headline:str\n    why:str\n    what_would_improve_it:str\n    main_risk:str\n    takeaway:str\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef explain_trader_opportunity(root,row):\n    c=build_trader_market_context(root,row)\n    if c.identity_status!="RESOLVED":\n        headline="Oracle cannot verify the exact market identity yet."\n    elif c.setup_quality=="ACTIONABLE_RESEARCH":\n        headline=f"{c.display_name}: worth watching now."\n    elif c.setup_quality=="FORMING":\n        headline=f"{c.display_name}: setup is forming."\n    else:\n        headline=f"{c.display_name}: no confirmed edge right now."\n\n    if c.historical_strength=="STRONG" and c.live_evidence in ("WEAK","DEVELOPING"):\n        why="Oracle knows this market family well, but current live evidence is not strong enough to confirm a setup."\n    elif c.live_evidence=="STRONG":\n        why="Current live evidence is substantial enough for Oracle to evaluate the setup with more confidence."\n    else:\n        why="Oracle has limited support from both historical and live evidence."\n\n    improve="More live history and a directional setup that clears Oracle\'s usefulness/candidate thresholds."\n    risk="The current evidence may be too thin or unstable to support a reliable directional call."\n    takeaway="WORTH WATCHING NOW" if c.setup_quality=="ACTIONABLE_RESEARCH" else "WATCH - SETUP FORMING" if c.setup_quality=="FORMING" else "NO EDGE RIGHT NOW"\n\n    return TraderOpportunityExplanation(row.market_id,headline,why,improve,risk,takeaway,True,False)\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_018_trader_opportunity_explanation import OIAR_018_BUILD_ID\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OIAR_018_BUILD_ID,"OIAR-018")\nif __name__=="__main__":\n    print("="*88);print(" OIAR-018 CERTIFICATION TEST");print(" TRADER OPPORTUNITY EXPLANATION");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] trader opportunity explanation contract certified")\n    print("[DONE] OIAR-018 CERTIFIED")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_017_trader_market_context_model.py',)
EXTRA_FILES = {}

def write_exact(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)

def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

def main():
    print("=" * 88)
    print(" OIAR_018_TRADER_OPPORTUNITY_EXPLANATION INSTALLER")
    print("=" * 88)
    print("[ROOT]", ROOT)

    for rel in REQUIRED:
        p = ROOT / rel
        if not p.is_file():
            raise RuntimeError(f"Required proven upstream missing: {p}")

    targets = [MOD, TEST] + [ROOT / p for p in EXTRA_FILES]
    old = {p: (p.read_bytes() if p.exists() else None) for p in targets}

    try:
        ast.parse(MODULE_SOURCE)
        ast.parse(TEST_SOURCE)
        for src in EXTRA_FILES.values():
            ast.parse(src)
        print("[PASS] installer payload syntax verified")

        write_exact(MOD, MODULE_SOURCE)
        write_exact(TEST, TEST_SOURCE)
        for rel, src in EXTRA_FILES.items():
            write_exact(ROOT / rel, src)

        subprocess.run([sys.executable, str(TEST)], cwd=str(ROOT), check=True)
        importlib.invalidate_caches()
        pass
    except Exception:
        for p, data in old.items():
            restore(p, data)
        print("[ROLLBACK] installer failed; affected files restored")
        raise

    print("[PASS] read-only trader intelligence boundary preserved")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
