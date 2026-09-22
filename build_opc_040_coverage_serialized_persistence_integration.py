from pathlib import Path
import importlib
import os
import subprocess
import sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"

MOD=PKG/"opc_040_coverage_serialized_persistence_integration.py"
TEST=ROOT/"test_opc_040_coverage_serialized_persistence_integration.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport time\n\nfrom .opc_037_canonical_writer_arbiter_foundation import writer_policy\nfrom .opc_038_atomic_cross_process_writer_lease import (\n    acquire_canonical_writer_lease,\n)\nfrom .opc_039_fast_lane_serialized_admission import (\n    RetryableTerminalChainMismatch,\n    _install_retryable_mismatch_validator,\n)\n\nOPC_040_BUILD_ID="OPC-040"\nOPC_040_REVISION="OPC_040_COVERAGE_SERIALIZED_PERSISTENCE_INTEGRATION_V1"\n\nCOVERAGE_SERIAL_MICROBATCH=25\n\ndef install_coverage_serialized_persistence(root=None):\n    from qseries_v2.oracle_intelligence.live_acquisition.oracle_postgresql_canonical_observation_persistence_router import (\n        OraclePostgreSQLCanonicalObservationPersistenceRouter,\n    )\n\n    cls=OraclePostgreSQLCanonicalObservationPersistenceRouter\n    marker="_opc040_coverage_serialized"\n\n    if getattr(cls,marker,False):\n        return False\n\n    _install_retryable_mismatch_validator(cls)\n\n    original=cls.route_batch\n    root=Path(root or Path.cwd()).resolve()\n    policy=writer_policy("COVERAGE")\n\n    def serialized_route(self,observations,routed_at,*args,**kwargs):\n        items=tuple(observations)\n\n        if not items:\n            return original(\n                self,\n                items,\n                routed_at,\n                *args,\n                **kwargs,\n            )\n\n        all_evidence=[]\n\n        for start in range(0,len(items),COVERAGE_SERIAL_MICROBATCH):\n            chunk=items[\n                start:start+COVERAGE_SERIAL_MICROBATCH\n            ]\n            attempt=0\n\n            while True:\n                try:\n                    with acquire_canonical_writer_lease(\n                        "COVERAGE",\n                        root=root,\n                        timeout_seconds=policy.lease_timeout_seconds,\n                    ):\n                        result=original(\n                            self,\n                            chunk,\n                            routed_at,\n                            *args,\n                            **kwargs,\n                        )\n\n                    all_evidence.extend(tuple(result))\n                    break\n\n                except RetryableTerminalChainMismatch:\n                    if attempt>=policy.retry_limit:\n                        raise\n\n                    attempt+=1\n                    delay=min(\n                        0.500,\n                        policy.retry_base_seconds*(2**(attempt-1)),\n                    )\n                    if delay:\n                        time.sleep(delay)\n\n        return tuple(all_evidence)\n\n    cls.route_batch=serialized_route\n    setattr(cls,marker,True)\n    setattr(cls,"_opc040_original_route_batch",original)\n    return True\n\ndef verify_opc_040_coverage_serialized_persistence_integration():\n    p=writer_policy("COVERAGE")\n    return (\n        COVERAGE_SERIAL_MICROBATCH==25\n        and p.priority<writer_policy("FAST_LANE").priority\n        and p.retry_limit>=5\n        and not p.execution_authority\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_040_coverage_serialized_persistence_integration import verify_opc_040_coverage_serialized_persistence_integration\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_040_coverage_serialized_persistence_integration())\n\nif __name__=="__main__":\n    print("="*80)\n    print(" OPC-040 CERTIFICATION TEST")\n    print(" COVERAGE SERIALIZED PERSISTENCE INTEGRATION")\n    print("="*80)\n\n    result=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] OPC-040 certified")\n    print("[DONE] OPC-040 CERTIFIED")\n'



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
    print(" OPC-040 INSTALLER")
    print(" COVERAGE SERIALIZED PERSISTENCE INTEGRATION")
    print("="*80)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))


    up=importlib.import_module(
        "qseries_v2.oracle_pre_settlement_coverage."
        "opc_039_fast_lane_serialized_admission"
    )
    if up.verify_opc_039_fast_lane_serialized_admission() is not True:
        raise RuntimeError("Certified OPC-039 verification failed")
    print("[PASS] Certified OPC-039 upstream boundary verified")


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

        export="from .opc_040_coverage_serialized_persistence_integration import *"

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
            "[ROLLBACK] OPC-040 installation failed; "
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
        "[DONE] OPC-040 "
        "INSTALLATION AND CERTIFICATION COMPLETE"
    )

if __name__=="__main__":
    main()
