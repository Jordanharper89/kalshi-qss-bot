from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_106r_scanner_hydration_contract_rate_limit_diagnostic.py"
TEST=ROOT/"test_usls_106r_scanner_hydration_contract_rate_limit_diagnostic.py"

MOD_TEXT=r"""from __future__ import annotations
import asyncio,inspect,json,time,re
from pathlib import Path

RAW="runtime_state/solana_opportunities/solana_scanner/raw_program_activity.jsonl"
S083="qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance/suls_083_persistent_event_driven_runtime.py"
O148="qseries_v2/oracle_adapters/independent/oad_148_solana_mainnet_chain_state_acquisition.py"

def _read(path):
 return Path(path).read_text(encoding="utf-8",errors="ignore")

def _func_excerpt(src,name):
 m=re.search(rf"^(?:async\s+)?def\s+{re.escape(name)}\s*\([^)]*\):",src,re.M)
 if not m:return []
 lines=src[m.start():].splitlines()
 out=[]
 for i,line in enumerate(lines):
  if i>0 and re.match(r"^(?:async\s+)?def\s+\w+\s*\(",line):break
  out.append(line)
  if len(out)>=120:break
 return out

def _raw_rows(root):
 p=Path(root)/RAW;out=[]
 for line in p.read_text(encoding="utf-8").splitlines():
  if line.strip():out.append(json.loads(line))
 return out

def _walk(x,key):
 if isinstance(x,dict):
  if x.get(key) not in (None,""):return x.get(key)
  for v in x.values():
   y=_walk(v,key)
   if y not in (None,""):return y
 elif isinstance(x,list):
  for v in x:
   y=_walk(v,key)
   if y not in (None,""):return y
 return None

def _sig(row):
 return row.get("signature") or _walk(row.get("raw_notification") or {},"signature")

async def _maybe(v):
 return await v if inspect.isawaitable(v) else v

async def probe(root,max_samples=3):
 from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_083_persistent_event_driven_runtime import _hydrate
 from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
 rows=_raw_rows(root);sigs=[];seen=set()
 for r in reversed(rows):
  s=_sig(r)
  if s and s not in seen:
   seen.add(s);sigs.append(str(s))
  if len(sigs)>=max_samples:break
 out=[]
 for i,s in enumerate(sigs):
  item={"signature":s,"hydrate_error":None,"hydrate_type":None,
        "direct_rpc_error":None,"direct_rpc_type":None,"direct_rpc_null":None}
  try:
   h=await _maybe(_hydrate(s,None,time.time()))
   item["hydrate_type"]=type(h).__name__
  except Exception as e:item["hydrate_error"]=repr(e)
  await asyncio.sleep(1.5)
  try:
   r=await _maybe(_rpc("getTransaction",[s,{"encoding":"jsonParsed","commitment":"confirmed",
        "maxSupportedTransactionVersion":0}]))
   item["direct_rpc_type"]=type(r).__name__
   item["direct_rpc_null"]=r is None
  except Exception as e:item["direct_rpc_error"]=repr(e)
  out.append(item)
  if i+1<len(sigs):await asyncio.sleep(2.5)
 return rows,out

def run(root,max_samples=3):
 root=Path(root)
 s083=_read(root/S083) if (root/S083).exists() else ""
 o148=_read(root/O148) if (root/O148).exists() else ""
 rows,probes=asyncio.run(probe(root,max_samples))
 hydrate_none=sum(x["hydrate_type"]=="NoneType" for x in probes)
 rpc_ok=sum(x["direct_rpc_error"] is None and x["direct_rpc_type"]!="NoneType" for x in probes)
 rate_limits=sum("429" in str(x["hydrate_error"]) or "429" in str(x["direct_rpc_error"]) for x in probes)
 if rpc_ok and hydrate_none:
  finding="HYDRATE_WRAPPER_CONTRACT_MISMATCH"
 elif rate_limits:
  finding="PUBLIC_RPC_RATE_LIMIT_BLOCKING_HYDRATION"
 elif probes and all(x["direct_rpc_null"] for x in probes if x["direct_rpc_error"] is None):
  finding="TRANSACTION_READBACK_RETURNED_NULL"
 else:
  finding="HYDRATION_ROOT_CAUSE_REQUIRES_SOURCE_REPAIR"
 return {"revision":"USLS_106R","raw_record_count":len(rows),"probe_count":len(probes),
  "finding":finding,"rate_limit_probe_count":rate_limits,"probes":probes,
  "hydrate_source_excerpt":_func_excerpt(s083,"_hydrate"),
  "rpc_source_excerpt":_func_excerpt(o148,"_rpc"),
  "certification_claimed":False,"execution_authority":False,"read_only":True}

def write(root,max_samples=3):
 d=run(root,max_samples)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase5_hydration_contract_rate_limit_diagnostic.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_106r_scanner_hydration_contract_rate_limit_diagnostic import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_diag(self):
  p,d=write(ROOT,max_samples=3)
  print("[STATE]",json.dumps({"raw_record_count":d["raw_record_count"],"probe_count":d["probe_count"],
   "finding":d["finding"],"rate_limit_probe_count":d["rate_limit_probe_count"]},sort_keys=True))
  for x in d["probes"]:print("[PROBE]",json.dumps(x,sort_keys=True))
  print("[HYDRATE_SOURCE]")
  for x in d["hydrate_source_excerpt"]:print(x)
  print("[RPC_SOURCE]")
  for x in d["rpc_source_excerpt"]:print(x)
  self.assertGreater(d["raw_record_count"],0,"RAW_PROGRAM_ACTIVITY_EMPTY")
  self.assertGreater(d["probe_count"],0,"NO_SIGNATURES_FOR_DIAGNOSTIC")
  self.assertGreater(len(d["hydrate_source_excerpt"]),0,"HYDRATE_SOURCE_NOT_FOUND")
  self.assertGreater(len(d["rpc_source_excerpt"]),0,"RPC_SOURCE_NOT_FOUND")
  self.assertFalse(d["certification_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-106R hydration contract/rate-limit diagnostic")
  print("[PASS] no hydration certification claimed")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
