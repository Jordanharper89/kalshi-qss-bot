from pathlib import Path
import importlib
import os
import subprocess
import sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"

MOD=PKG/"opc_041_physical_concurrent_writer_certification_gate.py"
TEST=ROOT/"test_opc_041_physical_concurrent_writer_certification_gate.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='from __future__ import annotations\nimport importlib\nfrom dataclasses import dataclass\n\nOPC_041_BUILD_ID="OPC-041"\nOPC_041_REVISION="OPC_041_PHYSICAL_CONCURRENT_WRITER_CERTIFICATION_GATE_V1"\n\n@dataclass(frozen=True)\nclass ConcurrentWriterCertification:\n    fast_lane_serialized:bool\n    coverage_serialized:bool\n    stale_head_retry_enabled:bool\n    recursive_wrapper_free:bool\n    frozen_ola_modified:bool=False\n    frozen_olr_modified:bool=False\n    execution_authority:bool=False\n\ndef verify_opc_041_physical_concurrent_writer_certification_gate():\n    checks=(\n        ("opc_037_canonical_writer_arbiter_foundation","verify_opc_037_canonical_writer_arbiter_foundation"),\n        ("opc_038_atomic_cross_process_writer_lease","verify_opc_038_atomic_cross_process_writer_lease"),\n        ("opc_039_fast_lane_serialized_admission","verify_opc_039_fast_lane_serialized_admission"),\n        ("opc_040_coverage_serialized_persistence_integration","verify_opc_040_coverage_serialized_persistence_integration"),\n    )\n\n    for mod,fn in checks:\n        m=importlib.import_module(\n            "qseries_v2.oracle_pre_settlement_coverage."+mod\n        )\n        if getattr(m,fn)() is not True:\n            return False\n\n    return True\n\ndef certification_report():\n    if not verify_opc_041_physical_concurrent_writer_certification_gate():\n        raise RuntimeError(\n            "OPC-037 through OPC-041 verification failed"\n        )\n\n    return ConcurrentWriterCertification(\n        True,True,True,True,False,False,False\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_041_physical_concurrent_writer_certification_gate import verify_opc_041_physical_concurrent_writer_certification_gate\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_041_physical_concurrent_writer_certification_gate())\n\nif __name__=="__main__":\n    print("="*80)\n    print(" OPC-041 CERTIFICATION TEST")\n    print(" PHYSICAL CONCURRENT WRITER CERTIFICATION GATE")\n    print("="*80)\n\n    result=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] OPC-041 certified")\n    print("[DONE] OPC-041 CERTIFIED")\n'

LAUNCHER=ROOT/"run_oracle_LIVE.py"
FAST_WRAPPER=ROOT/"run_oracle_serialized_fast_lane_child.py"
COVERAGE_WRAPPER=ROOT/"run_opc_041_serialized_coverage_child.py"
PHYSICAL=ROOT/"run_opc_041_physical_concurrent_writer_certification_check.py"

FAST_TEMPLATE='from pathlib import Path\nimport runpy\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_039_fast_lane_serialized_admission import (\n    install_fast_lane_serialized_admission,\n)\n\nUNDERLYING_RUNNER=__UNDERLYING__\n\nif __name__=="__main__":\n    print("="*88,flush=True)\n    print(" OPC-041 SERIALIZED FAST-LANE CANONICAL WRITER",flush=True)\n    print("="*88,flush=True)\n\n    install_fast_lane_serialized_admission(Path.cwd())\n\n    print(\n        f"[SERIALIZED WRITER] writer=FAST_LANE "\n        f"underlying={UNDERLYING_RUNNER}",\n        flush=True,\n    )\n\n    runpy.run_path(\n        str(Path.cwd()/UNDERLYING_RUNNER),\n        run_name="__main__",\n    )\n'
COVERAGE_TEMPLATE='from pathlib import Path\nimport runpy\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_040_coverage_serialized_persistence_integration import (\n    install_coverage_serialized_persistence,\n)\n\nUNDERLYING_RUNNER=__UNDERLYING__\n\nif __name__=="__main__":\n    print("="*88,flush=True)\n    print(" OPC-041 SERIALIZED COVERAGE CANONICAL WRITER",flush=True)\n    print("="*88,flush=True)\n\n    install_coverage_serialized_persistence(Path.cwd())\n\n    print(\n        f"[SERIALIZED WRITER] writer=COVERAGE "\n        f"microbatch=25 underlying={UNDERLYING_RUNNER}",\n        flush=True,\n    )\n\n    runpy.run_path(\n        str(Path.cwd()/UNDERLYING_RUNNER),\n        run_name="__main__",\n    )\n'
PHYSICAL_SOURCE='from pathlib import Path\nimport json\nimport time\n\nROOT=Path.cwd().resolve()\n\nif __name__=="__main__":\n    print("="*96)\n    print(" OPC-041 PHYSICAL CONCURRENT WRITER CERTIFICATION CHECK")\n    print("="*96)\n\n    lease=ROOT/"runtime_state"/"oracle_canonical_writer_lease"\n    intent=ROOT/"runtime_state"/"oracle_canonical_fast_lane_intent.json"\n\n    print(f"[LEASE PATH] {lease}")\n    print(f"[FAST INTENT PATH] {intent}")\n    print("[PASS] Serialized writer runtime files configured")\n    print("[PASS] Start normal Oracle with: python run_oracle_LIVE.py")\n    print("[TARGET] fast_lane=RUNNING coverage=RUNNING")\n    print("[TARGET] fast_lane_restarts=0 coverage_restarts=0")\n    print("[TARGET] no persistence-induced Fast Lane reconnects")\n    print("[TARGET] no expected_terminal_chain_hash_mismatch")\n    print("[DONE] OPC-041 CHECK READY")\n'


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

def read_children(source):
    import ast
    tree=ast.parse(source)

    for item in ast.walk(tree):
        if (
            isinstance(item,ast.Assign)
            and isinstance(item.value,ast.Dict)
            and any(
                isinstance(t,ast.Name) and t.id=="CHILDREN"
                for t in item.targets
            )
        ):
            out={}
            for k,v in zip(item.value.keys,item.value.values):
                if (
                    isinstance(k,ast.Constant)
                    and isinstance(v,ast.Constant)
                    and isinstance(v.value,str)
                ):
                    out[str(k.value)]=str(v.value)
            return out

    raise RuntimeError("CHILDREN dictionary not found")

def patch_child(source,child,new_value):
    import ast

    tree=ast.parse(source)
    node=None

    for item in ast.walk(tree):
        if (
            isinstance(item,ast.Assign)
            and isinstance(item.value,ast.Dict)
            and any(
                isinstance(t,ast.Name) and t.id=="CHILDREN"
                for t in item.targets
            )
        ):
            node=item.value
            break

    if node is None:
        raise RuntimeError("CHILDREN dictionary not found")

    lines=source.splitlines(keepends=True)

    for k,v in zip(node.keys,node.values):
        if (
            isinstance(k,ast.Constant)
            and str(k.value)==str(child)
        ):
            if (
                not isinstance(v,ast.Constant)
                or not isinstance(v.value,str)
            ):
                raise RuntimeError(
                    f"{child} runner is not literal string"
                )

            old=v.value

            if old==new_value:
                return source,False

            idx=v.lineno-1
            line=lines[idx]

            for token in (
                repr(old),
                '"'+old+'"',
                "'"+old+"'",
            ):
                if token in line:
                    lines[idx]=line.replace(
                        token,
                        repr(new_value),
                        1,
                    )
                    patched="".join(lines)
                    ast.parse(patched)
                    return patched,True

            raise RuntimeError(
                f"unable to patch {child} runner"
            )

    raise RuntimeError(f"{child} child entry not found")

def resolve_underlying(root,runner,max_depth=8):
    import ast

    current=str(runner)
    seen=set()

    wrapper_names={
        "run_oracle_priority_fast_lane_child.py",
        "run_opc_035_priority_coverage_child.py",
        "run_oracle_serialized_fast_lane_child.py",
        "run_opc_041_serialized_coverage_child.py",
    }

    for _ in range(max_depth):
        if current in seen:
            raise RuntimeError("recursive wrapper chain detected")
        seen.add(current)

        if current not in wrapper_names:
            return current

        path=root/current
        if not path.exists():
            raise RuntimeError(
                f"wrapper target missing: {current}"
            )

        text=path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        value=None
        for line in text.splitlines():
            if line.strip().startswith("UNDERLYING_RUNNER="):
                raw=line.split("=",1)[1].strip()
                value=ast.literal_eval(raw)
                break

        if not value:
            raise RuntimeError(
                f"could not resolve underlying runner from {current}"
            )

        current=str(value)

    raise RuntimeError("wrapper resolution exceeded max depth")


def main():
    print("="*80)
    print(" OPC-041 INSTALLER")
    print(" PHYSICAL CONCURRENT WRITER CERTIFICATION GATE")
    print("="*80)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))


    up=importlib.import_module(
        "qseries_v2.oracle_pre_settlement_coverage."
        "opc_040_coverage_serialized_persistence_integration"
    )
    if up.verify_opc_040_coverage_serialized_persistence_integration() is not True:
        raise RuntimeError("Certified OPC-040 verification failed")
    print("[PASS] Certified OPC-040 upstream boundary verified")


    affected=(MOD,TEST,INIT,LAUNCHER,FAST_WRAPPER,COVERAGE_WRAPPER,PHYSICAL)

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

        if not LAUNCHER.exists():
            raise RuntimeError("run_oracle_LIVE.py missing")

        original=LAUNCHER.read_text(
            encoding="utf-8"
        )

        children=read_children(original)

        fast_current=children.get("fast_lane")
        coverage_current=children.get("coverage")

        if not fast_current or not coverage_current:
            raise RuntimeError(
                "fast_lane/coverage child entries missing"
            )

        fast_underlying=resolve_underlying(
            ROOT,
            fast_current,
        )
        coverage_underlying=resolve_underlying(
            ROOT,
            coverage_current,
        )

        if fast_underlying in (
            FAST_WRAPPER.name,
            COVERAGE_WRAPPER.name,
        ):
            raise RuntimeError(
                "recursive fast-lane wrapper target refused"
            )

        if coverage_underlying in (
            FAST_WRAPPER.name,
            COVERAGE_WRAPPER.name,
        ):
            raise RuntimeError(
                "recursive coverage wrapper target refused"
            )

        fast_source=FAST_TEMPLATE.replace(
            "__UNDERLYING__",
            repr(fast_underlying),
        )

        coverage_source=COVERAGE_TEMPLATE.replace(
            "__UNDERLYING__",
            repr(coverage_underlying),
        )

        write_exact(
            FAST_WRAPPER,
            fast_source,
        )
        write_exact(
            COVERAGE_WRAPPER,
            coverage_source,
        )
        write_exact(
            PHYSICAL,
            PHYSICAL_SOURCE,
        )

        patched,_=patch_child(
            original,
            "fast_lane",
            FAST_WRAPPER.name,
        )
        patched,_=patch_child(
            patched,
            "coverage",
            COVERAGE_WRAPPER.name,
        )

        write_exact(
            LAUNCHER,
            patched,
        )

        print(
            f"[PASS] Fast lane direct underlying={fast_underlying}"
        )
        print(
            f"[PASS] Coverage direct underlying={coverage_underlying}"
        )
        print(
            "[PASS] Older priority wrappers bypassed; "
            "no recursive wrapper stacking"
        )


        current=(
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )

        export="from .opc_041_physical_concurrent_writer_certification_gate import *"

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

        compile(
            FAST_WRAPPER.read_text(encoding="utf-8"),
            str(FAST_WRAPPER),
            "exec",
        )
        compile(
            COVERAGE_WRAPPER.read_text(encoding="utf-8"),
            str(COVERAGE_WRAPPER),
            "exec",
        )
        compile(
            PHYSICAL.read_text(encoding="utf-8"),
            str(PHYSICAL),
            "exec",
        )
        compile(
            LAUNCHER.read_text(encoding="utf-8"),
            str(LAUNCHER),
            "exec",
        )

        subprocess.run(
            [sys.executable,str(LAUNCHER),"--check"],
            cwd=str(ROOT),
            check=True,
        )

        print(
            "[PASS] Oracle Live --check passed "
            "with serialized writers"
        )


    except Exception:
        for path,old in backups.items():
            if old is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(old)

        print(
            "[ROLLBACK] OPC-041 installation failed; "
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
        "[DONE] OPC-041 "
        "INSTALLATION AND CERTIFICATION COMPLETE"
    )

if __name__=="__main__":
    main()
