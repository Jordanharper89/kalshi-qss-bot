
from pathlib import Path
import ast

ROOT=Path.cwd()
MODULE="qseries_v2/oracle_source_network/certification/final_sports_persistence_certification.py"
TEST="test_osn_065_final_universal_sports_persistence_CURRENT_BOUNDARY_REBUILD.py"

MODULE_SOURCE='from dataclasses import dataclass\nfrom pathlib import Path\nimport ast\nimport subprocess\nimport sys\n\n@dataclass(frozen=True)\nclass FinalSportsPersistenceCertification:\n    osn060: bool\n    osn062_current_boundary: bool\n    osn063: bool\n    osn064: bool\n    single_writer: str\n    writer_id: str\n    canonicalizer: str\n    exact_readback: str\n    sports_persistence_ready: bool\n    execution_authority: bool = False\n\n\ndef _run_test(root, label, filename, timeout_seconds):\n    path = root / filename\n    if not path.exists():\n        raise RuntimeError(f"{label} current certified test missing: {filename}")\n\n    print(f"[RUN] {label}: {filename}", flush=True)\n\n    try:\n        completed = subprocess.run(\n            [sys.executable, str(path)],\n            cwd=str(root),\n            text=True,\n            capture_output=True,\n            timeout=timeout_seconds,\n        )\n    except subprocess.TimeoutExpired as exc:\n        raise RuntimeError(\n            f"{label} certification timed out after {timeout_seconds}s: {filename}"\n        ) from exc\n\n    if completed.stdout:\n        print(completed.stdout, end="" if completed.stdout.endswith("\\n") else "\\n")\n    if completed.stderr:\n        print(completed.stderr, end="" if completed.stderr.endswith("\\n") else "\\n")\n\n    if completed.returncode != 0:\n        raise RuntimeError(\n            f"{label} certification failed with exit code {completed.returncode}: {filename}"\n        )\n\n    print(f"[PASS] {label} current certified test passed", flush=True)\n    return True\n\n\ndef _verify_current_osn062_boundary(root):\n    boundary = root / "qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py"\n    if not boundary.exists():\n        raise RuntimeError("current sports single-writer boundary missing")\n\n    text = boundary.read_text(encoding="utf-8", errors="ignore")\n    tree = ast.parse(text)\n\n    functions = {\n        n.name\n        for n in ast.walk(tree)\n        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))\n    }\n    required_functions = {\n        "canonicalize",\n        "submit",\n        "await_commit",\n        "exact_readback",\n        "readback_count",\n    }\n    missing = required_functions - functions\n    if missing:\n        raise RuntimeError(\n            "current sports boundary missing required functions: " + repr(sorted(missing))\n        )\n\n    if \'WRITER_ID = "oracle.osn.sports"\' not in text:\n        raise RuntimeError("current sports boundary writer_id marker missing")\n\n    if "submit_observation_batch(" not in text:\n        raise RuntimeError("current sports boundary no longer routes through OPH-019 submit")\n\n    if "exact_postgresql_readback(" not in text:\n        raise RuntimeError("current sports boundary no longer routes through OAD-068 readback")\n\n    if "PRODUCER" in text:\n        raise RuntimeError("obsolete producer-style boundary marker still present")\n\n    print("[OSN062_CURRENT_BOUNDARY] writer_id=oracle.osn.sports")\n    print("[PASS] current OSN-062 single-writer contract verified directly")\n    print("[PASS] obsolete PRODUCER interface absent")\n    return True\n\n\ndef certify_final_sports_persistence():\n    root = Path.cwd().resolve()\n\n    osn060 = _run_test(\n        root,\n        "OSN-060",\n        "test_osn_060_final_pre_persistence_sports_event_certification.py",\n        90,\n    )\n\n    osn062 = _verify_current_osn062_boundary(root)\n\n    osn063 = _run_test(\n        root,\n        "OSN-063",\n        "test_osn_063_sports_single_writer_COMMIT_AWAIT_PHYSICAL_REBUILD.py",\n        90,\n    )\n\n    osn064 = _run_test(\n        root,\n        "OSN-064",\n        "test_osn_064_sports_persistence_READ_BEFORE_WRITE_IDEMPOTENCY_REBUILD.py",\n        90,\n    )\n\n    return FinalSportsPersistenceCertification(\n        osn060=osn060,\n        osn062_current_boundary=osn062,\n        osn063=osn063,\n        osn064=osn064,\n        single_writer="OPH-019",\n        writer_id="oracle.osn.sports",\n        canonicalizer="OAD-261",\n        exact_readback="OAD-068",\n        sports_persistence_ready=True,\n        execution_authority=False,\n    )\n'
TEST_SOURCE='from qseries_v2.oracle_source_network.certification.final_sports_persistence_certification import certify_final_sports_persistence\n\nresult = certify_final_sports_persistence()\nprint("[FINAL_SPORTS_PERSISTENCE]", result)\n\nassert result.osn060 is True\nassert result.osn062_current_boundary is True\nassert result.osn063 is True\nassert result.osn064 is True\nassert result.single_writer == "OPH-019"\nassert result.writer_id == "oracle.osn.sports"\nassert result.canonicalizer == "OAD-261"\nassert result.exact_readback == "OAD-068"\nassert result.sports_persistence_ready is True\nassert result.execution_authority is False\n\nprint("[PASS] pre-persistence sports event certification retained")\nprint("[PASS] current repaired OSN-062 single-writer contract certified directly")\nprint("[PASS] physical sports write -> await commit -> exact readback recertified")\nprint("[PASS] read-before-write replay idempotency recertified")\nprint("[PASS] universal sports persistence foundation certified")\nprint("[PASS] OSN-065 final sports persistence certification complete")\n'

REQUIRED=(
    "test_osn_060_final_pre_persistence_sports_event_certification.py",
    "test_osn_063_sports_single_writer_COMMIT_AWAIT_PHYSICAL_REBUILD.py",
    "test_osn_064_sports_persistence_READ_BEFORE_WRITE_IDEMPOTENCY_REBUILD.py",
    "qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py",
    "qseries_v2/oracle_source_network/certification/sports_single_writer_physical_gate.py",
    "qseries_v2/oracle_source_network/certification/sports_persistence_replay_gate.py",
    "qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py",
    "qseries_v2/oracle_adapters/independent/oad_261_universal_expansion_source_single_writer_postgresql_persistence.py",
    "qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py",
)

STALE_TESTS=(
    "test_osn_062_existing_single_writer_sports_boundary.py",
    "test_osn_063_sports_single_writer_POSTGRESQL_WRITER_ID_REPAIR.py",
    "test_osn_063_sports_single_writer_WRITER_ID_REPAIR_CLEAN.py",
    "test_osn_063_sports_single_writer_EXACT_BOUNDARY_CLEAN_REBUILD.py",
    "test_osn_064_sports_persistence_idempotent_replay_gate.py",
    "test_osn_064_sports_persistence_COMMIT_AWAIT_REPLAY_REBUILD.py",
)


def require(rel):
    p=ROOT/rel
    if not p.exists():
        raise SystemExit("[FAIL] required certified dependency missing: "+rel)
    print("[PASS] dependency verified:",rel)
    return p


def verify_current_boundary():
    p=require("qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py")
    text=p.read_text(encoding="utf-8",errors="ignore")
    tree=ast.parse(text)
    names={n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    needed={"canonicalize","submit","await_commit","exact_readback","readback_count"}
    missing=needed-names
    if missing:
        raise SystemExit("[FAIL] current boundary missing functions: "+repr(sorted(missing)))
    if 'WRITER_ID = "oracle.osn.sports"' not in text:
        raise SystemExit("[FAIL] current WRITER_ID marker missing")
    if "PRODUCER" in text:
        raise SystemExit("[FAIL] obsolete PRODUCER marker still present")
    if "submit_observation_batch(" not in text:
        raise SystemExit("[FAIL] OPH-019 submit routing missing")
    if "exact_postgresql_readback(" not in text:
        raise SystemExit("[FAIL] OAD-068 readback routing missing")
    print("[PASS] current repaired OSN-062/063 boundary verified")


def write_compile(rel,source):
    compile(source,rel,"exec")
    p=ROOT/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(source,encoding="utf-8")
    compile(p.read_text(encoding="utf-8"),str(p),"exec")
    print("[WRITE]",rel)
    print("[PASS] post-write compile verified:",rel)


def main():
    print("="*120)
    print(" OSN-065 FINAL UNIVERSAL SPORTS PERSISTENCE CURRENT-BOUNDARY REBUILD INSTALLER")
    print("="*120)

    for rel in REQUIRED:
        require(rel)

    verify_current_boundary()

    for stale in STALE_TESTS:
        if (ROOT/stale).exists():
            print("[INFO] stale test excluded:",stale)

    write_compile(MODULE,MODULE_SOURCE)
    write_compile(TEST,TEST_SOURCE)

    print("[PASS] stale OSN-062 PRODUCER-era test excluded")
    print("[PASS] current WRITER_ID boundary verified directly")
    print("[PASS] current OSN-063 physical certification retained")
    print("[PASS] current OSN-064 read-before-write certification retained")
    print("[PASS] subprocess certifications hard-time-bounded")
    print("[PASS] execution_authority=FALSE")


if __name__=="__main__":
    main()
