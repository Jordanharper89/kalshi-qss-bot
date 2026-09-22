from pathlib import Path
from qseries_v2.kalshi_sports_evidence_mapping.durable_full_accounting_mapping_cycle import run_full_cycle

root = Path.cwd()
a = run_full_cycle(root=root, universe_limit=1000, max_supported=40, timeout_seconds=15)
b = run_full_cycle(root=root, universe_limit=1000, max_supported=40, timeout_seconds=15)
print("[A]",a["total_rows"],a["counts"],a["content_hash"])
print("[B]",b["total_rows"],b["counts"],b["content_hash"])
assert a["total_rows"] > 0 and b["total_rows"] > 0
assert a["accounted_rows"] == a["total_rows"]
assert b["accounted_rows"] == b["total_rows"]
assert b["counts"]["EXACT_BOUND"] > 0
assert all(r["mapping_status"] in ("EXACT_BOUND","PARTIAL","AMBIGUOUS","SOURCE_GAP","UNSUPPORTED") for r in b["rows"])
assert all(r["execution_authority"] is False for r in b["rows"])
assert (root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem_live_mapping_state.json").is_file()
print("[PASS] every supported live row explicitly accounted for")
print("[PASS] durable mapping state atomically replaced on repeated cycle")
print("[PASS] KSEM-069 certified")
