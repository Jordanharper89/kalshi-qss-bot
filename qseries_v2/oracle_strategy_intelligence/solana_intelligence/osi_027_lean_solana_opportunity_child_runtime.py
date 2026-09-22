from __future__ import annotations
import json,time
from pathlib import Path
def registered_sources(root:Path)->dict:
 p=root/"runtime_state/solana_opportunities/source_registry.json"
 if not p.is_file():return {}
 return json.loads(p.read_text(encoding="utf-8"))
def health(root:Path,cycle:int,state:str,error=None)->Path:
 p=root/"runtime_state/solana_opportunities/health/child_status.json";p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps({"revision":"OSI_027","cycle_count":cycle,"state":state,"error":error,
 "updated_at":time.time(),"execution_authority":False,"read_only":True},indent=2,sort_keys=True),encoding="utf-8");return p
