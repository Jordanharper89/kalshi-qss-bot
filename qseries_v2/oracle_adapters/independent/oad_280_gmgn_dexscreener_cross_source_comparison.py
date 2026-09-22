from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .oad_279_gmgn_solana_token_intelligence_adapter import (
    acquire_current_gmgn_solana_token_intelligence,
)
from .oad_263_solana_token_pool_identity_liquidity_expansion import (
    expand_live_solana_token_pools,
)

READ_ONLY = True
PROBABILITY_ENABLED = False
DIRECTION_ENABLED = False
PUBLICATION_ALLOWED = False
EXECUTION_AUTHORITY = False


@dataclass(frozen=True, slots=True)
class GMGNDexScreenerMetricComparison:
    metric: str
    gmgn_value: float
    dexscreener_value: float
    relative_difference: float
    state: str


@dataclass(frozen=True, slots=True)
class GMGNDexScreenerComparison:
    token_address: str
    comparable_fields: int
    agreements: int
    contradictions: int
    metrics: tuple[GMGNDexScreenerMetricComparison, ...]
    gmgn_provider: str = "gmgn"
    dexscreener_provider: str = "dexscreener"
    probability: None = None
    direction: None = None
    execution_authority: bool = False


def _as_float(value: Any):
    if value is None or isinstance(value, bool):
        return None
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    if x != x or x in (float("inf"), float("-inf")):
        return None
    return x


def _find_numeric_by_keys(obj: Any, accepted_keys: set[str]):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if str(key).lower() in accepted_keys:
                numeric = _as_float(value)
                if numeric is not None:
                    return numeric
        for value in obj.values():
            numeric = _find_numeric_by_keys(value, accepted_keys)
            if numeric is not None:
                return numeric
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            numeric = _find_numeric_by_keys(value, accepted_keys)
            if numeric is not None:
                return numeric
    return None


def _best_dex_pool(dex_observation):
    payload = getattr(dex_observation, "payload", None)
    if not isinstance(payload, dict):
        raise RuntimeError("OAD-263 DexScreener observation payload missing")

    pools = payload.get("pools")
    if not isinstance(pools, (list, tuple)) or not pools:
        raise RuntimeError("OAD-263 DexScreener observation contains no pools")

    def liquidity(pool):
        if not isinstance(pool, dict):
            return -1.0
        value = _as_float(pool.get("liquidity_usd"))
        return value if value is not None else -1.0

    candidates = [p for p in pools if isinstance(p, dict)]
    if not candidates:
        raise RuntimeError("OAD-263 DexScreener pool rows invalid")
    return max(candidates, key=liquidity)


def _gmgn_metric_payload(gmgn_observation):
    payload = getattr(gmgn_observation, "payload", None)
    if not isinstance(payload, dict):
        raise RuntimeError("OAD-279 GMGN observation payload missing")
    return payload


def compare_live_gmgn_dexscreener_for_same_token(
    gmgn_observation=None,
    timeout_seconds=30.0,
):
    gmgn = gmgn_observation or acquire_current_gmgn_solana_token_intelligence(
        timeout_seconds=timeout_seconds,
        candidate_limit=5,
    )

    token = str(getattr(gmgn, "token_address", "") or "").strip()
    if not token:
        raise RuntimeError("OAD-279 GMGN observation missing token address")

    dex = expand_live_solana_token_pools(
        token_address=token,
        timeout_seconds=timeout_seconds,
    )

    dex_payload = getattr(dex, "payload", None)
    if not isinstance(dex_payload, dict):
        raise RuntimeError("OAD-263 DexScreener payload invalid")

    dex_token = str(dex_payload.get("token_address") or "").strip()
    if dex_token != token:
        raise RuntimeError(
            "cross-source token identity mismatch: GMGN="
            + token
            + " DexScreener="
            + dex_token
        )

    pool = _best_dex_pool(dex)
    gmgn_payload = _gmgn_metric_payload(gmgn)

    definitions = (
        (
            "price_usd",
            {"price_usd", "priceusd", "price"},
            ("price_usd",),
        ),
        (
            "liquidity_usd",
            {"liquidity_usd", "liquidityusd", "liquidity"},
            ("liquidity_usd",),
        ),
        (
            "volume_h24",
            {
                "volume_h24",
                "volume24h",
                "volume_24h",
                "volume24",
                "volume",
            },
            ("volume_h24",),
        ),
    )

    comparisons = []
    for metric, gmgn_keys, dex_keys in definitions:
        gmgn_value = _find_numeric_by_keys(gmgn_payload, gmgn_keys)

        dex_value = None
        for key in dex_keys:
            dex_value = _as_float(pool.get(key))
            if dex_value is not None:
                break

        if gmgn_value is None or dex_value is None:
            continue

        denom = max(abs(gmgn_value), abs(dex_value), 1e-12)
        relative_difference = abs(gmgn_value - dex_value) / denom
        state = (
            "AGREEMENT_WITHIN_20PCT"
            if relative_difference <= 0.20
            else "CONTRADICTION_GT_20PCT"
        )

        comparisons.append(
            GMGNDexScreenerMetricComparison(
                metric=metric,
                gmgn_value=gmgn_value,
                dexscreener_value=dex_value,
                relative_difference=relative_difference,
                state=state,
            )
        )

    agreements = sum(
        1 for row in comparisons
        if row.state == "AGREEMENT_WITHIN_20PCT"
    )
    contradictions = sum(
        1 for row in comparisons
        if row.state == "CONTRADICTION_GT_20PCT"
    )

    return GMGNDexScreenerComparison(
        token_address=token,
        comparable_fields=len(comparisons),
        agreements=agreements,
        contradictions=contradictions,
        metrics=tuple(comparisons),
        probability=None,
        direction=None,
        execution_authority=False,
    )


# Compatibility helper for the earlier deterministic OAD-280 capability.
def compare_gmgn_dexscreener(gmgn_metrics, dexscreener_metrics):
    if not isinstance(gmgn_metrics, dict) or not isinstance(dexscreener_metrics, dict):
        raise TypeError("comparison inputs must be dictionaries")

    rows = []
    aliases = (
        ("price_usd", ("price_usd", "price"), ("price_usd", "price")),
        ("liquidity_usd", ("liquidity_usd", "liquidity"), ("liquidity_usd", "liquidity")),
        ("volume_h24", ("volume_h24", "volume"), ("volume_h24", "volume")),
    )

    for metric, gkeys, dkeys in aliases:
        gv = next((_as_float(gmgn_metrics.get(k)) for k in gkeys if _as_float(gmgn_metrics.get(k)) is not None), None)
        dv = next((_as_float(dexscreener_metrics.get(k)) for k in dkeys if _as_float(dexscreener_metrics.get(k)) is not None), None)
        if gv is None or dv is None:
            continue
        denom = max(abs(gv), abs(dv), 1e-12)
        rel = abs(gv - dv) / denom
        state = "AGREEMENT_WITHIN_20PCT" if rel <= 0.20 else "CONTRADICTION_GT_20PCT"
        rows.append(GMGNDexScreenerMetricComparison(metric, gv, dv, rel, state))

    return GMGNDexScreenerComparison(
        token_address="deterministic-contract",
        comparable_fields=len(rows),
        agreements=sum(r.state == "AGREEMENT_WITHIN_20PCT" for r in rows),
        contradictions=sum(r.state == "CONTRADICTION_GT_20PCT" for r in rows),
        metrics=tuple(rows),
        probability=None,
        direction=None,
        execution_authority=False,
    )
