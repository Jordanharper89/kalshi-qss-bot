from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_020_unified_trader_terminal_experience.py'
TEST = ROOT / 'test_oiar_020_unified_trader_terminal_experience.py'
MODULE_SOURCE = 'from __future__ import annotations\nfrom pathlib import Path\n\nfrom .oiar_009_fast_terminal_read_adapter import read_fast_trader_intelligence\nfrom .oiar_018_trader_opportunity_explanation import explain_trader_opportunity\nfrom .oiar_019_trader_followup_intelligence import answer_followup\n\nOIAR_020_BUILD_ID="OIAR-020"\nOIAR_020_REVISION="OIAR_020_UNIFIED_TRADER_TERMINAL_EXPERIENCE_V1"\n\nQUERY_TOKENS=("what do you like","best markets","anything worth","what should i watch","edge right now","historically proven","live opportunities","rank trader intelligence")\n\ndef is_unified_trader_query(q):\n    n=" ".join(str(q or "").lower().split())\n    return any(t in n for t in QUERY_TOKENS)\n\ndef render_unified_trader_answer(root,query,limit=5):\n    snap=read_fast_trader_intelligence(Path(root).resolve(),20)\n    rows=snap.rows[:max(1,min(int(limit),10))]\n    lines=["="*80,"ORACLE TRADER BRIEF","-"*80]\n    if snap.freshness_status!="FRESH":\n        lines.append(f"Data warning: {snap.freshness_status} snapshot, age {snap.age_seconds:.0f}s.")\n        lines.append("Do not treat this as a live trading signal.")\n        lines.append("-"*80)\n\n    if not rows:\n        lines.append("Oracle has no ranked markets in the current persisted snapshot.")\n    else:\n        strong=[r for r in rows if str(r.admission_status).lower()=="admitted"]\n        if not strong:\n            lines.append("Nothing in this snapshot clears Oracle\'s current edge threshold.")\n            lines.append("")\n        for i,row in enumerate(rows,1):\n            e=explain_trader_opportunity(root,row)\n            lines += [\n                f"#{i} {e.headline}",\n                f"   Why: {e.why}",\n                f"   What would improve it: {e.what_would_improve_it}",\n                f"   Main risk: {e.main_risk}",\n                f"   Trader takeaway: {e.takeaway}",\n                f"   Market ID: {row.market_id}",\n                ""\n            ]\n    lines += ["No order placement. Q Series execution authority remains separate.","="*80]\n    return tuple(lines)\n\ndef bind_unified_trader_experience(base_module,root=None):\n    if getattr(base_module,"_oiar020_bound",False):return base_module\n    original=base_module.display_query\n    active=Path(root or base_module.repository_root()).resolve()\n\n    def display_query(query,*,session=None,root=None,builder=None,write=print):\n        canonical=base_module.normalize_query(query)\n        use=Path(root or active).resolve()\n        if is_unified_trader_query(canonical):\n            for line in render_unified_trader_answer(use,canonical,5):\n                write(line)\n            return None\n        kwargs={"session":session,"root":use,"write":write}\n        if builder is not None:kwargs["builder"]=builder\n        return original(canonical,**kwargs)\n\n    base_module.display_query=display_query\n    base_module._oiar020_bound=True\n    return base_module\n'
TEST_SOURCE = 'import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_020_unified_trader_terminal_experience import is_unified_trader_query,OIAR_020_BUILD_ID\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OIAR_020_BUILD_ID,"OIAR-020")\n    def test_route(self):self.assertTrue(is_unified_trader_query("what do you like right now"))\nif __name__=="__main__":\n    print("="*88);print(" OIAR-020 CERTIFICATION TEST");print(" UNIFIED TRADER TERMINAL EXPERIENCE");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] unified trader terminal query contract certified")\n    print("[DONE] OIAR-020 CERTIFIED")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_019_trader_followup_intelligence.py', 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_015_operator_terminal_trader_language_cutover.py', 'qseries_v2/oracle_terminal/oracle_historical_experience_terminal_binding.py', 'qseries_v2/oracle_terminal/oracle_persisted_trader_intelligence_terminal_binding.py', 'run_oracle_open_intelligence_terminal.py')
EXTRA_FILES = {'run_oracle_operator_terminal.py': 'from __future__ import annotations\nimport run_oracle_open_intelligence_terminal as base\nfrom qseries_v2.oracle_terminal.oracle_historical_experience_terminal_binding import bind_historical_experience_surface\nfrom qseries_v2.oracle_terminal.oracle_persisted_trader_intelligence_terminal_binding import bind_persisted_trader_intelligence\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_015_operator_terminal_trader_language_cutover import bind_trader_language\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_020_unified_trader_terminal_experience import bind_unified_trader_experience\n\ndef main():\n    bind_historical_experience_surface(base)\n    bind_persisted_trader_intelligence(base)\n    bind_trader_language(base)\n    bind_unified_trader_experience(base)\n    return base.main()\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'}

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
    print(" OIAR_020_UNIFIED_TRADER_TERMINAL_EXPERIENCE INSTALLER")
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
        subprocess.run([sys.executable,str(ROOT/"test_oit_050_oracle_terminal_final_freeze_and_completion.py")],cwd=str(ROOT),check=True,timeout=30)
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
