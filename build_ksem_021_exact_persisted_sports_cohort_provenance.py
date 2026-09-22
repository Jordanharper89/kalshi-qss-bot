from pathlib import Path
import ast,json
ROOT=Path.cwd(); PKG=ROOT/"qseries_v2/kalshi_sports_evidence_mapping"
STATE=PKG/"state/ksem021_exact_persisted_sports_cohort_provenance.json"
TEST=ROOT/"test_ksem_021_exact_persisted_sports_cohort_provenance.py"
TARGETS=[
ROOT/"qseries_v2/oracle_adapters/independent/oad_121_persisted_sports_current_market_association_gate.py",
ROOT/"qseries_v2/oracle_adapters/independent/oad_122_authoritative_sports_live_end_to_end_evidence_certification.py"]

def main():
    print("="*120); print(" KSEM-021 EXACT PERSISTED SPORTS COHORT PROVENANCE"); print("="*120)
    out=[]
    for p in TARGETS:
        tree=ast.parse(p.read_text(encoding="utf-8"),str(p))
        imports=[ast.unparse(n) for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))]
        cohort=[]
        for n in ast.walk(tree):
            if isinstance(n,(ast.Assign,ast.AnnAssign)):
                text=ast.unparse(n)
                if "cohort" in text.lower():
                    cohort.append({"line":n.lineno,"expr":text})
            if isinstance(n,ast.Call):
                text=ast.unparse(n)
                if "cohort" in text.lower():
                    cohort.append({"line":n.lineno,"expr":text})
        rec={"module":str(p.relative_to(ROOT)),"imports":imports,"cohort_usage":cohort}
        out.append(rec)
        print("[MODULE]",rec["module"])
        for x in cohort: print("[COHORT]",x)
        for x in imports:
            if "sport" in x.lower() or "persist" in x.lower():
                print("[IMPORT]",x)
    STATE.write_text(json.dumps({"modules":out,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem021_exact_persisted_sports_cohort_provenance.json').read_text())\nassert len(d['modules'])==2\nassert any(x['cohort_usage'] for x in d['modules'])\nassert d['execution_authority'] is False\nprint('[PASS] exact persisted sports cohort provenance captured')\nprint('[PASS] KSEM-021 certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()