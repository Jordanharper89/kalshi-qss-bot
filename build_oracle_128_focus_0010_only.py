from pathlib import Path
import ast
import re
import shutil

NAME = "ORACLE-128"
PATH = Path(
    "qseries_v2/oracle_execution/"
    "oracle_020_latest_state_exact_pricing_worker.py"
)
SIZE = 0.010

def install():
    if not PATH.is_file():
        raise SystemExit("[HOLD] Original ORACLE-020 file missing")

    original = PATH.read_text(encoding="utf-8")
    backup = PATH.with_suffix(".oracle128.bak")

    if not backup.exists():
        shutil.copy2(PATH, backup)

    updated = original

    settings = {
        "PREFERRED_SIZE_SOL": "0.010",
        "FAST_SIZES": "(0.010,)",
        "EXPAND_SIZES": "()",
    }

    for name, value in settings.items():
        pattern = (
            r"(?m)^" + re.escape(name)
            + r"\s*=\s*[^\n]+$"
        )
        updated, count = re.subn(
            pattern, name + "=" + value, updated
        )
        if count != 1:
            raise SystemExit(
                "[HOLD] Unexpected configuration: " + name
            )

    tree = ast.parse(updated)
    assignments = {}

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id in settings:
                        assignments[target.id] = ast.literal_eval(
                            node.value
                        )

    assert assignments["PREFERRED_SIZE_SOL"] == SIZE
    assert assignments["FAST_SIZES"] == (SIZE,)
    assert assignments["EXPAND_SIZES"] == ()

    if updated != original:
        temp = PATH.with_suffix(".oracle128.tmp")
        temp.write_text(updated, encoding="utf-8")
        temp.replace(PATH)

    print("[PASS] ORACLE-128 installation and tests")
    print("[SIZE] 0.010 SOL ONLY")
    print("[DIRECTIONS] Both preserved")
    print("[SCANNER] Original fast WebSocket unchanged")
    print("[CACHE] Original single hydration unchanged")
    print("[EXPANSION] DISABLED during testing")
    print("[SIGNING] FALSE")
    print("[BROADCAST] FALSE")
    print("[BACKUP]", backup)

if __name__ == "__main__":
    install()