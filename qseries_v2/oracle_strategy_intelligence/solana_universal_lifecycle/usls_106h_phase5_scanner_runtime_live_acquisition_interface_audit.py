from __future__ import annotations
import json,re
from pathlib import Path

NEEDLES=(
 "logsSubscribe","websockets","websocket","wss://","multidex_live_event_router",
 "decode_pumpswap_program_data","PUMP_SWAP","RAYDIUM_LAUNCHLAB","MOONIT","BOOP_FUN","HEAVEN"
)

def inspect_file(root,p):
 try:s=p.read_text(encoding="utf-8",errors="ignore")
 except Exception:return None
 score=sum(n.lower() in s.lower() for n in NEEDLES)
 if score<2:return None
 funcs=re.findall(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(([^)]*)\)",s,re.M)
 imports=[]
 for line in s.splitlines():
  if line.startswith("from ") or line.startswith("import "):
   if any(x in line.lower() for x in ("websocket","solana","suls_","usls_")):imports.append(line[:300])
 writes=[]
 for m in re.finditer(r"['\"]([^'\"]+\.json)['\"]",s):
  q=m.group(1)
  if "runtime_state" in s[max(0,m.start()-250):m.end()+250] or "json" in q:
   writes.append(q)
 return {"path":str(p.relative_to(root)),"score":score,
  "functions":[{"name":a,"args":b[:250]} for a,b in funcs[:80]],
  "imports":imports[:40],"json_names":sorted(set(writes))[:50]}

def build(root):
 root=Path(root);rows=[]
 for p in (root/"qseries_v2").rglob("*.py"):
  x=inspect_file(root,p)
  if x:rows.append(x)
 rows.sort(key=lambda x:(x["score"],len(x["functions"])),reverse=True)
 wanted=[x for x in rows if any(k in x["path"].lower() for k in
  ("usls_011","usls_014","usls_045","usls_046","suls_083","solana_universal_trade_tape","solana_universal_launch_scanner"))]
 return {"revision":"USLS_106H","candidate_count":len(wanted),"candidates":wanted[:60],
  "target":"SEPARATE_SOLANA_SCANNER_LIVE_BIRTH_PLUS_UNIVERSAL_TRADE_ACQUISITION",
  "required_properties":["SEPARATE_RUNTIME","READ_ONLY","RAW_KNOWN_PROGRAM_RETENTION",
   "UNKNOWN_RETENTION","NO_EXECUTION_AUTHORITY","REUSE_CERTIFIED_UPSTREAM_ACQUISITION"],
  "certification_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root)
 p=Path(root)/"runtime_state/solana_opportunities/universal_lifecycle/phase5_scanner_runtime_live_acquisition_interface_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
