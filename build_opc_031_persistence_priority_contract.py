from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_031_persistence_priority_contract.py"
TEST=ROOT/"test_opc_031_persistence_priority_contract.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nOPC_031_BUILD_ID="OPC-031"\nOPC_031_REVISION="OPC_031_PERSISTENCE_PRIORITY_CONTRACT_V1"\n\n@dataclass(frozen=True)\nclass PersistencePriority:\n    name:str\n    rank:int\n    blocking_timeout_seconds:float\n    microbatch_size:int\n    execution_authority:bool=False\n\nFAST_LANE=PersistencePriority("FAST_LANE",100,5.0,1,False)\nCOVERAGE=PersistencePriority("COVERAGE",20,5.0,25,False)\n\ndef priority_for_child(child_name):\n    name=str(child_name).strip().lower()\n    if name=="fast_lane":\n        return FAST_LANE\n    if name=="coverage":\n        return COVERAGE\n    raise ValueError("unsupported persistence child")\n\ndef verify_opc_031_persistence_priority_contract():\n    return (\n        FAST_LANE.rank>COVERAGE.rank\n        and FAST_LANE.microbatch_size==1\n        and COVERAGE.microbatch_size==25\n        and not FAST_LANE.execution_authority\n        and not COVERAGE.execution_authority\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_031_persistence_priority_contract import verify_opc_031_persistence_priority_contract\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_031_persistence_priority_contract())\n\nif __name__=="__main__":\n    print("="*80)\n    print(" OPC-031 CERTIFICATION TEST")\n    print(" PERSISTENCE PRIORITY CONTRACT")\n    print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OPC-031 certified")\n    print("[DONE] OPC-031 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)


def main():
    print("="*80)
    print(" OPC-031 INSTALLER")
    print(" PERSISTENCE PRIORITY CONTRACT")
    print("="*80)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_030_high_throughput_universal_coverage_gate")
    if up.verify_opc_030_high_throughput_universal_coverage_gate() is not True:
        raise RuntimeError("Certified OPC-030 verification failed")
    print("[PASS] Certified OPC-030 upstream boundary verified")

    affected=(MOD,TEST,INIT)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .opc_031_persistence_priority_contract import *"
        if export not in current:
            write_exact(INIT,current.rstrip()+"\n"+export+"\n")

        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),
            check=True,
        )

    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] OPC-031 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[DONE] OPC-031 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
