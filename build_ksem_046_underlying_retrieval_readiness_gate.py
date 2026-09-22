from pathlib import Path
import json

ROOT=Path.cwd()
STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
OUT=STATE/"ksem046_underlying_retrieval_readiness.json"
TEST=ROOT/"test_ksem_046_underlying_retrieval_readiness_gate.py"

def main():
    print("="*120); print(" KSEM-046 UNDERLYING RETRIEVAL READINESS GATE"); print("="*120)
    m=json.loads((STATE/"ksem044_underlying_ticker_resolution_measurement.json").read_text())
    c=json.loads((STATE/"ksem045_recovered_underlying_context.json").read_text())
    requested=int(m["requested"])
    resolved=int(m["counts"]["RESOLVED_PAIR"])+int(m["counts"]["RESOLVED_DIRECT"])
    missing=int(m["counts"]["NOT_FOUND"])
    rate=resolved/requested if requested else 0.0
    if resolved==requested and requested:
        decision="EXACT_POSTGRESQL_RETRIEVAL_READY_FOR_FULL_MVE_EXPANSION"
    elif resolved:
        decision="PARTIAL_POSTGRESQL_COVERAGE_REQUIRES_MISSING_TICKER_CLASSIFICATION"
    else:
        decision="POSTGRESQL_SNAPSHOT_PATH_HAS_NO_CURRENT_UNDERLYING_TICKER_COVERAGE"
    data={"sample_size":requested,"resolved":resolved,"not_found":missing,
          "resolution_rate":rate,"resolved_with_league_context":c["resolved_with_league_context"],
          "decision":decision,"execution_authority":False}
    print("[SAMPLE_SIZE]",requested); print("[RESOLVED]",resolved); print("[NOT_FOUND]",missing)
    print("[RESOLUTION_RATE]",f"{rate:.6f}"); print("[DECISION]",decision)
    OUT.write_text(json.dumps(data,indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem046_underlying_retrieval_readiness.json').read_text())\nassert d['sample_size']>0\nassert d['resolved']+d['not_found']==d['sample_size']\nassert d['decision']\nassert d['execution_authority'] is False\nprint('[PASS] underlying-market retrieval readiness classified from physical evidence')\nprint('[PASS] KSEM-046 certified')\n",encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()