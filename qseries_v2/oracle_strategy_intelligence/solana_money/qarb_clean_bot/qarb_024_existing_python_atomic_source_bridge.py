from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from typing import Any

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import (
    qarb_023b_v0_alt_atomic_packet_compaction as packet,
)

SOURCE_MODULE = (
    "qseries_v2.oracle_strategy_intelligence.solana_money."
    "qsb059_gav_reverse_atomic"
)
execution_authority = False


@dataclass(frozen=True)
class BridgeStatus:
    source_module: str
    compose_present: bool
    packet_gate_present: bool
    python_only_entry_present: bool
    execution_authority: bool = False


def load_source():
    return importlib.import_module(SOURCE_MODULE)


def bridge_status() -> BridgeStatus:
    qsb = load_source()
    compose = callable(getattr(qsb, "compose_reverse_candidates", None))
    packet_gate = callable(getattr(packet, "compile_best_v0", None))
    python_entry = compose and callable(getattr(qsb, "run", None))
    return BridgeStatus(
        source_module=SOURCE_MODULE,
        compose_present=compose,
        packet_gate_present=packet_gate,
        python_only_entry_present=python_entry,
    )


def compose_exact_candidates(user: Any, token: Any, pump_pool: Any,
                             meteora_pool: Any, start_sol: float) -> Any:
    qsb = load_source()
    fn = getattr(qsb, "compose_reverse_candidates", None)
    if not callable(fn):
        raise RuntimeError("EXACT_QSB_ATOMIC_COMPOSER_MISSING")
    return fn(user, token, pump_pool, meteora_pool, float(start_sol))


def candidate_instruction_sets(route):
    return load_source().candidate_instruction_sets(route)


def select_packet_fit(payer: Any, recent_blockhash: Any, route: Any):
    rows = candidate_instruction_sets(route)
    if not rows:
        raise RuntimeError("NO_EXACT_ATOMIC_INSTRUCTION_CANDIDATES")

    results = []
    for label, ixs, alts in rows:
        r = packet.compile_best_v0(
            payer=payer,
            recent_blockhash=recent_blockhash,
            instructions=ixs,
            lookup_tables=alts,
        )
        results.append((label, r))
        if r.ok:
            return {
                "ok": True,
                "label": label,
                "result": r,
                "execution_authority": False,
            }

    best = min(
        (r for _, r in results if getattr(r, "best", None) is not None),
        key=lambda x: x.best.size_bytes,
        default=None,
    )
    return {
        "ok": False,
        "status": "NO_PACKET_FIT",
        "best": best,
        "attempted": results,
        "execution_authority": False,
    }


def source_signature() -> str:
    qsb = load_source()
    fn = getattr(qsb, "compose_reverse_candidates", None)
    if not callable(fn):
        return "MISSING"
    return str(inspect.signature(fn))
