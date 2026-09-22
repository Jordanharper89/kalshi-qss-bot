from __future__ import annotations
import json
from pathlib import Path
REL="runtime_state/solana_opportunities"
DIRS=("intake","evidence","theses","outcomes","learning","health","reports")
def activate(root:Path)->dict:
 base=root/REL
 for d in DIRS:(base/d).mkdir(parents=True,exist_ok=True)
 manifest={"revision":"OSI_025","runtime_kind":"SOLANA_OPPORTUNITY",
  "primary_sources":["NATIVE_SOLANA","GMGN"],
  "context_sources":["COINBASE_SOL_REGIME"],
  "shared_acquisition":True,"execution_authority":False,"read_only":True,
  "directories":list(DIRS)}
 (base/"runtime_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding="utf-8")
 return manifest
