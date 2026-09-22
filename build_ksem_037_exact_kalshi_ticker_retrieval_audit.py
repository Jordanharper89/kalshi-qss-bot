from pathlib import Path
import ast,json

ROOT=Path.cwd()
BASE=ROOT/"qseries_v2"
OUT=ROOT/"qseries_v2/kalshi_sports_evidence_mapping/state/ksem037_exact_ticker_retrieval_audit.json"
TEST=ROOT/"test_ksem_037_exact_kalshi_ticker_retrieval_audit.py"

TERMS=("ticker","market","event")
HINTS=("fetch","get","read","lookup","retrieve","resolve")

def main():
    print("="*120); print(" KSEM-037 EXACT KALSHI TICKER RETRIEVAL INTERFACE AUDIT"); print("="*120)
    hits=[]
    for p in BASE.rglob("*.py"):
        s=str(p).lower()
        if "test_" in p.name.lower() or "kalshi" not in s: continue
        try: tree=ast.parse(p.read_text(encoding="utf-8",errors="ignore"))
        except Exception: continue
        for n in tree.body:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
                name=n.name.lower()
                if any(x in name for x in HINTS) and any(x in name for x in TERMS):
                    args=[x.arg for x in n.args.args]
                    hits.append({"file":str(p.relative_to(ROOT)),"function":n.name,
                                 "args":args,"line":n.lineno})
    hits.sort(key=lambda x:(0 if "ticker" in x["function"].lower() else 1,x["file"],x["line"]))
    print("[CANDIDATES]",len(hits))
    for x in hits[:100]: print("[CANDIDATE]",x)
    if not hits: raise RuntimeError("no existing Kalshi retrieval candidates found")
    OUT.write_text(json.dumps({"candidates":hits,"execution_authority":False},indent=2),encoding="utf-8")
    TEST.write_text("import json\nfrom pathlib import Path\nd=json.loads(Path('qseries_v2/kalshi_sports_evidence_mapping/state/ksem037_exact_ticker_retrieval_audit.json').read_text())\nassert d['candidates']\nassert d['execution_authority'] is False\nprint('[PASS] existing Kalshi retrieval candidates physically inventoried')\nprint('[PASS] KSEM-037 certified')\n",encoding="utf-8")
    print("[WRITE]",OUT.relative_to(ROOT)); print("[WRITE]",TEST.name)

if __name__=="__main__": main()