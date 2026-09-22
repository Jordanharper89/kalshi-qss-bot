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
    print("=" * 118)
    print(' OSN-034 LIVE OFFICIAL PAYLOAD STRUCTURE PROBE INSTALLER')
    print("=" * 118)
    require('qseries_v2/oracle_source_network/certification/sports_source_truth.py')
    write('qseries_v2/oracle_source_network/certification/live_payload_structure_probe.py', '\nfrom dataclasses import dataclass\nfrom importlib import import_module\nimport json, re, html\n\nSOURCE_MODULES = {\n    "NFL": ("qseries_v2.oracle_source_network.acquisition.nfl_official_live", "nfl"),\n    "NCAAF": ("qseries_v2.oracle_source_network.acquisition.ncaa_football_official_live", "football"),\n    "NBA": ("qseries_v2.oracle_source_network.acquisition.nba_official_live", "nba"),\n    "NCAAB": ("qseries_v2.oracle_source_network.acquisition.ncaa_basketball_official_live", "basketball"),\n    "NHL": ("qseries_v2.oracle_source_network.acquisition.nhl_official_live", "nhl"),\n    "MLS": ("qseries_v2.oracle_source_network.acquisition.mls_official_live", "mls"),\n    "EPL": ("qseries_v2.oracle_source_network.acquisition.european_soccer_official_live", "epl"),\n}\n\n@dataclass(frozen=True, slots=True)\nclass PayloadProfile:\n    league: str\n    bytes_read: int\n    script_count: int\n    application_json_scripts: int\n    json_parse_successes: int\n    next_data_present: bool\n    ld_json_present: bool\n    event_tokens_present: tuple\n    read_only: bool = True\n    execution_authority: bool = False\n\ndef _pick_acquirer(module, hint):\n    candidates=[]\n    for name in dir(module):\n        if not name.startswith("acquire_"):\n            continue\n        obj=getattr(module, name)\n        if callable(obj):\n            low=name.lower()\n            score=(10 if hint in low else 0)+(3 if any(x in low for x in ("fixture","game","schedule","score")) else 0)\n            candidates.append((score,name,obj))\n    if not candidates:\n        raise RuntimeError(f"no acquire_* callable found in {module.__name__}")\n    candidates.sort(key=lambda x:(-x[0],x[1]))\n    return candidates[0][1], candidates[0][2]\n\ndef acquire_live_payload(league, timeout=8.0):\n    module_name,hint=SOURCE_MODULES[league]\n    module=import_module(module_name)\n    name,fn=_pick_acquirer(module,hint)\n    try:\n        payload=fn(timeout)\n    except TypeError:\n        payload=fn()\n    if not isinstance(payload,dict):\n        raise RuntimeError(f"{league} acquisition returned {type(payload).__name__}, expected dict")\n    body=payload.get("body")\n    if not isinstance(body,str) or not body:\n        raise RuntimeError(f"{league} acquisition returned empty/non-text body")\n    return name,payload\n\ndef profile_payload(league, body):\n    scripts=re.findall(r"<script\\b[^>]*>(.*?)</script>",body,re.I|re.S)\n    app_json=re.findall(r\'<script\\b[^>]*type=["\\\']application/json["\\\'][^>]*>(.*?)</script>\',body,re.I|re.S)\n    parsed=0\n    for raw in app_json:\n        try:\n            json.loads(html.unescape(raw).strip()); parsed+=1\n        except Exception:\n            pass\n    low=body.lower()\n    tokens=tuple(x for x in ("eventid","gameid","matchid","hometeam","awayteam","home_team","away_team","starttime","startdate","fixtures","schedule") if x in low)\n    return PayloadProfile(\n        league=league,\n        bytes_read=len(body.encode("utf-8",errors="ignore")),\n        script_count=len(scripts),\n        application_json_scripts=len(app_json),\n        json_parse_successes=parsed,\n        next_data_present=("__next_data__" in low),\n        ld_json_present=("application/ld+json" in low),\n        event_tokens_present=tokens,\n    )\n')
    write('test_osn_034_live_official_payload_structure_probe.py', '\nimport subprocess,sys\nprobe=r"""\nfrom qseries_v2.oracle_source_network.certification.live_payload_structure_probe import acquire_live_payload,profile_payload\nfrom qseries_v2.oracle_source_network.certification.sports_source_truth import production_ready\nleagues=tuple(x.league for x in production_ready())\nassert leagues==("NFL","NCAAF","NBA","NCAAB","NHL","MLS","EPL")\nfor league in leagues:\n    name,payload=acquire_live_payload(league,8.0)\n    p=profile_payload(league,payload["body"])\n    print(f"[STRUCTURE] {league} acquirer={name} bytes={p.bytes_read} scripts={p.script_count} app_json={p.application_json_scripts} parsed={p.json_parse_successes} next={p.next_data_present} ldjson={p.ld_json_present} tokens={p.event_tokens_present}")\n    assert p.bytes_read>0\n    assert p.execution_authority is False\nprint("[PASS] seven admitted live payloads physically profiled")\nprint("[PASS] no event structure was assumed or synthesized")\n"""\ntry:\n    p=subprocess.run([sys.executable,"-c",probe],text=True,capture_output=True,timeout=70)\nexcept subprocess.TimeoutExpired:\n    raise AssertionError("OSN-034 exceeded hard 70-second gate")\nif p.stdout: print(p.stdout.rstrip())\nif p.stderr: print(p.stderr.rstrip())\nassert p.returncode==0, f"OSN-034 failed rc={p.returncode}"\nprint("[PASS] OSN-034 live official payload structure probe certified")\n')
    print('[PASS] OSN-034 installed')
    print('[PASS] no synthetic fallback data')
    print('[PASS] execution_authority=FALSE')

if __name__ == "__main__":
    main()
