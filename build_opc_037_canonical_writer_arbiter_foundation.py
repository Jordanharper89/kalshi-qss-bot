from pathlib import Path
import importlib
import os
import subprocess
import sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"

MOD=PKG/"opc_037_canonical_writer_arbiter_foundation.py"
TEST=ROOT/"test_opc_037_canonical_writer_arbiter_foundation.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nOPC_037_BUILD_ID="OPC-037"\nOPC_037_REVISION="OPC_037_CANONICAL_WRITER_ARBITER_FOUNDATION_V1"\n\n@dataclass(frozen=True)\nclass CanonicalWriterPolicy:\n    writer:str\n    priority:int\n    retry_limit:int\n    retry_base_seconds:float\n    lease_timeout_seconds:float\n    execution_authority:bool=False\n\nFAST_LANE_POLICY=CanonicalWriterPolicy(\n    "FAST_LANE",100,8,0.005,5.0,False\n)\n\nCOVERAGE_POLICY=CanonicalWriterPolicy(\n    "COVERAGE",20,8,0.025,10.0,False\n)\n\ndef writer_policy(writer):\n    name=str(writer).strip().upper()\n    if name=="FAST_LANE":\n        return FAST_LANE_POLICY\n    if name=="COVERAGE":\n        return COVERAGE_POLICY\n    raise ValueError("unsupported canonical writer")\n\ndef verify_opc_037_canonical_writer_arbiter_foundation():\n    return (\n        FAST_LANE_POLICY.priority>COVERAGE_POLICY.priority\n        and FAST_LANE_POLICY.retry_base_seconds<COVERAGE_POLICY.retry_base_seconds\n        and FAST_LANE_POLICY.retry_limit>=5\n        and COVERAGE_POLICY.retry_limit>=5\n        and not FAST_LANE_POLICY.execution_authority\n        and not COVERAGE_POLICY.execution_authority\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_037_canonical_writer_arbiter_foundation import verify_opc_037_canonical_writer_arbiter_foundation\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_037_canonical_writer_arbiter_foundation())\n\nif __name__=="__main__":\n    print("="*80)\n    print(" OPC-037 CERTIFICATION TEST")\n    print(" CANONICAL WRITER ARBITER FOUNDATION")\n    print("="*80)\n\n    result=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] OPC-037 certified")\n    print("[DONE] OPC-037 CERTIFIED")\n'



def write_exact(path,text):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    tmp=path.with_suffix(
        path.suffix+".tmp"
    )
    tmp.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )
    os.replace(tmp,path)



def main():
    print("="*80)
    print(" OPC-037 INSTALLER")
    print(" CANONICAL WRITER ARBITER FOUNDATION")
    print("="*80)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))


    up=importlib.import_module(
        "qseries_v2.oracle_pre_settlement_coverage."
        "opc_035_priority_persistence_activation_gate"
    )
    if up.verify_opc_035_priority_persistence_activation_gate() is not True:
        raise RuntimeError("Certified OPC-035 verification failed")
    print("[PASS] Certified OPC-035 upstream boundary verified")


    affected=(MOD,TEST,INIT)

    backups={
        path:(
            path.read_bytes()
            if path.exists()
            else None
        )
        for path in affected
    }

    try:
        write_exact(
            MOD,
            MODULE_SOURCE,
        )
        write_exact(
            TEST,
            TEST_SOURCE,
        )



        current=(
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )

        export="from .opc_037_canonical_writer_arbiter_foundation import *"

        if export not in current:
            write_exact(
                INIT,
                current.rstrip()+"\n"+export+"\n",
            )

        compile(
            MOD.read_text(encoding="utf-8"),
            str(MOD),
            "exec",
        )

        compile(
            TEST.read_text(encoding="utf-8"),
            str(TEST),
            "exec",
        )

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),
            check=True,
        )



    except Exception:
        for path,old in backups.items():
            if old is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(old)

        print(
            "[ROLLBACK] OPC-037 installation failed; "
            "affected files restored"
        )
        raise

    print(
        "[PASS] Wrote:",
        MOD.relative_to(ROOT),
    )
    print(
        "[PASS] Wrote:",
        TEST.name,
    )
    print(
        "[DONE] OPC-037 "
        "INSTALLATION AND CERTIFICATION COMPLETE"
    )

if __name__=="__main__":
    main()
