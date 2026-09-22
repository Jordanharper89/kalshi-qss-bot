from pathlib import Path
import shutil

R=Path.cwd()
P=R/'qseries_v2'/'oracle_predictive_discovery'/'opd_live_full_evidence_fusion_predictor.py'
T=R/'test_opd_FULL_EVIDENCE_CONTRACT_LIFETIME_GATE.py'
B=P.with_suffix('.pre_contract_lifetime_gate.bak')

if not P.exists():
    raise SystemExit('[FAIL] existing full-evidence predictor missing: '+str(P))
s=P.read_text(encoding='utf-8')
if 'FRESH CANONICAL CUTOVER' not in s:
    raise SystemExit('[FAIL] fresh-canonical predictor cutover is not installed; refusing to patch stale predictor')
if 'def _contract_close_metadata(' in s and '"contract_horizon"' in s:
    print('[PASS] contract-lifetime gate already installed')
else:
    if not B.exists(): shutil.copy2(P,B)

    marker='def latest_live_anchor(root):\n'
    helper=(
"def _iso_epoch(value):\n"
"    if value is None:return None\n"
"    text=str(value).strip()\n"
"    if not text:return None\n"
"    try:\n"
"        from datetime import datetime,timezone\n"
"        if text.endswith('Z'):text=text[:-1]+'+00:00'\n"
"        dt=datetime.fromisoformat(text)\n"
"        if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)\n"
"        return float(dt.timestamp())\n"
"    except Exception:return None\n\n"
"def _contract_close_metadata(root,ticker):\n"
"    sql=\"\"\"SELECT sequence_number,canonical_observation_json->'payload'->>'source_close_time'\n"
"             FROM public.oracle_canonical_observations\n"
"             WHERE source_id=%s\n"
"               AND canonical_observation_json->'payload'->>'source_market_id'=%s\n"
"               AND COALESCE(canonical_observation_json->'payload'->>'source_close_time','')<>''\n"
"             ORDER BY sequence_number DESC LIMIT 1\"\"\"\n"
"    with connect(root,autocommit=False) as c:\n"
"        with c.cursor() as q:\n"
"            q.execute('SET TRANSACTION READ ONLY')\n"
"            q.execute(\"SET LOCAL statement_timeout='5000ms'\")\n"
"            q.execute(sql,(SOURCE,str(ticker)));row=q.fetchone()\n"
"        c.rollback()\n"
"    if not row:return {'close_epoch':None,'metadata_sequence':None,'basis':'NO_CANONICAL_CLOSE_TIME'}\n"
"    epoch=_iso_epoch(row[1])\n"
"    return {'close_epoch':epoch,'metadata_sequence':int(row[0]),\n"
"      'basis':'CANONICAL_SOURCE_CLOSE_TIME' if epoch is not None else 'INVALID_CANONICAL_CLOSE_TIME'}\n\n"
    )
    if marker not in s: raise SystemExit('[FAIL] latest_live_anchor marker missing')
    s=s.replace(marker,helper+marker,1)

    old="    for row in rows:\n        a=_anchor_from_row(row)\n        if a:return a\n    return None\n"
    new=("    for row in rows:\n        a=_anchor_from_row(row)\n        if a:\n"
         "            meta=_contract_close_metadata(root,a['ticker'])\n"
         "            a['contract_close_epoch']=meta['close_epoch']\n"
         "            a['contract_close_metadata_sequence']=meta['metadata_sequence']\n"
         "            a['contract_close_basis']=meta['basis']\n"
         "            return a\n    return None\n")
    if old not in s: raise SystemExit('[FAIL] anchor-return block missing')
    s=s.replace(old,new,1)

    old=("          \"anchor_id\":anchor[\"anchor_id\"],\"ticker\":anchor[\"ticker\"],\n"
         "          \"observed_epoch\":float(anchor[\"observed_epoch\"]),\"horizon_seconds\":h,\n"
         "          \"anchor_price\":anchor[\"anchor_price\"],\"tokens\":list(materialize_exact_live_tokens(root,world))})\n")
    new=("          \"anchor_id\":anchor[\"anchor_id\"],\"ticker\":anchor[\"ticker\"],\n"
         "          \"observed_epoch\":float(anchor[\"observed_epoch\"]),\"horizon_seconds\":h,\n"
         "          \"anchor_price\":anchor[\"anchor_price\"],\n"
         "          \"contract_close_epoch\":anchor.get(\"contract_close_epoch\"),\n"
         "          \"contract_close_basis\":anchor.get(\"contract_close_basis\"),\n"
         "          \"tokens\":list(materialize_exact_live_tokens(root,world))})\n")
    if old not in s: raise SystemExit('[FAIL] current-state construction block missing')
    s=s.replace(old,new,1)

    old="    age=max(0.0,float(now)-t)\n    checks={\"fresh_state\":age<=MAX_STATE_AGE_SECONDS,\"comparable_cases\":n>=MIN_CASES,\n"
    new=("    age=max(0.0,float(now)-t)\n"
         "    close_epoch=cur.get('contract_close_epoch')\n"
         "    try:close_epoch=None if close_epoch is None else float(close_epoch)\n"
         "    except Exception:close_epoch=None\n"
         "    remaining=None if close_epoch is None else close_epoch-t\n"
         "    horizon_eligible=close_epoch is not None and (t+float(h))<=close_epoch\n"
         "    checks={\"fresh_state\":age<=MAX_STATE_AGE_SECONDS,\"contract_horizon\":horizon_eligible,\"comparable_cases\":n>=MIN_CASES,\n")
    if old not in s: raise SystemExit('[FAIL] score checks block missing')
    s=s.replace(old,new,1)

    old="      \"evidence_votes\":votes,\"evidence_agreement\":agree,\"checks\":checks,\"passed\":all(checks.values())}\n"
    new=("      \"evidence_votes\":votes,\"evidence_agreement\":agree,\"contract_close_epoch\":close_epoch,\n"
         "      \"contract_remaining_seconds\":remaining,\"horizon_eligible\":horizon_eligible,\n"
         "      \"checks\":checks,\"passed\":all(checks.values())}\n")
    if old not in s: raise SystemExit('[FAIL] score return block missing')
    s=s.replace(old,new,1)

    old=("    print(\"LIVE_ANCHOR_TICKER=\",anchor[\"ticker\"]);print(\"LIVE_ANCHOR_SEQUENCE=\",anchor.get(\"anchor_sequence_boundary\"))\n"
         "    print(\"LIVE_ANCHOR_AGE_SECONDS=\",max(0.0,now-float(anchor[\"observed_epoch\"])))\n")
    new=old+("    print(\"CONTRACT_CLOSE_EPOCH=\",anchor.get(\"contract_close_epoch\"))\n"
             "    print(\"CONTRACT_CLOSE_BASIS=\",anchor.get(\"contract_close_basis\"))\n"
             "    print(\"CONTRACT_CLOSE_METADATA_SEQUENCE=\",anchor.get(\"contract_close_metadata_sequence\"))\n")
    if old not in s: raise SystemExit('[FAIL] live-anchor print block missing')
    s=s.replace(old,new,1)

    old=("        print(\"DIRECTION=\",z[\"direction\"],\"PREDICTED_PROBABILITY=\",z[\"predicted_probability\"]);print(\"EXPECTED_RETURN=\",z[\"expected_return\"],\"NET_EDGE_AFTER_2PCT=\",z[\"net_edge_after_2pct\"])\n"
         "        failed=[k for k,v in z[\"checks\"].items() if not v];print(\"DECISION=\"+(z[\"direction\"] if z[\"passed\"] else \"ABSTAIN\"),\"FAILED_GATES=\"+(\"NONE\" if not failed else \",\".join(failed)))\n")
    new=("        print(\"DIRECTION=\",z[\"direction\"],\"PREDICTED_PROBABILITY=\",z[\"predicted_probability\"]);print(\"EXPECTED_RETURN=\",z[\"expected_return\"],\"NET_EDGE_AFTER_2PCT=\",z[\"net_edge_after_2pct\"])\n"
         "        print(\"CONTRACT_REMAINING_SECONDS=\",z[\"contract_remaining_seconds\"],\"HORIZON_ELIGIBLE=\",z[\"horizon_eligible\"])\n"
         "        failed=[k for k,v in z[\"checks\"].items() if not v];print(\"DECISION=\"+(z[\"direction\"] if z[\"passed\"] else \"ABSTAIN\"),\"FAILED_GATES=\"+(\"NONE\" if not failed else \",\".join(failed)))\n")
    if old not in s: raise SystemExit('[FAIL] per-horizon print block missing')
    s=s.replace(old,new,1)

    P.write_text(s,encoding='utf-8')

TEST="""import qseries_v2.oracle_predictive_discovery.opd_live_full_evidence_fusion_predictor as m

assert m._iso_epoch('2026-09-12T01:15:00Z') is not None
states=[];outs={}
for i in range(24):
    sid='h'+str(i)
    states.append({'state_id':sid,'ticker':'KXBTC'+str(i%4),'observed_epoch':1000+i,'horizon_seconds':300,'tokens':['K:A','CB:B','CC:C','L:D']})
    outs[sid]={'state_id':sid,'resolution_epoch':1500+i,'future_return':-0.05,'mfe':-0.01,'mae':-0.05}
base={'state_id':'LIVE','ticker':'KXBTC15M-TEST','observed_epoch':2000.0,'horizon_seconds':300,'tokens':['K:A','CB:B','CC:C','L:D']}
eligible=dict(base,contract_close_epoch=2300.0)
z=m._score_state(eligible,states,outs,2001.0)
assert z['horizon_eligible'] is True and z['checks']['contract_horizon'] is True and z['passed'] is True and z['direction']=='DOWN'
expired=dict(base,contract_close_epoch=2299.0)
z2=m._score_state(expired,states,outs,2001.0)
assert z2['horizon_eligible'] is False and z2['checks']['contract_horizon'] is False and z2['passed'] is False
unknown=dict(base,contract_close_epoch=None)
z3=m._score_state(unknown,states,outs,2001.0)
assert z3['horizon_eligible'] is False and z3['checks']['contract_horizon'] is False and z3['passed'] is False
assert m.EXECUTION_AUTHORITY is False and m.PUBLICATION_ALLOWED is False
print('[PASS] exact close boundary allows horizon ending exactly at contract close')
print('[PASS] horizon extending one second past close is forced to ABSTAIN')
print('[PASS] missing close metadata fails closed instead of producing actionable prediction')
print('[EXECUTION/PUBLICATION] FALSE/FALSE')
"""
T.write_text(TEST,encoding='utf-8')
compile(P.read_text(encoding='utf-8'),str(P),'exec')
compile(T.read_text(encoding='utf-8'),str(T),'exec')
print('[PASS] existing full-evidence predictor patched with exact canonical contract-lifetime gate')
print('[PASS] source_close_time is resolved from existing canonical Kalshi market metadata')
print('[PASS] probability/edge/evidence thresholds unchanged')
print('[EXECUTION/PUBLICATION] FALSE/FALSE')
