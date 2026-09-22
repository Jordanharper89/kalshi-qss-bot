from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from qseries_v2.oracle_source_network.persistence.sports_runtime_checkpoint import read_checkpoint
from qseries_v2.oracle_source_network.runtime.sports_gap_backfill_plan import plan_gap_backfill
from qseries_v2.oracle_source_network.persistence.sports_single_writer_boundary import exact_readback, readback_count


@dataclass(frozen=True)
class RestartRecovery:
    league: str
    checkpoint_found: bool
    checkpoint_observation_durable: bool
    replay_resubmitted: bool
    gap_seconds: int
    backfill_windows: int
    recovery_status: str
    execution_authority: bool = False


def recover_from_checkpoint(league, root=None, now=None):
    base = Path(root or Path.cwd()).resolve()
    checkpoint = read_checkpoint(league, root=base)
    if checkpoint is None:
        return RestartRecovery(
            league=str(league),
            checkpoint_found=False,
            checkpoint_observation_durable=False,
            replay_resubmitted=False,
            gap_seconds=0,
            backfill_windows=0,
            recovery_status="NO_CHECKPOINT_FULL_DISCOVERY_REQUIRED",
        )

    readback = exact_readback(checkpoint.observation_id, root=base)
    durable = readback_count(readback) >= 1
    if not durable:
        raise RuntimeError("checkpoint points to non-durable observation")

    current = now or datetime.now(timezone.utc).isoformat()
    gap = plan_gap_backfill(
        league,
        checkpoint.observed_at,
        current,
    )

    return RestartRecovery(
        league=str(league),
        checkpoint_found=True,
        checkpoint_observation_durable=True,
        replay_resubmitted=False,
        gap_seconds=gap.gap_seconds,
        backfill_windows=len(gap.windows),
        recovery_status="RECONCILE_BACKFILL_THEN_RESUME" if gap.windows else "RESUME_LIVE",
    )
