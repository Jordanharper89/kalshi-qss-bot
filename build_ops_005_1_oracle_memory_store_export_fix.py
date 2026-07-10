from pathlib import Path

ROOT = Path.cwd()
TARGET = ROOT / "qseries_v2" / "oracle_intelligence" / "oracle_persistent_memory_store.py"
TEST = ROOT / "test_ops_005_oracle_memory_store_runtime_path_migration.py"

code = TARGET.read_text(encoding="utf-8")

# Add backward-compatible module-level factory alias expected by existing __init__.py.
# This is not a runtime path compatibility layer. It preserves the existing public import name
# while keeping RuntimePaths as the canonical database path contract.
if "oracle_persistent_memory_store =" not in code:
    code = code.replace(
        "__all__ = [",
        "oracle_persistent_memory_store = create_oracle_persistent_memory_store\n\n\n__all__ = ["
    )

if '"oracle_persistent_memory_store",' not in code:
    code = code.replace(
        '    "create_oracle_persistent_memory_store",\n',
        '    "create_oracle_persistent_memory_store",\n    "oracle_persistent_memory_store",\n'
    )

TARGET.write_text(code, encoding="utf-8")

print("========================================")
print(" OPS-005.1 PATCH")
print(" Oracle Memory Store Export Fix")
print("========================================")
print(f"[OK] Patched {TARGET}")
print("")
print("[DONE] OPS-005.1 installed")
print("")
print("Run:")
print("py test_ops_005_oracle_memory_store_runtime_path_migration.py")