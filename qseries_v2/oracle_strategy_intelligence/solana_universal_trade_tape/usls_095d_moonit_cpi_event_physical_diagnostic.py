from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
ALPH="123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MOON="MoonCVVNZFSYkqNXP6bxHLPL6QQJiMagDL3qcqUQTrG"
CPI="e445a52e51cb9a1d"
TRADE="e445a52e51cb9a1dbddb7fd34ee661ee"
def b58d(s):
 n=0
 for c in s:n=n*58+ALPH.index(c)
 b=n.to_bytes((n.bit_length()+7)//8,"big") if n else b""
 return b"\0"*(len(s)-len(s.lstrip("1")))+b
def keys(tx):
 m=((tx or {}).get("transaction") or {}).get("message") or {}
 ks=[x.get("pubkey") if isinstance(x,dict) else x for x in m.get("accountKeys") or []]
 la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
 return ks+(la.get("writable") or [])+(la.get("readonly") or [])
def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((b/"remaining_venue_exact_account_roles.json").read_text(encoding="utf-8"))
 rows=[];prefix=Counter();programs=Counter()
 for x in src["rows"]:
  if x["venue"]!="MOONIT":continue
  tx=x["transaction"];ks=keys(tx)
  for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
   for j,ix in enumerate(g.get("instructions") or []):
    pid=ix.get("programId")
    if not pid and isinstance(ix.get("programIdIndex"),int) and ix["programIdIndex"]<len(ks):pid=ks[ix["programIdIndex"]]
    programs[str(pid)]+=1
    if not ix.get("data"):continue
    try:raw=b58d(ix["data"])
    except Exception:continue
    h=raw[:16].hex();prefix[h]+=1
    if pid==MOON or h.startswith(CPI) or h.startswith(TRADE):
     rows.append({"signature":x["signature"],"trade_side":x["side"],"group_index":g.get("index"),
      "inner_ordinal":j,"program_id":pid,"data_len":len(raw),"prefix16_hex":h,
      "account_count":len(ix.get("accounts") or [])})
 return {"revision":"USLS_095D","candidate_rows":rows,"candidate_count":len(rows),
  "top_prefixes":prefix.most_common(20),"top_programs":programs.most_common(20),
  "execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/moonit_cpi_event_physical_diagnostic.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
