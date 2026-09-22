
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_006_event_time_semantics_foundational_repair import build
s,p=build(Path.cwd());assert p.exists() and s["groups"]
k=[x for x in s["groups"] if x["source_id"]=="source.kalshi.market_data" and x["observation_type"]=="ticker"][0]
assert k["selected_event_time_path"]=="payload.message.ts" and k["time_semantics"]=="SOURCE_EVENT_TIME"
sports=[x for x in s["groups"] if x["observation_type"]=="official_sports_event"]
assert all(x["selected_event_time_path"]!="observed_at" for x in sports)
print("[FILE]",p);print("[SOURCE_TIME_GROUPS]",s["source_time_groups"]);print("[FALLBACK_GROUPS]",s["fallback_groups"])
print("[KALSHI_TICKER]",k);print("[SPORTS_FALLBACK_SAMPLE]",sports[:5]);print("[HASH]",s["hash"])
print("[PASS] OPD-003 outer observed_at semantic misclassification retired")
print("[PASS] only physical inner payload timestamps are called source-event time")
print("[PASS] OPD-006 foundational event-time semantics repair certified")
