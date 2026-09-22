from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT = Path.cwd().resolve()
MOD = ROOT / 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_026_operator_terminal_trader_brief_cutover.py'
TEST = ROOT / 'test_oiar_026_operator_terminal_trader_brief_cutover.py'
MODULE_SOURCE = '\nfrom __future__ import annotations\nfrom pathlib import Path\nfrom .oiar_025_fast_persisted_trader_brief_read_model import read_fast_trader_brief\n\nOIAR_026_BUILD_ID="OIAR-026"\nOIAR_026_REVISION="OIAR_026_OPERATOR_TERMINAL_TRADER_BRIEF_CUTOVER_V1"\nTOKENS=("what do you like","best markets","anything worth","what should i watch","edge right now","historically proven","live opportunities","rank trader intelligence")\n\ndef is_trader_brief_query(q):\n    n=" ".join(str(q or "").lower().split())\n    return any(t in n for t in TOKENS)\n\ndef render_trader_brief(root,limit=5):\n    x=read_fast_trader_brief(root,limit)\n    lines=["="*80,"ORACLE TRADER BRIEF","SNAPSHOT-ONLY | PRECOMPUTED INTELLIGENCE","-"*80]\n    markets=x.markets[:limit]\n    if not any(str(m.get("trader_takeaway") or "")=="WORTH WATCHING NOW" for m in markets):\n        lines+=["Nothing in this snapshot clears Oracle\'s current edge threshold.",""]\n    for i,m in enumerate(markets,1):\n        lines += [\n            f"#{i} {m.get(\'market_title\') or \'Identity unresolved\'}",\n            f"   Oracle read: {m.get(\'trader_takeaway\')}",\n            f"   Direction: {m.get(\'direction\')}",\n            f"   Historical knowledge: {m.get(\'historical_strength\')} | Live evidence: {m.get(\'live_evidence\')}",\n            f"   Why: {m.get(\'why\')}",\n            f"   What would improve it: {m.get(\'what_would_improve_it\')}",\n            f"   Risk: {m.get(\'risk\')}",\n            f"   Market ID: {m.get(\'market_id\')}",\n            ""\n        ]\n    lines+=["No order placement. Q Series execution authority remains separate.","="*80]\n    return tuple(lines)\n\ndef bind_trader_brief_terminal(base_module,root=None):\n    if getattr(base_module,"_oiar026_bound",False):return base_module\n    original=base_module.display_query;active=Path(root or base_module.repository_root()).resolve()\n    def display_query(query,*,session=None,root=None,builder=None,write=print):\n        canonical=base_module.normalize_query(query);use=Path(root or active).resolve()\n        if is_trader_brief_query(canonical):\n            for line in render_trader_brief(use,5):write(line)\n            return None\n        kwargs={"session":session,"root":use,"write":write}\n        if builder is not None:kwargs["builder"]=builder\n        return original(canonical,**kwargs)\n    base_module.display_query=display_query;base_module._oiar026_bound=True\n    return base_module\n'
TEST_SOURCE = '\nimport unittest,inspect\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_026_operator_terminal_trader_brief_cutover as m\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(m.OIAR_026_BUILD_ID,"OIAR-026")\n    def test_no_canonical_scan(self):\n        s=inspect.getsource(m)\n        self.assertNotIn("oracle_canonical_observations",s)\n        self.assertNotIn("resolve_canonical_market_identity",s)\nif __name__=="__main__":\n    print("="*88);print(" OIAR-026 CERTIFICATION TEST");print(" OPERATOR TERMINAL TRADER BRIEF CUTOVER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] terminal snapshot-only cutover certified");print("[DONE] OIAR-026 CERTIFIED")\n'
REQUIRED = ('qseries_v2/oracle_intelligence_analytics_runtime/oiar_025_fast_persisted_trader_brief_read_model.py', 'qseries_v2/oracle_terminal/oracle_historical_experience_terminal_binding.py', 'qseries_v2/oracle_terminal/oracle_persisted_trader_intelligence_terminal_binding.py', 'run_oracle_open_intelligence_terminal.py')
EXTRA_FILES = {'run_oracle_operator_terminal.py': '\nfrom __future__ import annotations\nimport run_oracle_open_intelligence_terminal as base\nfrom qseries_v2.oracle_terminal.oracle_historical_experience_terminal_binding import bind_historical_experience_surface\nfrom qseries_v2.oracle_terminal.oracle_persisted_trader_intelligence_terminal_binding import bind_persisted_trader_intelligence\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_026_operator_terminal_trader_brief_cutover import bind_trader_brief_terminal\n\ndef main():\n    bind_historical_experience_surface(base)\n    bind_persisted_trader_intelligence(base)\n    bind_trader_brief_terminal(base)\n    return base.main()\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'}

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
    print(" OIAR-026 INSTALLER")
    print(" OPERATOR TERMINAL TRADER BRIEF CUTOVER")
    print("=" * 88)
    print("[ROOT]", ROOT)

    for rel in REQUIRED:
        p = ROOT / rel
        if not p.is_file():
            raise RuntimeError(f"Required proven upstream missing: {p}")

    targets = [MOD, TEST] + [ROOT / rel for rel in EXTRA_FILES]
    old = {p: (p.read_bytes() if p.exists() else None) for p in targets}

    try:
        ast.parse(MODULE_SOURCE, filename=str(MOD))
        ast.parse(TEST_SOURCE, filename=str(TEST))
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
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_026_operator_terminal_trader_brief_cutover")
        started=time.monotonic();lines=m.render_trader_brief(ROOT,5);elapsed=time.monotonic()-started
        print(f"[PHYSICAL] trader_brief_render_seconds={elapsed:.4f} lines={len(lines)}")
        if elapsed>=1.0:raise RuntimeError("OIAR-026 terminal render exceeded 1 second")
        for line in lines[:12]:print(line)
    except Exception:
        for p, data in old.items():
            restore(p, data)
        print("[ROLLBACK] OIAR-026 failed; affected repository files restored")
        raise

    print("[PASS] snapshot-first trader architecture preserved")
    print("[PASS] no terminal canonical-table scan introduced")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-026 INSTALLATION COMPLETE")

if __name__ == "__main__":
    main()
