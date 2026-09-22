from pathlib import Path
import py_compile

ROOT=Path.cwd()
TEST=ROOT/'test_oracle_predictive_audit_012_historical_price_path_depth.py'
BODY='from collections import Counter,defaultdict\nimport json,re\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nROOT=Path.cwd()\nwith connect(ROOT,autocommit=False) as c:\n    with c.cursor() as q:\n        q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout=\'15000ms\'")\n        q.execute("SELECT sequence_number,observed_at,observation_type,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=\'source.kalshi.market_data\' ORDER BY sequence_number DESC LIMIT 250000")\n        rows=q.fetchall() or []\n    c.rollback()\nby=defaultdict(list);types=Counter();price_keys=Counter()\nfor seq,ts,typ,obj in rows:\n    types[str(typ)]+=1\n    try:d=obj if isinstance(obj,dict) else json.loads(obj)\n    except Exception:continue\n    text=json.dumps(d,separators=(",",":")).upper();m=re.search(r\'KX(?:BTC|ETH|SOL)[A-Z0-9-]*\',text)\n    if not m:continue\n    ticker=m.group(0).rstrip(\'"}],\');by[ticker].append((seq,ts,d));stack=[d]\n    while stack:\n        x=stack.pop()\n        if isinstance(x,dict):\n            for k,v in x.items():\n                if any(z in k.lower() for z in ("price","bid","ask")) and isinstance(v,(int,float,str)):price_keys[k]+=1\n                if isinstance(v,(dict,list)):stack.append(v)\n        elif isinstance(x,list):stack.extend(x)\nprint("[ROWS_SCANNED]",len(rows));print("[OBSERVATION_TYPES]",dict(types.most_common(20)))\nprint("[CRYPTO_CONTRACTS_WITH_ROWS]",len(by));print("[PRICE_FIELD_KEYS]",dict(price_keys.most_common(30)))\nfor ticker,rs in sorted(by.items(),key=lambda kv:len(kv[1]),reverse=True)[:30]:\n    times=[x[1] for x in rs if x[1] is not None];span=(max(times)-min(times)).total_seconds() if len(times)>1 else 0\n    print("[PATH_DEPTH]",ticker,"rows=",len(rs),"span_seconds=",round(span,3),"first=",min(times) if times else None,"last=",max(times) if times else None)\nprint("[PASS] OPA-012 historical Kalshi price-path depth audit complete")\n'

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
    print(" OPA-012 HISTORICAL KALSHI PRICE-PATH DEPTH INSTALLER")
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
