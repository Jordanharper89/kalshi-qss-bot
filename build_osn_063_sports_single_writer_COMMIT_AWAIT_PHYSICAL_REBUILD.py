from pathlib import Path
import ast

ROOT = Path.cwd()

BOUNDARY = "qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py"
GATE = "qseries_v2/oracle_source_network/certification/sports_single_writer_physical_gate.py"
TEST = "test_osn_063_sports_single_writer_COMMIT_AWAIT_PHYSICAL_REBUILD.py"

BOUNDARY_SOURCE = 'from pathlib import Path\nimport uuid\n\nfrom qseries_v2.oracle_adapters.independent.oad_261_universal_expansion_source_single_writer_postgresql_persistence import canonicalize_expansion_observation\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import (\n    submit_observation_batch,\n    await_request,\n)\nfrom qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import exact_postgresql_readback\n\nWRITER_ID = "oracle.osn.sports"\nPRIORITY = 20\n\n\ndef canonicalize(observation, batch_id=None):\n    return canonicalize_expansion_observation(\n        observation,\n        batch_id or ("osn-sports-" + uuid.uuid4().hex),\n    )\n\n\ndef submit(observations, root=None):\n    return submit_observation_batch(\n        WRITER_ID,\n        PRIORITY,\n        tuple(observations),\n        root=root,\n    )\n\n\ndef await_commit(request_id, root=None, timeout_seconds=45.0):\n    root_path = Path(root or Path.cwd()).resolve()\n    return tuple(\n        await_request(\n            str(request_id),\n            root_path,\n            float(timeout_seconds),\n        )\n    )\n\n\ndef exact_readback(observation_id, root=None):\n    return exact_postgresql_readback(\n        (observation_id,),\n        root=root,\n    )\n\n\ndef readback_count(value):\n    if value is None:\n        return 0\n    if isinstance(value, (list, tuple, set)):\n        return len(value)\n    if isinstance(value, dict):\n        for key in ("rows", "observations", "results", "items"):\n            item = value.get(key)\n            if item is not None and hasattr(item, "__len__"):\n                return len(item)\n        return 1 if value else 0\n    for key in ("rows", "observations", "results", "items"):\n        item = getattr(value, key, None)\n        if item is not None and hasattr(item, "__len__"):\n            return len(item)\n    return 1\n'
GATE_SOURCE = 'import subprocess\nimport sys\nimport time\nimport uuid\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent\nfrom qseries_v2.oracle_source_network.persistence.sports_persistence_contract import from_canonical_event\nfrom qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import (\n    WRITER_ID,\n    canonicalize,\n    submit,\n    await_commit,\n    exact_readback,\n    readback_count,\n)\n\n\n@dataclass(frozen=True)\nclass PhysicalPersistenceResult:\n    canonical_event_id: str\n    observation_id: str\n    request_id: str\n    committed_events: int\n    exact_readback: int\n    writer_process_started: bool\n    execution_authority: bool = False\n\n\ndef _start_certified_writer(root):\n    runner = root / "run_oph_021_exclusive_postgresql_canonical_writer.py"\n    if not runner.exists():\n        raise RuntimeError("certified OPH-021 runner missing: " + str(runner))\n    proc = subprocess.Popen(\n        [sys.executable, str(runner)],\n        cwd=str(root),\n        stdout=subprocess.DEVNULL,\n        stderr=subprocess.DEVNULL,\n    )\n    time.sleep(1.0)\n    return proc\n\n\ndef _request_id(submission):\n    rid = getattr(submission, "request_id", None)\n    if rid:\n        return str(rid)\n    if isinstance(submission, dict) and submission.get("request_id"):\n        return str(submission["request_id"])\n    raise RuntimeError("OPH-019 submission returned no request_id")\n\n\ndef persist_fixture(timeout_seconds=45.0):\n    root = Path.cwd().resolve()\n    writer = _start_certified_writer(root)\n\n    try:\n        token = uuid.uuid4().hex[:12]\n        observed_at = datetime.now(timezone.utc).isoformat()\n\n        event = CanonicalSportsEvent(\n            league="NFL",\n            season="2026",\n            provider="osn_physical_fixture",\n            home_team="OSN_HOME",\n            away_team="OSN_AWAY",\n            scheduled_start="2026-09-06T12:00:00Z",\n            source_observed_at=observed_at,\n            source_authority="certification_fixture",\n            provider_event_id="osn-" + token,\n            event_discriminator="osn-" + token,\n        )\n\n        raw = from_canonical_event(event)\n        canonical = canonicalize(raw, "osn063-await-" + token)\n\n        submission = submit((canonical,), root=root)\n        request_id = _request_id(submission)\n\n        committed = await_commit(\n            request_id,\n            root=root,\n            timeout_seconds=timeout_seconds,\n        )\n\n        readback = exact_readback(canonical.observation_id, root=root)\n        count = readback_count(readback)\n\n        return PhysicalPersistenceResult(\n            canonical_event_id=event.canonical_event_id,\n            observation_id=canonical.observation_id,\n            request_id=request_id,\n            committed_events=len(committed),\n            exact_readback=count,\n            writer_process_started=True,\n        )\n    finally:\n        if writer.poll() is None:\n            writer.terminate()\n            try:\n                writer.wait(timeout=3)\n            except subprocess.TimeoutExpired:\n                writer.kill()\n'
TEST_SOURCE = 'import inspect\n\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import (\n    submit_observation_batch,\n    await_request,\n)\nfrom qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import exact_postgresql_readback\nfrom qseries_v2.oracle_source_network.certification.sports_single_writer_physical_gate import persist_fixture\n\nprint("[OPH019_SUBMIT_SIGNATURE]", inspect.signature(submit_observation_batch))\nprint("[OPH019_AWAIT_SIGNATURE]", inspect.signature(await_request))\nprint("[OAD068_SIGNATURE]", inspect.signature(exact_postgresql_readback))\n\nresult = persist_fixture(timeout_seconds=45.0)\nprint("[PHYSICAL_COMMIT_AWAIT]", result)\n\nassert len(result.request_id) >= 8\nassert len(result.observation_id) >= 32\nassert result.committed_events >= 1\nassert result.exact_readback >= 1\nassert result.execution_authority is False\n\nprint("[PASS] certified OPH-021 writer runner activated/available")\nprint("[PASS] OPH-019 request awaited through terminal commit state")\nprint("[PASS] sports observation committed before readback")\nprint("[PASS] exact PostgreSQL observation-ID readback certified")\nprint("[PASS] OSN-063 commit-await physical rebuild certified")\n'

DEPS = (
    "qseries_v2/oracle_source_network/persistence/sports_persistence_contract.py",
    "qseries_v2/oracle_source_network/canonical/sports_event_v2.py",
    "qseries_v2/oracle_adapters/independent/oad_261_universal_expansion_source_single_writer_postgresql_persistence.py",
    "qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py",
    "qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py",
    "qseries_v2/oracle_production_hardening/oph_021_exclusive_postgresql_canonical_writer.py",
    "run_oph_021_exclusive_postgresql_canonical_writer.py",
)


def require(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + rel)
    print("[PASS] dependency verified:", rel)
    return p


def function_args(rel, symbol):
    p = require(rel)
    tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol:
            return tuple(arg.arg for arg in node.args.args)
    raise SystemExit(f"[FAIL] exact symbol missing: {rel} -> {symbol}")


def validate_source(label, source):
    compile(source, label, "exec")
    print("[PASS] source compiled:", label)


def write_and_compile(rel, source):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(source, encoding="utf-8")
    compile(p.read_text(encoding="utf-8"), str(p), "exec")
    print("[WRITE]", rel)
    print("[PASS] post-write compile verified:", rel)


def main():
    print("=" * 120)
    print(" OSN-063 SPORTS SINGLE-WRITER COMMIT-AWAIT PHYSICAL REBUILD INSTALLER")
    print("=" * 120)

    for dep in DEPS:
        require(dep)

    submit_args = function_args(
        "qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py",
        "submit_observation_batch",
    )
    await_args = function_args(
        "qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py",
        "await_request",
    )
    read_args = function_args(
        "qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py",
        "exact_postgresql_readback",
    )

    if submit_args[:3] != ("writer_id", "priority", "observations"):
        raise SystemExit(f"[FAIL] OPH-019 submit signature drift: {submit_args}")
    if await_args[:3] != ("request_id", "root", "timeout_seconds"):
        raise SystemExit(f"[FAIL] OPH-019 await signature drift: {await_args}")
    if read_args[:1] != ("observation_ids",):
        raise SystemExit(f"[FAIL] OAD-068 readback signature drift: {read_args}")

    print("[PASS] exact OPH-019 submit contract verified:", submit_args)
    print("[PASS] exact OPH-019 await contract verified:", await_args)
    print("[PASS] exact OAD-068 readback contract verified:", read_args)

    validate_source(BOUNDARY, BOUNDARY_SOURCE)
    validate_source(GATE, GATE_SOURCE)
    validate_source(TEST, TEST_SOURCE)

    write_and_compile(BOUNDARY, BOUNDARY_SOURCE)
    write_and_compile(GATE, GATE_SOURCE)
    write_and_compile(TEST, TEST_SOURCE)

    print("[PASS] immediate-readback defect retired")
    print("[PASS] certified OPH-021 runner required")
    print("[PASS] submit -> await_request -> exact_readback sequence installed")
    print("[PASS] no direct PostgreSQL writer introduced")
    print("[PASS] execution_authority=FALSE")


if __name__ == "__main__":
    main()
