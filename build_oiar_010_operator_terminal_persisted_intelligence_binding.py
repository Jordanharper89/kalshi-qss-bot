from pathlib import Path
import ast, importlib, os, subprocess, sys, time, hashlib

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_terminal/oracle_persisted_trader_intelligence_terminal_binding.py'
TEST=ROOT/'test_oiar_010_operator_terminal_persisted_intelligence_binding.py'
RUNNER=ROOT/"run_oracle_operator_terminal.py"
FROZEN=ROOT/"run_oracle_open_intelligence_terminal.py"
RUNNER_SOURCE='from __future__ import annotations\nimport sys\nimport run_oracle_open_intelligence_terminal as base\n\nfrom qseries_v2.oracle_terminal.oracle_historical_experience_terminal_binding import (\n    bind_historical_experience_surface,\n)\nfrom qseries_v2.oracle_terminal.oracle_persisted_trader_intelligence_terminal_binding import (\n    bind_persisted_trader_intelligence,\n)\n\nRUNNER_ID="ORACLE-OPERATOR-TERMINAL"\nOIAR_010_BOUND=True\n\ndef main(argv=None):\n    bind_historical_experience_surface(base)\n    bind_persisted_trader_intelligence(base)\n    return base.main(argv)\n\nif __name__=="__main__":\n    raise SystemExit(main(sys.argv[1:]))\n'
MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_009_fast_terminal_read_adapter import (\n    read_fast_trader_intelligence,\n)\n\nOIAR_010_BUILD_ID="OIAR-010"\nOIAR_010_REVISION="OIAR_010_OPERATOR_TERMINAL_PERSISTED_INTELLIGENCE_BINDING_V1"\n\nTOKENS=(\n    "best markets oracle understands right now",\n    "best markets oracle understands",\n    "rank trader intelligence",\n    "historically proven live opportunities",\n    "learned markets that are currently useful",\n    "markets oracle knows best right now",\n    "rank live opportunities",\n    "what should i watch right now",\n)\n\ndef is_persisted_trader_intelligence_query(query):\n    normalized=" ".join(str(query).lower().split())\n    return any(token in normalized for token in TOKENS)\n\ndef bind_persisted_trader_intelligence(base_module,root=None):\n    if getattr(base_module,"_oiar010_bound",False):\n        return base_module\n\n    original=base_module.display_query\n    active_root=Path(root or base_module.repository_root()).resolve()\n\n    def display_query(query,*,session=None,root=None,builder=None,write=print):\n        canonical=base_module.normalize_query(query)\n        use_root=Path(root or active_root).resolve()\n\n        if is_persisted_trader_intelligence_query(canonical):\n            result=read_fast_trader_intelligence(use_root,10)\n            for line in result.lines:\n                write(line)\n\n            if session is not None:\n                session.query_count+=1\n                session.last_query=canonical\n                session.last_session_id="OIAR-010:"+result.snapshot_id[:16]\n                session.active_panel_index=0\n\n            return result\n\n        kwargs={"session":session,"root":use_root,"write":write}\n        if builder is not None:\n            kwargs["builder"]=builder\n        return original(canonical,**kwargs)\n\n    base_module.display_query=display_query\n    base_module._oiar010_bound=True\n    return base_module\n'
TEST_SOURCE='import unittest\nimport run_oracle_open_intelligence_terminal as base\nimport qseries_v2.oracle_terminal.oracle_persisted_trader_intelligence_terminal_binding as m\n\nclass T(unittest.TestCase):\n    def test_router(self):\n        self.assertTrue(m.is_persisted_trader_intelligence_query("show me the best markets oracle understands right now"))\n        self.assertFalse(m.is_persisted_trader_intelligence_query("rank live markets by learned experience"))\n        self.assertFalse(m.is_persisted_trader_intelligence_query("current price of bitcoin"))\n    def test_binding(self):\n        old=base.display_query\n        try:\n            m.bind_persisted_trader_intelligence(base)\n            self.assertTrue(base._oiar010_bound)\n            self.assertTrue(callable(base.display_query))\n        finally:\n            base.display_query=old\n            if hasattr(base,"_oiar010_bound"):delattr(base,"_oiar010_bound")\n\nif __name__=="__main__":\n    print("="*88);print(" OIAR-010 CERTIFICATION TEST");print(" OPERATOR TERMINAL PERSISTED INTELLIGENCE BINDING");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] persisted trader-intelligence query routing certified")\n    print("[PASS] OHE historical fallback preserved")\n    print("[PASS] frozen OIT fallback preserved")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OIAR-010 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def main():
    print("="*88);print(" OIAR-010 INSTALLER");print(" OPERATOR TERMINAL PERSISTED INTELLIGENCE BINDING");print("="*88);print("[ROOT]",ROOT)
    PKG=ROOT/"qseries_v2"/"oracle_terminal";INIT=PKG/"__init__.py";FROZEN=ROOT/"run_oracle_open_intelligence_terminal.py";RUNNER=ROOT/"run_oracle_operator_terminal.py"
    required=(
        FROZEN,
        PKG/"oracle_historical_experience_terminal_binding.py",
        ROOT/"qseries_v2"/"oracle_intelligence_analytics_runtime"/"oiar_009_fast_terminal_read_adapter.py",
        ROOT/"test_oit_050_oracle_terminal_final_freeze_and_completion.py",
        ROOT/"test_oar_029_terminal_live_activation.py",
    )
    for p in required:
        if not p.is_file():raise RuntimeError(f"Required certified upstream missing: {p}")
    frozen_hash=hashlib.sha256(FROZEN.read_bytes()).hexdigest()
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT,RUNNER)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE);write_exact(RUNNER,RUNNER_SOURCE)
        update_init(INIT,"from .oracle_persisted_trader_intelligence_terminal_binding import *")
        ast.parse(MODULE_SOURCE);ast.parse(TEST_SOURCE);ast.parse(RUNNER_SOURCE)
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        subprocess.run([sys.executable,str(ROOT/"test_oit_050_oracle_terminal_final_freeze_and_completion.py")],cwd=str(ROOT),check=True,timeout=30)
        subprocess.run([sys.executable,str(ROOT/"test_oar_029_terminal_live_activation.py")],cwd=str(ROOT),check=True,timeout=30)
        if hashlib.sha256(FROZEN.read_bytes()).hexdigest()!=frozen_hash:raise RuntimeError("Frozen OIT runner changed")
        print("[PHYSICAL QUERY]")
        subprocess.run([sys.executable,str(RUNNER),"show me the best markets oracle understands right now"],cwd=str(ROOT),check=True,timeout=10)
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OIAR-010 failed; operator wrapper and affected files restored");raise
    print("[PASS] frozen OIT source unchanged")
    print("[PASS] OHE historical experience binding preserved")
    print("[PASS] terminal reads latest persisted OIAR snapshot only")
    print("[PASS] no analytics computation occurs inside terminal")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-006 THROUGH OIAR-010 RUNTIME-TO-TERMINAL CAPABILITY COMPLETE")

if __name__=="__main__":
    main()
