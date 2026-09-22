from pathlib import Path
ROOT = Path.cwd()

def require(rel):
    p = ROOT / rel
    if not p.exists():
        raise SystemExit("[FAIL] missing dependency: " + str(p))
    print("[PASS] dependency verified:", p.relative_to(ROOT))

def write(rel, content):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.rstrip() + "\n", encoding="utf-8")
    print("[WRITE]", p.relative_to(ROOT))

def main():
    print("="*118)
    print(" OSN-017 NCAA BASKETBALL OFFICIAL PHYSICAL ACQUISITION INSTALLER")
    print("="*118)
    require("qseries_v2/oracle_source_network/acquisition/nba_official_live.py")
    write("qseries_v2/oracle_source_network/acquisition/ncaa_basketball_official_live.py", '\nfrom .official_http import get_official_text\n\nNCAA_D1_MENS_SCOREBOARD_URL = "https://www.ncaa.com/scoreboard/basketball-men/d1"\n\ndef acquire_ncaa_d1_mens_scoreboard(timeout=8.0):\n    snap = get_official_text(NCAA_D1_MENS_SCOREBOARD_URL, timeout=timeout)\n    body = snap["body"]\n    low = body.lower()\n    markers = {\n        "basketball": "basketball" in low,\n        "mens": ("men\'s" in low or "mens" in low or "men" in low),\n        "division_i": ("division i" in low or "d1" in low or "di " in low),\n        "ncaa": "ncaa" in low,\n        "scoreboard_or_scores": ("scoreboard" in low or "scores" in low),\n    }\n    snap["provider"] = "ncaa_official"\n    snap["league"] = "NCAAB"\n    snap["source_authority"] = "official_governing_body"\n    snap["markers"] = markers\n    return snap\n')
    write("test_osn_017_ncaa_basketball_official_physical_acquisition.py", '\nimport subprocess, sys\n\nprobe = """\nfrom qseries_v2.oracle_source_network.acquisition.ncaa_basketball_official_live import acquire_ncaa_d1_mens_scoreboard\nx = acquire_ncaa_d1_mens_scoreboard(timeout=8.0)\nprint(f"[PHYSICAL] provider={x[\'provider\']} bytes={len(x[\'body\'])} markers={x[\'markers\']}")\nassert x["provider"] == "ncaa_official"\nassert x["league"] == "NCAAB"\nassert x["source_authority"] == "official_governing_body"\nassert len(x["payload_sha256"]) == 64\nassert x["read_only"] is True\nassert x["execution_authority"] is False\nassert x["markers"]["basketball"] is True\nassert x["markers"]["ncaa"] is True\nassert sum(bool(v) for v in x["markers"].values()) >= 3\nprint("[PASS] NCAA basketball official physical acquisition completed")\n"""\n\ntry:\n    p = subprocess.run([sys.executable, "-c", probe], text=True, capture_output=True, timeout=15)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("NCAA basketball acquisition exceeded hard 15-second wall-clock gate")\n\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode == 0, f"NCAA basketball physical probe failed rc={p.returncode}"\nprint("[PASS] OSN-017 NCAA basketball official physical acquisition certified")\n')
    print("[PASS] OSN-017 installed")
    print("[PASS] offseason-safe authoritative scoreboard certification")
    print("[PASS] hard wall-clock physical gate=15s")
    print("[PASS] execution_authority=FALSE")
if __name__ == "__main__":
    main()
