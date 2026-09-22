from __future__ import annotations

from pathlib import Path

from .oiar_054_proven_current_trader_analytics import (
    read_latest_current_trader_analytics,
)

OIAR_055_BUILD_ID = "OIAR-055"
OIAR_055_REVISION = "OIAR_055_PROVEN_CURRENT_OPERATOR_TERMINAL_CUTOVER_V1"

TOKENS = (
    "what do you like",
    "plays for today",
    "plays today",
    "what are the plays",
    "anything bullish",
    "anything bearish",
    "strongest",
    "what should i watch",
    "live opportunities",
    "edge right now",
)


def is_current_trader_query(q):
    n = " ".join(str(q or "").lower().split())
    return any(t in n for t in TOKENS)


def _score(m):
    try:
        return float(
            m.get("admission", {}).get("admission_score", 0) or 0
        )
    except Exception:
        return 0.0


def _direction(m):
    c = m.get("candidate", {})
    f = m.get("features", {})

    for k in (
        "research_direction",
        "direction",
        "candidate_direction",
    ):
        v = c.get(k) or f.get(k)
        if v:
            return str(v).upper()

    return "NEUTRAL"


def render_current_trader_read(root=None, limit=5):
    x = read_latest_current_trader_analytics(root)

    if not x:
        raise RuntimeError(
            "OIAR-055 requires OIAR-054 analytics snapshot"
        )

    markets = sorted(
        x.get("markets", []),
        key=lambda m: (-_score(m), m.get("market_id", "")),
    )[:max(1, min(int(limit), 10))]

    lines = [
        "=" * 80,
        "ORACLE CURRENT TRADER READ",
        "PROVEN CURRENT CANONICAL COHORT | INDEXED HISTORY | OIA ANALYTICS",
        "-" * 80,
    ]

    for i, m in enumerate(markets, 1):
        meta = m.get("market", {})
        adm = m.get("admission", {})
        use = m.get("usefulness", {})
        cand = m.get("candidate", {})

        lines += [
            f"#{i} {meta.get('title') or m.get('market_id')}",
            f"   Market: {m.get('market_id')}",
            f"   Direction: {_direction(m)}",
            (
                f"   Admission: "
                f"{adm.get('admission_status', 'UNKNOWN')} | "
                f"Score: {adm.get('admission_score', 0)}"
            ),
            (
                f"   Usefulness: "
                f"{use.get('usefulness_classification', 'UNKNOWN')} | "
                f"Score: {use.get('usefulness_score', 0)}"
            ),
            (
                f"   Candidate: "
                f"{cand.get('candidate_family', 'UNKNOWN')} | "
                f"History rows: {m.get('history_rows', 0)}"
            ),
            "",
        ]

    lines += [
        "No order placement. Q Series execution authority remains separate.",
        "=" * 80,
    ]

    return tuple(lines)


def bind_current_trader_terminal(base_module, root=None):
    if getattr(base_module, "_oiar055_bound", False):
        return base_module

    original = base_module.display_query
    active = Path(
        root or base_module.repository_root()
    ).resolve()

    def display_query(
        query,
        *,
        session=None,
        root=None,
        builder=None,
        write=print,
    ):
        canonical = base_module.normalize_query(query)
        use = Path(root or active).resolve()

        if is_current_trader_query(canonical):
            for line in render_current_trader_read(use, 5):
                write(line)
            return None

        kwargs = {
            "session": session,
            "root": use,
            "write": write,
        }

        if builder is not None:
            kwargs["builder"] = builder

        return original(canonical, **kwargs)

    base_module.display_query = display_query
    base_module._oiar055_bound = True

    return base_module


def physical_probe(root=None):
    lines = render_current_trader_read(root, 5)

    return {
        "lines": len(lines),
        "header": lines[1],
        "execution_authority": False,
    }
