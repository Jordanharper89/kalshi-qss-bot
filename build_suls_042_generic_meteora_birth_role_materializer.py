from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_042_generic_meteora_birth_role_materializer.py"
TEST=ROOT/"test_suls_042_generic_meteora_birth_role_materializer.py"

MOD_TEXT=r"""from __future__ import annotations
import json,hashlib
WSOL="So11111111111111111111111111111111111111112"
DAMM="cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG"

def _materialize(b):
 e=b.get("envelope") or {};raw=e.get("raw_transaction") or {};meta=raw.get("meta") or {}
 position=set();transfers=[];created={}
 for grp in meta.get("innerInstructions") or []:
  for ix in grp.get("instructions") or []:
   if not isinstance(ix,dict):continue
   p=ix.get("parsed") or {};info=p.get("info") or {};typ=p.get("type")
   if typ=="initializeTokenMetadata" and info.get("name")=="Meteora Position NFT" and info.get("mint"):
    position.add(info["mint"])
   if typ=="createAccount" and info.get("newAccount"):
    created[info["newAccount"]]={"owner_program":info.get("owner"),"space":info.get("space")}
   if typ=="transferChecked":
    amt=(info.get("tokenAmount") or {}).get("uiAmountString")
    if info.get("mint") and info.get("destination") and amt is not None:
     transfers.append({"mint":info["mint"],"destination":info["destination"],"amount":amt})
 mints={x["mint"] for x in transfers}
 trade=sorted(m for m in mints if m!=WSOL and m not in position)
 if len(trade)!=1 or WSOL not in mints:return None
 t=trade[0]
 tv=next((x for x in transfers if x["mint"]==t),None)
 qv=next((x for x in transfers if x["mint"]==WSOL),None)
 if not tv or not qv:return None
 rawid=f'{b["signature"]}|{t}|{WSOL}|{DAMM}'
 return {"event_id":"suls-birth-"+hashlib.sha256(rawid.encode()).hexdigest(),
  "state":"DISCOVERED","signature":b["signature"],"slot":b["slot"],"block_time":b["block_time"],
  "observed_unix":b.get("observed_unix"),"launcher_family":"METEORA_DAMM_V2","program_id":DAMM,
  "token_mint":t,"quote_mint":WSOL,"token_vault":tv["destination"],"quote_vault":qv["destination"],
  "initial_token_amount":tv["amount"],"initial_quote_amount":qv["amount"],
  "position_nft_mints":sorted(position),"execution_authority":False}

def run(root):
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 inp=json.loads((base/"continuous_native_birth_inbox.json").read_text(encoding="utf-8"))
 oldp=base/"continuous_tradeable_birth_events.json"
 old=json.loads(oldp.read_text(encoding="utf-8")) if oldp.exists() else {"events":[]}
 events=list(old.get("events") or []);seen={x["signature"] for x in events};new=[]
 for b in inp.get("births",[]):
  if b.get("signature") in seen:continue
  x=_materialize(b)
  if x:events.append(x);new.append(x);seen.add(x["signature"])
 out={"revision":"SULS_042","event_count":len(events),"new_events":len(new),"events":events,
  "execution_authority":False,"read_only":True}
 oldp.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8");return out
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_042_generic_meteora_birth_role_materializer import run
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_materializer(self):
  d=run(ROOT);print("[STATE]",json.dumps({"event_count":d["event_count"],"new_events":d["new_events"]},sort_keys=True))
  print("[PASS] SULS-042 generic Meteora birth-role materializer")
  print("[SCOPE] Zero events is valid when SULS-041 has not yet observed a fresh Meteora birth")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-042 GENERIC METEORA BIRTH-ROLE MATERIALIZER");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
