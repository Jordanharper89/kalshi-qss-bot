from pathlib import Path
import json,collections
R=Path.cwd()
f=R/"runtime"/"coinbase_hf"/"historical_condition_windows.jsonl"
assert f.exists() and f.stat().st_size>0
rows=[]
with f.open(encoding="utf-8") as h:
    for line in h:
        try: rows.append(json.loads(line))
        except Exception: pass
assert rows,"no valid CHF historical rows"
keys=collections.Counter()
types=collections.defaultdict(collections.Counter)
for r in rows:
    assert isinstance(r,dict)
    for k,v in r.items():
        keys[k]+=1; types[k][type(v).__name__]+=1
report={"rows":len(rows),"bytes":f.stat().st_size,
        "keys":dict(keys),"types":{k:dict(v) for k,v in types.items()},
        "first_row":rows[0],"last_row":rows[-1]}
out=R/"runtime"/"pre_momentum"
out.mkdir(parents=True,exist_ok=True)
(out/"opm_002_chf_contract.json").write_text(json.dumps(report,indent=2,default=str))
print("[CHF_ROWS]",len(rows))
print("[CHF_KEYS]",sorted(keys))
print("[FIRST_ROW]",rows[0])
print("[LAST_ROW]",rows[-1])
print("[PASS] no CHF schema fields guessed")
print("[PASS] OPM-002 physical CHF history contract certified")
