from __future__ import annotations
from dataclasses import dataclass
from .oad_294_solana_universe_durable_change_detection import detect_and_checkpoint_solana_universe_changes
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
@dataclass(frozen=True,slots=True)
class SolanaPoolLifecycle:
 current_tokens:int; current_pools:int; newly_seen_pools:tuple; missing_since_prior:tuple; migration_candidates:tuple; execution_authority:bool=False
def track_solana_pool_lifecycle(root=None,timeout_seconds=30.0,max_tokens=12):
 d=detect_and_checkpoint_solana_universe_changes(root,timeout_seconds,max_tokens)
 # Missing is evidence of disappearance from the bounded observed universe only.
 # It is not labeled "dead" without stronger chain evidence.
 migrations=tuple()
 return SolanaPoolLifecycle(d.current_tokens,d.current_pools,d.new_pools,d.missing_pools,migrations,False)
