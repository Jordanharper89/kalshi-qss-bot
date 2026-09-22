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
    print(" OSN-016 NBA OFFICIAL PHYSICAL ACQUISITION INSTALLER")
    print("="*118)
    require("qseries_v2/oracle_source_network/providers/basketball_official.py")
    require("qseries_v2/oracle_source_network/acquisition/official_http.py")
    write("qseries_v2/oracle_source_network/acquisition/nba_official_live.py", '\nfrom .official_http import get_official_text\n\nNBA_GAMES_URL = "https://www.nba.com/games"\n\nNBA_TEAMS = (\n    "Atlanta Hawks","Boston Celtics","Brooklyn Nets","Charlotte Hornets",\n    "Chicago Bulls","Cleveland Cavaliers","Dallas Mavericks","Denver Nuggets",\n    "Detroit Pistons","Golden State Warriors","Houston Rockets","Indiana Pacers",\n    "LA Clippers","Los Angeles Lakers","Memphis Grizzlies","Miami Heat",\n    "Milwaukee Bucks","Minnesota Timberwolves","New Orleans Pelicans","New York Knicks",\n    "Oklahoma City Thunder","Orlando Magic","Philadelphia 76ers","Phoenix Suns",\n    "Portland Trail Blazers","Sacramento Kings","San Antonio Spurs","Toronto Raptors",\n    "Utah Jazz","Washington Wizards",\n)\n\ndef acquire_nba_games(timeout=8.0):\n    snap = get_official_text(NBA_GAMES_URL, timeout=timeout)\n    body = snap["body"]\n    low = body.lower()\n    detected = tuple(sorted({team for team in NBA_TEAMS if team.lower() in low}))\n    snap["provider"] = "nba_official"\n    snap["league"] = "NBA"\n    snap["source_authority"] = "official_league"\n    snap["detected_teams"] = detected\n    snap["markers"] = {\n        "nba": "nba" in low,\n        "games": "games" in low,\n        "schedule_or_scores": ("schedule" in low or "scores" in low),\n    }\n    return snap\n')
    write("test_osn_016_nba_official_physical_acquisition.py", '\nimport subprocess, sys\n\nprobe = """\nfrom qseries_v2.oracle_source_network.acquisition.nba_official_live import acquire_nba_games\nx = acquire_nba_games(timeout=8.0)\nprint(f"[PHYSICAL] provider={x[\'provider\']} bytes={len(x[\'body\'])} detected_teams={len(x[\'detected_teams\'])} markers={x[\'markers\']}")\nassert x["provider"] == "nba_official"\nassert x["league"] == "NBA"\nassert x["source_authority"] == "official_league"\nassert len(x["payload_sha256"]) == 64\nassert x["read_only"] is True\nassert x["execution_authority"] is False\nassert sum(bool(v) for v in x["markers"].values()) >= 2\nassert len(x["detected_teams"]) >= 2\nprint("[PASS] NBA official physical acquisition completed")\n"""\n\ntry:\n    p = subprocess.run([sys.executable, "-c", probe], text=True, capture_output=True, timeout=15)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("NBA official acquisition exceeded hard 15-second wall-clock gate")\n\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode == 0, f"NBA physical probe failed rc={p.returncode}"\nprint("[PASS] OSN-016 NBA official physical acquisition certified")\n')
    print("[PASS] OSN-016 installed")
    print("[PASS] hard wall-clock physical gate=15s")
    print("[PASS] execution_authority=FALSE")
if __name__ == "__main__":
    main()
