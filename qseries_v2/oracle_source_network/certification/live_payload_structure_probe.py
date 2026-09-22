
from dataclasses import dataclass
from importlib import import_module
import json, re, html

SOURCE_MODULES = {
    "NFL": ("qseries_v2.oracle_source_network.acquisition.nfl_official_live", "nfl"),
    "NCAAF": ("qseries_v2.oracle_source_network.acquisition.ncaa_football_official_live", "football"),
    "NBA": ("qseries_v2.oracle_source_network.acquisition.nba_official_live", "nba"),
    "NCAAB": ("qseries_v2.oracle_source_network.acquisition.ncaa_basketball_official_live", "basketball"),
    "NHL": ("qseries_v2.oracle_source_network.acquisition.nhl_official_live", "nhl"),
    "MLS": ("qseries_v2.oracle_source_network.acquisition.mls_official_live", "mls"),
    "EPL": ("qseries_v2.oracle_source_network.acquisition.european_soccer_official_live", "epl"),
}

@dataclass(frozen=True, slots=True)
class PayloadProfile:
    league: str
    bytes_read: int
    script_count: int
    application_json_scripts: int
    json_parse_successes: int
    next_data_present: bool
    ld_json_present: bool
    event_tokens_present: tuple
    read_only: bool = True
    execution_authority: bool = False

def _pick_acquirer(module, hint):
    candidates=[]
    for name in dir(module):
        if not name.startswith("acquire_"):
            continue
        obj=getattr(module, name)
        if callable(obj):
            low=name.lower()
            score=(10 if hint in low else 0)+(3 if any(x in low for x in ("fixture","game","schedule","score")) else 0)
            candidates.append((score,name,obj))
    if not candidates:
        raise RuntimeError(f"no acquire_* callable found in {module.__name__}")
    candidates.sort(key=lambda x:(-x[0],x[1]))
    return candidates[0][1], candidates[0][2]

def acquire_live_payload(league, timeout=8.0):
    module_name,hint=SOURCE_MODULES[league]
    module=import_module(module_name)
    name,fn=_pick_acquirer(module,hint)
    try:
        payload=fn(timeout)
    except TypeError:
        payload=fn()
    if not isinstance(payload,dict):
        raise RuntimeError(f"{league} acquisition returned {type(payload).__name__}, expected dict")
    body=payload.get("body")
    if not isinstance(body,str) or not body:
        raise RuntimeError(f"{league} acquisition returned empty/non-text body")
    return name,payload

def profile_payload(league, body):
    scripts=re.findall(r"<script\b[^>]*>(.*?)</script>",body,re.I|re.S)
    app_json=re.findall(r'<script\b[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>',body,re.I|re.S)
    parsed=0
    for raw in app_json:
        try:
            json.loads(html.unescape(raw).strip()); parsed+=1
        except Exception:
            pass
    low=body.lower()
    tokens=tuple(x for x in ("eventid","gameid","matchid","hometeam","awayteam","home_team","away_team","starttime","startdate","fixtures","schedule") if x in low)
    return PayloadProfile(
        league=league,
        bytes_read=len(body.encode("utf-8",errors="ignore")),
        script_count=len(scripts),
        application_json_scripts=len(app_json),
        json_parse_successes=parsed,
        next_data_present=("__next_data__" in low),
        ld_json_present=("application/ld+json" in low),
        event_tokens_present=tokens,
    )
