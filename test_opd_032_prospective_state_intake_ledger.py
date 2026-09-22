
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_032_prospective_state_intake_ledger import summary
s,p=summary(Path.cwd());assert p.exists() and s["states"]>=0 and s["all_post_freeze"]
print("[FILE]",p);print("[STATES]",s["states"]);print("[TRIGGER_STATES]",s["trigger_states"]);print("[UNIQUE_TICKERS]",s["unique_tickers"])
print("[PASS] OPD-032 prospective state intake ledger ready; only post-freeze states are admissible")
