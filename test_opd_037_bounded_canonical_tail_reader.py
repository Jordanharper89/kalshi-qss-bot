
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_037_bounded_canonical_tail_reader import build
s,p=build(Path.cwd());assert p.exists() and s["bounded_sequence_query"] and not s["whole_table_aggregate_used"] and s["monotonic"]
print("[FILE]",p);print("[ROWS]",s["rows"]);print("[BOUNDED]",s["bounded_sequence_query"]);print("[MONOTONIC]",s["monotonic"]);print("[PASS] OPD-037 bounded canonical tail reader certified")
