from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path

EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class MissingSlotSchedule:
    last_committed_slot:int|None
    finalized_head:int
    scheduled_slots:tuple[int,...]
    remaining_lag_slots:int
    caught_up:bool
    execution_authority:bool=False

def build_missing_slot_schedule(last_committed_slot, finalized_head, max_slots=32, skipped_slots=()):
    head=int(finalized_head)
    if max_slots < 1:
        raise ValueError("max_slots must be >= 1")
    skipped={int(x) for x in skipped_slots}
    start=head if last_committed_slot is None else int(last_committed_slot)+1

    if start > head:
        return MissingSlotSchedule(last_committed_slot, head, (), 0, True, False)

    universe=[s for s in range(start, head+1) if s not in skipped]
    scheduled=tuple(universe[:max_slots])
    remaining=max(0, len(universe)-len(scheduled))

    return MissingSlotSchedule(
        last_committed_slot,
        head,
        scheduled,
        remaining,
        remaining == 0,
        False,
    )

def _checkpoint_candidates(root: Path):
    fixed = (
        root/"runtime_state"/"solana_universal_chain"/"checkpoint.json",
        root/"runtime_state"/"solana_universal_chain_checkpoint.json",
    )
    seen=set()
    for p in fixed:
        if p not in seen:
            seen.add(p)
            yield p

    rs=root/"runtime_state"
    if rs.is_dir():
        for p in rs.rglob("*.json"):
            name=p.name.lower()
            parent=str(p.parent).lower()
            if "solana" in name or "solana" in parent:
                if "checkpoint" in name or "continuity" in name or "chain" in parent:
                    if p not in seen:
                        seen.add(p)
                        yield p

def _extract_slot(obj):
    if isinstance(obj, dict):
        for key in (
            "last_committed_slot",
            "checkpoint_slot",
            "committed_slot",
            "through_slot",
            "last_slot",
            "slot",
        ):
            v=obj.get(key)
            if isinstance(v, int):
                return v

        for value in obj.values():
            found=_extract_slot(value)
            if found is not None:
                return found

    elif isinstance(obj, list):
        for value in obj:
            found=_extract_slot(value)
            if found is not None:
                return found

    return None

def read_last_committed_slot(root=None):
    r=Path(root).resolve() if root else Path.cwd().resolve()

    for p in _checkpoint_candidates(r):
        if not p.is_file():
            continue
        try:
            payload=json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue

        found=_extract_slot(payload)
        if found is not None:
            return int(found)

    return None
