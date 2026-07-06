from pathlib import Path
from datetime import datetime
import shutil

TARGET = Path("oracle_continuous_intelligence.py")

PATCH_BLOCK = r'''

# ============================================================
# ORACLE-046.0.2 Architecture-Aware Consensus Integration
# ============================================================

try:
    from oracle_consensus_engine import oracle_consensus_engine
except Exception:
    oracle_consensus_engine = None


def _oracle046_apply_consensus_to_ranked(ranked):
    if oracle_consensus_engine is None or not isinstance(ranked, list):
        return ranked

    enriched = []

    for item in ranked:
        if not isinstance(item, dict):
            enriched.append(item)
            continue

        try:
            consensus = oracle_consensus_engine.calculate_consensus(item)

            item["consensus"] = consensus
            item["consensus_confidence"] = consensus.get("consensus_confidence", 0)
            item["consensus_strength"] = consensus.get("consensus_strength", "UNKNOWN")
            item["consensus_final_recommendation"] = consensus.get("final_recommendation", "WATCH")
            item["engine_agreement_pct"] = consensus.get("engine_agreement_pct", 0)
            item["weighted_agreement"] = consensus.get("weighted_agreement", 0)
            item["consensus_conflicts"] = consensus.get("conflicts", [])

            base_score = float(item.get("adaptive_score", item.get("overall_score", 0)) or 0)
            consensus_conf = float(consensus.get("consensus_confidence", 0) or 0)
            weighted_agreement = float(consensus.get("weighted_agreement", 0) or 0)

            item["consensus_rank_score"] = round(
                (base_score * 0.45)
                + (consensus_conf * 0.40)
                + (weighted_agreement * 0.15),
                2,
            )

        except Exception as exc:
            item["consensus"] = {
                "status": "error",
                "error": str(exc),
                "final_recommendation": "WATCH",
            }
            item["consensus_confidence"] = 0
            item["consensus_strength"] = "ERROR"
            item["consensus_final_recommendation"] = "WATCH"
            item["consensus_rank_score"] = float(item.get("adaptive_score", item.get("overall_score", 0)) or 0)

        enriched.append(item)

    enriched.sort(
        key=lambda x: x.get("consensus_rank_score", x.get("adaptive_score", x.get("overall_score", 0)))
        if isinstance(x, dict) else 0,
        reverse=True,
    )

    return enriched


def _oracle046_enrich_state():
    try:
        if "_state" in globals() and isinstance(_state, dict):
            if isinstance(_state.get("last_ranked"), list):
                _state["last_ranked"] = _oracle046_apply_consensus_to_ranked(_state["last_ranked"])

            _state["consensus_status"] = {
                "status": "ok" if oracle_consensus_engine is not None else "missing",
                "ranked_with_consensus": len(_state.get("last_ranked") or []),
                "top_consensus": (_state.get("last_ranked") or [])[:5],
            }
    except Exception as exc:
        if "_state" in globals() and isinstance(_state, dict):
            _state["consensus_status"] = {
                "status": "error",
                "error": str(exc),
            }


if "_oracle046_original_process_opportunities" not in globals() and "process_opportunities" in globals():
    _oracle046_original_process_opportunities = process_opportunities

    def process_opportunities(*args, **kwargs):
        result = _oracle046_original_process_opportunities(*args, **kwargs)

        if isinstance(result, list):
            result = _oracle046_apply_consensus_to_ranked(result)

        if isinstance(result, dict):
            for key in ("ranked", "last_ranked", "opportunities"):
                if isinstance(result.get(key), list):
                    result[key] = _oracle046_apply_consensus_to_ranked(result[key])

        _oracle046_enrich_state()
        return result


if "_oracle046_original_run_cycle" not in globals() and "run_cycle" in globals():
    _oracle046_original_run_cycle = run_cycle

    def run_cycle(*args, **kwargs):
        result = _oracle046_original_run_cycle(*args, **kwargs)
        _oracle046_enrich_state()
        return result


if "_oracle046_original_status" not in globals() and "status" in globals():
    _oracle046_original_status = status

    def status(*args, **kwargs):
        result = _oracle046_original_status(*args, **kwargs)
        _oracle046_enrich_state()

        if isinstance(result, dict):
            if isinstance(result.get("last_ranked"), list):
                result["last_ranked"] = _oracle046_apply_consensus_to_ranked(result["last_ranked"])

            if isinstance(result.get("pipeline_status"), dict):
                ps = result["pipeline_status"]
                if isinstance(ps.get("last_ranked"), list):
                    ps["last_ranked"] = _oracle046_apply_consensus_to_ranked(ps["last_ranked"])

            result["consensus_status"] = {
                "status": "ok" if oracle_consensus_engine is not None else "missing",
                "ranked_with_consensus": len(result.get("last_ranked") or result.get("pipeline_status", {}).get("last_ranked") or []),
            }

        return result


if "_oracle046_original_diagnostics" not in globals() and "diagnostics" in globals():
    _oracle046_original_diagnostics = diagnostics

    def diagnostics(*args, **kwargs):
        result = _oracle046_original_diagnostics(*args, **kwargs)
        if isinstance(result, dict):
            result["oracle_046_consensus_integration"] = {
                "status": "installed",
                "engine_available": oracle_consensus_engine is not None,
            }
        return result

# ============================================================
# END ORACLE-046.0.2
# ============================================================
'''


def backup(path: Path):
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    b = path.with_suffix(path.suffix + f".bak_oracle046_0_2_{stamp}")
    shutil.copy2(path, b)
    return b


def main():
    print("===================================")
    print(" ORACLE-046.0.2 INSTALLER")
    print(" Architecture-Aware Consensus Fix")
    print("===================================")

    if not TARGET.exists():
        raise FileNotFoundError("oracle_continuous_intelligence.py not found")

    text = TARGET.read_text(encoding="utf-8", errors="ignore")

    if "ORACLE-046.0.2 Architecture-Aware Consensus Integration" in text:
        print("[SKIP] ORACLE-046.0.2 already installed")
        return

    b = backup(TARGET)

    marker = 'if __name__ == "__main__":'
    if marker in text:
        text = text.replace(marker, PATCH_BLOCK + "\n\n" + marker, 1)
    else:
        text = text + "\n\n" + PATCH_BLOCK + "\n"

    TARGET.write_text(text, encoding="utf-8")

    print(f"[OK] Patched {TARGET}")
    print(f"[OK] Backup created: {b}")
    print("")
    print("Tests:")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); import pprint; pprint.pp(o.status().get('last_ranked', [{}])[0].get('consensus'))\"")
    print(" python -c \"import oracle_continuous_intelligence as o; o.run_cycle(); print(o.status().get('last_ranked', [{}])[0].get('consensus_final_recommendation'))\"")
    print("")
    print("[DONE] ORACLE-046.0.2 installed")


if __name__ == "__main__":
    main()