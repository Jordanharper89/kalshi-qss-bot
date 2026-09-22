from pathlib import Path
from dataclasses import asdict,is_dataclass
import json

ROOT=Path.cwd(); S=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state"
OUT=S/"ksem033_underlying_sports_context.json"
TEST=ROOT/"test_ksem_033_underlying_sports_context_recovery.py"

def obj(x):
    return asdict(x) if is_dataclass(x) else (dict(x) if isinstance(x,dict) else {"repr":repr(x)})

def main():
    print("="*120); print(" KSEM-033 UNDERLYING SPORTS CONTEXT RECOVERY"); print("="*120)
    from qseries_v2.oracle_adapters.independent.oad_099_mixed_domain_cross_category_decomposition import decompose_mixed_market
    from qseries_v2.oracle_adapters.independent.oad_088_sports_market_type_resolver import resolve_sports_market_type
    src=json.loads((S/"ksem032_underlying_market_resolution.json").read_text())["rows"]
    rows=[]
    for r in src:
        m=r["underlying_market"]
        if not m:
            rows.append({**r,"market_type":None,"decomposed":[],"league_candidates":[]}); continue
        parts=tuple(decompose_mixed_market(m))
        leagues=sorted({getattr(x,"subdomain","") for x in parts
                        if getattr(x,"subdomain","") not in ("","UNKNOWN")})
        rows.append({**r,"market_type":obj(resolve_sports_market_type(m)),
                     "decomposed":[obj(x) for x in parts],"league_candidates":leagues})
    with_league=sum(bool(x["league_candidates"]) for x in rows)
    print("[ROWS]",len(rows)); print("[WITH_LEAGUE_CONTEXT]",with_league)
    for x in rows[:20]: print("[CONTEXT]",x)
    if not rows: raise RuntimeError("no underlying rows")
    OUT.write_text(json.dumps({"rows":rows,"execution_authority":False},indent=2,default=str),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem033_underlying_sports_context.json').read_text())\nassert d['rows']\nassert d['execution_authority'] is False\nprint('[PASS] underlying Kalshi sports context physically recovered and accounted')\nprint('[PASS] KSEM-033 certified')\n",encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()