from pathlib import Path
from datetime import datetime,timezone
import importlib.util

R=Path.cwd()
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_013b_canonical_durable_prediction_ledger_rebuild import read_predictions
from qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import read_pinned_pool_history

base=R/"qseries_v2"/"oracle_adapters"/"independent"
hits=sorted(base.glob("oad_314*.py"))
assert hits,f"[FAIL] no physical OAD-314 module found under {base}"

oad314=None
for path in hits:
 spec=importlib.util.spec_from_file_location("slop040c_oad314",path)
 mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
 if hasattr(mod,"_price_for_pair"):
  oad314=(path,mod._price_for_pair);break

assert oad314,f"[FAIL] _price_for_pair absent from {[x.name for x in hits]}"
path314,price_for_pair=oad314
print("[OAD-314 PHYSICAL]",path314.name)

now=datetime.now(timezone.utc); eligible=[]
for p in read_predictions(R):
 try:
  f=datetime.fromisoformat(str(p.frozen_at).replace("Z","+00:00"))
  if (now-f).total_seconds()>=60: eligible.append(((now-f).total_seconds(),p,f))
 except Exception: pass
eligible.sort(key=lambda x:x[0],reverse=True)

print("[MATURE PREDICTIONS]",len(eligible))
for age,p,frozen in eligible[:15]:
 rows=list(read_pinned_pool_history(token_address=p.token_address,root=R,limit=512))
 after=[]; priced=[]
 for row in rows:
  raw=row.get("observed_at") or row.get("timestamp") or row.get("captured_at")
  try: t=datetime.fromisoformat(str(raw).replace("Z","+00:00"))
  except Exception: continue
  if t<=frozen: continue
  after.append(row)
  try: px=price_for_pair(row,p.pair_address)
  except Exception: px=None
  if px is not None: priced.append((t,px))

 print("\n[PREDICTION]",p.prediction_id)
 print(" token=",p.token_address)
 print(" frozen_pair=",p.pair_address)
 print(" age_seconds=",round(age,3))
 print(" history_rows=",len(rows))
 print(" post_freeze_token_rows=",len(after))
 print(" post_freeze_priced_pair_rows=",len(priced))
 if priced:
  print(" first_future_price=",priced[0])
  print(" last_future_price=",priced[-1])
  print(" state=EXACT_PAIR_PRICE_HISTORY_EXISTS")
 elif after: print(" state=TOKEN_HISTORY_EXISTS_BUT_FROZEN_PAIR_PRICE_MISSING")
 else: print(" state=POST_FREEZE_TOKEN_HISTORY_MISSING")

print("\n[PASS] physical frozen-pair diagnostic completed read-only")
print("[PASS] execution_authority=FALSE")