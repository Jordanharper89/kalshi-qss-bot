from pathlib import Path
import ast

ROOT=Path.cwd().resolve()
P=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_live_full_evidence_fusion_predictor.py"
TEST=ROOT/"test_opd_FULL_EVIDENCE_PROSPECTIVE_REALIZED_EDGE_GATE_REBUILD.py"

if not P.exists():
    raise SystemExit(f"[FAIL] predictor missing: {P}")

src=P.read_text(encoding="utf-8")
if "REALTIME_TRADE_TICKER_ANCHOR_ROOT_V1" not in src:
    raise SystemExit("[FAIL] realtime family-anchor root cutover missing")
if "EXACT_CONTRACT_FAMILY_ROOT_CUTOVER_V1" not in src:
    raise SystemExit("[FAIL] exact contract-family root cutover missing")
if "PREDICTION_LEDGER_REVISION" not in src:
    raise SystemExit("[FAIL] immutable prediction ledger boundary missing")

tree=ast.parse(src)
fn=next((n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="_score_state"),None)
if fn is None:
    raise SystemExit("[FAIL] _score_state not found")
if "_score_state_preprospective" in src:
    raise SystemExit("[FAIL] prospective realized-edge gate already appears installed")

lines=src.splitlines(True)
header=lines[fn.lineno-1]
lines[fn.lineno-1]=header.replace("def _score_state(","def _score_state_preprospective(",1)
src="".join(lines)

GATE=r'''
PROSPECTIVE_EDGE_GATE_REVISION="PROSPECTIVE_REALIZED_EDGE_GATE_V1"
PROSPECTIVE_EDGE_MIN_N=12
PROSPECTIVE_EDGE_MIN_TICKERS=3
PROSPECTIVE_EDGE_Z=1.2815515655446004
PROSPECTIVE_EDGE_PROB_BIN=0.10
PROSPECTIVE_EDGE_AGREE_BIN=0.25

def _prospective_contract_family(ticker):
    u=str(ticker or "").upper()
    if u.startswith("KXBTC15M") or u.startswith("KXETH15M") or u.startswith("KXSOL15M"):
        return "CRYPTO_15M"
    if u.startswith("KXBTCD") or u.startswith("KXETHD") or u.startswith("KXSOLD"):
        return "CRYPTO_DAILY_THRESHOLD"
    if u.startswith("KXBTC-") or u.startswith("KXETH-") or u.startswith("KXSOL-"):
        return "CRYPTO_RANGE"
    if u.startswith("KXBTC") or u.startswith("KXETH") or u.startswith("KXSOL"):
        return "CRYPTO_OTHER"
    return "NON_CRYPTO"

def _prospective_bin(v,width):
    try:
        x=float(v)
    except Exception:
        return None
    x=max(0.0,min(1.0,x))
    return round(int(x/width)*width,6)

def _prospective_rows(root):
    p=Path(root)/"runtime"/"predictive_data"/"opd_full_evidence_live_outcome_ledger.jsonl"
    return _rows(p)

def _prospective_resolution_epoch(row):
    for k in ("resolution_epoch","resolved_epoch","outcome_resolved_epoch","materialized_epoch"):
        try:
            v=row.get(k)
            if v is not None:
                return float(v)
        except Exception:
            pass
    return None

def _prospective_segment_stats(score,root,cutoff_epoch):
    st=score.get("state") or {}
    asset=str(score.get("asset") or _asset(st.get("ticker")) or "")
    horizon=int(score.get("horizon_seconds") or 0)
    direction=str(score.get("direction") or "")
    family=_prospective_contract_family(st.get("ticker"))
    pbin=_prospective_bin(score.get("predicted_probability"),PROSPECTIVE_EDGE_PROB_BIN)
    abin=_prospective_bin(score.get("evidence_agreement"),PROSPECTIVE_EDGE_AGREE_BIN)

    eligible=[]
    for r in _prospective_rows(root):
        if r.get("resolution_status")!="RESOLVED_EXACT_FUTURE":
            continue
        resolved_at=_prospective_resolution_epoch(r)
        if resolved_at is None or resolved_at>float(cutoff_epoch):
            continue
        rticker=str(r.get("ticker") or "")
        if _asset(rticker)!=asset:
            continue
        try:
            if int(r.get("horizon_seconds") or -1)!=horizon:
                continue
        except Exception:
            continue
        if str(r.get("predicted_direction") or r.get("direction") or "")!=direction:
            continue
        if _prospective_contract_family(rticker)!=family:
            continue
        if _prospective_bin(r.get("predicted_probability"),PROSPECTIVE_EDGE_PROB_BIN)!=pbin:
            continue
        if _prospective_bin(r.get("evidence_agreement"),PROSPECTIVE_EDGE_AGREE_BIN)!=abin:
            continue
        try:
            dr=float(r.get("directional_return"))
        except Exception:
            continue
        eligible.append((r,dr-HURDLE))

    n=len(eligible)
    tickers=len({str(r.get("ticker") or "") for r,_ in eligible})
    vals=[v for _,v in eligible]
    mean=(sum(vals)/n) if n else None
    if n>=2:
        var=sum((v-mean)**2 for v in vals)/(n-1)
        sd=var**0.5
        se=sd/(n**0.5)
        lower=mean-PROSPECTIVE_EDGE_Z*se
    else:
        sd=se=lower=None
    positive=sum(1 for v in vals if v>0)
    return {
      "revision":PROSPECTIVE_EDGE_GATE_REVISION,
      "segment":{
        "asset":asset,"contract_family":family,"horizon_seconds":horizon,
        "direction":direction,"probability_bin":pbin,"agreement_bin":abin,
      },
      "n":n,"unique_tickers":tickers,"mean_net_after_2pct":mean,
      "net_stddev":sd,"net_standard_error":se,"lower_bound_net_after_2pct":lower,
      "positive_net_rate":(positive/n) if n else None,
      "strict_cutoff_epoch":float(cutoff_epoch),
    }

def _prospective_gate_apply(score,root=None):
    root=Path(root or Path.cwd()).resolve()
    st=score.get("state") or {}
    cutoff=float(st.get("observed_epoch") or 0.0)
    stats=_prospective_segment_stats(score,root,cutoff)
    ok=(
      stats["n"]>=PROSPECTIVE_EDGE_MIN_N and
      stats["unique_tickers"]>=PROSPECTIVE_EDGE_MIN_TICKERS and
      stats["lower_bound_net_after_2pct"] is not None and
      stats["lower_bound_net_after_2pct"]>0.0
    )
    score["prospective_realized_edge"]=stats
    score["checks"]["prospective_realized_edge"]=bool(ok)
    score["passed"]=all(score["checks"].values())
    return score

def _score_state(cur,states,outcomes,now):
    score=_score_state_preprospective(cur,states,outcomes,now)
    return _prospective_gate_apply(score,Path.cwd())
'''

marker="def _score_state_preprospective("
if marker not in src:
    raise SystemExit("[FAIL] renamed scorer marker missing")
src=src.replace(marker,GATE+"\n"+marker,1)

target="scores=[_score_state(x,states,outs,now) for x in current]"
replacement="scores=[_prospective_gate_apply(_score_state_preprospective(x,states,outs,now),root) for x in current]"
if target in src:
    src=src.replace(target,replacement,1)

compile(src,str(P),"exec")
P.write_text(src,encoding="utf-8")

TEST_SOURCE=r'''from pathlib import Path
import json,tempfile
import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as m

assert m.EXECUTION_AUTHORITY is False
assert m.PUBLICATION_ALLOWED is False
assert m.HURDLE==0.020
assert m.MIN_NET_EDGE==0.005
assert m.PROSPECTIVE_EDGE_GATE_REVISION=="PROSPECTIVE_REALIZED_EDGE_GATE_V1"
assert m.PROSPECTIVE_EDGE_MIN_N==12
assert m.PROSPECTIVE_EDGE_MIN_TICKERS==3

base_score={
 "state":{"ticker":"KXBTCD-NOW-T77000","observed_epoch":2000.0},
 "asset":"BTC","horizon_seconds":60,"direction":"DOWN",
 "predicted_probability":0.72,"evidence_agreement":1.0,
 "checks":{"fresh_state":True,"comparable_cases":True,"ticker_breadth":True,
           "mean_similarity":True,"direction_probability":True,"net_edge":True,
           "evidence_agreement":True},
 "passed":True,
}

def outcome(i,net,resolved=1900.0,ticker=None,prob=.72,agree=1.0):
    return {
      "prediction_id":f"P{i}","resolution_status":"RESOLVED_EXACT_FUTURE",
      "resolution_epoch":resolved,
      "ticker":ticker or f"KXBTCD-HIST{i%4}-T77000",
      "horizon_seconds":60,"predicted_direction":"DOWN",
      "predicted_probability":prob,"evidence_agreement":agree,
      "directional_return":0.02+net,
    }

with tempfile.TemporaryDirectory() as td:
    root=Path(td)
    p=root/"runtime"/"predictive_data"/"opd_full_evidence_live_outcome_ledger.jsonl"
    p.parent.mkdir(parents=True)

    rows=[outcome(i,.04 if i%3 else .02,ticker=f"KXBTCD-H{i%4}-T77000") for i in range(18)]
    rows.append(outcome(99,9.0,resolved=2100.0,ticker="KXBTCD-FUTURE-T77000"))
    p.write_text("\n".join(json.dumps(x) for x in rows)+"\n",encoding="utf-8")
    s=m._prospective_gate_apply(dict(base_score,checks=dict(base_score["checks"])),root)
    z=s["prospective_realized_edge"]
    assert z["n"]==18
    assert z["unique_tickers"]==4
    assert z["mean_net_after_2pct"]>0
    assert z["lower_bound_net_after_2pct"]>0
    assert s["checks"]["prospective_realized_edge"] is True
    assert s["passed"] is True

    rows=[outcome(i,-.015,ticker=f"KXBTCD-H{i%4}-T77000") for i in range(18)]
    p.write_text("\n".join(json.dumps(x) for x in rows)+"\n",encoding="utf-8")
    s=m._prospective_gate_apply(dict(base_score,checks=dict(base_score["checks"])),root)
    assert s["prospective_realized_edge"]["mean_net_after_2pct"]<0
    assert s["checks"]["prospective_realized_edge"] is False
    assert s["passed"] is False

    rows=[outcome(i,.05,ticker=f"KXBTCD-H{i%2}-T77000") for i in range(5)]
    p.write_text("\n".join(json.dumps(x) for x in rows)+"\n",encoding="utf-8")
    s=m._prospective_gate_apply(dict(base_score,checks=dict(base_score["checks"])),root)
    assert s["prospective_realized_edge"]["n"]==5
    assert s["checks"]["prospective_realized_edge"] is False

src=Path("qseries_v2/oracle_predictive_discovery/opd_live_full_evidence_fusion_predictor.py").read_text(encoding="utf-8")
assert "def _score_state_preprospective(" in src
assert 'PROSPECTIVE_EDGE_GATE_REVISION="PROSPECTIVE_REALIZED_EDGE_GATE_V1"' in src
assert '"prospective_realized_edge"' in src
assert "lower_bound_net_after_2pct" in src
assert "resolution_status" in src
assert "resolved_at>float(cutoff_epoch)" in src
assert "REALTIME_TRADE_TICKER_ANCHOR_ROOT_V1" in src
assert "EXACT_CONTRACT_FAMILY_ROOT_CUTOVER_V1" in src

print("[PASS] prospective realized-edge gate installed inside existing full-evidence scorer")
print("[PASS] exact resolved prospective outcomes are now a first-class actionability gate")
print("[PASS] horizon + direction + contract-family + probability + agreement regime matched")
print("[PASS] future-resolved rows are excluded by strict pre-anchor cutoff")
print("[PASS] positive mean alone is insufficient; conservative net lower bound must exceed zero")
print("[PASS] minimum 12 resolved cases across 3 tickers required")
print("[PASS] negative/sparse prospective economics force abstention")
print("[PASS] original 2pct hurdle and every existing evidence gate preserved")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
'''
TEST.write_text(TEST_SOURCE,encoding="utf-8")
compile(TEST_SOURCE,str(TEST),"exec")

print("[PASS] prospective realized-edge learning gate installed into existing predictor")
print("[TARGET] existing _score_state -> family ranking -> immutable prediction ledger")
print("[LEARNING SOURCE] exact resolved prospective outcome ledger only")
print("[ANTI-LEAKAGE] outcomes must be resolved before current anchor epoch")
print("[ECONOMICS] conservative lower-bound net after fixed 2pct hurdle must be > 0")
print("[MIN SUPPORT] 12 resolved cases / 3 unique tickers")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
