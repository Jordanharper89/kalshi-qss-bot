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
    print(" OSN-011 NFL OFFICIAL PHYSICAL ACQUISITION INSTALLER")
    print("="*118)
    require("qseries_v2/oracle_source_network/providers/football_official.py")
    write("qseries_v2/oracle_source_network/acquisition/official_http.py", '\nfrom urllib.request import Request, urlopen\nfrom datetime import datetime, timezone\nimport hashlib\n\nDEFAULT_TIMEOUT_SECONDS = 8.0\n\ndef utc_now_iso():\n    return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")\n\ndef get_official_text(url: str, timeout: float = DEFAULT_TIMEOUT_SECONDS):\n    timeout = float(timeout)\n    if timeout <= 0 or timeout > 20:\n        raise ValueError("timeout must be >0 and <=20 seconds")\n    req = Request(\n        url,\n        headers={\n            "User-Agent": "Mozilla/5.0 QSeries-Oracle-OSN/1.0",\n            "Accept": "text/html,application/xhtml+xml",\n            "Connection": "close",\n        },\n        method="GET",\n    )\n    with urlopen(req, timeout=timeout) as r:\n        status = getattr(r, "status", 200)\n        body = r.read().decode("utf-8", errors="replace")\n    if status != 200:\n        raise RuntimeError(f"HTTP status {status}")\n    if not body.strip():\n        raise RuntimeError("empty official source body")\n    return {\n        "url": url,\n        "observed_at": utc_now_iso(),\n        "body": body,\n        "payload_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),\n        "read_only": True,\n        "execution_authority": False,\n    }\n')
    write("qseries_v2/oracle_source_network/acquisition/nfl_official_live.py", '\nimport re\nfrom .official_http import get_official_text\n\nNFL_SCORES_URL = "https://www.nfl.com/scores"\n\nNFL_TEAMS = (\n    "Arizona Cardinals","Atlanta Falcons","Baltimore Ravens","Buffalo Bills",\n    "Carolina Panthers","Chicago Bears","Cincinnati Bengals","Cleveland Browns",\n    "Dallas Cowboys","Denver Broncos","Detroit Lions","Green Bay Packers",\n    "Houston Texans","Indianapolis Colts","Jacksonville Jaguars","Kansas City Chiefs",\n    "Las Vegas Raiders","Los Angeles Chargers","Los Angeles Rams","Miami Dolphins",\n    "Minnesota Vikings","New England Patriots","New Orleans Saints","New York Giants",\n    "New York Jets","Philadelphia Eagles","Pittsburgh Steelers","San Francisco 49ers",\n    "Seattle Seahawks","Tampa Bay Buccaneers","Tennessee Titans","Washington Commanders",\n)\n\ndef acquire_nfl_scores(timeout=8.0):\n    snap = get_official_text(NFL_SCORES_URL, timeout=timeout)\n    body = snap["body"]\n    detected = tuple(sorted({team for team in NFL_TEAMS if team.lower() in body.lower()}))\n    snap["provider"] = "nfl_official"\n    snap["league"] = "NFL"\n    snap["source_authority"] = "official_league"\n    snap["detected_teams"] = detected\n    return snap\n')
    write("test_osn_011_nfl_official_physical_acquisition.py", '\nimport subprocess, sys\n\nprobe = """\nfrom qseries_v2.oracle_source_network.acquisition.nfl_official_live import acquire_nfl_scores\nx = acquire_nfl_scores(timeout=8.0)\nprint(f"[PHYSICAL] provider={x[\'provider\']} bytes={len(x[\'body\'])} detected_teams={len(x[\'detected_teams\'])}")\nassert x["provider"] == "nfl_official"\nassert x["league"] == "NFL"\nassert x["source_authority"] == "official_league"\nassert len(x["payload_sha256"]) == 64\nassert x["read_only"] is True\nassert x["execution_authority"] is False\nassert len(x["detected_teams"]) >= 2\nprint("[PASS] NFL official physical acquisition completed")\n"""\n\ntry:\n    p = subprocess.run([sys.executable, "-c", probe], text=True, capture_output=True, timeout=15)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("NFL official acquisition exceeded hard 15-second wall-clock gate")\n\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode == 0, f"NFL physical probe failed rc={p.returncode}"\nprint("[PASS] OSN-011 NFL official physical acquisition certified")\n')
    print("[PASS] OSN-011 installed")
    print("[PASS] hard wall-clock physical gate=15s")
    print("[PASS] execution_authority=FALSE")
if __name__ == "__main__":
    main()
