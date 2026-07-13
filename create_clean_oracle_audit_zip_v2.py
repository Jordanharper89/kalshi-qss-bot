from __future__ import annotations

import os
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
OUTPUT_ZIP = REPO_ROOT.parent / f"{REPO_ROOT.name}-oracle-audit.zip"

EXCLUDED_DIR_NAMES = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "node_modules",
}

EXCLUDED_FILE_NAMES = {
    ".env", ".env.local", ".env.production", ".env.development",
    ".env.test", "desktop.ini",
}

EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".pyd", ".log"}

SECRET_NAME_FRAGMENTS = (
    "database_url", "secret", "credentials", "private_key",
)


def should_exclude(path: Path) -> bool:
    relative = path.relative_to(REPO_ROOT)

    if any(part in EXCLUDED_DIR_NAMES for part in relative.parts[:-1]):
        return True

    name_lower = path.name.lower()

    if name_lower in EXCLUDED_FILE_NAMES:
        return True

    if name_lower.startswith(".env."):
        return True

    if path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True

    if any(fragment in name_lower for fragment in SECRET_NAME_FRAGMENTS):
        return True

    return False


def main() -> None:
    print("========================================")
    print(" Q SERIES / ORACLE CLEAN AUDIT ZIP")
    print("========================================")
    print(f"[ROOT] {REPO_ROOT}")
    print(f"[ZIP ] {OUTPUT_ZIP}")

    included_count = 0
    excluded_count = 0

    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    with zipfile.ZipFile(
        OUTPUT_ZIP,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for root, dirs, files in os.walk(REPO_ROOT):
            root_path = Path(root)
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIR_NAMES]

            for filename in files:
                source_path = root_path / filename

                if should_exclude(source_path):
                    excluded_count += 1
                    continue

                archive_name = Path(REPO_ROOT.name) / source_path.relative_to(REPO_ROOT)
                archive.write(source_path, archive_name.as_posix())
                included_count += 1

    print(f"[OK] Included files: {included_count}")
    print(f"[OK] Excluded files: {excluded_count}")
    print("[DONE] Clean audit ZIP created:")
    print(OUTPUT_ZIP)


if __name__ == "__main__":
    main()
