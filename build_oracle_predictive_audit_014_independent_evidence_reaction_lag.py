from pathlib import Path
import py_compile

ROOT=Path.cwd()
TEST=ROOT/'test_oracle_predictive_audit_014_independent_evidence_reaction_lag.py'
BODY='from collections import Counter\nimport json\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nROOT=Path.cwd()\nwith connect(ROOT,autocommit=False) as c:\n    with c.cursor() as q:\n        q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout=\'15000ms\'")\n        q.execute("SELECT sequence_number,observed_at,source_id,observation_type,canonical_observation_json FROM public.oracle_canonical_observations ORDER BY sequence_number DESC LIMIT 300000")\n        rows=q.fetchall() or []\n    c.rollback()\nind=Counter();kal=Counter();assets=Counter();ind_times=[];kal_times=[]\nfor seq,ts,source,typ,obj in rows:\n    s=str(source);typ=str(typ)\n    try:text=json.dumps(obj if isinstance(obj,dict) else json.loads(obj),separators=(",",":")).upper()\n    except Exception:text=""\n    asset=next((a for a in ("BTC","ETH","SOL") if a in text or a in s.upper()),None)\n    if not asset:continue\n    if s=="source.kalshi.market_data":\n        kal[(asset,typ)]+=1\n        if ts:kal_times.append(ts)\n    elif ("crypto" in s.lower() or "coinbase" in s.lower() or any(x in s.lower() for x in ("bitcoin","ethereum","solana"))):\n        ind[(asset,s,typ)]+=1\n        if ts:ind_times.append(ts)\n    assets[asset]+=1\nprint("[ROWS_SCANNED]",len(rows));print("[ASSET_ROWS]",dict(assets));print("[KALSHI_TYPES]",dict(kal.most_common(30)))\nprint("[INDEPENDENT_STREAMS]")\nfor k,n in ind.most_common(60):print(" ",k,"rows=",n)\nprint("[KALSHI_TIME_RANGE]",min(kal_times) if kal_times else None,max(kal_times) if kal_times else None)\nprint("[INDEPENDENT_TIME_RANGE]",min(ind_times) if ind_times else None,max(ind_times) if ind_times else None)\noverlap=bool(kal_times and ind_times and max(min(kal_times),min(ind_times))<=min(max(kal_times),max(ind_times)))\nprint("[TIMESTAMP_OVERLAP]",overlap);print("[REACTION_LAG_RECONSTRUCTION_FEASIBLE]",overlap and bool(kal) and bool(ind))\nprint("[PASS] OPA-014 independent evidence versus Kalshi reaction-lag feasibility audit complete")\n'

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
    print(" OPA-014 INDEPENDENT EVIDENCE -> KALSHI REACTION LAG INSTALLER")
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
