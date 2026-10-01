from __future__ import annotations
RULE={"family":"PUMP_SWAP","feature":"first_price","op":"LT","threshold":4.326921673424848e-07}
def match(first_price):
 try:return float(first_price)<RULE["threshold"]
 except Exception:return False
def contract():
 return {"revision":"SSR_026","rule":RULE,"source":"SSR_025_HELDOUT_POSITIVE_PUMPSWAP_RULE",
  "heldout_est_net_reference":0.08548642124900678,"heldout_match_count_reference":1,
  "goal":"ACCUMULATE_NEW_PROSPECTIVE_MATCHES_ONLY","profitability_claimed":False,
  "execution_authority":False,"read_only":True}
