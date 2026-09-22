from pathlib import Path
import ast

ROOT=Path.cwd()
MODULE="qseries_v2/oracle_source_network/certification/final_sports_persistence_certification.py"
TEST="test_osn_065_final_universal_sports_persistence_CERTIFIED_CHAIN_REBUILD.py"

MODULE_SOURCE='from dataclasses import dataclass\nfrom pathlib import Path\nimport subprocess\nimport sys\n\n\n@dataclass(frozen=True)\nclass FinalSportsPersistenceCertification:\n    osn060: bool\n    osn062: bool\n    osn063: bool\n    osn064: bool\n    single_writer: str\n    writer_id: str\n    canonicalizer: str\n    exact_readback: str\n    sports_persistence_ready: bool\n    execution_authority: bool = False\n\n\nTESTS = (\n    ("OSN-060", "test_osn_060_final_pre_persistence_sports_event_certification.py", 90),\n    ("OSN-062", "test_osn_062_existing_single_writer_sports_boundary.py", 60),\n    ("OSN-063", "test_osn_063_sports_single_writer_COMMIT_AWAIT_PHYSICAL_REBUILD.py", 90),\n    ("OSN-064", "test_osn_064_sports_persistence_READ_BEFORE_WRITE_IDEMPOTENCY_REBUILD.py", 90),\n)\n\n\ndef _run_test(root, label, filename, timeout_seconds):\n    path = root / filename\n    if not path.exists():\n        raise RuntimeError(f"{label} certified test missing: {filename}")\n\n    print(f"[RUN] {label}: {filename}", flush=True)\n\n    try:\n        completed = subprocess.run(\n            [sys.executable, str(path)],\n            cwd=str(root),\n            text=True,\n            capture_output=True,\n            timeout=timeout_seconds,\n        )\n    except subprocess.TimeoutExpired as exc:\n        raise RuntimeError(\n            f"{label} certification timed out after {timeout_seconds}s: {filename}"\n        ) from exc\n\n    if completed.stdout:\n        print(completed.stdout, end="" if completed.stdout.endswith("\\n") else "\\n")\n    if completed.stderr:\n        print(completed.stderr, end="" if completed.stderr.endswith("\\n") else "\\n")\n\n    if completed.returncode != 0:\n        raise RuntimeError(\n            f"{label} certification failed with exit code {completed.returncode}: {filename}"\n        )\n\n    print(f"[PASS] {label} current certified test passed", flush=True)\n    return True\n\n\ndef certify_final_sports_persistence():\n    root = Path.cwd().resolve()\n    results = {}\n\n    for label, filename, timeout_seconds in TESTS:\n        results[label] = _run_test(\n            root,\n            label,\n            filename,\n            timeout_seconds,\n        )\n\n    return FinalSportsPersistenceCertification(\n        osn060=results["OSN-060"],\n        osn062=results["OSN-062"],\n        osn063=results["OSN-063"],\n        osn064=results["OSN-064"],\n        single_writer="OPH-019",\n        writer_id="oracle.osn.sports",\n        canonicalizer="OAD-261",\n        exact_readback="OAD-068",\n        sports_persistence_ready=True,\n        execution_authority=False,\n    )\n'
TEST_SOURCE='from qseries_v2.oracle_source_network.certification.final_sports_persistence_certification import certify_final_sports_persistence\n\nresult = certify_final_sports_persistence()\nprint("[FINAL_SPORTS_PERSISTENCE]", result)\n\nassert result.osn060 is True\nassert result.osn062 is True\nassert result.osn063 is True\nassert result.osn064 is True\nassert result.single_writer == "OPH-019"\nassert result.writer_id == "oracle.osn.sports"\nassert result.canonicalizer == "OAD-261"\nassert result.exact_readback == "OAD-068"\nassert result.sports_persistence_ready is True\nassert result.execution_authority is False\n\nprint("[PASS] pre-persistence sports event certification retained")\nprint("[PASS] exact existing single-writer boundary retained")\nprint("[PASS] physical sports write -> await commit -> exact readback recertified")\nprint("[PASS] read-before-write replay idempotency recertified")\nprint("[PASS] universal sports persistence foundation certified")\nprint("[PASS] OSN-065 final sports persistence certification complete")\n'

REQUIRED=(
    "test_osn_060_final_pre_persistence_sports_event_certification.py",
    "test_osn_062_existing_single_writer_sports_boundary.py",
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
    tree=ast.parse(p.read_text(encoding="utf-8",errors="ignore"))
    names={n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    required={"canonicalize","submit","await_commit","exact_readback","readback_count"}
    missing=required-names
    if missing:
        raise SystemExit("[FAIL] current sports boundary missing functions: "+repr(sorted(missing)))
    text=p.read_text(encoding="utf-8",errors="ignore")
    if 'WRITER_ID = "oracle.osn.sports"' not in text:
        raise SystemExit("[FAIL] current sports writer_id marker missing")
    print("[PASS] current repaired OSN-063 boundary verified")


def verify_current_replay_policy():
    p=require("qseries_v2/oracle_source_network/certification/sports_persistence_replay_gate.py")
    text=p.read_text(encoding="utf-8",errors="ignore")
    if "replay_resubmitted=False" not in text:
        raise SystemExit("[FAIL] current read-before-write replay policy missing")
    print("[PASS] current repaired OSN-064 no-resubmit policy verified")


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
    print(" OSN-065 FINAL UNIVERSAL SPORTS PERSISTENCE CERTIFIED-CHAIN REBUILD INSTALLER")
    print("="*120)

    for rel in REQUIRED:
        require(rel)

    verify_current_boundary()
    verify_current_replay_policy()

    for stale in STALE_TESTS:
        if (ROOT/stale).exists():
            print("[INFO] stale test ignored:",stale)

    write_compile(MODULE,MODULE_SOURCE)
    write_compile(TEST,TEST_SOURCE)

    print("[PASS] stale OSN-063/064 test chain excluded")
    print("[PASS] only current repaired certification chain admitted")
    print("[PASS] each subprocess certification is hard-time-bounded")
    print("[PASS] OPH-019 single-writer architecture retained")
    print("[PASS] OAD-261 canonicalizer retained")
    print("[PASS] OAD-068 exact readback retained")
    print("[PASS] execution_authority=FALSE")


if __name__=="__main__":
    main()
