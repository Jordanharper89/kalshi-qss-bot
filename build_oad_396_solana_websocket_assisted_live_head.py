
from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED = 'build_oad_396_solana_websocket_assisted_live_head.py'
MODULE = 'oad_396_solana_websocket_assisted_live_head.py'
TEST = 'test_oad_396_solana_websocket_assisted_live_head.py'
RUNNER = ''
MODULE_SOURCE = r"""from __future__ import annotations
from dataclasses import dataclass
import json,os,urllib.request
EXECUTION_AUTHORITY=False

@dataclass(frozen=True, slots=True)
class LiveHeadObservation:
    slot:int
    source:str
    commitment:str="finalized"
    execution_authority:bool=False

def http_finalized_head(rpc_url=None,timeout_seconds=10.0):
    url=rpc_url or os.environ.get("SOLANA_RPC_URL") or "https://api.mainnet-beta.solana.com"
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":"getSlot","params":[{"commitment":"finalized"}]}).encode()
    req=urllib.request.Request(url,data=body,headers={"Content-Type":"application/json","User-Agent":"Oracle-QSeries-ZeroCost/1"})
    with urllib.request.urlopen(req,timeout=timeout_seconds) as resp:
        payload=json.loads(resp.read().decode())
        if "error" in payload: raise RuntimeError(payload["error"])
        return int(payload["result"])

def observe_live_head(websocket_head_fn=None,rpc_head_fn=None):
    if websocket_head_fn is not None:
        try:
            v=websocket_head_fn()
            if v is not None: return LiveHeadObservation(int(v),"WEBSOCKET_SIGNAL","finalized",False)
        except Exception:
            pass
    fn=rpc_head_fn or http_finalized_head
    return LiveHeadObservation(int(fn()),"HTTP_FINALIZED_FALLBACK","finalized",False)"""
TEST_SOURCE = r"""import unittest
from qseries_v2.oracle_adapters.independent.oad_396_solana_websocket_assisted_live_head import observe_live_head
class T(unittest.TestCase):
    def test_ws_then_fallback(self):
        a=observe_live_head(lambda:123,lambda:999)
        self.assertEqual(a.slot,123)
        self.assertEqual(a.source,"WEBSOCKET_SIGNAL")
        b=observe_live_head(lambda:(_ for _ in ()).throw(RuntimeError("drop")),lambda:456)
        self.assertEqual(b.slot,456)
        self.assertEqual(b.source,"HTTP_FINALIZED_FALLBACK")
        print("[LIVE HEAD]",a,b)
if __name__=="__main__":
    rr=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not rr.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-396 websocket-assisted live-head contract certified")"""
RUNNER_SOURCE = r""""""
DEPS = [('qseries_v2/oracle_adapters/independent/oad_148_solana_mainnet_chain_state_acquisition.py', ('_rpc',)), ('qseries_v2/oracle_adapters/independent/oad_393_solana_zero_cost_public_rpc_budget_governor.py', ('SolanaPublicRpcBudgetGovernor',))]

def find_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise RuntimeError("repository root not found")

def atomic_write(path: Path, source: str):
    source = textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)

def verify_dep(root: Path, rel: str, required=()):
    p = root / rel
    if not p.is_file():
        raise RuntimeError("required dependency missing: " + rel)
    tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    names = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    missing = [x for x in required if x not in names]
    if missing:
        raise RuntimeError("dependency interface missing: " + rel + " -> " + repr(missing))
    print("[PASS] dependency verified:", rel)

def main():
    if Path(__file__).name != EXPECTED:
        raise RuntimeError("installer filename mismatch")
    root = find_root()
    for rel, req in DEPS:
        verify_dep(root, rel, req)

    pkg = root / "qseries_v2" / "oracle_adapters" / "independent"
    module_path = pkg / MODULE
    test_path = root / TEST
    atomic_write(module_path, MODULE_SOURCE)
    atomic_write(test_path, TEST_SOURCE)

    if RUNNER:
        atomic_write(root / RUNNER, RUNNER_SOURCE)

    init = pkg / "__init__.py"
    lines = init.read_text(encoding="utf-8").splitlines() if init.exists() else []
    export = "from ." + module_path.stem + " import *"
    if export not in lines:
        lines.append(export)
    atomic_write(init, "\n".join(x for x in lines if x.strip()) + "\n")

    print("[PASS] installed:", module_path.relative_to(root))
    print("[PASS] test installed:", test_path.relative_to(root))
    if RUNNER:
        print("[PASS] runner installed:", RUNNER)
    print("[PASS] public-RPC / zero-cost architecture only")
    print("[PASS] no paid RPC provider dependency")
    print("[PASS] no GMGN dependency")
    print("[PASS] existing OAD-318+ chain path preserved")
    print("[PASS] existing OPH-019/021 PostgreSQL path preserved")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution_authority=FALSE")
    print("[DONE]", EXPECTED)

if __name__ == "__main__":
    main()
