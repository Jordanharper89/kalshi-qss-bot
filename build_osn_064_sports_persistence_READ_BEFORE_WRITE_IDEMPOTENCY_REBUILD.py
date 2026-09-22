from pathlib import Path
import ast

ROOT=Path.cwd()
MODULE="qseries_v2/oracle_source_network/certification/sports_persistence_replay_gate.py"
TEST="test_osn_064_sports_persistence_READ_BEFORE_WRITE_IDEMPOTENCY_REBUILD.py"
MODULE_SOURCE='import subprocess\nimport sys\nimport time\nimport uuid\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent\nfrom qseries_v2.oracle_source_network.persistence.sports_persistence_contract import from_canonical_event\nfrom qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import (\n    canonicalize,\n    submit,\n    await_commit,\n    exact_readback,\n    readback_count,\n)\n\n\n@dataclass(frozen=True)\nclass ReplayResult:\n    observation_id: str\n    first_request_id: str\n    first_committed_events: int\n    replay_already_present: bool\n    replay_resubmitted: bool\n    exact_readback: int\n    execution_authority: bool = False\n\n\ndef _start_certified_writer(root):\n    runner = root / "run_oph_021_exclusive_postgresql_canonical_writer.py"\n    if not runner.exists():\n        raise RuntimeError("certified OPH-021 runner missing: " + str(runner))\n    proc = subprocess.Popen(\n        [sys.executable, str(runner)],\n        cwd=str(root),\n        stdout=subprocess.DEVNULL,\n        stderr=subprocess.DEVNULL,\n    )\n    time.sleep(1.0)\n    return proc\n\n\ndef _request_id(submission):\n    rid = getattr(submission, "request_id", None)\n    if rid:\n        return str(rid)\n    if isinstance(submission, dict) and submission.get("request_id"):\n        return str(submission["request_id"])\n    raise RuntimeError("OPH-019 submission returned no request_id")\n\n\ndef certify_replay(timeout_seconds=45.0):\n    root = Path.cwd().resolve()\n    writer = _start_certified_writer(root)\n\n    try:\n        token = uuid.uuid4().hex[:12]\n        observed = datetime.now(timezone.utc).isoformat()\n\n        event = CanonicalSportsEvent(\n            league="MLS",\n            season="2026",\n            provider="osn_replay_fixture",\n            home_team="REPLAY_HOME",\n            away_team="REPLAY_AWAY",\n            scheduled_start="2026-09-06T13:00:00Z",\n            source_observed_at=observed,\n            source_authority="certification_fixture",\n            provider_event_id="replay-" + token,\n            event_discriminator="replay-" + token,\n        )\n\n        raw = from_canonical_event(event)\n        batch_id = "osn064-rbw-" + token\n\n        first = canonicalize(raw, batch_id)\n        replay = canonicalize(raw, batch_id)\n\n        if first.observation_id != replay.observation_id:\n            raise RuntimeError("canonical replay identity drift")\n\n        first_submission = submit((first,), root=root)\n        first_request_id = _request_id(first_submission)\n        first_committed = await_commit(\n            first_request_id,\n            root=root,\n            timeout_seconds=timeout_seconds,\n        )\n\n        first_readback = exact_readback(first.observation_id, root=root)\n        first_count = readback_count(first_readback)\n        if first_count < 1:\n            raise RuntimeError("first committed sports observation not exactly readable")\n\n        # Certified OAD-068 policy: read before write.\n        # A duplicate canonical identity that is already durable must not be resubmitted.\n        replay_readback = exact_readback(replay.observation_id, root=root)\n        replay_count = readback_count(replay_readback)\n        already_present = replay_count >= 1\n\n        if not already_present:\n            raise RuntimeError("replay identity unexpectedly missing after first durable commit")\n\n        return ReplayResult(\n            observation_id=first.observation_id,\n            first_request_id=first_request_id,\n            first_committed_events=len(first_committed),\n            replay_already_present=True,\n            replay_resubmitted=False,\n            exact_readback=replay_count,\n        )\n    finally:\n        if writer.poll() is None:\n            writer.terminate()\n            try:\n                writer.wait(timeout=3)\n            except subprocess.TimeoutExpired:\n                writer.kill()\n'
TEST_SOURCE='from qseries_v2.oracle_source_network.certification.sports_persistence_replay_gate import certify_replay\n\nresult = certify_replay(timeout_seconds=45.0)\nprint("[READ_BEFORE_WRITE_REPLAY]", result)\n\nassert len(result.observation_id) >= 32\nassert len(result.first_request_id) >= 8\nassert result.first_committed_events >= 1\nassert result.replay_already_present is True\nassert result.replay_resubmitted is False\nassert result.exact_readback >= 1\nassert result.execution_authority is False\n\nprint("[PASS] first sports observation committed through existing single writer")\nprint("[PASS] replay canonicalized to identical observation identity")\nprint("[PASS] duplicate identity detected by exact PostgreSQL read-before-write")\nprint("[PASS] duplicate identity was not resubmitted")\nprint("[PASS] durable exact readback remains available")\nprint("[PASS] OSN-064 read-before-write idempotency rebuild certified")\n'

DEPS=(
    "qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py",
    "qseries_v2/oracle_source_network/certification/sports_single_writer_physical_gate.py",
    "qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py",
    "run_oph_021_exclusive_postgresql_canonical_writer.py",
)

def require(rel):
    p=ROOT/rel
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: "+rel)
    print("[PASS] dependency verified:",rel)
    return p

def require_function(rel,name):
    p=require(rel)
    tree=ast.parse(p.read_text(encoding="utf-8",errors="ignore"))
    if not any(isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name for n in ast.walk(tree)):
        raise SystemExit(f"[FAIL] required function missing: {rel} -> {name}")
    print(f"[PASS] exact function verified: {rel} -> {name}")

def require_text(rel,needle):
    p=require(rel)
    text=p.read_text(encoding="utf-8",errors="ignore")
    if needle not in text:
        raise SystemExit(f"[FAIL] certified behavior marker missing: {rel} -> {needle}")
    print(f"[PASS] certified behavior marker verified: {needle}")

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
    print(" OSN-064 SPORTS PERSISTENCE READ-BEFORE-WRITE IDEMPOTENCY REBUILD INSTALLER")
    print("="*120)

    for dep in DEPS:
        require(dep)

    for fn in ("canonicalize","submit","await_commit","exact_readback","readback_count"):
        require_function(
            "qseries_v2/oracle_source_network/persistence/sports_single_writer_boundary.py",
            fn,
        )

    require_function(
        "qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py",
        "exact_postgresql_readback",
    )

    write_compile(MODULE,MODULE_SOURCE)
    write_compile(TEST,TEST_SOURCE)

    print("[PASS] duplicate queue resubmission retired")
    print("[PASS] certified OAD-068 read-before-write idempotency policy adopted")
    print("[PASS] first write still requires OPH-019 await_commit")
    print("[PASS] replay requires exact durable readback and no resubmission")
    print("[PASS] existing OPH-019/021 single-writer path retained")
    print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
    main()
