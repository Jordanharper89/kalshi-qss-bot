\

from __future__ import annotations
from dataclasses import dataclass
from collections import Counter

READ_ONLY=True
PROBABILITY_ENABLED=False
DIRECTION_ENABLED=False
PUBLICATION_ALLOWED=False
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class SolanaRestartIdempotencyResult:
    before_ids: tuple
    replay_ids: tuple
    new_ids: tuple
    duplicate_replay_ids: tuple
    duplicate_with_existing_ids: tuple
    accepted_new_ids: tuple
    idempotent: bool
    state: str
    execution_authority: bool=False

def reconcile_restart_idempotency(existing_ids,replay_ids):
    before=tuple(dict.fromkeys(str(x) for x in existing_ids))
    replay=tuple(str(x) for x in replay_ids)
    counts=Counter(replay)
    duplicate_replay=tuple(sorted(x for x,n in counts.items() if n>1))
    existing=set(before)
    duplicate_existing=tuple(x for x in dict.fromkeys(replay) if x in existing)
    accepted=tuple(x for x in dict.fromkeys(replay) if x not in existing)
    idempotent=(len(set(accepted))==len(accepted))
    state="RESTART_REPLAY_IDEMPOTENT" if idempotent else "RESTART_REPLAY_DUPLICATE_FAILURE"
    return SolanaRestartIdempotencyResult(before,replay,accepted,duplicate_replay,duplicate_existing,accepted,idempotent,state,False)

