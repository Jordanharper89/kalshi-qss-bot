from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_021_production_coverage_child_contract.py";TEST=ROOT/"test_opc_021_production_coverage_child_contract.py";INIT=PKG/"__init__.py"
MODULE='from dataclasses import dataclass\n@dataclass(frozen=True)\nclass ProductionCoverageChildContract:\n    child_name:str="coverage"\n    runner_name:str="run_opc_025_continuous_coverage_child.py"\n    terminal_dependency:bool=False\n    execution_authority:bool=False\n    restart_supervised:bool=True\n    durable_resume:bool=True\n    full_universe_rotation:bool=True\ndef build_production_coverage_child_contract(): return ProductionCoverageChildContract()\ndef verify_opc_021_production_coverage_child_contract():\n    c=build_production_coverage_child_contract()\n    return c.child_name=="coverage" and c.restart_supervised and c.durable_resume and c.full_universe_rotation and not c.terminal_dependency and not c.execution_authority\n';TESTSRC='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_021_production_coverage_child_contract import verify_opc_021_production_coverage_child_contract\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_opc_021_production_coverage_child_contract())\nif __name__=="__main__":\n    print("="*72);print(" OPC-021 CERTIFICATION TEST");print(" PRODUCTION COVERAGE CHILD CONTRACT");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OPC-021 certified");print("[DONE] OPC-021 CERTIFIED")\n'

def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)

def main():
    print("="*72);print(" OPC-021 INSTALLER");print(" PRODUCTION COVERAGE CHILD CONTRACT");print("="*72);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_020_oracle_live_runtime_integration_gate")
    if up.verify_opc_020_oracle_live_runtime_integration_gate() is not True: raise RuntimeError("OPC-020 failed")
    print("[PASS] Certified OPC-020 upstream boundary verified")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE);write_exact(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else "";ex="from .opc_021_production_coverage_child_contract import *"
        if ex not in cur: write_exact(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] OPC-021 installation failed");raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT));print("[PASS] Wrote:",TEST.name);print("[DONE] OPC-021 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
