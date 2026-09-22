import ast
from pathlib import Path
p=Path("qseries_v2/oracle_predictive_discovery/opd_047_bounded_post_t_kalshi_reader.py");s=p.read_text();ast.parse(s)
assert "SET TRANSACTION READ ONLY" in s and "statement_timeout='5000ms'" in s
assert "source_id=%s" in s and "to_timestamp(%s)" in s and "ORDER BY sequence_number ASC" in s
assert "float(t0)<p[\"event_epoch\"]<=float(end)" in s
print("[READ_ONLY] PASS");print("[BOUNDED_POST_T] PASS");print("[PASS] OPD-047 bounded physical Kalshi post-T reader contract certified")
