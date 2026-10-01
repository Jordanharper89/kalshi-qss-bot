from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_049_faster_native_trigger_foundation_audit.py"
TEST=ROOT/"test_suls_049_faster_native_trigger_foundation_audit.py"

MOD_TEXT=r"""from __future__ import annotations
import json,re
from pathlib import Path

TERMS={
 "processed":("commitment\":\"processed","commitment': 'processed","commitment='processed'","commitment=\"processed\""),
 "confirmed":("commitment\":\"confirmed","commitment': 'confirmed","commitment='confirmed'","commitment=\"confirmed\""),
 "websocket":("websocket","websockets","ws://","wss://"),
 "logs_subscribe":("logssubscribe",),
 "block_subscribe":("blocksubscribe",),
 "program_subscribe":("programsubscribe",),
 "signature_subscribe":("signaturesubscribe",),
 "slot_subscribe":("slotsubscribe",),
 "generic_rpc":("_rpc(","urlopen(","request("),
}

def audit(root):
 base=root/"qseries_v2"
 rows=[]
 for p in base.rglob("*.py"):
  try: src=p.read_text(encoding="utf-8",errors="ignore");low=src.lower()
  except Exception: continue
  hits={k:any(t.lower() in low for t in vals) for k,vals in TERMS.items()}
  if any(hits[k] for k in ("processed","confirmed","websocket","logs_subscribe","block_subscribe","program_subscribe","signature_subscribe","slot_subscribe")):
   rows.append({"path":str(p.relative_to(root)),"hits":hits,
    "excerpt":"\n".join(line for line in src.splitlines() if any(t.lower() in line.lower() for vals in TERMS.values() for t in vals))[:10000]})
 rows.sort(key=lambda x:x["path"])
 return {"revision":"SULS_049","candidate_count":len(rows),"candidates":rows,
  "execution_authority":False,"read_only":True,
  "scope":"Repository-wide lexical foundation audit only; no capability claim"}

def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/faster_native_trigger_foundation_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_049_faster_native_trigger_foundation_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT);print("[CANDIDATE_COUNT]",d["candidate_count"])
  for x in d["candidates"][:50]:
   print("[CANDIDATE]",x["path"],json.dumps(x["hits"],sort_keys=True))
   if x.get("excerpt"):print("[EXCERPT]");print(x["excerpt"][:3000])
  print("[PASS] SULS-049 faster native trigger foundation audit")
  print("[SCOPE]",d["scope"])
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-049 FASTER NATIVE TRIGGER FOUNDATION AUDIT");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
