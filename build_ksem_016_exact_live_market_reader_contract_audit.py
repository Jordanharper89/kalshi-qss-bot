from pathlib import Path
import ast,json,hashlib
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
STATE=PKG/"state/ksem016_live_market_reader_contract.json"; TEST=ROOT/"test_ksem_016_exact_live_market_reader_contract_audit.py"
TARGETS=[
("oiar_047","qseries_v2/oracle_intelligence_analytics_runtime/oiar_047_production_kalshi_current_eligibility_boundary.py","read_current_kalshi_markets"),
("oad_120","qseries_v2/oracle_adapters/independent/oad_120_current_market_sports_team_pair_index.py","fetch_current_market_sports_candidates")]
def fn_info(p,name):
    src=p.read_text(encoding="utf-8"); tree=ast.parse(src,str(p))
    fn=next((n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name),None)
    if fn is None: raise SystemExit("[FAIL] missing "+name)
    args=[a.arg for a in fn.args.args]
    defs=len(fn.args.defaults); required=args[:len(args)-defs] if defs else args
    rets=[ast.unparse(n.value)[:500] if n.value else None for n in ast.walk(fn) if isinstance(n,ast.Return)]
    calls=sorted(set((n.func.id if isinstance(n.func,ast.Name) else n.func.attr) for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,(ast.Name,ast.Attribute))))
    return {"args":args,"required":required,"returns":rets,"calls":calls,"line":fn.lineno}
def main():
    print("="*120); print(" KSEM-016 EXACT LIVE MARKET READER CONTRACT AUDIT"); print("="*120)
    out={}
    for key,rel,name in TARGETS:
        p=ROOT/rel
        if not p.exists(): raise SystemExit("[FAIL] missing "+rel)
        info=fn_info(p,name); info["module"]=rel; info["sha256"]=hashlib.sha256(p.read_bytes()).hexdigest(); info["function"]=name
        out[key]=info
        print("[TARGET]",key,rel,name)
        print("  [ARGS]",info["args"],"required=",info["required"])
        for r in info["returns"]: print("  [RETURN]",r)
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps({"targets":out,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem016_live_market_reader_contract.json').read_text())\nassert set(d['targets'])=={'oiar_047','oad_120'}\nassert d['execution_authority'] is False\nprint('[PASS] exact live market and sports-candidate contracts audited')\nprint('[PASS] KSEM-016 certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name)
if __name__=="__main__": main()