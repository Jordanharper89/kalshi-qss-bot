from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("oracle_consensus_engine.py")

PATCH_BLOCK = r'''

# ============================================================
# ORACLE-046.0.5 Consensus Terminal Formatter
# ============================================================

def _oracle04605_fmt_num(value, digits=2):
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return "0.00"


def _oracle04605_build_compact_card(result, opportunity=None):
    if not isinstance(result, dict):
        return "🧠 ORACLE CONSENSUS\nStatus: unavailable"

    opportunity = opportunity if isinstance(opportunity, dict) else {}

    ticker = (
        opportunity.get("ticker")
        or opportunity.get("market_ticker")
        or result.get("ticker")
        or "UNKNOWN"
    )

    title = (
        opportunity.get("title")
        or opportunity.get("market_title")
        or result.get("title")
        or "Untitled opportunity"
    )

    final = result.get("final_recommendation", "WATCH")
    conf = result.get("consensus_confidence", 0)
    strength = result.get("consensus_strength", "UNKNOWN")
    agreement = result.get("engine_agreement_pct", 0)
    weighted = result.get("weighted_agreement", 0)
    counts = result.get("direction_counts") or {}
    scores = result.get("weighted_direction_scores") or {}
    conflicts = result.get("conflicts") or []

    vote_lines = []
    for direction in ("BUY YES", "BUY NO", "WATCH", "PASS"):
        if direction in counts:
            vote_lines.append(
                f"{direction}: {counts.get(direction, 0)} engines | power {_oracle04605_fmt_num(scores.get(direction, 0))}"
            )

    if not vote_lines:
        vote_lines.append("No engine votes detected")

    conflict_text = ", ".join(conflicts) if conflicts else "None"

    calibration = result.get("calibration") or {}
    adapter = result.get("adapter") or {}

    reason_bits = []

    if adapter.get("status") == "applied":
        reason_bits.append("Signal adapter translated ranked opportunity fields into subsystem votes.")

    if calibration.get("status") == "applied":
        reason_bits.append(
            f"Calibrated recommendation: {calibration.get('calibrated_recommendation', final)}."
        )

    if final == "PASS":
        reason_bits.append("Consensus rejected execution because defensive/pass power dominated or confidence was insufficient.")
    elif final == "WATCH":
        reason_bits.append("Consensus sees enough signal to monitor, but not enough confirmed strength for execution.")
    elif final in ("BUY YES", "BUY NO"):
        reason_bits.append("Consensus reached directional execution-grade agreement.")

    if not reason_bits:
        reason_bits.append("Consensus generated from weighted subsystem votes.")

    return (
        "🧠 ORACLE CONSENSUS\n"
        f"Ticker: {ticker}\n"
        f"Market: {title}\n\n"
        f"Final: {final}\n"
        f"Strength: {strength}\n"
        f"Confidence: {_oracle04605_fmt_num(conf)}%\n"
        f"Engine Agreement: {_oracle04605_fmt_num(agreement)}%\n"
        f"Weighted Agreement: {_oracle04605_fmt_num(weighted)}%\n\n"
        "Votes / Power:\n"
        + "\n".join(f"- {line}" for line in vote_lines)
        + "\n\n"
        f"Conflicts: {conflict_text}\n\n"
        "Reason:\n"
        + "\n".join(f"- {line}" for line in reason_bits)
    )


def _oracle04605_build_terminal_card(result, opportunity=None):
    compact = _oracle04605_build_compact_card(result, opportunity)

    votes = result.get("votes") if isinstance(result, dict) else []
    vote_lines = []

    if isinstance(votes, list):
        for vote in votes:
            if not isinstance(vote, dict):
                continue
            vote_lines.append(
                f"- {vote.get('engine')}: {vote.get('direction')} "
                f"({vote.get('confidence')}% conf, weight {vote.get('weight')})"
            )

    if not vote_lines:
        vote_lines.append("- No detailed votes available")

    return (
        "\n================ ORACLE CONSENSUS TERMINAL ================\n"
        + compact
        + "\n\nDetailed Engine Votes:\n"
        + "\n".join(vote_lines)
        + "\n============================================================\n"
    )


if "OracleConsensusEngine" in globals():
    if "_oracle04605_original_calculate_consensus" not in globals():
        _oracle04605_original_calculate_consensus = OracleConsensusEngine.calculate_consensus

        def _oracle04605_calculate_consensus(self, opportunity):
            result = _oracle04605_original_calculate_consensus(self, opportunity)

            if isinstance(result, dict):
                result["compact_card"] = _oracle04605_build_compact_card(result, opportunity)
                result["terminal_card"] = _oracle04605_build_terminal_card(result, opportunity)
                result["formatter"] = {
                    "version": "ORACLE-046.0.5",
                    "status": "applied",
                    "formats": ["compact_card", "terminal_card"],
                }

            return result

        OracleConsensusEngine.calculate_consensus = _oracle04605_calculate_consensus

# ============================================================
# END ORACLE-046.0.5
# ============================================================
'''


def backup(path):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle046_0_5_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-046.0.5 INSTALLER")
    print(" Consensus Terminal Formatter")
    print("===================================")

    if not TARGET.exists():
        raise FileNotFoundError("oracle_consensus_engine.py not found")

    text = TARGET.read_text(encoding="utf-8", errors="ignore")

    if "ORACLE-046.0.5 Consensus Terminal Formatter" in text:
        print("[SKIP] ORACLE-046.0.5 already installed")
        return

    b = backup(TARGET)

    if 'if __name__ == "__main__":' in text:
        text = text.replace('if __name__ == "__main__":', PATCH_BLOCK + '\n\nif __name__ == "__main__":', 1)
    else:
        text += "\n\n" + PATCH_BLOCK + "\n"

    TARGET.write_text(text, encoding="utf-8")

    print(f"[OK] Patched {TARGET}")
    print(f"[OK] Backup created: {b}")
    print("")
    print("Tests:")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); c=o.status().get('last_ranked',[{}])[0].get('consensus'); print(c.get('compact_card'))\"")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); c=o.status().get('last_ranked',[{}])[0].get('consensus'); print(c.get('formatter'))\"")
    print("")
    print("[DONE] ORACLE-046.0.5 installed")


if __name__ == "__main__":
    main()