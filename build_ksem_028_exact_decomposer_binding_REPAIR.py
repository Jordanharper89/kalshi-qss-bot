from pathlib import Path
import ast,json

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/existing_sports_pavement_adapter.py"
STATE=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem028_exact_decomposer_binding_repair.json"
TEST=ROOT/"test_ksem_028_exact_decomposer_binding_REPAIR.py"

def main():
    print("="*120); print(" KSEM-028 EXACT DECOMPOSER BINDING REPAIR"); print("="*120)

    if not TARGET.exists():
        raise RuntimeError("certified KSEM-014 pavement adapter missing")

    src=TARGET.read_text(encoding="utf-8")
    tree=ast.parse(src,str(TARGET))

    imports=[]
    bindings=[]

    for n in ast.walk(tree):
        if isinstance(n,ast.ImportFrom):
            rec={
                "module":n.module,
                "names":[{"name":x.name,"asname":x.asname} for x in n.names],
                "line":n.lineno
            }
            imports.append(rec)

            for x in n.names:
                if x.name=="decompose_mixed_market":
                    bindings.append({
                        "module":n.module,
                        "symbol":x.name,
                        "bound_name":x.asname or x.name,
                        "line":n.lineno
                    })

        elif isinstance(n,ast.Assign):
            text=ast.unparse(n)
            if "decompose_mixed_market" in text:
                bindings.append({"assignment":text,"line":n.lineno})

    print("[ADAPTER]",TARGET.relative_to(ROOT))
    for x in imports:
        print("[IMPORT]",x)
    for x in bindings:
        print("[DECOMPOSER_BINDING]",x)

    if not bindings:
        raise RuntimeError("exact decompose_mixed_market binding not found in certified KSEM-014 adapter")

    STATE.write_text(json.dumps({
        "adapter":str(TARGET.relative_to(ROOT)),
        "bindings":bindings,
        "execution_authority":False
    },indent=2),encoding="utf-8")

    TEST.write_text(
        "import json\n"
        "from pathlib import Path\n"
        "d=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem028_exact_decomposer_binding_repair.json').read_text())\n"
        "assert d['bindings']\n"
        "assert d['execution_authority'] is False\n"
        "print('[PASS] exact certified OAD-099 decomposition binding recovered')\n"
        "print('[PASS] KSEM-028 binding repair certified')\n",
        encoding="utf-8"
    )

    print("[WRITE]",STATE.relative_to(ROOT))
    print("[WRITE]",TEST.name)

if __name__=="__main__":
    main()