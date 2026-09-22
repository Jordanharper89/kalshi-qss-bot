from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import tempfile


@dataclass(frozen=True)
class SportsCheckpoint:
    league: str
    observation_id: str
    observed_at: str
    committed_readback_count: int
    checkpointed_at: str
    execution_authority: bool = False


def _checkpoint_path(root, league):
    return Path(root) / "qseries_v2" / "oracle_source_network" / "state" / "sports_checkpoints" / (league.lower() + ".json")


def commit_checkpoint_after_readback(league, observation_id, observed_at, exact_readback_count, root=None):
    if int(exact_readback_count) < 1:
        raise RuntimeError("checkpoint prohibited before exact durable readback")

    base = Path(root or Path.cwd()).resolve()
    path = _checkpoint_path(base, league)
    path.parent.mkdir(parents=True, exist_ok=True)

    value = SportsCheckpoint(
        league=str(league),
        observation_id=str(observation_id),
        observed_at=str(observed_at),
        committed_readback_count=int(exact_readback_count),
        checkpointed_at=datetime.now(timezone.utc).isoformat(),
    )

    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(asdict(value), fh, sort_keys=True, separators=(",", ":"))
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)

    return value


def read_checkpoint(league, root=None):
    base = Path(root or Path.cwd()).resolve()
    path = _checkpoint_path(base, league)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return SportsCheckpoint(**data)
