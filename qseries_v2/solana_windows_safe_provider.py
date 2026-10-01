from __future__ import annotations
import json, time
from pathlib import Path
from qseries_v2.solana_universal_money_runner_v2 import StableUniversalProvider

class WindowsSafeUniversalProvider(StableUniversalProvider):
    def __init__(self,root:Path,max_tokens=48,active_tokens=24,timeout=10.0,refresh_seconds=90.0):
        super().__init__(root,max_tokens,active_tokens,timeout,refresh_seconds)
        self.cache_path=Path(root).resolve()/"runtime_state/qseries/solana_adaptive_runtime_v3/universe_cache.json"
        self.cache_path.parent.mkdir(parents=True,exist_ok=True)
        self.cache_persist_errors=0

    def _persist(self):
        payload={"tokens":self.tokens,"last_refresh":self.last_refresh,"cursor":self.cursor}
        try:
            self.cache_path.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
        except Exception:
            self.cache_persist_errors+=1
            # Cache persistence must never kill live surveillance.
            return False
        return True
