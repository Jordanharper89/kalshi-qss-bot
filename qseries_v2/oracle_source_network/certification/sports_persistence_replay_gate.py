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
    canonicalize,
    submit,
    await_commit,
    exact_readback,
    readback_count,
)


@dataclass(frozen=True)
class ReplayResult:
    observation_id: str
    first_request_id: str
    first_committed_events: int
    replay_already_present: bool
    replay_resubmitted: bool
    exact_readback: int
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


def certify_replay(timeout_seconds=45.0):
    root = Path.cwd().resolve()
    writer = _start_certified_writer(root)

    try:
        token = uuid.uuid4().hex[:12]
        observed = datetime.now(timezone.utc).isoformat()

        event = CanonicalSportsEvent(
            league="MLS",
            season="2026",
            provider="osn_replay_fixture",
            home_team="REPLAY_HOME",
            away_team="REPLAY_AWAY",
            scheduled_start="2026-09-06T13:00:00Z",
            source_observed_at=observed,
            source_authority="certification_fixture",
            provider_event_id="replay-" + token,
            event_discriminator="replay-" + token,
        )

        raw = from_canonical_event(event)
        batch_id = "osn064-rbw-" + token

        first = canonicalize(raw, batch_id)
        replay = canonicalize(raw, batch_id)

        if first.observation_id != replay.observation_id:
            raise RuntimeError("canonical replay identity drift")

        first_submission = submit((first,), root=root)
        first_request_id = _request_id(first_submission)
        first_committed = await_commit(
            first_request_id,
            root=root,
            timeout_seconds=timeout_seconds,
        )

        first_readback = exact_readback(first.observation_id, root=root)
        first_count = readback_count(first_readback)
        if first_count < 1:
            raise RuntimeError("first committed sports observation not exactly readable")

        # Certified OAD-068 policy: read before write.
        # A duplicate canonical identity that is already durable must not be resubmitted.
        replay_readback = exact_readback(replay.observation_id, root=root)
        replay_count = readback_count(replay_readback)
        already_present = replay_count >= 1

        if not already_present:
            raise RuntimeError("replay identity unexpectedly missing after first durable commit")

        return ReplayResult(
            observation_id=first.observation_id,
            first_request_id=first_request_id,
            first_committed_events=len(first_committed),
            replay_already_present=True,
            replay_resubmitted=False,
            exact_readback=replay_count,
        )
    finally:
        if writer.poll() is None:
            writer.terminate()
            try:
                writer.wait(timeout=3)
            except subprocess.TimeoutExpired:
                writer.kill()
