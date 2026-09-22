
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_021_family_condition_outcome_cohort import build
s,p=build(Path.cwd()); assert s["row_count"]>0 and s["family_identity_physical"] and not s["edge_proven"]
print("[COHORT]",p); print("[ROWS]",s["row_count"]); print("[HASH]",s["cohort_hash"])
from collections import Counter
print("[TOP_FAMILIES]",Counter(x["family_key"] for x in s["rows"]).most_common(25))
print("[PASS] OED-021 family-conditioned outcome cohort certified")
