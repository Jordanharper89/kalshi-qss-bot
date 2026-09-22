from pathlib import Path
import ast,json

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/oracle_source_network/providers/uniform_sports_provider.py"
STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem025_canonical_provider_result_contract.json"
TEST=ROOT/"test_ksem_025_exact_canonical_provider_result_contract_REPAIR.py"

def main():
    print("="*120); print(" KSEM-025 EXACT CANONICAL PROVIDER RESULT CONTRACT REPAIR"); print("="*120)
    src=TARGET.read_text(encoding="utf-8")
    tree=ast.parse(src,str(TARGET))
    found=[]
    for n in tree.body:
        if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in ("CanonicalProviderResult","acquire_canonical_events"):
            rec={"name":n.name,"line":n.lineno,"body":ast.unparse(n)}
            found.append(rec)
            print(f"[{n.name.upper()}]")
            print(rec["body"])
    if len(found)!=2:
        raise RuntimeError("exact CanonicalProviderResult/acquire_canonical_events contract not found")
    STATE.write_text(json.dumps({"contracts":found,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text(
        "import json\nfrom pathlib import Path\n"
        "d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem025_canonical_provider_result_contract.json').read_text())\n"
        "names={x['name'] for x in d['contracts']}\n"
        "assert 'CanonicalProviderResult' in names\n"
        "assert 'acquire_canonical_events' in names\n"
        "assert d['execution_authority'] is False\n"
        "print('[PASS] exact CanonicalProviderResult contract captured')\n"
        "print('[PASS] KSEM-025 repair audit certified')\n",encoding="utf-8")
    print("[WRITE]",STATE.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()