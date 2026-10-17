"""MTR-157: precise compiled-v0 artifact handoff; no signing or network in default mode."""
import argparse
import ast
import base64
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "qseries_v2/oracle_execution/solana_atomic_executor/runtime.py"
CANONICAL = "HSEM6g4Txajd6EHPav7GBanr4eXc5zzSs4cmySthg97r"

def contract():
    tree = ast.parse(RUNTIME.read_text(encoding="utf-8"))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            calls = [ast.unparse(c.func) for c in ast.walk(node) if isinstance(c, ast.Call)]
            selected = [c for c in calls if "compile_candidate" in c or "signed_tx" in c or "simulate_current" in c]
            if selected:
                found.append((node.name, node.lineno, tuple(sorted(set(selected)))))
    return found

def verify_file(path):
    from .mtr_153_v0_alt_account_resolver import _parse_v0
    raw = base64.b64decode(Path(path).read_text(encoding="ascii").strip(), validate=True)
    if not 1 <= len(raw) <= 1232:
        raise ValueError("TX_SIZE_INVALID")
    _, instructions, refs = _parse_v0(raw)
    if CANONICAL not in (table for table, _, _ in refs):
        raise ValueError("CANONICAL_ALT_NOT_REFERENCED")
    return {"tx_sha256": hashlib.sha256(raw).hexdigest(), "instructions": len(instructions), "lookup_tables": tuple(x[0] for x in refs)}

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--transaction-base64-file", type=Path)
    args = ap.parse_args(argv)
    if not RUNTIME.is_file():
        raise SystemExit("[HOLD] Canonical runtime missing")
    rows = contract()
    for name, line, calls in rows:
        print("[MTR157_COMPILE_PATH]", name, "line=", line, "calls=", ",".join(calls))
    if not rows:
        raise SystemExit("[HOLD] Compiler/simulation path not found")
    if args.transaction_base64_file:
        try:
            result = verify_file(args.transaction_base64_file)
        except (OSError, ValueError, TypeError) as exc:
            raise SystemExit("[HOLD] Invalid compiled v0 transaction: " + type(exc).__name__) from exc
        print("[MTR157_TX_SHA256]", result["tx_sha256"])
        print("[MTR157_ALT_MATCH] TRUE")
        print("[MTR157_INSTRUCTIONS]", result["instructions"])
        print("[MTR157_TRANSACTION_LINK] OFFLINE_ONLY")
    else:
        print("[MTR157_TRANSACTION_LINK] AWAITING_CANONICAL_COMPILED_V0_FILE")
    print("[RPC] NOT_CALLED")
    print("[PROTECTED_PROFIT] FALSE")
    print("[PRIVATE_KEY] NOT_USED")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")

if __name__ == "__main__":
    main()
