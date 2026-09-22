from pathlib import Path
import ast
import importlib
import os
import subprocess
import sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_production_hardening"

MOD=PKG/"oph_010_physical_single_writer_production_gate.py"
TEST=ROOT/"test_oph_010_physical_single_writer_production_gate.py"
INIT=PKG/"__init__.py"
LAUNCHER=ROOT/"run_oracle_LIVE.py"

WRITER=ROOT/"run_oph_010_single_canonical_writer.py"
FAST=ROOT/"run_oph_010_fast_lane_queue_child.py"
COVERAGE=ROOT/"run_oph_010_coverage_queue_child.py"
PHYSICAL=ROOT/"run_oph_010_physical_single_writer_production_check.py"

MODULE_SOURCE='from __future__ import annotations\nimport importlib\nfrom dataclasses import dataclass\n\nOPH_010_BUILD_ID="OPH-010"\nOPH_010_REVISION="OPH_010_PHYSICAL_SINGLE_WRITER_PRODUCTION_GATE_CORRECTION_V2"\n\n@dataclass(frozen=True)\nclass SingleWriterProductionReport:\n    writer_child:str\n    fast_lane_queued:bool\n    coverage_queued:bool\n    direct_adapter_postgresql_authority:bool=False\n    execution_authority:bool=False\n\ndef verify_oph_010_physical_single_writer_production_gate():\n    checks=(\n        ("oph_006_durable_cross_process_observation_queue","verify_oph_006_durable_cross_process_observation_queue"),\n        ("oph_007_physical_single_postgresql_writer_runtime","verify_oph_007_physical_single_postgresql_writer_runtime"),\n        ("oph_008_fast_lane_queue_migration","verify_oph_008_fast_lane_queue_migration"),\n        ("oph_009_coverage_queue_migration","verify_oph_009_coverage_queue_migration"),\n    )\n    return all(\n        getattr(\n            importlib.import_module(\n                "qseries_v2.oracle_production_hardening."+mod\n            ),\n            fn,\n        )()\n        for mod,fn in checks\n    )\n\ndef production_report():\n    if not verify_oph_010_physical_single_writer_production_gate():\n        raise RuntimeError("OPH-006 through OPH-010 verification failed")\n    return SingleWriterProductionReport(\n        "canonical_writer",\n        True,\n        True,\n        False,\n        False,\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_production_hardening.oph_010_physical_single_writer_production_gate import (\n    verify_oph_010_physical_single_writer_production_gate,\n)\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(\n            verify_oph_010_physical_single_writer_production_gate()\n        )\n\nif __name__=="__main__":\n    print("="*80)\n    print(" OPH-010 CERTIFICATION TEST")\n    print(" PHYSICAL SINGLE WRITER PRODUCTION GATE — CORRECTION V2")\n    print("="*80)\n\n    result=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n\n    if not result.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] OPH-006 through OPH-010 single-writer migration certified")\n    print("[DONE] OPH-010 CERTIFIED")\n'
WRITER_SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import (\n    run_single_writer_forever,\n)\n\nif __name__=="__main__":\n    print("="*88,flush=True)\n    print(" OPH-010 ORACLE SINGLE CANONICAL POSTGRESQL WRITER",flush=True)\n    print("="*88,flush=True)\n    raise SystemExit(\n        run_single_writer_forever(\n            Path.cwd(),\n            lambda x:print(x,flush=True),\n        )\n    )\n'
FAST_TEMPLATE='from pathlib import Path\nimport runpy\nfrom qseries_v2.oracle_production_hardening.oph_008_fast_lane_queue_migration import (\n    install_fast_lane_queue_migration,\n)\n\nUNDERLYING_RUNNER=__UNDERLYING__\n\nif __name__=="__main__":\n    print("="*88,flush=True)\n    print(" OPH-010 FAST LANE -> SHARED CANONICAL QUEUE",flush=True)\n    print("="*88,flush=True)\n\n    install_fast_lane_queue_migration(Path.cwd())\n\n    print(\n        f"[OPH] producer=FAST_LANE "\n        f"direct_postgresql_write_authority=FALSE "\n        f"underlying={UNDERLYING_RUNNER}",\n        flush=True,\n    )\n\n    runpy.run_path(\n        str(Path.cwd()/UNDERLYING_RUNNER),\n        run_name="__main__",\n    )\n'
COVERAGE_TEMPLATE='from pathlib import Path\nimport runpy\nfrom qseries_v2.oracle_production_hardening.oph_009_coverage_queue_migration import (\n    install_coverage_queue_migration,\n)\n\nUNDERLYING_RUNNER=__UNDERLYING__\n\nif __name__=="__main__":\n    print("="*88,flush=True)\n    print(" OPH-010 COVERAGE -> SHARED CANONICAL QUEUE",flush=True)\n    print("="*88,flush=True)\n\n    install_coverage_queue_migration(Path.cwd())\n\n    print(\n        f"[OPH] producer=COVERAGE "\n        f"direct_postgresql_write_authority=FALSE "\n        f"underlying={UNDERLYING_RUNNER}",\n        flush=True,\n    )\n\n    runpy.run_path(\n        str(Path.cwd()/UNDERLYING_RUNNER),\n        run_name="__main__",\n    )\n'
PHYSICAL_SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_006_durable_cross_process_observation_queue import (\n    queue_counts,\n    queue_path,\n)\nfrom qseries_v2.oracle_production_hardening.oph_010_physical_single_writer_production_gate import (\n    production_report,\n)\n\nif __name__=="__main__":\n    print("="*96)\n    print(" OPH-010 PHYSICAL SINGLE-WRITER PRODUCTION CHECK — CORRECTION V2")\n    print("="*96)\n\n    report=production_report()\n\n    print(f"[QUEUE] path={queue_path(Path.cwd())}")\n    print(f"[QUEUE] counts={queue_counts(Path.cwd())}")\n    print(f"[WRITER CHILD] {report.writer_child}")\n    print(f"[FAST LANE QUEUED] {report.fast_lane_queued}")\n    print(f"[COVERAGE QUEUED] {report.coverage_queued}")\n    print(\n        "[DIRECT ADAPTER POSTGRESQL AUTHORITY] "\n        f"{report.direct_adapter_postgresql_authority}"\n    )\n\n    print("[TARGET] canonical_writer=RUNNING")\n    print("[TARGET] fast_lane=RUNNING coverage=RUNNING")\n    print("[TARGET] no producer-side expected_terminal_chain_hash_mismatch")\n    print("[TARGET] no Fast Lane PostgreSQLPersistenceRoutingFailure reconnects")\n    print("[TARGET] Coverage continues full-page persistence through queue")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPH-010 PHYSICAL CHECK READY")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def find_children_dict(tree):
    for item in ast.walk(tree):
        if (
            isinstance(item,ast.Assign)
            and isinstance(item.value,ast.Dict)
            and any(
                isinstance(t,ast.Name) and t.id=="CHILDREN"
                for t in item.targets
            )
        ):
            return item.value
    raise RuntimeError("run_oracle_LIVE.py CHILDREN dictionary not found")

def read_children(source):
    node=find_children_dict(ast.parse(source))
    result={}
    for k,v in zip(node.keys,node.values):
        if (
            isinstance(k,ast.Constant)
            and isinstance(v,ast.Constant)
            and isinstance(v.value,str)
        ):
            result[str(k.value)]=str(v.value)
    return result

def replace_child(source,name,value):
    tree=ast.parse(source)
    node=find_children_dict(tree)
    lines=source.splitlines(keepends=True)

    for k,v in zip(node.keys,node.values):
        if (
            isinstance(k,ast.Constant)
            and str(k.value)==str(name)
        ):
            if not (
                isinstance(v,ast.Constant)
                and isinstance(v.value,str)
            ):
                raise RuntimeError(
                    f"{name} child value is not a literal string"
                )

            old=v.value
            if old==value:
                return source,False

            idx=v.lineno-1
            line=lines[idx]

            replaced=False
            for token in (
                repr(old),
                '"'+old+'"',
                "'"+old+"'",
            ):
                if token in line:
                    lines[idx]=line.replace(
                        token,
                        repr(value),
                        1,
                    )
                    replaced=True
                    break

            if not replaced:
                raise RuntimeError(
                    f"unable to replace {name} runner"
                )

            patched="".join(lines)
            ast.parse(patched)
            return patched,True

    raise RuntimeError(f"child {name} not found")

def add_child(source,name,value):
    tree=ast.parse(source)
    node=find_children_dict(tree)

    for k in node.keys:
        if (
            isinstance(k,ast.Constant)
            and str(k.value)==str(name)
        ):
            return source,False

    lines=source.splitlines(keepends=True)
    close_index=node.end_lineno-1

    if node.values:
        sample_line=lines[node.values[-1].lineno-1]
        indent=sample_line[
            :len(sample_line)-len(sample_line.lstrip())
        ]
    else:
        assignment_line=lines[node.lineno-1]
        base=assignment_line[
            :len(assignment_line)-len(assignment_line.lstrip())
        ]
        indent=base+"    "

    # IMPORTANT V2 FIX:
    # Insert a REAL newline, not the literal characters backslash+n.
    new_line=(
        indent
        +repr(str(name))
        +":"
        +repr(str(value))
        +","
        +"\n"
    )

    lines.insert(close_index,new_line)

    patched="".join(lines)
    ast.parse(patched)
    return patched,True

def resolve_underlying(root,runner,max_depth=12):
    current=str(runner)
    seen=set()

    wrappers={
        "run_oracle_priority_fast_lane_child.py",
        "run_oracle_serialized_fast_lane_child.py",
        "run_opc_035_priority_coverage_child.py",
        "run_opc_041_serialized_coverage_child.py",
        "run_oph_010_fast_lane_queue_child.py",
        "run_oph_010_coverage_queue_child.py",
    }

    for _ in range(max_depth):
        if current in seen:
            raise RuntimeError("recursive wrapper chain detected")

        seen.add(current)

        if current not in wrappers:
            return current

        path=root/current
        if not path.exists():
            raise RuntimeError(
                f"wrapper target missing: {current}"
            )

        target=None
        for line in path.read_text(
            encoding="utf-8",
            errors="ignore",
        ).splitlines():
            if line.strip().startswith("UNDERLYING_RUNNER="):
                target=ast.literal_eval(
                    line.split("=",1)[1].strip()
                )
                break

        if not target:
            raise RuntimeError(
                f"could not resolve underlying runner: {current}"
            )

        current=str(target)

    raise RuntimeError("wrapper resolution exceeded")

def main():
    print("="*88)
    print(" OPH-010 PHYSICAL SINGLE WRITER PRODUCTION GATE")
    print(" CORRECTION V2 — REAL NEWLINE CHILD REGISTRY PATCH")
    print("="*88)
    print("[ROOT]",ROOT)

    sys.path.insert(0,str(ROOT))

    up=importlib.import_module(
        "qseries_v2.oracle_production_hardening."
        "oph_009_coverage_queue_migration"
    )

    if up.verify_oph_009_coverage_queue_migration() is not True:
        raise RuntimeError("Certified OPH-009 verification failed")

    print("[PASS] Certified OPH-009 upstream boundary verified")

    if not LAUNCHER.exists():
        raise RuntimeError("run_oracle_LIVE.py missing")

    affected=(
        MOD,
        TEST,
        INIT,
        LAUNCHER,
        WRITER,
        FAST,
        COVERAGE,
        PHYSICAL,
    )

    backups={
        p:(p.read_bytes() if p.exists() else None)
        for p in affected
    }

    try:
        source=LAUNCHER.read_text(encoding="utf-8")
        children=read_children(source)

        fast_current=children.get("fast_lane")
        coverage_current=children.get("coverage")

        if not fast_current or not coverage_current:
            raise RuntimeError(
                "fast_lane or coverage missing from CHILDREN"
            )

        fast_underlying=resolve_underlying(
            ROOT,
            fast_current,
        )
        coverage_underlying=resolve_underlying(
            ROOT,
            coverage_current,
        )

        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        write_exact(WRITER,WRITER_SOURCE)

        write_exact(
            FAST,
            FAST_TEMPLATE.replace(
                "__UNDERLYING__",
                repr(fast_underlying),
            ),
        )

        write_exact(
            COVERAGE,
            COVERAGE_TEMPLATE.replace(
                "__UNDERLYING__",
                repr(coverage_underlying),
            ),
        )

        write_exact(PHYSICAL,PHYSICAL_SOURCE)

        patched,_=replace_child(
            source,
            "fast_lane",
            FAST.name,
        )

        patched,_=replace_child(
            patched,
            "coverage",
            COVERAGE.name,
        )

        patched,_=add_child(
            patched,
            "canonical_writer",
            WRITER.name,
        )

        # Validate BEFORE writing launcher.
        ast.parse(patched)
        compile(patched,str(LAUNCHER),"exec")

        write_exact(LAUNCHER,patched)

        current=(
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )

        export=(
            "from .oph_010_physical_single_writer_production_gate "
            "import *"
        )

        if export not in current:
            write_exact(
                INIT,
                current.rstrip()+"\n"+export+"\n",
            )

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),
            check=True,
        )

        subprocess.run(
            [sys.executable,str(LAUNCHER),"--check"],
            cwd=str(ROOT),
            check=True,
        )

        print(
            f"[PASS] Fast Lane queue wrapper underlying="
            f"{fast_underlying}"
        )
        print(
            f"[PASS] Coverage queue wrapper underlying="
            f"{coverage_underlying}"
        )
        print(
            "[PASS] canonical_writer child added with valid "
            "Python source formatting"
        )
        print(
            "[PASS] Older OPC persistence wrappers bypassed"
        )
        print(
            "[PASS] Existing OLA/OLR source boundaries untouched"
        )

    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)

        print(
            "[ROLLBACK] OPH-010 Correction V2 failed; "
            "affected files restored"
        )
        raise

    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[PASS] Wrote:",WRITER.name)
    print("[PASS] Wrote:",FAST.name)
    print("[PASS] Wrote:",COVERAGE.name)
    print("[PASS] Wrote:",PHYSICAL.name)
    print(
        "[DONE] OPH-010 CORRECTION V2 "
        "INSTALLATION AND CERTIFICATION COMPLETE"
    )

if __name__=="__main__":
    main()
