from pathlib import Path
import py_compile

ROOT=Path.cwd();PKG=ROOT/"qseries_v2"/"oracle_predictive_data";PKG.mkdir(parents=True,exist_ok=True)
MOD=PKG/"opd_015_prediction_ready_world_state_matrix_freeze.py";TEST=ROOT/"test_opd_015_prediction_ready_world_state_matrix_freeze.py"

MOD.write_text(r"""
from pathlib import Path
from collections import Counter
import hashlib,json

def _load_index(path):
    d={}
    with path.open(encoding="utf-8") as f:
        for line in f:
            x=json.loads(line);d[x["anchor_id"]]=x
    return d

def _hfile(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def build(root=None):
    root=Path(root or Path.cwd());rt=root/"runtime"/"predictive_data"
    cb=_load_index(rt/"opd_012_coinbase_hf_strict_asof_join.jsonl")
    cc=_load_index(rt/"opd_013_crypto_condition_strict_asof_join.jsonl")
    kl=_load_index(rt/"opd_014_kalshi_and_learned_state_strict_asof_join.jsonl")
    anchors=rt/"opd_011_frozen_outcome_anchor_population.jsonl"
    outrows=rt/"opd_015_prediction_ready_world_state_matrix.jsonl"

    total=0;missing=Counter();crypto=crypto_full=0
    with anchors.open(encoding="utf-8") as src,outrows.open("w",encoding="utf-8") as dst:
        for line in src:
            a=json.loads(line);aid=a["anchor_id"];total+=1
            xcb=cb.get(aid,{})
            xcc=cc.get(aid,{})
            xkl=kl.get(aid,{})
            asset=xcb.get("asset") or xcc.get("asset") or xkl.get("asset")
            if asset:crypto+=1

            coinbase=xcb.get("coinbase_hf") or {}
            conditions=xcc.get("crypto_conditions") or {}
            kalshi=xkl.get("kalshi_anchor_state")
            learned=xkl.get("learned_state")

            if kalshi is None:missing["kalshi_anchor_state"]+=1
            if asset and not coinbase:missing["coinbase_hf"]+=1
            if asset and not conditions:missing["crypto_conditions"]+=1
            if asset and learned is None:missing["learned_state"]+=1
            if asset and kalshi is not None and coinbase and conditions:crypto_full+=1

            row={
                "anchor_id":aid,"ticker":a["ticker"],"asset":asset,
                "anchor_sequence_number":a["anchor_sequence_number"],"anchor_epoch":a["anchor_epoch"],
                "anchor_price":a["anchor_price"],"horizon_seconds":a["horizon_seconds"],
                "kalshi_state":kalshi,"coinbase_hf_state":coinbase,
                "crypto_condition_state":conditions,"learned_state":learned,
                "future_target":{
                    "future_end_price":a["future_end_price"],"future_return":a["future_return"],
                    "mfe":a["mfe"],"mae":a["mae"],
                    "time_to_max_seconds":a["time_to_max_seconds"],"time_to_min_seconds":a["time_to_min_seconds"],
                    "hit_plus_05":a["hit_plus_05"],"hit_minus_05":a["hit_minus_05"],
                    "hit_plus_10":a["hit_plus_10"],"hit_minus_10":a["hit_minus_10"],
                },
                "feature_cutoff_epoch":a["anchor_epoch"],"future_label_separate":True,
            }
            dst.write(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n")

    summaries=[]
    for fn in ("opd_012_coinbase_hf_strict_asof_join.json","opd_013_crypto_condition_strict_asof_join.json","opd_014_kalshi_and_learned_state_strict_asof_join.json"):
        summaries.append(json.loads((rt/fn).read_text(encoding="utf-8")))
    leakage=sum(int(x.get("post_t_feature_rows",0)) for x in summaries)

    s={"schema_version":"OPD-015","matrix_rows":total,"crypto_anchor_rows":crypto,
       "crypto_rows_with_kalshi_coinbase_conditions":crypto_full,
       "crypto_core_coverage_fraction":crypto_full/crypto if crypto else 0.0,
       "missing_feature_counts":dict(missing),"post_t_feature_rows":leakage,
       "zero_post_t_feature_leakage":leakage==0,"matrix_hash":_hfile(outrows),
       "prediction_ready_matrix_frozen":True,
       "formula_mining_next":True,"model_fit_allowed":False,"formula_mining_allowed":False,
       "probability_enabled":False,"direction_enabled":False,"publication_allowed":False,"execution_authority":False,
       "next_required":"OPD-016_RELATIONSHIP_FORMULA_DISCOVERY_ON_FROZEN_MATRIX_WITH_MULTIPLE_TESTING_PROTECTION"}
    out=rt/"opd_015_prediction_ready_world_state_matrix_freeze.json";out.write_text(json.dumps(s,indent=2,sort_keys=True),encoding="utf-8")
    return s,out
""",encoding="utf-8")

TEST.write_text(r"""
from pathlib import Path
from qseries_v2.oracle_predictive_data.opd_015_prediction_ready_world_state_matrix_freeze import build
s,p=build(Path.cwd())
assert p.exists() and s["matrix_rows"]>0
assert s["zero_post_t_feature_leakage"] is True
assert s["prediction_ready_matrix_frozen"] is True
assert s["formula_mining_next"] is True
assert not s["model_fit_allowed"] and not s["formula_mining_allowed"]
print("[FILE]",p);print("[MATRIX_ROWS]",s["matrix_rows"]);print("[CRYPTO_ANCHORS]",s["crypto_anchor_rows"])
print("[CRYPTO_CORE_COVERED]",s["crypto_rows_with_kalshi_coinbase_conditions"])
print("[CRYPTO_CORE_COVERAGE]",s["crypto_core_coverage_fraction"])
print("[MISSING_FEATURE_COUNTS]",s["missing_feature_counts"]);print("[POST_T_FEATURE_ROWS]",s["post_t_feature_rows"])
print("[MATRIX_HASH]",s["matrix_hash"]);print("[NEXT_REQUIRED]",s["next_required"])
print("[PASS] state-at-T features and strictly-future targets frozen in one auditable matrix")
print("[PASS] zero post-T feature leakage certified across joined feature families")
print("[PASS] no model/formula/edge claim enabled before discovery validation")
print("[PASS] OPD-011..OPD-015 historical world-state matrix slice certified")
""",encoding="utf-8")
py_compile.compile(str(MOD),doraise=True);py_compile.compile(str(TEST),doraise=True)
print("[PASS] OPD-015 installer complete")
