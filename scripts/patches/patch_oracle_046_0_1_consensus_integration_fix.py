from pathlib import Path
from datetime import datetime
import shutil
import re

ROOT = Path.cwd()
TARGET = ROOT / "oracle_continuous_intelligence.py"

PATCH_CODE = r'''
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

    helper = r'''

def _apply_consensus_to_ranked(ranked):
    """
    ORACLE-046.0.1
    Enrich ranked opportunities with Consensus Engine output.
    """
    if oracle_consensus_engine is None:
        return ranked

    if not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        try:
            if not isinstance(item, dict):
                enriched.append(item)
                continue

            consensus = oracle_consensus_engine.calculate_consensus(item)

            item["consensus"] = consensus
            item["consensus_confidence"] = consensus.get("consensus_confidence", 0)
            item["consensus_strength"] = consensus.get("consensus_strength", "UNKNOWN")
            item["consensus_final_recommendation"] = consensus.get("final_recommendation", "WATCH")
            item["engine_agreement_pct"] = consensus.get("engine_agreement_pct", 0)
            item["weighted_agreement"] = consensus.get("weighted_agreement", 0)
            item["consensus_conflicts"] = consensus.get("conflicts", [])
            item["terminal_summary"] = consensus.get("terminal_summary", "")

            # Consensus-aware ranking score.
            base = float(item.get("adaptive_score", item.get("overall_score", 0)) or 0)
            conf = float(consensus.get("consensus_confidence", 0) or 0)
            weighted = float(consensus.get("weighted_agreement", 0) or 0)

            item["consensus_rank_score"] = round(
                (base * 0.45) + (conf * 0.40) + (weighted * 0.15),
                2,
            )

            enriched.append(item)

        except Exception as exc:
            if isinstance(item, dict):
                item["consensus"] = {
                    "status": "error",
                    "error": str(exc),
                    "final_recommendation": "WATCH",
                }
            enriched.append(item)

    enriched.sort(
        key=lambda x: x.get("consensus_rank_score", x.get("adaptive_score", x.get("overall_score", 0)))
        if isinstance(x, dict) else 0,
        reverse=True,
    )

    return enriched
'''

    if "def _apply_consensus_to_ranked" not in text:
        # Add helper before diagnostics/status functions if possible.
        marker = "\ndef diagnostics("
        if marker in text:
            text = text.replace(marker, helper + marker, 1)
        else:
            text += helper

    # Patch common ranked assignment patterns.
    replacements = [
        (
            r'(_state\["last_ranked"\]\s*=\s*)(ranked)',
            r'\1_apply_consensus_to_ranked(ranked)'
        ),
        (
            r"(_state\['last_ranked'\]\s*=\s*)(ranked)",
            r"\1_apply_consensus_to_ranked(ranked)"
        ),
        (
            r'("last_ranked"\s*:\s*)(ranked)',
            r'\1_apply_consensus_to_ranked(ranked)'
        ),
        (
            r"('last_ranked'\s*:\s*)(ranked)",
            r"\1_apply_consensus_to_ranked(ranked)"
        ),
    ]

    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text)

    # If ranked is returned directly from process_opportunities, wrap it.
    text = re.sub(
        r"return\s+ranked",
        "return _apply_consensus_to_ranked(ranked)",
        text
    )

    if text == original:
        print("[WARN] No changes made. File may already be patched or structure is unusual.")
        return

    b = backup(TARGET)
    TARGET.write_text(text, encoding="utf-8")

    print("===================================")
    print(" ORACLE-046.0.1 INSTALLED")
    print(" Consensus Integration Fix")
    print("===================================")
    print(f"Backup created: {b}")
    print("")
    print("Tests:")
    print(" python oracle_continuous_intelligence.py")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); import pprint; pprint.pp(o.status().get('last_ranked', [{}])[0].get('consensus'))\"")


if __name__ == "__main__":
    patch()
'''

Path("patch_oracle_046_0_1_consensus_integration_fix_inner.py").write_text(PATCH_CODE, encoding="utf-8")
exec(PATCH_CODE)