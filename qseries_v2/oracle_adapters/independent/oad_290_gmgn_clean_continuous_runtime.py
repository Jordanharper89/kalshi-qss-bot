from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import time

from .oad_289_gmgn_clean_single_writer_persistence import persist_current_gmgn

READ_ONLY = True
PROBABILITY_ENABLED = False
DIRECTION_ENABLED = False
PUBLICATION_ALLOWED = False
EXECUTION_AUTHORITY = False

MAX_ERROR_DETAIL = 1800


@dataclass(frozen=True, slots=True)
class Checkpoint:
    cycles: int = 0
    successes: int = 0
    failures: int = 0
    last_success_at: str | None = None
    last_error: str | None = None
    last_token_address: str | None = None
    last_observation_ids: tuple = ()
    execution_authority: bool = False


def checkpoint_path(root=None):
    p = Path(root or Path.cwd()).resolve() / "runtime_state"
    p.mkdir(parents=True, exist_ok=True)
    return p / "oad_290_gmgn_clean_runtime.json"


def load_checkpoint(root=None):
    p = checkpoint_path(root)
    if not p.exists():
        return Checkpoint()
    d = json.loads(p.read_text(encoding="utf-8"))
    return Checkpoint(
        int(d["cycles"]),
        int(d["successes"]),
        int(d["failures"]),
        d.get("last_success_at"),
        d.get("last_error"),
        d.get("last_token_address"),
        tuple(d.get("last_observation_ids") or ()),
        False,
    )


def save(c, root=None):
    p = checkpoint_path(root)
    d = asdict(c)
    d["last_observation_ids"] = list(c.last_observation_ids)
    t = p.with_suffix(".tmp")
    t.write_text(
        json.dumps(d, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(t, p)


def _bounded_error_detail(exc):
    detail = str(exc).strip()
    if not detail:
        detail = repr(exc)
    detail = " ".join(detail.split())
    return detail[:MAX_ERROR_DETAIL]


def cycle(root=None):
    c = load_checkpoint(root)
    try:
        r = persist_current_gmgn(root)
        n = Checkpoint(
            c.cycles + 1,
            c.successes + 1,
            c.failures,
            datetime.now(timezone.utc).isoformat(),
            None,
            r.token_address,
            r.observation_ids,
            False,
        )
        save(n, root)
        return r, n
    except Exception as exc:
        detail = _bounded_error_detail(exc)
        save(
            Checkpoint(
                c.cycles + 1,
                c.successes,
                c.failures + 1,
                c.last_success_at,
                detail,
                c.last_token_address,
                c.last_observation_ids,
                False,
            ),
            root,
        )
        raise


def run(max_cycles=None, cadence_seconds=60.0, root=None, progress=print):
    done = 0
    backoff = 5.0

    while max_cycles is None or done < int(max_cycles):
        try:
            r, c = cycle(root)
            done += 1
            backoff = 5.0
            progress(
                f"[GMGN2] cycle={c.cycles} status=SUCCESS "
                f"token={r.token_address} committed_new={r.committed_new} "
                f"exact_readback={r.exact_readback} execution_authority=FALSE"
            )
            if max_cycles is None or done < int(max_cycles):
                time.sleep(float(cadence_seconds))

        except KeyboardInterrupt:
            raise

        except Exception as exc:
            done += 1
            c = load_checkpoint(root)
            wait = min(
                600.0,
                max(
                    5.0,
                    float(getattr(exc, "retry_after_seconds", backoff)),
                ),
            )
            detail = _bounded_error_detail(exc)
            progress(
                f"[GMGN2] cycle={c.cycles} status=COOLDOWN "
                f"error_type={type(exc).__name__} "
                f"error_detail={detail!r} "
                f"retry_in={wait:.1f}s execution_authority=FALSE"
            )
            if max_cycles is None or done < int(max_cycles):
                time.sleep(wait)
            backoff = min(60.0, backoff * 2)

    return load_checkpoint(root)
