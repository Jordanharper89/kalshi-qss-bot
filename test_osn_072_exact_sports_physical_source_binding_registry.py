from pathlib import Path
from qseries_v2.oracle_source_network.certification.exact_sports_physical_source_bindings import verify_bindings

root = Path.cwd()

assert (root / "test_osn_071_exact_sports_source_interface_inventory_NCAA_PATH_REPAIR.py").exists()

r = verify_bindings(root=root)
print("[BINDINGS]", r["admitted"])

for league, meta in r["discovery"].items():
    print(f"[DISCOVERY] {league} chosen={meta['chosen']}")
    for candidate in meta["candidates"]:
        print(f"  [CANDIDATE] {candidate}")

assert r["admitted"] == ("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL")
assert r["held"] == ("NCAAB", "MLB_CANONICAL_EVENT_EXTRACTION_CERT_REQUIRED")
assert r["blocked"] == ("UCL",)
assert r["execution_authority"] is False
assert len(r["bindings"]) == 6

for binding in r["bindings"]:
    assert (root / binding.test_file).exists(), binding
    assert binding.admitted is True
    assert binding.execution_authority is False

mls = next(b for b in r["bindings"] if b.league == "MLS")
assert "exact_query" in mls.test_file.lower()
assert "event_surface_physical_probe" not in mls.test_file.lower()

ncaaf = next(b for b in r["bindings"] if b.league == "NCAAF")
assert "scoreboard" in ncaaf.test_file.lower()
assert "extractor" in ncaaf.test_file.lower()

print("[PASS] repaired OSN-071 dependency verified")
print("[PASS] exact physical source tests discovered from current repo")
print("[PASS] repaired candidates preferred over stale variants")
print("[PASS] known failed bare MLS probe excluded")
print("[PASS] six admitted league bindings resolved")
print("[PASS] OSN-072 discovery rebuild certified")
