from pathlib import Path
import py_compile
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2"/"oracle_edge_discovery"
MOD=PKG/"oed_026_exact_chronological_validation_population.py"
TEST=ROOT/"test_oed_026_exact_chronological_validation_population.py"

MOD.write_text(r"""
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
import hashlib, json, re

EMBARGO_SECONDS=900

def _h(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def _mag(r):
    if r["detector_family"]=="CROSS_CONTRACT_DISPERSION":
        z=abs(float(r.get("initial_gap",0)))
        return "LT_20C" if z<.2 else ("20_TO_40C" if z<.4 else "GE_40C")
    z=abs(float(r.get("signal_return",0)))
    return "LT_5BP" if z<.0005 else ("5_TO_10BP" if z<.001 else "GE_10BP")

def build(root=None):
    root=Path(root or Path.cwd())
    frozen=json.loads((root/"runtime"/"edge_discovery"/"oed_025_validation_population_freeze.json").read_text())
    rows=json.loads((root/"runtime"/"edge_discovery"/"oed_022_independent_event_population.json").read_text())["rows"]
    labels=json.loads((root/"runtime"/"edge_discovery"/"oed_017_post_anomaly_path_labels.json").read_text())["events"]

    anchor={x["event_id"]:x.get("anchor_epoch") for x in labels if x.get("anchor_epoch") is not None}
    eligible={(x["detector_family"],x["family_key"],int(x["horizon_seconds"]),x["magnitude_bucket"]) for x in frozen["validation_candidates"]}

    groups=defaultdict(list)
    missing_anchor=0
    for r in rows:
        k=(r["detector_family"],r["family_key"],int(r["horizon_seconds"]),_mag(r))
        if k not in eligible:
            continue
        ts=anchor.get(r["event_id"])
        if ts is None:
            missing_anchor+=1
            continue
        tickers=sorted(r.get("tickers") or ([r["ticker"]] if r.get("ticker") else []))
        rr={**r,"anchor_epoch":float(ts),"anchor_utc":datetime.fromtimestamp(float(ts),timezone.utc).isoformat(),
            "calendar_day_utc":datetime.fromtimestamp(float(ts),timezone.utc).strftime("%Y-%m-%d"),
            "ticker_set":tickers,"condition_key":"|".join(map(str,k))}
        groups[k].append(rr)

    out=[]
    for k,rs in sorted(groups.items()):
        rs.sort(key=lambda x:(x["anchor_epoch"],x["event_id"]))
        if len(rs)<20:
            continue
        cut=max(1,min(len(rs)-1,int(len(rs)*0.70)))
        raw_train=rs[:cut]; raw_test=rs[cut:]
        train_end=raw_train[-1]["anchor_epoch"]
        test=[x for x in raw_test if x["anchor_epoch"]>train_end+EMBARGO_SECONDS]
        train_days=sorted(set(x["calendar_day_utc"] for x in raw_train))
        test=[x for x in test if x["calendar_day_utc"] not in set(train_days)]
        status="READY" if len(test)>=5 else "HOLD_INSUFFICIENT_ISOLATED_TEST"
        out.append({"condition_key":"|".join(map(str,k)),"detector_family":k[0],"family_key":k[1],
                    "horizon_seconds":k[2],"magnitude_bucket":k[3],"total_rows":len(rs),
                    "train_rows":raw_train,"test_rows":test,"train_n":len(raw_train),"test_n":len(test),
                    "train_days":train_days,"test_days":sorted(set(x["calendar_day_utc"] for x in test)),
                    "split":"CHRONOLOGICAL_70_30_PLUS_900S_EMBARGO_PLUS_UNSEEN_UTC_DAY","status":status})

    payload={"schema_version":"OED-026","created_at":datetime.now(timezone.utc).isoformat(),
             "source_freeze_hash":frozen["freeze_hash"],"conditions":out,"condition_count":len(out),
             "ready_count":sum(x["status"]=="READY" for x in out),"missing_anchor_rows":missing_anchor,
             "embargo_seconds":EMBARGO_SECONDS,"random_split_used":False,"population_hash":_h(out),
             "edge_proven":False,"probability_enabled":False,"direction_enabled":False,
             "publication_allowed":False,"execution_authority":False}
    p=root/"runtime"/"edge_discovery"/"oed_026_chronological_validation_population.json"
    p.write_text(json.dumps(payload,sort_keys=True,indent=2),encoding="utf-8")
    return payload,p
""",encoding="utf-8")

TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_edge_discovery.oed_026_exact_chronological_validation_population import build
s,p=build(Path.cwd())
assert p.exists() and s["condition_count"]>0 and s["random_split_used"] is False
for c in s["conditions"]:
    if c["test_rows"]:
        assert max(x["anchor_epoch"] for x in c["train_rows"])+s["embargo_seconds"] < min(x["anchor_epoch"] for x in c["test_rows"])
        assert set(c["train_days"]).isdisjoint(set(c["test_days"]))
print("[FILE]",p)
print("[CONDITIONS]",s["condition_count"])
print("[READY]",s["ready_count"])
print("[MISSING_ANCHOR_ROWS]",s["missing_anchor_rows"])
print("[POPULATION_HASH]",s["population_hash"])
for c in s["conditions"][:25]:
    print(" ",{k:c[k] for k in ("condition_key","total_rows","train_n","test_n","train_days","test_days","status")})
print("[PASS] chronological train-before-test enforced")
print("[PASS] 900-second embargo enforced")
print("[PASS] unseen UTC-day isolation enforced")
print("[PASS] OED-026 exact chronological validation population certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True); py_compile.compile(str(TEST),doraise=True)
print("[PASS] OED-026 installer complete")
