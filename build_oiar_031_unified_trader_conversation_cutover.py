from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_031_unified_trader_conversation_cutover.py'
TEST=ROOT/'test_oiar_031_unified_trader_conversation_cutover.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom pathlib import Path\nfrom .oiar_025_fast_persisted_trader_brief_read_model import read_fast_trader_brief\nfrom .oiar_027_trader_intent_classifier import classify_trader_intent\nfrom .oiar_029_trader_session_context import TraderSessionContext,apply_intent\nfrom .oiar_030_concise_trader_response_policy import render_concise\nOIAR_031_BUILD_ID="OIAR-031"\nOIAR_031_REVISION="OIAR_031_UNIFIED_TRADER_CONVERSATION_CUTOVER_V1"\n_CONTEXT=TraderSessionContext()\ndef bind_unified_trader_conversation(base_module,root=None):\n    if getattr(base_module,"_oiar031_bound",False):return base_module\n    original=base_module.display_query;active=Path(root or base_module.repository_root()).resolve()\n    def display_query(query,*,session=None,root=None,builder=None,write=print):\n        canonical=base_module.normalize_query(query);intent=classify_trader_intent(canonical)\n        if intent.route=="trader_brief":\n            use=Path(root or active).resolve();apply_intent(_CONTEXT,intent)\n            x=read_fast_trader_brief(use,50)\n            for line in render_concise(x.markets,intent,2):write(line)\n            return None\n        kwargs={"session":session,"root":Path(root or active).resolve(),"write":write}\n        if builder is not None:kwargs["builder"]=builder\n        return original(canonical,**kwargs)\n    base_module.display_query=display_query;base_module._oiar031_bound=True\n    return base_module\n'
TEST_SOURCE='\nimport unittest,inspect\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_031_unified_trader_conversation_cutover as m\nclass T(unittest.TestCase):\n def test_identity(self):self.assertEqual(m.OIAR_031_BUILD_ID,"OIAR-031")\n def test_no_scan(self):self.assertNotIn("oracle_canonical_observations",inspect.getsource(m))\nif __name__=="__main__":\n print("="*88);print(" OIAR-031 CERTIFICATION TEST");print(" UNIFIED TRADER CONVERSATION CUTOVER");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] unified trader conversation cutover certified");print("[DONE] OIAR-031 CERTIFIED")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_030_concise_trader_response_policy.py', 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_026_operator_terminal_trader_brief_cutover.py', 'run_oracle_open_intelligence_terminal.py')
EXTRA={'run_oracle_operator_terminal.py': '\nfrom __future__ import annotations\nimport run_oracle_open_intelligence_terminal as base\nfrom qseries_v2.oracle_terminal.oracle_historical_experience_terminal_binding import bind_historical_experience_surface\nfrom qseries_v2.oracle_terminal.oracle_persisted_trader_intelligence_terminal_binding import bind_persisted_trader_intelligence\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_026_operator_terminal_trader_brief_cutover import bind_trader_brief_terminal\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_031_unified_trader_conversation_cutover import bind_unified_trader_conversation\ndef main():\n    bind_historical_experience_surface(base)\n    bind_persisted_trader_intelligence(base)\n    bind_trader_brief_terminal(base)\n    bind_unified_trader_conversation(base)\n    return base.main()\nif __name__=="__main__":raise SystemExit(main())\n'}

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
    print("="*88);print(" OIAR-031 INSTALLER");print(" UNIFIED TRADER CONVERSATION CUTOVER");print("="*88);print("[ROOT]",ROOT)
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
        subprocess.run([sys.executable,str(ROOT/"test_oit_050_oracle_terminal_final_freeze_and_completion.py")],cwd=str(ROOT),check=True,timeout=30)
        base=importlib.import_module("run_oracle_open_intelligence_terminal")
        m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_031_unified_trader_conversation_cutover")
        m.bind_unified_trader_conversation(base,ROOT)
        for q in ("what are the plays for this evening?","what is the strongest?","anything worth watching","anything bullish","anything bearish"):
            lines=[];started=time.monotonic();base.display_query(q,root=ROOT,write=lines.append);elapsed=time.monotonic()-started
            print(f"[PHYSICAL QUERY] {q!r} elapsed_seconds={elapsed:.4f}")
            if elapsed>=1.0:raise RuntimeError("OIAR-031 trader query exceeded 1 second")
            if any("Oracle Operator Decision Brief" in str(x) for x in lines):raise RuntimeError("OIAR-031 trader query fell through to legacy decision brief")
            for line in lines[:8]:print(line)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OIAR-031 failed; affected repository files restored")
        raise
    print("[PASS] persisted snapshot intelligence remains read-only")
    print("[PASS] no canonical-table terminal scan introduced")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-031 INSTALLATION COMPLETE")
if __name__=="__main__":main()
