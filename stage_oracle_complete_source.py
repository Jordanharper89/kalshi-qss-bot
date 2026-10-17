from pathlib import Path
import os
import subprocess

SKIP_DIRS = {
    ".git", "node_modules", "venv", ".venv", "env",
    "__pycache__", ".pytest_cache", ".mypy_cache",
    ".next", "dist", "runtime_state", "secrets",
    "wallets", "oracle_audit", ".idea", ".vscode"
}

SKIP_ROOTS = {
    "state", "logs", "runtime", "small_debug_zip"
}

SOURCE_EXT = {
    ".py", ".mjs", ".cjs", ".js", ".jsx", ".ts", ".tsx",
    ".css", ".html", ".sql", ".toml", ".yaml", ".yml",
    ".md", ".cmd", ".bat", ".ini", ".cfg", ".sh",
    ".proto", ".idl"
}

CONFIG_NAMES = {
    "package.json", "package-lock.json", "tsconfig.json",
    "jsconfig.json", "pyproject.toml", "setup.cfg",
    ".gitignore", "dockerfile", "makefile"
}

branch = subprocess.check_output(
    ["git", "branch", "--show-current"], text=True
).strip()

if branch != "oracle-full-local-sync-20261016":
    raise SystemExit(
        "STOP: switch to oracle-full-local-sync-20261016 first"
    )

raw = subprocess.check_output([
    "git", "ls-files", "-co", "--exclude-standard", "-z"
])

selected = []
skipped_large = []

for entry in raw.split(b"\0"):
    if not entry:
        continue

    name = os.fsdecode(entry).replace("\\", "/")
    path = Path(name)
    parts = [part.lower() for part in path.parts]
    filename = path.name.lower()
    extension = path.suffix.lower()

    if any(part in SKIP_DIRS for part in parts):
        continue
    if parts and parts[0] in SKIP_ROOTS:
        continue
    if filename.startswith(".env"):
        continue
    if any(word in filename for word in (
        "private_key", "keypair.json", "wallet.json",
        "seed_phrase", "recovery_phrase", "credentials.json"
    )):
        continue

    include = (
        extension in SOURCE_EXT
        or filename in CONFIG_NAMES
    )

    if extension == ".json":
        include = (
            name.startswith(("qseries_v2/", "tools/"))
            or filename in CONFIG_NAMES
        )

    if extension == ".txt":
        include = (
            name.startswith(("qseries_v2/", "docs/"))
            or filename.startswith(("requirements", "readme"))
        )

    if not include or not path.is_file():
        continue

    limit = 2_000_000 if extension in {".json", ".txt"} else 10_000_000

    if path.stat().st_size > limit:
        skipped_large.append(name)
        continue

    selected.append(name)

selected = sorted(set(selected))

required = [
    "qseries_v2/oracle_execution/solana_atomic_executor/oracle_500_scanner_machine.py",
    "qseries_v2/oracle_execution/solana_atomic_executor/oracle_504_execution_engine.py",
    "qseries_v2/oracle_execution/solana_atomic_executor/oracle_525_native_inventory_hydration.py",
]

if any(not Path(p).is_file() for p in required):
    raise SystemExit("STOP: required Oracle source file missing")

if not selected:
    raise SystemExit("STOP: no source files found")

subprocess.run(
    ["git", "restore", "--staged", "--", "."],
    check=True
)

payload = b"\0".join(os.fsencode(p) for p in selected) + b"\0"

subprocess.run(
    ["git", "add", "-A", "--pathspec-from-file=-",
     "--pathspec-file-nul"],
    input=payload,
    check=True
)

print("[PASS] COMPLETE ORACLE SOURCE STAGING")
print("[BRANCH]", branch)
print("[SOURCE_FILES_SELECTED]", len(selected))
print("[OVERSIZED_FILES_EXCLUDED]", len(skipped_large))
print("[RUNTIME_AND_SECRET_PATHS_EXCLUDED] TRUE")
print("[READY_FOR_SECURITY_REVIEW] TRUE")
print("[COMMITTED] FALSE")
print("[PUSHED] FALSE")