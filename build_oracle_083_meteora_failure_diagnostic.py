
"""ORACLE-083: native Meteora simulation failure diagnostics."""
import argparse
import ast
import json
from pathlib import Path

ROOT = Path.cwd()
PKG = ROOT / "qseries_v2/oracle_execution/solana_atomic_executor"
TARGET = PKG / "oracle_077_native_executor.py"
REPORT = ROOT / "runtime_state/oracle/oracle_live_execution/oracle_083_sim_failure.json"
MARK = "ORACLE083_EXACT_SIMULATION_FAILURE_TRACE"

HOOK = '''
# ORACLE083_EXACT_SIMULATION_FAILURE_TRACE
_oracle083_original_simulate = simulate_native

def simulate_native(compiled, user):
    import json
    import re
    from pathlib import Path

    result = _oracle083_original_simulate(compiled, user)
    if not isinstance(result, dict):
        return result

    err = result.get("err")
    if err is None:
        print("[ORACLE083_SIM] SUCCESS", flush=True)
        return result

    def safe(value):
        if isinstance(value, dict):
            return {str(k): safe(v) for k, v in value.items()
                    if str(k).lower() not in (
                        "raw", "transaction", "signature", "secret",
                        "private_key", "rpc_url", "api_key")}
        if isinstance(value, (list, tuple)):
            return [safe(v) for v in value[:20]]
        if isinstance(value, (int, float, bool)) or value is None:
            return value
        text = str(value)
        text = re.sub(r"https?://\\\\S+", "[URL_REDACTED]", text)
        text = re.sub(r"(?i)api.key[=:][^\\\\s&]+", "api_key=[REDACTED]", text)
        return text[:350]

    logs = result.get("logs") or []
    selected = []
    for line in logs:
        text = str(line)
        if any(word in text.lower() for word in (
                "invoke", "failed", "error", "consumed",
                "instruction:", "program log:", "success")):
            selected.append(safe(text))

    index = None
    if isinstance(err, dict):
        instruction = err.get("InstructionError")
        if isinstance(instruction, (list, tuple)) and instruction:
            index = instruction[0]

    payload = {
        "status": "UNSIGNED_SIMULATION_REJECTED",
        "instruction_index": index,
        "error": safe(err),
        "units": safe(result.get("units")),
        "log_count": len(logs),
        "program_trace": selected[-60:],
        "execution_authority": False,
        "broadcast": False,
        "realized_profit": False,
    }
    path = Path("runtime_state/oracle/oracle_live_execution/oracle_083_sim_failure.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print("[ORACLE083_FAILURE]", json.dumps(payload, sort_keys=True), flush=True)
    print("[ORACLE083_REPORT]", path, flush=True)
    return result
'''

def install():
    if not TARGET.is_file():
        raise RuntimeError("ORACLE077_EXECUTOR_NOT_FOUND")
    source = TARGET.read_text(encoding="utf-8")
    if MARK in source:
        print("[PASS] ORACLE083_ALREADY_INSTALLED")
        return
    tree = ast.parse(source)
    names = [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]
    if names.count("simulate_native") != 1:
        raise RuntimeError("ORACLE077_SIMULATION_CONTRACT_MISMATCH")
    updated = source.rstrip() + "\n\n" + HOOK
    ast.parse(updated)
    backup = TARGET.with_name("oracle_077_native_executor.before_oracle083.py")
    if not backup.exists():
        backup.write_text(source, encoding="utf-8")
    TARGET.write_text(updated, encoding="utf-8")
    print("[PASS] ORACLE083_DIAGNOSTIC_INSTALLED")
    print("[BOUNDARY] NO_SCANNER_CHANGE NO_SIGNING NO_BROADCAST")

def test():
    ast.parse(HOOK)
    if TARGET.is_file():
        ast.parse(TARGET.read_text(encoding="utf-8"))
    assert "return result" in HOOK
    assert "instruction_index" in HOOK
    assert "program_trace" in HOOK
    assert "broadcast" in HOOK
    print("[PASS] ORACLE083_OFFLINE_DIAGNOSTIC_TESTS")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()
    test() if args.test else install()
