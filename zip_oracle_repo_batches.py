from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path.cwd()
OUT = ROOT / "_oracle_repo_batches"
MAX_RAW = 20 * 1024 * 1024

SKIP_DIRS = {
    ".git", "venv", ".venv", "__pycache__", ".pytest_cache",
    "runtime", "_oracle_repo_batches", "node_modules"
}
SKIP_NAMES = {
    ".env", ".env.local", ".env.production",
    "private_key.pem", "kalshi_private_key.pem"
}
SKIP_SUFFIXES = {
    ".zip", ".pyc", ".pyo", ".log", ".sqlite", ".db", ".pem", ".key"
}

OUT.mkdir(exist_ok=True)

files = []
for p in ROOT.rglob("*"):
    if not p.is_file():
        continue
    rel = p.relative_to(ROOT)
    if any(part in SKIP_DIRS for part in rel.parts):
        continue
    if p.name in SKIP_NAMES or p.suffix.lower() in SKIP_SUFFIXES:
        continue
    files.append((p, rel, p.stat().st_size))

files.sort(key=lambda x: str(x[1]).lower())

batch = 1
used = 0
z = None

for src, rel, size in files:
    if z is None or (used and used + size > MAX_RAW):
        if z:
            z.close()
        path = OUT / f"oracle_repo_batch_{batch:03d}.zip"
        z = ZipFile(path, "w", ZIP_DEFLATED, compresslevel=6)
        print("[BATCH]", path.name)
        batch += 1
        used = 0
    z.write(src, rel)
    used += size

if z:
    z.close()

print("[DONE] files=", len(files), "batches=", batch - 1)
print("[OUTPUT]", OUT)