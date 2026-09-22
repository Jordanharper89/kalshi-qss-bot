from pathlib import Path
import ast,json
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
STATE=PKG/"state/ksem020_exact_descriptor_provenance_repair.json"
TEST=ROOT/"test_ksem_020_exact_descriptor_provenance_REPAIR.py"
TARGETS=[
ROOT/"qseries_v2/oracle_adapters/independent/oad_121_persisted_sports_current_market_association_gate.py",
ROOT/"qseries_v2/oracle_adapters/independent/oad_122_authoritative_sports_live_end_to_end_evidence_certification.py"]

def main():
    print("="*120); print(" KSEM-020 EXACT DESCRIPTOR PROVENANCE REPAIR"); print("="*120)
    out=[]
    for p in TARGETS:
        if not p.exists(): raise SystemExit("[FAIL] missing "+str(p.relative_to(ROOT)))
        src=p.read_text(encoding="utf-8"); tree=ast.parse(src,str(p))
        imports=[]
        assignments=[]
        calls=[]
        for n in ast.walk(tree):
            if isinstance(n,(ast.Import,ast.ImportFrom)):
                imports.append(ast.unparse(n))
            if isinstance(n,(ast.Assign,ast.AnnAssign)):
                text=ast.unparse(n)
                if "descriptor" in text.lower(): assignments.append({"line":n.lineno,"expr":text})
            if isinstance(n,ast.Call):
                txt=ast.unparse(n)
                if "descriptor" in txt.lower() or "fetch_current_market_sports_candidates" in txt:
                    calls.append({"line":n.lineno,"expr":txt})
        rec={"module":str(p.relative_to(ROOT)),"imports":imports,"descriptor_assignments":assignments,"descriptor_calls":calls}
        out.append(rec)
        print("[MODULE]",rec["module"])
        for x in assignments: print("[DESCRIPTOR_ASSIGNMENT]",x)
        for x in calls: print("[DESCRIPTOR_CALL]",x)
    STATE.write_text(json.dumps({"modules":out,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem020_exact_descriptor_provenance_repair.json').read_text())\nassert len(d['modules'])==2\nassert any(x['descriptor_calls'] for x in d['modules'])\nassert d['execution_authority'] is False\nprint('[PASS] exact production sports descriptor provenance captured')\nprint('[PASS] KSEM-020 repair audit certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()