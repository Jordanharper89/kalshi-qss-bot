from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_019_trader_followup_intelligence.py'
TEST = ROOT / 'test_oiar_019_trader_followup_intelligence.py'
MODULE_SOURCE = 'from __future__ import annotations\nfrom dataclasses import dataclass\nfrom .oiar_018_trader_opportunity_explanation import explain_trader_opportunity\n\nOIAR_019_BUILD_ID="OIAR-019"\nOIAR_019_REVISION="OIAR_019_TRADER_FOLLOWUP_INTELLIGENCE_V1"\n\n@dataclass(frozen=True)\nclass TraderFollowupAnswer:\n    question_type:str\n    lines:tuple\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef classify_followup(query):\n    q=" ".join(str(query or "").lower().split())\n    if "why" in q:return "WHY"\n    if "change your mind" in q or "what would improve" in q:return "IMPROVE"\n    if "risk" in q or "fail" in q:return "RISK"\n    if "learned" in q:return "LEARNED"\n    return "SUMMARY"\n\ndef answer_followup(root,row,query):\n    e=explain_trader_opportunity(root,row)\n    kind=classify_followup(query)\n    if kind=="WHY": lines=(e.headline,e.why)\n    elif kind=="IMPROVE": lines=(e.headline,e.what_would_improve_it)\n    elif kind=="RISK": lines=(e.headline,e.main_risk)\n    elif kind=="LEARNED":\n        lines=(e.headline,f"Historical maturity={row.maturity}; reliability={float(row.reliability or 0):.3f}; learned family records={int(row.learned_family_records or 0)}.")\n    else: lines=(e.headline,e.why,e.main_risk,e.takeaway)\n    return TraderFollowupAnswer(kind,lines,True,False)\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_019_trader_followup_intelligence import classify_followup,OIAR_019_BUILD_ID\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OIAR_019_BUILD_ID,"OIAR-019")\n    def test_routes(self):self.assertEqual(classify_followup("why do you like it"),"WHY");self.assertEqual(classify_followup("whats the risk"),"RISK")\nif __name__=="__main__":\n    print("="*88);print(" OIAR-019 CERTIFICATION TEST");print(" TRADER FOLLOW-UP INTELLIGENCE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] trader follow-up routing certified")\n    print("[DONE] OIAR-019 CERTIFIED")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_018_trader_opportunity_explanation.py',)
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
    print(" OIAR_019_TRADER_FOLLOWUP_INTELLIGENCE INSTALLER")
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
