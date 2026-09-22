from __future__ import annotations

import hashlib
import json
from pathlib import Path

BUILD_ID = "OAR-030"
OAR_030_REVISION = "OAR_030_FINAL_CERTIFICATION_FREEZE_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False
FROZEN = True
DEFECT_CORRECTIONS_ONLY = True

ROOT = Path('C:\\Users\\jorda\\OneDrive\\Documents\\GitHub\\kalshi-qss-bot')
MANIFEST = Path('C:\\Users\\jorda\\OneDrive\\Documents\\GitHub\\kalshi-qss-bot\\qseries_v2\\observation_adapter_runtime\\OAR_FINAL_FREEZE_MANIFEST.json')


def _sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def verify_oar_final_freeze() -> bool:
    payload = json.loads(
        MANIFEST.read_text(
            encoding="utf-8"
        )
    )

    if payload["frozen"] is not True:
        return False

    if (
        payload["defect_corrections_only"]
        is not True
    ):
        return False

    for item in payload["files"]:
        path = ROOT / item["path"]

        if not path.is_file():
            return False

        if _sha(path) != item["sha256"]:
            return False

    return True


__all__ = [
    "BUILD_ID",
    "OAR_030_REVISION",
    "READ_ONLY",
    "EXECUTION_ALLOWED",
    "PUBLICATION_ALLOWED",
    "PERSISTENCE_ALLOWED",
    "FROZEN",
    "DEFECT_CORRECTIONS_ONLY",
    "verify_oar_final_freeze",
]
