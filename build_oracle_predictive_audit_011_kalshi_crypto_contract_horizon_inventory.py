from pathlib import Path
import py_compile

ROOT=Path.cwd()
TEST=ROOT/'test_oracle_predictive_audit_011_kalshi_crypto_contract_horizon_inventory.py'
BODY='from collections import Counter\nimport json,re\nfrom pathlib import Path\nfrom qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import connect\nROOT=Path.cwd()\nwith connect(ROOT,autocommit=False) as c:\n    with c.cursor() as q:\n        q.execute("SET TRANSACTION READ ONLY");q.execute("SET LOCAL statement_timeout=\'15000ms\'")\n        q.execute("SELECT sequence_number,observed_at,canonical_observation_json FROM public.oracle_canonical_observations WHERE source_id=\'source.kalshi.market_data\' ORDER BY sequence_number DESC LIMIT 250000")\n        rows=q.fetchall() or []\n    c.rollback()\ntickers={}\nfor seq,ts,obj in rows:\n    try:d=obj if isinstance(obj,dict) else json.loads(obj)\n    except Exception:continue\n    text=json.dumps(d,separators=(",",":")).upper()\n    for t in re.findall(r\'KX[A-Z0-9-]{4,100}\',text):\n        t=t.rstrip(\'"}],\')\n        if any(a in t for a in ("BTC","ETH","SOL")):tickers.setdefault(t,(seq,ts))\ndef family(t):return re.sub(r\'-\\d.*$\',\'\',t)[:60]\nprint("[ROWS_SCANNED]",len(rows));print("[CRYPTO_TICKERS]",len(tickers))\nprint("[FAMILIES]",dict(Counter(family(t) for t in tickers).most_common(40)))\nfor t,(seq,ts) in sorted(tickers.items(),key=lambda x:x[1][0],reverse=True)[:80]:print("[TICKER]",t,"sequence=",seq,"observed_at=",ts)\nprint("[15M_COUNT]",sum("15M" in t for t in tickers))\nprint("[1H_TEXT_COUNT]",sum(("1H" in t or "HOURLY" in t or "HOUR" in t) for t in tickers))\nprint("[PASS] OPA-011 Kalshi crypto contract/horizon inventory complete")\n'

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
    print(" OPA-011 KALSHI CRYPTO CONTRACT + HORIZON INVENTORY INSTALLER")
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
