from __future__ import annotations
import json
from pathlib import Path

PATHS=(
"runtime_state/solana_opportunities/universal_launch_scanner/canonical_universal_birth_events.json",
"runtime_state/solana_opportunities/universal_launch_scanner/pump_canonical_birth_horizons.json",
"runtime_state/solana_opportunities/universal_launch_scanner/pump_create_v2_decoded_births.json",
)

def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():
            if isinstance(v,(dict,list)):yield from walk(v)
    elif isinstance(x,list):
        for v in x:
            if isinstance(v,(dict,list)):yield from walk(v)

class BirthIndex:
    def __init__(self,root:Path):
        self.root=Path(root).resolve();self.mtimes={};self.births={}
    def refresh(self):
        for rel in PATHS:
            p=self.root/rel
            if not p.is_file():continue
            try:mt=p.stat().st_mtime_ns
            except OSError:continue
            if self.mtimes.get(str(p))==mt:continue
            self.mtimes[str(p)]=mt
            try:obj=json.loads(p.read_text(encoding="utf-8",errors="ignore"))
            except Exception:continue
            for d in walk(obj):
                token=d.get("token_address") or d.get("token_mint")
                t=d.get("birth_observed_unix") or d.get("observed_unix") or d.get("block_time")
                try:t=float(t)
                except Exception:continue
                if token and t>0:
                    token=str(token)
                    if token not in self.births or t<self.births[token]:self.births[token]=t
    def age(self,event):
        try:a=float(event.get("birth_age_seconds",-1))
        except Exception:a=-1
        if a>=0:return a
        t=self.births.get(str(event.get("token")))
        return max(0.0,float(event["t"])-t) if t else -1.0
