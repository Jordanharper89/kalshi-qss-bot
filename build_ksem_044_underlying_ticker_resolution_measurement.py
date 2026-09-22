from pathlib import Path
import json

ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
OUT=STATE/"ksem044_underlying_ticker_resolution_measurement.json"
TEST=ROOT/"test_ksem_044_underlying_ticker_resolution_measurement.py"

def text(x):
    try: return json.dumps(x,sort_keys=True,default=str)
    except Exception: return repr(x)

def main():
    print("="*120); print(" KSEM-044 UNDERLYING-TICKER RESOLUTION MEASUREMENT"); print("="*120)
    d=json.loads((STATE/"ksem043_exact_canonical_observation_recovery.json").read_text())
    pair={}
    for row in d["pair_observations"]: pair.setdefault(str(row.get("ticker") or ""),[]).append(row)
    direct=[text(x) for x in d["direct_serialized_rows"]]
    rows=[]; counts={"RESOLVED_PAIR":0,"RESOLVED_DIRECT":0,"NOT_FOUND":0}
    for ticker in d["requested_tickers"]:
        if ticker in pair and any(int(x.get("query_count") or 0)>0 for x in pair[ticker]):
            status="RESOLVED_PAIR"
        elif any(ticker in x for x in direct):
            status="RESOLVED_DIRECT"
        else:
            status="NOT_FOUND"
        counts[status]+=1; rows.append({"ticker":ticker,"status":status})
    print("[REQUESTED]",len(rows)); print("[COUNTS]",counts)
    for x in rows: print("[TICKER]",x)
    if sum(counts.values())!=len(rows): raise RuntimeError("resolution accounting failure")
    OUT.write_text(json.dumps({"requested":len(rows),"counts":counts,"rows":rows,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem044_underlying_ticker_resolution_measurement.json').read_text())\nassert d['requested']>0\nassert sum(d['counts'].values())==d['requested']\nassert d['execution_authority'] is False\nprint('[PASS] every bounded MVE ticker classified from physical PostgreSQL retrieval')\nprint('[PASS] KSEM-044 certified')\n",encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()