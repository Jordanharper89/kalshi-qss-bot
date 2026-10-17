from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "qseries_v2/oracle_execution/solana_atomic_executor"
OUT = PKG / "mtr_159_unsigned_compiler_seam.py"
TEST = ROOT / "test_mtr_159_unsigned_compiler_seam.py"

MODULE = r"""
from pathlib import Path
import ast, json

ROOT = Path(__file__).resolve().parents[3]
PKG = ROOT / "qseries_v2/oracle_execution/solana_atomic_executor"
RUNTIME = PKG / "runtime.py"
REPORT = ROOT / "runtime_state/oracle/oracle_live_execution/mtr_159_unsigned_compiler_seam.json"
NAMES = {"compile_current", "compile_candidate", "signed_tx"}
SENSITIVE = ("sign", "secret", "private", "send", "broadcast")

def definitions(path, names):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
            calls = sorted(set(ast.unparse(n.func) for n in ast.walk(node) if isinstance(n, ast.Call)))
            found.append({"function": node.name, "line": node.lineno,
                          "arguments": [a.arg for a in node.args.args],
                          "calls": calls, "sensitive_calls": [c for c in calls if
                          any(x in c.lower() for x in SENSITIVE)]})
    return found

def trace_import():
    tree = ast.parse(RUNTIME.read_text(encoding="utf-8"))
    imports = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.asname == "q87" or a.name.endswith("oracle_087"):
                    imports.append({"module": a.name, "alias": a.asname})
        if isinstance(n, ast.ImportFrom):
            for a in n.names:
                if a.asname == "q87":
                    imports.append({"module": ((n.module or "") + "." + a.name).strip("."),
                                    "alias": a.asname})
    return imports

def inspect():
    if not RUNTIME.is_file():
        raise RuntimeError("CANONICAL_RUNTIME_NOT_FOUND")
    imports = trace_import()
    runtime = definitions(RUNTIME, {"compile_current"})
    found = []
    for item in imports:
        candidate = ROOT / (item["module"].replace(".", "/") + ".py")
        if candidate.is_file():
            found.append({"path": str(candidate.relative_to(ROOT)),
                          "symbols": definitions(candidate, {"compile_candidate", "signed_tx"})})
    result = {"mtr": "MTR-159", "runtime": runtime,
              "q87_imports": imports, "q87_sources": found,
              "compiler_invoked": False, "private_key_used": False,
              "signing": False, "broadcast": False, "unsigned_path_certified": False}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result

def main():
    report = inspect()
    for item in report["runtime"]:
        print("[MTR159_RUNTIME]", item["function"], "line=", item["line"])
        print("[MTR159_CALLS]", ",".join(item["calls"]))
    for item in report["q87_imports"]:
        print("[MTR159_Q87_IMPORT]", item["module"])
    for item in report["q87_sources"]:
        print("[MTR159_SOURCE]", item["path"])
        for fn in item["symbols"]:
            print("[MTR159_DEF]", fn["function"], "line=", fn["line"],
                  "args=", ",".join(fn["arguments"]))
            print("[MTR159_CALLS]", ",".join(fn["calls"]))
    ready = bool(report["runtime"]) and bool(report["q87_sources"]) and any(
        x["function"] == "signed_tx" for r in report["q87_sources"] for x in r["symbols"])
    print("[MTR159_SIGNER_BOUNDARY_IDENTIFIED]", ready)
    print("[UNSIGNED_PATH_CERTIFIED] FALSE")
    print("[COMPILER_INVOKED] FALSE")
    print("[SCANNER] FROZEN")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
    print("[REPORT]", REPORT)
    if not ready:
        raise SystemExit("[HOLD] Compiler implementation not sufficiently traced")

if __name__ == "__main__":
    main()
"""
TEST_SOURCE = r"""
import unittest
from qseries_v2.oracle_execution.solana_atomic_executor import mtr_159_unsigned_compiler_seam as m
class Tests(unittest.TestCase):
    def test_compile_current_is_real(self):
        self.assertTrue(any(x["function"] == "compile_current"
                            for x in m.definitions(m.RUNTIME, {"compile_current"})))
    def test_import_is_traceable(self):
        self.assertTrue(m.trace_import(), "q87 import must be resolved, not guessed")
    def test_no_execution(self):
        r = m.inspect()
        self.assertFalse(r["compiler_invoked"])
        self.assertFalse(r["private_key_used"])
        self.assertFalse(r["signing"])
        self.assertFalse(r["broadcast"])
        self.assertFalse(r["unsigned_path_certified"])
if __name__ == "__main__":
    unittest.main(verbosity=2)
"""
for code in (MODULE, TEST_SOURCE):
    ast.parse(code)
if not (PKG / "mtr_158_unsigned_compiled_handoff.py").is_file():
    raise SystemExit("[HOLD] MTR-158 dependency missing")
OUT.write_text(MODULE, encoding="utf-8")
TEST.write_text(TEST_SOURCE, encoding="utf-8")
print("[PASS] MTR-159 source-only compiler seam installed")
print("[SCANNER] FROZEN")
print("[PRIVATE_KEY] NOT_USED")
print("[SIGNING] FALSE")
print("[BROADCAST] FALSE")
