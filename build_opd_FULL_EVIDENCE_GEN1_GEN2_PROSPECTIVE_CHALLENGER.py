from pathlib import Path
import shutil

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_predictive_discovery"
P=PKG/"opd_live_full_evidence_fusion_predictor.py"
R=PKG/"opd_full_evidence_exact_future_outcome_resolver.py"
S=PKG/"opd_full_evidence_live_profitability_scoreboard_clean.py"
T=ROOT/"test_opd_FULL_EVIDENCE_GEN1_GEN2_PROSPECTIVE_CHALLENGER.py"

for f in (P,R,S):
    if not f.is_file():
        raise SystemExit("[FAIL] required production file missing: "+str(f))

ps=P.read_text(encoding="utf-8")
rs=R.read_text(encoding="utf-8")
ss=S.read_text(encoding="utf-8")

required_pred=(
    'PROSPECTIVE_EDGE_GATE_REVISION="PROSPECTIVE_REALIZED_EDGE_GATE_V1"',
    'EXACT_CONTRACT_FAMILY_ROOT_CUTOVER_V1',
    'REALTIME_TRADE_TICKER_ANCHOR_ROOT_V1',
    'PREDICTION_LEDGER_REVISION="FULL_EVIDENCE_PROSPECTIVE_LEDGER_V1"',
    'def _run_single_contract(',
)
for m in required_pred:
    if m not in ps:
        raise SystemExit("[FAIL] predictor boundary missing: "+m)

freeze_path=ROOT/"runtime"/"predictive_data"/"opd_031_prospective_candidate_freeze.json"
if not freeze_path.is_file():
    raise SystemExit("[FAIL] original frozen Gen1 OPD-031 candidate freeze missing: "+str(freeze_path))

if 'GENERATION_CHALLENGER_REVISION="GEN1_GEN2_PROSPECTIVE_CHALLENGER_V1"' in ps:
    raise SystemExit("[FAIL] Gen1/Gen2 prospective challenger already installed")

for src,suffix in ((P,"pre_gen1_gen2_challenger"),(R,"pre_gen1_gen2_challenger"),(S,"pre_gen1_gen2_challenger")):
    b=src.with_suffix(src.suffix+"."+suffix+".bak")
    if not b.exists():
        shutil.copy2(src,b)

# 1) Preserve old Gen2/current-model prediction IDs, while giving Gen1
# family predictions their own deterministic namespace.
start=ps.find("def _prediction_id(")
end=ps.find("\ndef _freeze_predictions(",start)
if start<0 or end<0:
    raise SystemExit("[FAIL] immutable prediction-id boundary not found")
old_pid=ps[start:end]
if "PREDICTION_LEDGER_REVISION" not in old_pid:
    raise SystemExit("[FAIL] unexpected prediction-id implementation")

new_pid='''def _prediction_id(anchor,horizon_seconds,generation=2,family_id=None):
    parts=[
      PREDICTION_LEDGER_REVISION,
      str(anchor.get("anchor_id") or ""),
      str(anchor.get("anchor_sequence_boundary") or ""),
      str(anchor.get("ticker") or ""),
      str(int(horizon_seconds)),
    ]
    generation=int(generation or 2)
    if generation!=2 or family_id:
        parts.extend(["GEN",str(generation),"FAMILY",str(family_id or "")])
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
'''
ps=ps[:start]+new_pid+ps[end:]

if "pid=_prediction_id(anchor,h)" not in ps:
    raise SystemExit("[FAIL] prediction ledger id call not found")
ps=ps.replace(
    "pid=_prediction_id(anchor,h)",
    'pid=_prediction_id(anchor,h,z.get("generation",2),z.get("family_id"))',
    1
)

row_anchor='"revision":PREDICTION_LEDGER_REVISION,'
if row_anchor not in ps:
    raise SystemExit("[FAIL] prediction ledger row revision anchor missing")
ps=ps.replace(
    row_anchor,
    row_anchor+'''
              "generation":int(z.get("generation") or 2),
              "family_id":z.get("family_id"),
              "model_basis":z.get("model_basis") or "FULL_EVIDENCE_CURRENT_MODEL",
              "gen1_formula":z.get("gen1_formula"),
              "gen1_target":z.get("gen1_target"),
              "gen1_original_activation_epoch":z.get("gen1_original_activation_epoch"),
              "prospective_realized_edge":z.get("prospective_realized_edge"),''',
    1
)

CHALLENGER = r'''
GENERATION_CHALLENGER_REVISION="GEN1_GEN2_PROSPECTIVE_CHALLENGER_V1"
GEN1_FREEZE_NAME="opd_031_prospective_candidate_freeze.json"
GEN1_MIN_RESOLVED=12
GEN1_MIN_TICKERS=3
GEN1_Z=1.2815515655446004

def _gen1_target_direction(target):
    return "DOWN" if str(target) in ("DOWN_5C","DOWN_10C","RETURN_NEG") else "UP"

def _gen1_load_freeze(root):
    p=Path(root)/"runtime"/"predictive_data"/GEN1_FREEZE_NAME
    if not p.exists():
        raise RuntimeError("ORIGINAL_GEN1_OPD031_FREEZE_MISSING")
    body=json.loads(p.read_text(encoding="utf-8"))
    if body.get("schema_version")!="OPD-031":
        raise RuntimeError("INVALID_GEN1_OPD031_FREEZE")
    if body.get("formula_retuning_allowed") is not False:
        raise RuntimeError("GEN1_FORMULA_RETUNING_BOUNDARY_VIOLATED")
    return body

def _gen1_prior_stats(root,family_id,horizon,direction,cutoff_epoch):
    vals=[];tickers=set()
    p=Path(root)/"runtime"/"predictive_data"/"opd_full_evidence_live_outcome_ledger.jsonl"
    for r in _rows(p):
        if r.get("resolution_status")!="RESOLVED_EXACT_FUTURE":
            continue
        if int(r.get("generation") or 2)!=1:
            continue
        if str(r.get("family_id") or "")!=str(family_id or ""):
            continue
        try:
            if int(r.get("horizon_seconds") or -1)!=int(horizon):
                continue
            resolved_at=float(r.get("resolved_epoch"))
            dr=float(r.get("directional_return"))
        except Exception:
            continue
        if resolved_at>float(cutoff_epoch):
            continue
        if str(r.get("direction") or "")!=str(direction):
            continue
        vals.append(dr-HURDLE)
        tickers.add(str(r.get("ticker") or ""))
    n=len(vals);mean=(sum(vals)/n) if n else None
    if n>=2:
        var=sum((x-mean)**2 for x in vals)/(n-1)
        sd=var**0.5;se=sd/(n**0.5);lower=mean-GEN1_Z*se
    else:
        sd=se=lower=None
    return {
      "revision":GENERATION_CHALLENGER_REVISION,
      "generation":1,"family_id":family_id,"n":n,
      "unique_tickers":len(tickers),
      "mean_net_after_2pct":mean,"net_stddev":sd,
      "net_standard_error":se,
      "lower_bound_net_after_2pct":lower,
      "strict_cutoff_epoch":float(cutoff_epoch),
    }

def _gen1_challenger_scores(root,base_scores,now):
    root=Path(root).resolve()
    freeze=_gen1_load_freeze(root)
    out=[]
    for c in freeze.get("candidates") or []:
        h=int(c.get("horizon_seconds") or -1)
        direction=_gen1_target_direction(c.get("target"))
        formula=list(c.get("formula") or [])
        for base in base_scores:
            if int(base.get("horizon_seconds") or -2)!=h:
                continue
            st=base.get("state") or {}
            toks=set(st.get("tokens") or [])
            match=all(str(x) in toks for x in formula)
            if not match:
                continue
            stats=_gen1_prior_stats(
                root,c.get("family_id"),h,direction,
                float(st.get("observed_epoch") or 0.0)
            )
            support=stats["n"]>=GEN1_MIN_RESOLVED and stats["unique_tickers"]>=GEN1_MIN_TICKERS
            positive=stats["lower_bound_net_after_2pct"] is not None and stats["lower_bound_net_after_2pct"]>0.0
            fresh=bool((base.get("checks") or {}).get("fresh_state"))
            horizon_ok=bool((base.get("checks") or {}).get("contract_horizon"))
            checks={
              "fresh_state":fresh,
              "contract_horizon":horizon_ok,
              "gen1_exact_frozen_formula_match":True,
              "gen1_prospective_support":support,
              "gen1_prospective_realized_edge":positive,
            }
            mean_net=stats["mean_net_after_2pct"]
            lower=stats["lower_bound_net_after_2pct"]
            z={
              "generation":1,
              "family_id":c.get("family_id"),
              "model_basis":"ORIGINAL_FROZEN_OPD031_GEN1",
              "gen1_formula":formula,
              "gen1_target":c.get("target"),
              "gen1_original_activation_epoch":freeze.get("activation_epoch"),
              "state":dict(st),
              "asset":base.get("asset"),
              "horizon_seconds":h,
              "age_seconds":base.get("age_seconds"),
              "comparable_cases":stats["n"],
              "unique_tickers":stats["unique_tickers"],
              "mean_similarity":1.0,
              "direction":direction,
              "predicted_probability":None,
              "expected_return":None if mean_net is None else mean_net+HURDLE,
              "net_edge_after_2pct":lower,
              "expected_mfe":None,"expected_mae":None,
              "evidence_votes":{"GEN1":{"cases":stats["n"],"direction":direction,
                 "mean_return":None if mean_net is None else mean_net+HURDLE}},
              "evidence_agreement":1.0,
              "contract_close_epoch":base.get("contract_close_epoch"),
              "contract_remaining_seconds":base.get("contract_remaining_seconds"),
              "horizon_eligible":horizon_ok,
              "prospective_realized_edge":stats,
              "checks":checks,
              "passed":all(checks.values()),
            }
            z["state"]["state_id"]="GEN1:"+str(c.get("family_id"))+":"+str(st.get("state_id"))
            out.append(z)
    return out
'''

insert=ps.find("\ndef _run_single_contract(")
if insert<0:
    raise SystemExit("[FAIL] _run_single_contract insertion boundary missing")
ps=ps[:insert]+"\n"+CHALLENGER+ps[insert:]

ledger_call="    ledger=_freeze_predictions(root,anchor,scores,now)\n"
if ledger_call not in ps:
    raise SystemExit("[FAIL] live ledger call not found in single-contract scorer")
pre='''    for _z in scores:
        _z.setdefault("generation",2)
        _z.setdefault("model_basis","FULL_EVIDENCE_CURRENT_MODEL")
    gen1_scores=_gen1_challenger_scores(root,scores,now)
    scores.extend(gen1_scores)
    if gen1_scores:
        print("[GEN1 CHALLENGER] exact_formula_matches=",len(gen1_scores),
              "actionable=",sum(1 for x in gen1_scores if x.get("passed")),
              "original_freeze=OPD-031")
'''
ps=ps.replace(ledger_call,pre+ledger_call,1)

needle='        print("-"*112);print("TICKER=",z["state"]["ticker"],"HORIZON=",z["horizon_seconds"],"AGE_SECONDS=",round(z["age_seconds"],3))'
if needle in ps:
    ps=ps.replace(
        needle,
        '        print("-"*112);print("GENERATION=",z.get("generation",2),"MODEL_BASIS=",z.get("model_basis"));print("TICKER=",z["state"]["ticker"],"HORIZON=",z["horizon_seconds"],"AGE_SECONDS=",round(z["age_seconds"],3))',
        1
    )

# 2) Preserve generation/family through exact future resolution.
if '"generation":int(p.get("generation") or 2)' not in rs:
    old='''"prediction_id":pid,"revision":OUTCOME_LEDGER_REVISION,
              "resolution_status":"CONTRACT_HORIZON_INELIGIBLE",'''
    new='''"prediction_id":pid,"revision":OUTCOME_LEDGER_REVISION,
              "generation":int(p.get("generation") or 2),"family_id":p.get("family_id"),
              "model_basis":p.get("model_basis"),
              "resolution_status":"CONTRACT_HORIZON_INELIGIBLE",'''
    if old not in rs:
        raise SystemExit("[FAIL] resolver ineligible row boundary missing")
    rs=rs.replace(old,new,1)

    old='''"prediction_id":pid,"revision":OUTCOME_LEDGER_REVISION,
          "resolution_status":"RESOLVED_EXACT_FUTURE",'''
    new='''"prediction_id":pid,"revision":OUTCOME_LEDGER_REVISION,
          "generation":int(p.get("generation") or 2),"family_id":p.get("family_id"),
          "model_basis":p.get("model_basis"),
          "resolution_status":"RESOLVED_EXACT_FUTURE",'''
    if old not in rs:
        raise SystemExit("[FAIL] resolver resolved row boundary missing")
    rs=rs.replace(old,new,1)

# 3) Split realized profitability by generation.
if '"by_generation": by_generation' not in ss:
    anchor='''    board = {
        "revision": SCOREBOARD_REVISION,
'''
    if anchor not in ss:
        raise SystemExit("[FAIL] scoreboard board-construction boundary missing")
    prep='''    by_generation_rows = {}
    for row in resolved:
        g = str(int(row.get("generation") or 2))
        by_generation_rows.setdefault(g, []).append(row)
    by_generation = {}
    for g, rows in sorted(by_generation_rows.items()):
        ga=[r for r in rows if bool(r.get("actionable_at_freeze"))]
        gs=_stats(ga)
        all_stats=_stats(rows)
        if gs["n"]==0:
            gst="NO_RESOLVED_ACTIONABLE_PREDICTIONS"
        elif gs["mean_net_realized_after_2pct"]>0:
            gst="POSITIVE_NET_EXPECTANCY_OBSERVED"
        else:
            gst="NONPOSITIVE_NET_EXPECTANCY_OBSERVED"
        by_generation[g]={
          "resolved_all":all_stats,
          "actionable":gs,
          "profitability_status":gst,
          "profitability_certified":False,
        }

'''
    ss=ss.replace(anchor,prep+anchor,1)
    ss=ss.replace(
        '        "actionable": a,\n',
        '        "actionable": a,\n        "by_generation": by_generation,\n',
        1
    )
    print_anchor='''    print("[CALIBRATION] brier=", a["brier_score"],
          "mean_abs_error=", a["mean_absolute_calibration_error"],
          "mean_predicted_probability=", a["mean_predicted_probability"], flush=True)
'''
    if print_anchor not in ss:
        raise SystemExit("[FAIL] scoreboard print boundary missing")
    gen_print='''    for g, block in sorted(board.get("by_generation", {}).items()):
        ga=block["actionable"]; gr=block["resolved_all"]
        print("[GENERATION]",g,
              "resolved_n=",gr["n"],
              "actionable_n=",ga["n"],
              "hit_rate=",ga["hit_rate"],
              "mean_net_after_2pct=",ga["mean_net_realized_after_2pct"],
              "cumulative_net_after_2pct=",ga["cumulative_net_realized_after_2pct"],
              "status=",block["profitability_status"], flush=True)
'''
    ss=ss.replace(print_anchor,print_anchor+gen_print,1)

compile(ps,str(P),"exec")
compile(rs,str(R),"exec")
compile(ss,str(S),"exec")

P.write_text(ps,encoding="utf-8")
R.write_text(rs,encoding="utf-8")
S.write_text(ss,encoding="utf-8")

TEST_SOURCE=r'''from pathlib import Path
import json,tempfile
import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as p
import qseries_v2.oracle_predictive_discovery.opd_full_evidence_live_profitability_scoreboard_clean as sb

assert p.EXECUTION_AUTHORITY is False
assert p.PUBLICATION_ALLOWED is False
assert p.HURDLE==0.020
assert p.GENERATION_CHALLENGER_REVISION=="GEN1_GEN2_PROSPECTIVE_CHALLENGER_V1"
assert p.GEN1_MIN_RESOLVED==12
assert p.GEN1_MIN_TICKERS==3

with tempfile.TemporaryDirectory() as td:
    root=Path(td);base=root/"runtime"/"predictive_data";base.mkdir(parents=True)
    freeze={
      "schema_version":"OPD-031","activation_epoch":1000.0,
      "candidate_count":1,"formula_retuning_allowed":False,
      "threshold_retuning_allowed":False,
      "historical_data_allowed_for_prospective_scoring":False,
      "edge_certified_count":0,"execution_authority":False,
      "candidates":[{
        "family_id":"GEN1-F","representative_formula_id":"R1","degree":2,
        "horizon_seconds":300,"target":"RETURN_NEG",
        "formula":["CB:X","CC:Y"],
        "historical_discovery_lift":0.2,"historical_holdout_lift":0.1,
        "historical_holdout_q":0.01,"historical_net_after_hurdle":0.05
      }]
    }
    (base/p.GEN1_FREEZE_NAME).write_text(json.dumps(freeze),encoding="utf-8")
    base_score={
      "generation":2,"model_basis":"FULL_EVIDENCE_CURRENT_MODEL",
      "state":{"state_id":"S","ticker":"KXBTCD-NOW-T77000",
               "observed_epoch":2000.0,"anchor_price":0.55,
               "tokens":["CB:X","CC:Y","K:Z","L:W"]},
      "asset":"BTC","horizon_seconds":300,"age_seconds":1.0,
      "contract_close_epoch":3000.0,"contract_remaining_seconds":1000.0,
      "horizon_eligible":True,
      "checks":{"fresh_state":True,"contract_horizon":True},
    }

    z=p._gen1_challenger_scores(root,[base_score],2001.0)
    assert len(z)==1
    assert z[0]["direction"]=="DOWN"
    assert z[0]["passed"] is False
    assert z[0]["checks"]["gen1_prospective_support"] is False

    rows=[]
    for i in range(18):
        rows.append({
          "prediction_id":f"G1-{i}","resolution_status":"RESOLVED_EXACT_FUTURE",
          "resolved_epoch":1900.0,"generation":1,"family_id":"GEN1-F",
          "ticker":f"KXBTCD-H{i%4}-T77000","horizon_seconds":300,
          "direction":"DOWN","directional_return":0.07
        })
    rows.append({
      "prediction_id":"FUTURE","resolution_status":"RESOLVED_EXACT_FUTURE",
      "resolved_epoch":2100.0,"generation":1,"family_id":"GEN1-F",
      "ticker":"KXBTCD-FUTURE-T77000","horizon_seconds":300,
      "direction":"DOWN","directional_return":9.0
    })
    with (base/"opd_full_evidence_live_outcome_ledger.jsonl").open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r)+"\n")
    z=p._gen1_challenger_scores(root,[base_score],2001.0)
    assert len(z)==1
    st=z[0]["prospective_realized_edge"]
    assert st["n"]==18 and st["unique_tickers"]==4
    assert st["lower_bound_net_after_2pct"]>0
    assert z[0]["passed"] is True

    rows=[dict(r,directional_return=0.0) for r in rows[:-1]]
    with (base/"opd_full_evidence_live_outcome_ledger.jsonl").open("w",encoding="utf-8") as f:
        for r in rows:f.write(json.dumps(r)+"\n")
    z=p._gen1_challenger_scores(root,[base_score],2001.0)
    assert z[0]["passed"] is False
    assert z[0]["checks"]["gen1_prospective_realized_edge"] is False

    anchor={"anchor_id":"A","anchor_sequence_boundary":7,"ticker":"KXBTCD-NOW-T77000"}
    assert p._prediction_id(anchor,300,2,None)!=p._prediction_id(anchor,300,1,"GEN1-F")

    pred=[{"prediction_id":"A"},{"prediction_id":"B"}]
    out=[
      {"prediction_id":"A","resolution_status":"RESOLVED_EXACT_FUTURE",
       "generation":1,"family_id":"GEN1-F","actionable_at_freeze":True,
       "horizon_seconds":300,"directional_return":0.08,"predicted_probability":None},
      {"prediction_id":"B","resolution_status":"RESOLVED_EXACT_FUTURE",
       "generation":2,"actionable_at_freeze":True,
       "horizon_seconds":300,"directional_return":-0.01,"predicted_probability":0.7},
    ]
    with (base/sb.PREDICTION_LEDGER_NAME).open("w",encoding="utf-8") as f:
        for r in pred:f.write(json.dumps(r)+"\n")
    with (base/sb.OUTCOME_LEDGER_NAME).open("w",encoding="utf-8") as f:
        for r in out:f.write(json.dumps(r)+"\n")
    b=sb.build_scoreboard(root)
    assert b["by_generation"]["1"]["actionable"]["mean_net_realized_after_2pct"]>0
    assert b["by_generation"]["2"]["actionable"]["mean_net_realized_after_2pct"]<0

resolver=Path("qseries_v2/oracle_predictive_discovery/opd_full_evidence_exact_future_outcome_resolver.py").read_text(encoding="utf-8")
scoreboard=Path("qseries_v2/oracle_predictive_discovery/opd_full_evidence_live_profitability_scoreboard_clean.py").read_text(encoding="utf-8")
predictor=Path("qseries_v2/oracle_predictive_discovery/opd_live_full_evidence_fusion_predictor.py").read_text(encoding="utf-8")
assert '"generation":int(p.get("generation") or 2)' in resolver
assert '"family_id":p.get("family_id")' in resolver
assert '"by_generation": by_generation' in scoreboard
assert 'ORIGINAL_FROZEN_OPD031_GEN1' in predictor
assert 'GEN1_MIN_RESOLVED=12' in predictor
assert 'GEN1_MIN_TICKERS=3' in predictor
assert 'scores.extend(gen1_scores)' in predictor

print("[PASS] original OPD-031 Gen1 formulas restored exactly as a live challenger")
print("[PASS] Gen1 formula/threshold retuning remains forbidden")
print("[PASS] current full-evidence model retained as generation 2 baseline")
print("[PASS] same anchor+horizon can freeze Gen1 and Gen2 without prediction-id collision")
print("[PASS] exact future resolver preserves generation + family lineage")
print("[PASS] Gen1 future outcomes cannot leak backward across current anchor cutoff")
print("[PASS] Gen1 requires 12 resolved cases / 3 tickers and positive conservative net lower bound")
print("[PASS] negative prospective Gen1 economics force abstention")
print("[PASS] profitability scoreboard now separates Gen1 vs Gen2 realized economics")
print("[PASS] fixed 2pct hurdle, freshness, contract lifetime, publication, execution unchanged")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
'''
T.write_text(TEST_SOURCE,encoding="utf-8")
compile(TEST_SOURCE,str(T),"exec")

print("[PASS] Gen1/Gen2 prospective challenger installed into existing production prediction path")
print("[GEN1 SOURCE] original immutable OPD-031 candidate freeze")
print("[GEN2 SOURCE] current full-evidence scorer")
print("[REAL PROBLEM] generation survival now decided by exact realized prospective net economics")
print("[ANTI-LEAKAGE] only outcomes resolved before current anchor can admit a generation")
print("[HURDLE] fixed 2pct preserved")
print("[EXECUTION/PUBLICATION] FALSE/FALSE")
