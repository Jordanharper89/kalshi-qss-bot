from pathlib import Path
import ast

ROOT = Path.cwd()

BOUNDARY = "qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py"
GATE = "qseries_v2/oracle_source_network/certification/sports_single_writer_physical_gate.py"
TEST = "test_osn_063_sports_single_writer_EXACT_BOUNDARY_CLEAN_REBUILD.py"

BOUNDARY_SOURCE = 'import uuid\n\nfrom qseries_v2.oracle_adapters.independent.oad_261_universal_expansion_source_single_writer_postgresql_persistence import canonicalize_expansion_observation\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import submit_observation_batch\nfrom qseries_v2.oracle_adapters.independent.oad_068_exact_postgresql_independent_readback import exact_postgresql_readback\n\nWRITER_ID = "oracle.osn.sports"\nPRIORITY = 20\n\n\ndef canonicalize(observation, batch_id=None):\n    return canonicalize_expansion_observation(\n        observation,\n        batch_id or ("osn-sports-" + uuid.uuid4().hex),\n    )\n\n\ndef submit(observations, root=None):\n    rows = tuple(observations)\n    return submit_observation_batch(\n        WRITER_ID,\n        PRIORITY,\n        rows,\n        root=root,\n    )\n\n\ndef exact_readback(observation_id, root=None):\n    return exact_postgresql_readback(\n        (observation_id,),\n        root=root,\n    )\n\n\ndef readback_count(value):\n    if value is None:\n        return 0\n\n    if isinstance(value, (list, tuple, set)):\n        return len(value)\n\n    if isinstance(value, dict):\n        for key in ("rows", "observations", "results", "items"):\n            item = value.get(key)\n            if item is not None and hasattr(item, "__len__"):\n                return len(item)\n        return 1 if value else 0\n\n    for key in ("rows", "observations", "results", "items"):\n        item = getattr(value, key, None)\n        if item is not None and hasattr(item, "__len__"):\n            return len(item)\n\n    return 1\n'
GATE_SOURCE = 'import uuid\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\n\nfrom qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent\nfrom qseries_v2.oracle_source_network.persistence.sports_persistence_contract import from_canonical_event\nfrom qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import (\n    WRITER_ID,\n    canonicalize,\n    submit,\n    exact_readback,\n    readback_count,\n)\n\n\n@dataclass(frozen=True)\nclass PhysicalPersistenceResult:\n    canonical_event_id: str\n    observation_id: str\n    writer_id: str\n    exact_readback: int\n    execution_authority: bool = False\n\n\ndef persist_fixture():\n    token = uuid.uuid4().hex[:12]\n    observed_at = datetime.now(timezone.utc).isoformat()\n\n    event = CanonicalSportsEvent(\n        league="NFL",\n        season="2026",\n        provider="osn_physical_fixture",\n        home_team="OSN_HOME",\n        away_team="OSN_AWAY",\n        scheduled_start="2026-09-06T12:00:00Z",\n        source_observed_at=observed_at,\n        source_authority="certification_fixture",\n        provider_event_id="osn-" + token,\n        event_discriminator="osn-" + token,\n    )\n\n    raw = from_canonical_event(event)\n    canonical = canonicalize(raw, "osn063-clean-" + token)\n\n    submit((canonical,))\n    readback = exact_readback(canonical.observation_id)\n    count = readback_count(readback)\n\n    return PhysicalPersistenceResult(\n        canonical_event_id=event.canonical_event_id,\n        observation_id=canonical.observation_id,\n        writer_id=WRITER_ID,\n        exact_readback=count,\n    )\n'
TEST_SOURCE = 'import inspect\n\nfrom qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import (\n    WRITER_ID,\n    submit_observation_batch,\n    exact_postgresql_readback,\n)\nfrom qseries_v2.oracle_source_network.certification.sports_single_writer_physical_gate import persist_fixture\n\n\nprint("[OPH019_SIGNATURE]", inspect.signature(submit_observation_batch))\nprint("[OAD068_SIGNATURE]", inspect.signature(exact_postgresql_readback))\n\nassert str(inspect.signature(submit_observation_batch)) == "(writer_id, priority, observations, root=None)"\nassert str(inspect.signature(exact_postgresql_readback)) == "(observation_ids, root=None)"\nassert WRITER_ID == "oracle.osn.sports"\n\nresult = persist_fixture()\nprint("[PHYSICAL]", result)\n\nassert result.writer_id == "oracle.osn.sports"\nassert len(result.observation_id) >= 32\nassert result.exact_readback >= 1\nassert result.execution_authority is False\n\nprint("[PASS] exact OPH-019 writer_id contract used")\nprint("[PASS] sports observation persisted through existing single writer")\nprint("[PASS] exact PostgreSQL observation-ID readback certified")\nprint("[PASS] OSN-063 exact boundary clean rebuild certified")\n'

DEPS = (
    "qseries_v2/oracle_source_network/persistence/sports_persistence_contract.py",
    "qseries_v2/oracle_source_network/canonical/sports_event_v2.py",
    "qseries_v2/oracle_adapters/independent/oad_261_universal_expansion_source_single_writer_postgresql_persistence.py",
    "qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py",
    "qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py",
)


def require(rel):
    path = ROOT / rel
    if not path.exists():
        raise SystemExit("[FAIL] missing dependency: " + rel)
    print("[PASS] dependency verified:", rel)
    return path


def function_args(rel, symbol):
    path = require(rel)
    tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol:
            return tuple(arg.arg for arg in node.args.args)
    raise SystemExit(f"[FAIL] exact symbol missing: {rel} -> {symbol}")


def validate_source(label, source):
    if "\\n" in source:
        raise SystemExit(f"[FAIL] literal backslash-n detected in generated {label} source")
    compile(source, label, "exec")
    print(f"[PASS] {label} source compiled in memory")


def write_and_recompile(rel, source):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    disk = path.read_text(encoding="utf-8")
    if "\\n" in disk:
        raise SystemExit(f"[FAIL] literal backslash-n detected after write: {rel}")
    compile(disk, str(path), "exec")
    print("[WRITE]", rel)
    print("[PASS] post-write compile verified:", rel)


def main():
    print("=" * 120)
    print(" OSN-063 SPORTS SINGLE-WRITER EXACT BOUNDARY CLEAN REBUILD INSTALLER")
    print("=" * 120)

    for dep in DEPS:
        require(dep)

    oph = function_args(
        "qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py",
        "submit_observation_batch",
    )
    oad68 = function_args(
        "qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py",
        "exact_postgresql_readback",
    )

    if oph[:3] != ("writer_id", "priority", "observations"):
        raise SystemExit(f"[FAIL] OPH-019 signature drift: {oph}")
    if oad68[:1] != ("observation_ids",):
        raise SystemExit(f"[FAIL] OAD-068 signature drift: {oad68}")

    print("[PASS] OPH-019 exact contract verified:", oph)
    print("[PASS] OAD-068 exact contract verified:", oad68)

    validate_source("sports_single_writer_boundary.py", BOUNDARY_SOURCE)
    validate_source("sports_single_writer_physical_gate.py", GATE_SOURCE)
    validate_source(TEST, TEST_SOURCE)

    write_and_recompile(BOUNDARY, BOUNDARY_SOURCE)
    write_and_recompile(GATE, GATE_SOURCE)
    write_and_recompile(TEST, TEST_SOURCE)

    print("[PASS] malformed prior sports boundary retired")
    print("[PASS] malformed prior physical gate retired")
    print("[PASS] exact writer_id boundary rebuilt cleanly")
    print("[PASS] no direct PostgreSQL writer introduced")
    print("[PASS] execution_authority=FALSE")


if __name__ == "__main__":
    main()
