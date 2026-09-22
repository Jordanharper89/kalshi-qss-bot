from pathlib import Path
from qseries_v2.kalshi_sports_evidence_mapping.continuous_mapping_worker import run_worker_cycle
root=Path.cwd()
a=run_worker_cycle(root=root); b=run_worker_cycle(root=root)
print("[A]",a["total_rows"],a["counts"],a["content_hash"])
print("[B]",b["total_rows"],b["counts"],b["content_hash"])
assert a["total_rows"]>0 and b["total_rows"]>0
assert a["accounted_rows"]==a["total_rows"] and b["accounted_rows"]==b["total_rows"]
assert a["execution_authority"] is False and b["probability_enabled"] is False
assert (root/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem_worker_heartbeat.json").is_file()
print("[PASS] bounded production worker cycles completed with durable heartbeat")
print("[PASS] KSEM-071 certified")
