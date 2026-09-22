from pathlib import Path
import zipfile
from datetime import datetime

ROOT = Path.cwd()
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT = ROOT / f"kalshi-qss-bot-oracle-audit-{STAMP}.zip"

EXCLUDED_DIRS = {
    ".git", "venv", ".venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "node_modules"
}
EXCLUDED_FILES = {
    ".env", ".env.local", ".env.production", ".env.development"
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}

def allowed(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in rel.parts):
        return False
    if path.name in EXCLUDED_FILES:
        return False
    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    if path == OUTPUT:
        return False
    if path.name.startswith("kalshi-qss-bot-oracle-audit-") and path.suffix == ".zip":
        return False
    return True

files = [p for p in ROOT.rglob("*") if p.is_file() and allowed(p)]

with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED) as zf:
    for path in files:
        zf.write(path, path.relative_to(ROOT))

print("========================================")
print(" ORACLE CLEAN AUDIT ZIP")
print("========================================")
print(f"[OK] Created: {OUTPUT}")
print(f"[OK] Files included: {len(files)}")
print("[OK] runtime/oracle_live_shadow included if present")
print("[OK] .env excluded")
print("[OK] venv excluded")
print("[OK] .git excluded")
print()
print("[DONE] Upload this ZIP to ChatGPT")
