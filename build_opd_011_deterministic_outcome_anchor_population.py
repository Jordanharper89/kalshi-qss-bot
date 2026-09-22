from pathlib import Path
import py_compile

ROOT=Path.cwd(); PKG=ROOT/"qseries_v2"/"oracle_predictive_data"; PKG.mkdir(parents=True,exist_ok=True)
MOD=PKG/"opd_011_deterministic_outcome_anchor_population.py"
TEST=ROOT/"test_opd_011_deterministic_outcome_anchor_population.py"

MOD.write_text(r"""
from pathlib import Path
import hashlib,json

def _h(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def build(root=None):
    root=Path(root or Path.cwd()); rt=root/"runtime"/"predictive_data"
    src=json.loads((rt/"opd_005_future_outcome_census.json").read_text(encoding="utf-8"))
    outcomes=list(src.get("outcomes") or [])
    if not outcomes: raise RuntimeError("NO_OPD005_OUTCOMES")

    anchors=[]
    for x in outcomes:
        row={
            "anchor_id":_h([x["ticker"],x["anchor_sequence_number"],x["anchor_epoch"],x["horizon_seconds"]]),
            "ticker":x["ticker"],
            "anchor_sequence_number":int(x["anchor_sequence_number"]),
            "anchor_epoch":float(x["anchor_epoch"]),
            "anchor_price":float(x["anchor_price"]),
            "horizon_seconds":int(x["horizon_seconds"]),
            "future_end_price":float(x["future_end_price"]),
            "future_return":float(x["future_return"]),
            "mfe":float(x["mfe"]),
            "mae":float(x["mae"]),
            "time_to_max_seconds":float(x["time_to_max_seconds"]),
            "time_to_min_seconds":float(x["time_to_min_seconds"]),
            "hit_plus_05":bool(x["hit_plus_05"]),
            "hit_minus_05":bool(x["hit_minus_05"]),
            "hit_plus_10":bool(x["hit_plus_10"]),
            "hit_minus_10":bool(x["hit_minus_10"]),
            "label_strictly_future":bool(x.get("label_strictly_future")),
        }
        anchors.append(row)

    anchors.sort(key=lambda x:(x["anchor_epoch"],x["ticker"],x["horizon_seconds"],x["anchor_sequence_number"]))
    if not all(x["label_strictly_future"] for x in anchors):
        raise RuntimeError("NON_FUTURE_LABEL_PRESENT")

    data=rt/"opd_011_frozen_outcome_anchor_population.jsonl"
    with data.open("w",encoding="utf-8") as f:
        for x in anchors:f.write(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n")

    s={
        "schema_version":"OPD-011","anchor_rows":len(anchors),
        "unique_anchor_ids":len({x["anchor_id"] for x in anchors}),
        "ticker_count":len({x["ticker"] for x in anchors}),
        "horizons":sorted({x["horizon_seconds"] for x in anchors}),
        "source_outcome_hash":src.get("outcome_hash"),
        "anchor_population_hash":_h(anchors),
        "target_population_frozen":True,"feature_join_performed":False,
        "model_fit_allowed":False,"formula_mining_allowed":False,
        "probability_enabled":False,"direction_enabled":False,
        "publication_allowed":False,"execution_authority":False,
    }
    out=rt/"opd_011_deterministic_outcome_anchor_population.json"
    out.write_text(json.dumps(s,indent=2,sort_keys=True),encoding="utf-8")
    return s,out
""",encoding="utf-8")

TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_011_deterministic_outcome_anchor_population import build
s,p=build(Path.cwd())
assert p.exists() and s["anchor_rows"]>0
assert s["anchor_rows"]==s["unique_anchor_ids"]
assert s["target_population_frozen"] and not s["feature_join_performed"]
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[ANCHOR_ROWS]",s["anchor_rows"]);print("[TICKERS]",s["ticker_count"])
print("[HORIZONS]",s["horizons"]);print("[ANCHOR_HASH]",s["anchor_population_hash"])
print("[PASS] exact OPD-005 outcome population frozen without feature filtering")
print("[PASS] target labels remain strictly future and immutable for downstream joins")
print("[PASS] OPD-011 deterministic outcome-anchor population certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True);py_compile.compile(str(TEST),doraise=True)
print("[PASS] OPD-011 installer complete")
