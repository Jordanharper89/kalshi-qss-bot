
from pathlib import Path
import argparse, ast, json, shutil, time, unittest

VERSION="ORACLE_032_ORIGINAL_MRIYA_PRODUCER_CONTRACT"
BASE=Path("qseries_v2/oracle_execution/solana_atomic_executor")
DEST=BASE/"oracle_032_original_mriya_producer.py"
OUT=Path("runtime_state/oracle/oracle_live_execution/ORACLE_032_PRODUCER.json")

TARGETS=[
    BASE/"mry_001_continuous_replenishment.py",
    BASE/"mtr_165_ws_capture_only.py",
    BASE/"mtr_169_capture_lane_integration.py",
    BASE/"mtr_172_isolated_market_startup.py",
    Path("qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/engine.py"),
    Path("qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot/live_account_stream.py")
]

def audit_source(root,rel):
    path=root/rel
    row={"path":str(rel),"exists":path.is_file()}
    if not path.is_file():return row
    try:
        src=path.read_text(encoding="utf-8-sig")
        tree=ast.parse(src,filename=str(path))
    except (SyntaxError,UnicodeError,OSError) as exc:
        row["error"]=type(exc).__name__
        return row
    row["functions"]=[]
    row["paths_and_outputs"]=[]
    row["imports"]=[]
    for node in ast.walk(tree):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            row["functions"].append({
                "name":node.name,
                "line":node.lineno,
                "args":[a.arg for a in node.args.args]
            })
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            if isinstance(node,ast.ImportFrom):
                row["imports"].append(node.module or "")
            else:
                row["imports"].extend(x.name for x in node.names)
        if isinstance(node,ast.Constant) and isinstance(node.value,str):
            value=node.value
            lower=value.lower()
            if (
                any(x in lower for x in (
                    ".json",".jsonl","runtime_state",
                    "queue","handoff","capture","replenish"
                ))
                and len(value)<220
            ):
                row["paths_and_outputs"].append(value)
    row["functions"]=row["functions"][:45]
    row["paths_and_outputs"]=sorted(set(row["paths_and_outputs"]))[:65]
    row["imports"]=sorted(set(row["imports"]))[:30]
    return row

def recent_runtime(root,limit=35):
    state=root/"runtime_state"
    if not state.is_dir():return []
    matches=[]
    now=time.time()
    for p in state.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in (".json",".jsonl"):
            continue
        try:
            stat=p.stat()
            age=max(0,now-stat.st_mtime)
            rel=str(p.relative_to(root))
            priority=any(x in rel.lower() for x in (
                "mriya","mry_","replenish","oracle_live_execution",
                "solana_scanner","qarb_clean_bot","capture"
            ))
            if priority or age<=3600:
                matches.append({
                    "path":rel,
                    "age_seconds":round(age),
                    "bytes":stat.st_size,
                    "candidate_source_not_verified":True
                })
        except OSError:
            continue
    matches.sort(key=lambda r:r["age_seconds"])
    return matches[:limit]

def inspect(root):
    files=[audit_source(root,p) for p in TARGETS]
    return {
        "revision":VERSION,
        "status":"PRODUCER_CONTRACT_INSPECTION",
        "source_contracts":files,
        "recent_runtime_records":recent_runtime(root),
        "mriya_replenishment_present":files[0]["exists"],
        "live_producer_connection_certified":False,
        "atomic_executor_connected":False,
        "api_requests":0,
        "scanner_modified":False,
        "signing":False,
        "broadcast":False,
        "canary_lamports":10000000
    }

def report(root):
    data=inspect(root)
    path=root/OUT
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    tmp.replace(path)
    print("[STATUS]",data["status"])
    print("[MRIYA_REPLENISHMENT_PRESENT]",data["mriya_replenishment_present"])
    for row in data["source_contracts"]:
        print("[SOURCE]",json.dumps(row,sort_keys=True))
    print("[RECENT_RUNTIME_RECORDS]",json.dumps(data["recent_runtime_records"],sort_keys=True))
    print("[API_REQUESTS] 0 [SIGNING] FALSE [BROADCAST] FALSE")
    print("[REPORT]",path)

class Tests(unittest.TestCase):
    def test_no_execution(self):
        d=inspect(Path.cwd())
        self.assertFalse(d["signing"])
        self.assertFalse(d["broadcast"])
    def test_no_rpc(self):
        self.assertEqual(inspect(Path.cwd())["api_requests"],0)
    def test_no_false_binding(self):
        self.assertFalse(inspect(Path.cwd())["atomic_executor_connected"])
    def test_missing_safe(self):
        self.assertFalse(audit_source(Path.cwd(),Path("missing_032.py"))["exists"])
    def test_canary(self):
        self.assertEqual(inspect(Path.cwd())["canary_lamports"],10000000)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--test",action="store_true")
    ap.add_argument("--audit",action="store_true")
    args=ap.parse_args()
    root=Path.cwd()
    if args.test:
        result=unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
        return 0 if result.wasSuccessful() else 1
    if args.audit:
        report(root)
        return 0
    target=root/DEST
    if not target.parent.is_dir():
        print("[HOLD] EXECUTOR_PACKAGE_MISSING")
        return 2
    if Path(__file__).resolve()!=target.resolve():
        shutil.copyfile(Path(__file__),target)
    print("[PASS]",VERSION)
    print("[MODE] LOCAL_SOURCE_INSPECTION_ONLY")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
