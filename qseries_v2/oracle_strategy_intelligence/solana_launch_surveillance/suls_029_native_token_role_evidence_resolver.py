from __future__ import annotations
import json
def run(root):
 txd=json.loads((root/"runtime_state/solana_opportunities/launch_surveillance/exact_candidate_transaction.json").read_text(encoding="utf-8"))
 ixd=json.loads((root/"runtime_state/solana_opportunities/launch_surveillance/exact_instruction_accounts.json").read_text(encoding="utf-8"))
 ixmap={x["signature"]:x for x in ixd.get("rows",[])};rows=[]
 for t in txd.get("transactions",[]):
  e=t.get("envelope") or {};sig=e.get("signature");keys=(ixmap.get(sig) or {}).get("account_keys") or []
  pre=e.get("pre_token_balances") or [];post=e.get("post_token_balances") or [];balances=[]
  for b in post:
   idx=b.get("accountIndex") if isinstance(b,dict) else None
   if not isinstance(idx,int):continue
   pre_b=next((x for x in pre if isinstance(x,dict) and x.get("accountIndex")==idx),None)
   balances.append({"account_index":idx,"account":keys[idx] if idx<len(keys) else None,
    "mint":b.get("mint"),"owner":b.get("owner"),"program_id":b.get("programId"),
    "pre_ui":None if not pre_b else (pre_b.get("uiTokenAmount") or {}).get("uiAmountString"),
    "post_ui":(b.get("uiTokenAmount") or {}).get("uiAmountString")})
  target_accounts=sorted({a for x in (ixmap.get(sig) or {}).get("target_instructions",[]) for a in x.get("accounts",[]) if a})
  overlap=[b for b in balances if b.get("account") in target_accounts]
  rows.append({"signature":sig,"target_accounts":target_accounts,"target_token_balance_overlap":overlap,
   "distinct_mints":sorted({b["mint"] for b in overlap if b.get("mint")})})
 return {"revision":"SULS_029","rows":rows,"execution_authority":False}
def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_token_role_evidence.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
