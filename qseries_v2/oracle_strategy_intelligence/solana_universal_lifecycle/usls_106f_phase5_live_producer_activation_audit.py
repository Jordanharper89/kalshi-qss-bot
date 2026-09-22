from __future__ import annotations
import json,re
from pathlib import Path

TARGETS={
 "BIRTH":"confirmed_tradeable_birth_events.json",
 "PUMPSWAP":"pumpswap_048c_repaired_trades.json",
 "REMAINING":"remaining_venue_universal_trade_rows.json",
 "LAUNCHLAB":"launchlab_universal_trade_rows.json",
}
RUNTIME_TERMS=("run_oracle_live","runtime","worker","loop","start","register","child","heartbeat")

def scan(root):
 root=Path(root);files=[]
 for p in (root/"qseries_v2").rglob("*.py"):
  try:s=p.read_text(encoding="utf-8",errors="ignore")
  except Exception:continue
  hits=[k for k,v in TARGETS.items() if v in s]
  if not hits:continue
  defs=re.findall(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(",s,re.M)
  runtime=[t for t in RUNTIME_TERMS if t.lower() in s.lower()]
  writes=bool(re.search(r"(write_text|json\.dump|open\s*\([^\n]*['\"]w|replace\s*\()",s,re.I))
  files.append({"path":str(p.relative_to(root)),"targets":hits,"functions":defs[:80],
   "runtime_terms":runtime,"writes_output":writes})
 return files

def registrations(root,paths):
 root=Path(root);out=[]
 needles=[Path(x).stem for x in paths]
 for p in [root/"run_oracle_live.py",root/"qseries_v2"]:
  plist=[p] if p.is_file() else list(p.rglob("*.py")) if p.exists() else []
  for f in plist:
   try:s=f.read_text(encoding="utf-8",errors="ignore")
   except Exception:continue
   h=[n for n in needles if n in s]
   if h:out.append({"path":str(f.relative_to(root)),"module_mentions":h})
 return out

def build(root):
 producers=scan(root)
 regs=registrations(root,[x["path"] for x in producers])
 by={k:[] for k in TARGETS}
 for x in producers:
  for k in x["targets"]:by[k].append(x["path"])
 return {"revision":"USLS_106F","targets":TARGETS,"producer_count":len(producers),
  "producers":producers,"producer_paths_by_target":by,"runtime_registration_hits":regs,
  "finding":"STATIC_SNAPSHOT_SOURCES_REQUIRE_LIVE_PRODUCER_OR_SHARED_CAPTURE_ACTIVATION",
  "certification_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_lifecycle/phase5_live_producer_activation_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
