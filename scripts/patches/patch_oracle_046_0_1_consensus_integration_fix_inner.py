
"""
ORACLE-046.0.1 Consensus Integration Fix

Safely integrates oracle_consensus_engine into function-based
oracle_continuous_intelligence.py architecture.
"""

from pathlib import Path
from datetime import datetime
import shutil
import re


TARGET = Path("oracle_continuous_intelligence.py")


def backup(path: Path):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(path.suffix + f".bak_oracle046_0_1_{stamp}")
    shutil.copy2(path, backup_path)
    return backup_path


def patch():
    if not TARGET.exists():
        raise FileNotFoundError("oracle_continuous_intelligence.py not found")

    text = TARGET.read_text(encoding="utf-8", errors="ignore")
    original = text

    if "from oracle_consensus_engine import oracle_consensus_engine" not in text:
        text = (
            "try:\n"
            "    from oracle_consensus_engine import oracle_consensus_engine\n"
            "except Exception:\n"
            "    oracle_consensus_engine = None\n\n"
            + text
        )

    helper = r