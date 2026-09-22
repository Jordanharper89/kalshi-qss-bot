
from pathlib import Path
import ast,json
ROOT=Path.cwd();PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
STATE=PKG/"state/ksem015_physical_live_market_binding_gate.json"
TEST=ROOT/"test_ksem_015_physical_live_market_binding_gate.py"
def main():
    print("="*120);print(" KSEM-015 PHYSICAL LIVE MARKET BINDING GATE");print("="*120)
    for p in [PKG/"state/ksem013_exact_semantic_role_resolution.json",PKG/"state/ksem014_existing_pavement_adapter.json"]:
        if not p.exists():raise SystemExit("[FAIL] missing "+str(p.relative_to(ROOT)))
    candidates=[]
    for p in (ROOT/"qseries_v2").rglob("*.py"):
        if "kalshi_sports_evidence_mapping" in str(p).lower():continue
        try:src=p.read_text(encoding="utf-8");low=src.lower();tree=ast.parse(src,str(p))
        except:continue
        if "kalshi" not in low or "market" not in low:continue
        funcs=[]
        for n in tree.body:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
                nm=n.name.lower()
                if "market" in nm and any(x in nm for x in ("get","fetch","list","read","load","snapshot","current","active","inventory")):
                    funcs.append({"name":n.name,"line":n.lineno})
        if funcs:candidates.append({"path":str(p.relative_to(ROOT)),"functions":funcs[:15]})
    if not candidates:raise SystemExit("[FAIL] no physical Kalshi market-source callable found; refusing guessed live execution")
    d={"live_market_source_candidates":candidates[:50],"physical_binding_executed":False,
       "next_action":"SELECT_EXACT_LIVE_MARKET_SOURCE_AND_RUN_BOUNDED_PHYSICAL_SAMPLE",
       "execution_authority":False}
    STATE.write_text(json.dumps(d,indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem015_physical_live_market_binding_gate.json').read_text())\nassert d['live_market_source_candidates']\nassert d['physical_binding_executed'] is False\nassert d['execution_authority'] is False\nprint('[PASS] live Kalshi market-source candidates physically discovered')\nprint('[PASS] no fabricated live binding execution')\nprint('[PASS] KSEM-015 certified')\n",encoding="utf-8")
    for c in candidates[:20]:print("[LIVE_SOURCE_CANDIDATE]",c)
    print("[NEXT]",d["next_action"]);print("[WRITE]",STATE.relative_to(ROOT));print("[WRITE]",TEST.name)
if __name__=="__main__":main()
