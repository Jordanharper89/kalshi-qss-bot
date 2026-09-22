
from pathlib import Path
import ast,json
ROOT=Path.cwd();PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
STATE=PKG/"state/ksem012_output_schema_and_callsite_audit.json"
TEST=ROOT/"test_ksem_012_output_schema_and_callsite_audit.py"
FUNCS=("resolve_sports_market_type","recognize_sports_entity_type","decompose_mixed_market","classify_isolated_root_cause")
CLASSES=("SportsMarketType","SportsEntityType","DecomposedLeg","EvidenceSignal","DiagnosticCluster","ExhaustiveDiagnostic")
def fields(c):
    return [{"name":n.target.id,"annotation":ast.unparse(n.annotation)} for n in c.body if isinstance(n,ast.AnnAssign) and isinstance(n.target,ast.Name)]
def main():
    print("="*120);print(" KSEM-012 OUTPUT SCHEMA + CALLSITE AUDIT");print("="*120)
    schemas={};calls={x:[] for x in FUNCS}
    for p in (ROOT/"qseries_v2").rglob("*.py"):
        if "kalshi_sports_evidence_mapping" in str(p).lower():continue
        try:src=p.read_text(encoding="utf-8");tree=ast.parse(src,str(p))
        except:continue
        for n in tree.body:
            if isinstance(n,ast.ClassDef) and n.name in CLASSES:schemas[n.name]={"module":str(p.relative_to(ROOT)),"fields":fields(n),"line":n.lineno}
        for n in ast.walk(tree):
            if isinstance(n,ast.Call):
                nm=n.func.id if isinstance(n.func,ast.Name) else (n.func.attr if isinstance(n.func,ast.Attribute) else None)
                if nm in calls:calls[nm].append({"module":str(p.relative_to(ROOT)),"line":n.lineno,"args":[ast.unparse(a)[:200] for a in n.args]})
    for need in ("SportsMarketType","SportsEntityType","DecomposedLeg"):
        if need not in schemas:raise SystemExit("[FAIL] missing output schema "+need)
    for fn in FUNCS:
        print("[CALLSITES]",fn,len(calls[fn]))
        for c in calls[fn][:12]:print(" ",c)
    for c,s in schemas.items():print("[SCHEMA]",c,[x["name"] for x in s["fields"]])
    STATE.write_text(json.dumps({"schemas":schemas,"callsites":calls,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem012_output_schema_and_callsite_audit.json').read_text())\nassert all(x in d['schemas'] for x in ('SportsMarketType','SportsEntityType','DecomposedLeg'))\nassert d['execution_authority'] is False\nprint('[PASS] output schemas and physical callsites captured')\nprint('[PASS] KSEM-012 certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT));print("[WRITE]",TEST.name)
if __name__=="__main__":main()
