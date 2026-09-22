from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_025_physical_oracle_live_runtime_activation_gate.py";TEST=ROOT/"test_opc_025_physical_oracle_live_runtime_activation_gate.py";INIT=PKG/"__init__.py"
MODULE='import importlib\nfrom dataclasses import dataclass\n@dataclass(frozen=True)\nclass OPC025Activation:\n    child_name:str;runner_name:str;certified:bool;terminal_dependency:bool=False;execution_authority:bool=False\ndef verify_opc_025_physical_oracle_live_runtime_activation_gate():\n    checks=(("opc_021_production_coverage_child_contract","verify_opc_021_production_coverage_child_contract"),("opc_022_rotating_universe_cursor_load_budget","verify_opc_022_rotating_universe_cursor_load_budget"),("opc_023_rotating_full_universe_coverage_cycle","verify_opc_023_rotating_full_universe_coverage_cycle"),("opc_024_supervised_24x7_coverage_runtime","verify_opc_024_supervised_24x7_coverage_runtime"))\n    return all(getattr(importlib.import_module("qseries_v2.oracle_pre_settlement_coverage."+m),f)() for m,f in checks)\ndef activation_report():\n    if not verify_opc_025_physical_oracle_live_runtime_activation_gate(): raise RuntimeError("OPC activation failed")\n    return OPC025Activation("coverage","run_opc_025_continuous_coverage_child.py",True,False,False)\n';TESTSRC='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_025_physical_oracle_live_runtime_activation_gate import verify_opc_025_physical_oracle_live_runtime_activation_gate\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_opc_025_physical_oracle_live_runtime_activation_gate())\nif __name__=="__main__":\n    print("="*72);print(" OPC-025 CERTIFICATION TEST");print(" PHYSICAL ORACLE LIVE RUNTIME ACTIVATION GATE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OPC-025 certified");print("[DONE] OPC-025 CERTIFIED")\n'
RUNNER=ROOT/"run_opc_025_continuous_coverage_child.py"
LAUNCHER=ROOT/"run_oracle_LIVE.py"
RUNNER_SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_022_rotating_universe_cursor_load_budget import CoverageLoadBudget\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_024_supervised_24x7_coverage_runtime import run_supervised_coverage_forever\nif __name__=="__main__":\n    print("="*72,flush=True);print(" OPC-025 CONTINUOUS UNIVERSAL PRE-SETTLEMENT COVERAGE CHILD",flush=True);print("="*72,flush=True)\n    b=CoverageLoadBudget();print(f"[COVERAGE] page_limit={b.page_limit} max_snapshots_per_cycle={b.max_snapshots_per_cycle} sleep_seconds={b.cycle_sleep_seconds}",flush=True)\n    raise SystemExit(run_supervised_coverage_forever(Path.cwd(),b,lambda x:print(x,flush=True)))\n'

def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def patch_launcher_children(source):
    import ast
    tree=ast.parse(source);node=None
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets) and isinstance(item.value,ast.Dict):
            node=item.value;break
    if node is None: raise RuntimeError("run_oracle_LIVE.py CHILDREN dictionary not found")
    for k in node.keys:
        if isinstance(k,ast.Constant) and k.value=="coverage": return source,False
    lines=source.splitlines(keepends=True);close=node.end_lineno-1
    base=lines[node.lineno-1];indent=base[:len(base)-len(base.lstrip())]+"    "
    if node.values:
        sample=lines[node.values[-1].lineno-1];indent=sample[:len(sample)-len(sample.lstrip())]
    lines.insert(close,indent+'"coverage":"run_opc_025_continuous_coverage_child.py",\n')
    patched="".join(lines);ast.parse(patched);return patched,True

def main():
    print("="*72);print(" OPC-025 INSTALLER");print(" PHYSICAL ORACLE LIVE RUNTIME ACTIVATION GATE");print("="*72);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_024_supervised_24x7_coverage_runtime")
    if up.verify_opc_024_supervised_24x7_coverage_runtime() is not True: raise RuntimeError("OPC-024 failed")
    print("[PASS] Certified OPC-024 upstream boundary verified")
    affected=(MOD,TEST,INIT,RUNNER,LAUNCHER);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE);write_exact(TEST,TESTSRC)
        write_exact(RUNNER,RUNNER_SOURCE)
        if not LAUNCHER.is_file(): raise RuntimeError("run_oracle_LIVE.py missing")
        patched,changed=patch_launcher_children(LAUNCHER.read_text(encoding="utf-8"))
        if changed: write_exact(LAUNCHER,patched)
        print("[PASS] Oracle Live CHILDREN registry contains coverage child")
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else "";ex="from .opc_025_physical_oracle_live_runtime_activation_gate import *"
        if ex not in cur: write_exact(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        compile(LAUNCHER.read_text(encoding="utf-8"),str(LAUNCHER),"exec")
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True)
        print("[PASS] Oracle Live --check passed after coverage binding")

    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] OPC-025 installation failed");raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT));print("[PASS] Wrote:",TEST.name);print("[DONE] OPC-025 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
