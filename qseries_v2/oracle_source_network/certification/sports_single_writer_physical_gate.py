import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_source_network.canonical.sports_event_v2 import CanonicalSportsEvent
from qseries_v2.oracle_source_network.persistence.sports_persistence_contract import from_canonical_event
from qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import (
    WRITER_ID,
    canonicalize,
    submit,
    await_commit,
    exact_readback,
    readback_count,
)


@dataclass(frozen=True)
class PhysicalPersistenceResult:
    canonical_event_id: str
    observation_id: str
    request_id: str
    committed_events: int
    exact_readback: int
    writer_process_started: bool
    execution_authority: bool = False


def _start_certified_writer(root):
    runner = root / "run_oph_021_exclusive_postgresql_canonical_writer.py"
    if not runner.exists():
        raise RuntimeError("certified OPH-021 runner missing: " + str(runner))
    proc = subprocess.Popen(
        [sys.executable, str(runner)],
        cwd=str(root),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.0)
    return proc


def _request_id(submission):
    rid = getattr(submission, "request_id", None)
    if rid:
        return str(rid)
    if isinstance(submission, dict) and submission.get("request_id"):
        return str(submission["request_id"])
    raise RuntimeError("OPH-019 submission returned no request_id")


def persist_fixture(timeout_seconds=45.0):
    root = Path.cwd().resolve()
    writer = _start_certified_writer(root)

    try:
        token = uuid.uuid4().hex[:12]
        observed_at = datetime.now(timezone.utc).isoformat()

        event = CanonicalSportsEvent(
            league="NFL",
            season="2026",
            provider="osn_physical_fixture",
            home_team="OSN_HOME",
            away_team="OSN_AWAY",
            scheduled_start="2026-09-06T12:00:00Z",
            source_observed_at=observed_at,
            source_authority="certification_fixture",
            provider_event_id="osn-" + token,
            event_discriminator="osn-" + token,
        )

        raw = from_canonical_event(event)
        canonical = canonicalize(raw, "osn063-await-" + token)

        submission = submit((canonical,), root=root)
        request_id = _request_id(submission)

        committed = await_commit(
            request_id,
            root=root,
            timeout_seconds=timeout_seconds,
        )

        readback = exact_readback(canonical.observation_id, root=root)
        count = readback_count(readback)

        return PhysicalPersistenceResult(
            canonical_event_id=event.canonical_event_id,
            observation_id=canonical.observation_id,
            request_id=request_id,
            committed_events=len(committed),
            exact_readback=count,
            writer_process_started=True,
        )
    finally:
        if writer.poll() is None:
            writer.terminate()
            try:
                writer.wait(timeout=3)
            except subprocess.TimeoutExpired:
                writer.kill()
