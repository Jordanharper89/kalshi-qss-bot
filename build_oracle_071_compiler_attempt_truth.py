"""ORACLE-071: show bounded compiler attempt diagnostics."""
from pathlib import Path
import ast
import shutil
import sys

TARGET = Path(
    "qseries_v2/oracle_execution/solana_atomic_executor/"
    "oracle_051_original_scanner_alt_and_size_gate.py"
)
MARKER = "ORACLE071_COMPILER_ATTEMPT_TRUTH"


def install():
    source = TARGET.read_text(encoding="utf-8")
    if MARKER in source:
        print("[PASS] ORACLE071_ALREADY_INSTALLED")
        return
    tree = ast.parse(source)
    matches = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name == "compile_existing_alt":
                matches.append(node)
    assert len(matches) == 1, "COMPILER_FUNCTION_NOT_UNIQUE"
    function = matches[0]
    lines = source.splitlines(keepends=True)
    insertion = None
    for i in range(function.lineno - 1, function.end_lineno):
        if 'result["reason"] = "HOLD_NO_LEGAL_HELPER_COMPLETE_V0"' in lines[i]:
            insertion = i + 1
            break
    assert insertion is not None, "COMPILER_REJECTION_ANCHOR_MISSING"
    indent = lines[insertion - 1][:len(lines[insertion - 1]) - len(lines[insertion - 1].lstrip())]
    addition = (
        indent + "# " + MARKER + "\n"
        + indent + "for attempt in result['attempts'][:8]:\n"
        + indent + "    print('[ORACLE071_COMPILE_ATTEMPT]', "
        + "{k: attempt.get(k) for k in "
        + "('candidate', 'alt_count', 'alt_check', 'error', 'detail', 'bytes') "
        + "if k in attempt}, flush=True)\n"
    )
    lines.insert(insertion, addition)
    updated = "".join(lines)
    ast.parse(updated)
    backup = TARGET.with_name(TARGET.stem + ".before_oracle071.py")
    if not backup.exists():
        shutil.copy2(TARGET, backup)
    TARGET.write_text(updated, encoding="utf-8")
    print("[PASS] ORACLE071_COMPILER_ATTEMPT_TRUTH_INSTALLED")
    print("[BOUNDARY] DIAGNOSTICS_ONLY_NO_SIGNING_NO_BROADCAST")


def test():
    source = TARGET.read_text(encoding="utf-8")
    ast.parse(source)
    assert MARKER in source
    assert "HOLD_NO_LEGAL_HELPER_COMPLETE_V0" in source
    assert "ORACLE071_COMPILE_ATTEMPT" in source
    print("[PASS] ORACLE071_COMPILER_ATTEMPT_TRUTH_TEST")


if __name__ == "__main__":
    test() if "--test" in sys.argv else install()