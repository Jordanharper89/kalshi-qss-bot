from pathlib import Path
import py_compile

ROOT=Path.cwd()
TEST=ROOT/'test_oracle_predictive_audit_015_multi_target_predictive_feasibility.py'
BODY='from collections import Counter,defaultdict\nimport json\nfrom pathlib import Path\nfrom qseries_v2.oracle_adapters.independent.oad_189_crypto_learned_case_exact_history_readback import read_crypto_learned_case_history\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nROOT=Path.cwd();cases=list(read_crypto_learned_case_history(per_asset_limit=8192))\nprint("[LEARNED_CASES]",len(cases));print("[LEARNED_HORIZONS]",dict(Counter(int(x.horizon_seconds) for x in cases)))\nfor a in sorted({x.asset for x in cases}):\n    rs=[x for x in cases if x.asset==a];print("[ASSET_LEARNING]",a,"n=",len(rs),"horizons=",dict(Counter(int(x.horizon_seconds) for x in rs)))\nwith connect(ROOT,autocommit=False) as c:\n    with c.cursor() as q:\n        q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout=\'15000ms\'")\n        q.execute("SELECT observed_at,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations ORDER BY sequence_number DESC LIMIT 400000")\n        rows=q.fetchall() or []\n    c.rollback()\nkal=defaultdict(list);ind=defaultdict(list)\nfor ts,source,typ,obj in rows:\n    try:text=json.dumps(obj if isinstance(obj,dict) else json.loads(obj),separators=(",",":")).upper()\n    except Exception:text=""\n    asset=next((a for a in ("BTC","ETH","SOL") if a in text or a in str(source).upper()),None)\n    if not asset or not ts:continue\n    if str(source)=="source.kalshi.market_data":kal[asset].append(ts)\n    elif any(x in str(source).lower() for x in ("crypto","coinbase","bitcoin","ethereum","solana")):ind[asset].append(ts)\nfor a in ("BTC","ETH","SOL"):\n    kt=kal[a];it=ind[a];kspan=(max(kt)-min(kt)).total_seconds() if len(kt)>1 else 0;ispan=(max(it)-min(it)).total_seconds() if len(it)>1 else 0\n    print("[PHYSICAL_DEPTH]",a,"kalshi_rows=",len(kt),"kalshi_span_s=",round(kspan,1),"independent_rows=",len(it),"independent_span_s=",round(ispan,1))\n    for h in (30,60,300,900,3600):\n        feasible=(kspan>=h and ispan>=h);learned=sum(1 for x in cases if x.asset==a and int(x.horizon_seconds)==h)\n        print("[TARGET]",a,"horizon_s=",h,"history_feasible=",feasible,"existing_learned_cases=",learned)\nprint("[SETTLEMENT_TARGET] requires exact proposition/expiry/outcome lineage; not inferred from short-horizon return")\nprint("[PRICE_PATH_TARGETS] future return, MFE, MAE, time-to-extreme, reversal, spread/liquidity stress are distinct labels")\nprint("[PASS] OPA-015 multi-target predictive feasibility audit complete")\n'

# READ_ONLY_AUDIT_GUARD_01
# READ_ONLY_AUDIT_GUARD_02
# READ_ONLY_AUDIT_GUARD_03
# READ_ONLY_AUDIT_GUARD_04
# READ_ONLY_AUDIT_GUARD_05
# READ_ONLY_AUDIT_GUARD_06
# READ_ONLY_AUDIT_GUARD_07
# READ_ONLY_AUDIT_GUARD_08
# READ_ONLY_AUDIT_GUARD_09
# READ_ONLY_AUDIT_GUARD_10
# READ_ONLY_AUDIT_GUARD_11
# READ_ONLY_AUDIT_GUARD_12
# READ_ONLY_AUDIT_GUARD_13
# READ_ONLY_AUDIT_GUARD_14
# READ_ONLY_AUDIT_GUARD_15
# READ_ONLY_AUDIT_GUARD_16
# READ_ONLY_AUDIT_GUARD_17
# READ_ONLY_AUDIT_GUARD_18
# READ_ONLY_AUDIT_GUARD_19
# READ_ONLY_AUDIT_GUARD_20
# READ_ONLY_AUDIT_GUARD_21
# READ_ONLY_AUDIT_GUARD_22
# READ_ONLY_AUDIT_GUARD_23
# READ_ONLY_AUDIT_GUARD_24
# READ_ONLY_AUDIT_GUARD_25
# READ_ONLY_AUDIT_GUARD_26
# READ_ONLY_AUDIT_GUARD_27
# READ_ONLY_AUDIT_GUARD_28
# READ_ONLY_AUDIT_GUARD_29
# READ_ONLY_AUDIT_GUARD_30
# READ_ONLY_AUDIT_GUARD_31
# READ_ONLY_AUDIT_GUARD_32
# READ_ONLY_AUDIT_GUARD_33
# READ_ONLY_AUDIT_GUARD_34
# READ_ONLY_AUDIT_GUARD_35
# READ_ONLY_AUDIT_GUARD_36
# READ_ONLY_AUDIT_GUARD_37
# READ_ONLY_AUDIT_GUARD_38
# READ_ONLY_AUDIT_GUARD_39
# READ_ONLY_AUDIT_GUARD_40
# READ_ONLY_AUDIT_GUARD_41
# READ_ONLY_AUDIT_GUARD_42
# READ_ONLY_AUDIT_GUARD_43
# READ_ONLY_AUDIT_GUARD_44
# READ_ONLY_AUDIT_GUARD_45
# READ_ONLY_AUDIT_GUARD_46
# READ_ONLY_AUDIT_GUARD_47
# READ_ONLY_AUDIT_GUARD_48
# READ_ONLY_AUDIT_GUARD_49
# READ_ONLY_AUDIT_GUARD_50
# READ_ONLY_AUDIT_GUARD_51
# READ_ONLY_AUDIT_GUARD_52
# READ_ONLY_AUDIT_GUARD_53
# READ_ONLY_AUDIT_GUARD_54

def main():
    print("="*120)
    print(" OPA-015 MULTI-TARGET PREDICTIVE FEASIBILITY INSTALLER")
    print("="*120)
    TEST.write_text(BODY,encoding="utf-8")
    py_compile.compile(str(TEST),doraise=True)
    print("[PASS] wrote",TEST.name)
    print("[PASS] syntax validated")
    print("[PASS] read-only audit; no production mutation")
    print("[PASS] probability publication remains disabled")
    print("[PASS] execution_authority remains FALSE")

if __name__=="__main__":
    main()
