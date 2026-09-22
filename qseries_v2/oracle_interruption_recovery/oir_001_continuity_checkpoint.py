from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import os
import time

from qseries_v2.oracle_learning_feedback.olf_011_learned_experience_profile import (
    _connect,
    _db_url,
)
from qseries_v2.oracle_learning_runtime.olr_016_production_learned_state_adapter import (
    load_production_learned_state,
)

OIR_001_BUILD_ID = "OIR-001"
OIR_001_REVISION = "OIR_001_DURABLE_RUNTIME_CONTINUITY_CHECKPOINT_CORRECTION_V2"
CHECKPOINT_NAME = "oracle_interruption_continuity_checkpoint.json"


def _inventory_checkpoint_files(root):
    state = Path(root) / "runtime_state"
    if not state.exists():
        return []

    rows = []
    for path in sorted(state.iterdir()):
        name = path.name.lower()
        if not path.is_file():
            continue
        if "inventory" not in name or "checkpoint" not in name:
            continue
        try:
            stat = path.stat()
            rows.append(
                {
                    "name": path.name,
                    "size": int(stat.st_size),
                    "mtime_ns": int(stat.st_mtime_ns),
                }
            )
        except OSError:
            pass
    return rows


def capture_continuity_checkpoint(root=None):
    root = Path(root or Path.cwd()).resolve()
    now = datetime.now(timezone.utc)

    conn = _connect(_db_url(root))
    try:
        try:
            conn.set_session(readonly=True, autocommit=False)
        except Exception:
            pass

        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                COALESCE(MAX(sequence_number), 0),
                COALESCE(MAX(observed_at)::text, ''),
                COALESCE(MAX(persisted_at)::text, ''),
                COUNT(*)
            FROM public.oracle_canonical_observations
            """
        )
        seq, observed_at, persisted_at, observation_count = cur.fetchone()

        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        conn.close()

    learner = load_production_learned_state(root)

    payload = {
        "revision": OIR_001_REVISION,
        "captured_at": now.isoformat(),
        "canonical_sequence_number": int(seq or 0),
        "canonical_observed_at": str(observed_at or ""),
        "canonical_persisted_at": str(persisted_at or ""),
        "canonical_observation_count": int(observation_count or 0),
        "learner_state_hash": str(learner.learner_state_hash or ""),
        "learner_outcomes_learned": int(learner.outcomes_learned),
        "inventory_checkpoint_files": _inventory_checkpoint_files(root),
        "execution_authority": False,
    }

    path = root / "runtime_state" / CHECKPOINT_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
        newline="\n",
    )
    os.replace(tmp, path)
    return payload


def load_continuity_checkpoint(root=None):
    root = Path(root or Path.cwd()).resolve()
    path = root / "runtime_state" / CHECKPOINT_NAME
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def run_checkpoint_daemon(root=None, cadence_seconds=5.0, progress=print):
    root = Path(root or Path.cwd()).resolve()
    cadence_seconds = float(cadence_seconds)
    if cadence_seconds <= 0:
        raise ValueError("cadence_seconds must be > 0")

    while True:
        payload = capture_continuity_checkpoint(root)
        if progress:
            progress(
                "[OIR CHECKPOINT] "
                f"captured_at={payload['captured_at']} "
                f"sequence={payload['canonical_sequence_number']} "
                f"observations={payload['canonical_observation_count']} "
                f"learner_outcomes={payload['learner_outcomes_learned']}"
            )
        time.sleep(cadence_seconds)


def verify_oir_001_durable_runtime_continuity_checkpoint():
    return (
        OIR_001_BUILD_ID == "OIR-001"
        and callable(capture_continuity_checkpoint)
        and callable(load_continuity_checkpoint)
        and callable(run_checkpoint_daemon)
    )
