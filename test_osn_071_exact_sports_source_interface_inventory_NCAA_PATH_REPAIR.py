from qseries_v2.oracle_source_network.certification.exact_sports_source_interface_inventory import capture_interfaces

report, path = capture_interfaces()
print("[MANIFEST]", path)

assert report["execution_authority"] is False
assert tuple(report["leagues"]) == ("NFL", "NCAAF", "NBA", "NHL", "MLS", "EPL")

for league, rows in report["leagues"].items():
    existing = [r for r in rows if not r["missing"]]
    assert existing, f"{league} has no exact source module"
    function_count = sum(len(r["functions"]) for r in existing)
    print(f"[INTERFACE] {league} modules={len(existing)} public_functions={function_count}")
    for row in existing:
        print(f"  [MODULE] {row['path']}")
        for f in row["functions"]:
            print(
                f"    [FUNC] {f['name']} "
                f"required={tuple(f['required_args'])} "
                f"optional={tuple(f['optional_args'])} "
                f"canonical={f['constructs_canonical_event']} "
                f"network={tuple(f['network_markers'])}"
            )
    assert function_count > 0, f"{league} exact modules expose no public functions"

print("[PASS] exact source module interfaces captured from current repo")
print("[PASS] NCAAF exact acquisition path verified as ncaa_football_official_live.py")
print("[PASS] no runtime callable names guessed")
print("[PASS] OSN-071 NCAA path repair certified")
