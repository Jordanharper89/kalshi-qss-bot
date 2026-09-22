from __future__ import annotations
import ast,json
TOKENS=("websocket","subscribe","logsSubscribe","programSubscribe","blockSubscribe","slotSubscribe","signatureSubscribe","getBlock","getTransaction","getSignaturesForAddress","program_id","programid","instruction","transaction")
def audit(root):
 base=root/"qseries_v2/oracle_adapters/independent";rows=[]
 for p in base.glob("oad_*solana*.py"):
  text=p.read_text(encoding="utf-8",errors="ignore");low=text.lower();hits=sorted({t for t in TOKENS if t.lower() in low});funcs=[]
  try: funcs=[n.name for n in ast.walk(ast.parse(text)) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]
  except Exception: pass
  if hits: rows.append({"file":str(p.relative_to(root)),"hits":hits,"functions":funcs[:80]})
 return {"revision":"SULS_007","files_with_native_signals":len(rows),"rows":rows,"execution_authority":False}
def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_capability_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
