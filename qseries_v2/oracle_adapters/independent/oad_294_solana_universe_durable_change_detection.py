from __future__ import annotations
import json,os
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
from .oad_293_solana_token_pool_identity_dedup_registry import build_solana_token_pool_identity_registry
READ_ONLY=True; PROBABILITY_ENABLED=False; DIRECTION_ENABLED=False; PUBLICATION_ALLOWED=False; EXECUTION_AUTHORITY=False
STATE="runtime_state/oad_294_solana_universe_registry.json"
@dataclass(frozen=True,slots=True)
class SolanaUniverseDelta:
 observed_at:str; current_tokens:int; current_pools:int; new_tokens:tuple; new_pools:tuple; missing_pools:tuple; execution_authority:bool=False
def detect_and_checkpoint_solana_universe_changes(root=None,timeout_seconds=30.0,max_tokens=12):
 root=Path(root or Path.cwd()).resolve(); p=root/STATE
 prior={"tokens":[],"pools":[]}
 if p.is_file():
  try: prior=json.loads(p.read_text(encoding="utf-8"))
  except Exception: prior={"tokens":[],"pools":[]}
 r=build_solana_token_pool_identity_registry(timeout_seconds,max_tokens)
 tokens=sorted({x.token_address for x in r.identities}); pools=sorted({x.pair_address for x in r.identities})
 pt=set(prior.get("tokens") or ()); pp=set(prior.get("pools") or ())
 now=datetime.now(timezone.utc).isoformat()
 data={"observed_at":now,"tokens":tokens,"pools":pools}
 p.parent.mkdir(parents=True,exist_ok=True); tmp=p.with_suffix(".tmp"); tmp.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n",encoding="utf-8"); os.replace(tmp,p)
 return SolanaUniverseDelta(now,len(tokens),len(pools),tuple(sorted(set(tokens)-pt)),tuple(sorted(set(pools)-pp)),tuple(sorted(pp-set(pools))),False)
