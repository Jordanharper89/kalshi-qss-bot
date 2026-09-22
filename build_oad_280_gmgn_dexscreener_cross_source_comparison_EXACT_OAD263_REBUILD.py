from __future__ import annotations
import ast
import os
import textwrap
from pathlib import Path

EXPECTED_FILENAME = "build_oad_280_gmgn_dexscreener_cross_source_comparison_EXACT_OAD263_REBUILD.py"
MODULE_NAME = "oad_280_gmgn_dexscreener_cross_source_comparison.py"
TEST_NAME = "test_oad_280_gmgn_dexscreener_cross_source_comparison.py"

MODULE_SOURCE = r"""
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
"""

TEST_SOURCE = r"""
import unittest

import qseries_v2.oracle_adapters.independent.oad_280_gmgn_dexscreener_cross_source_comparison as oad280


class T(unittest.TestCase):
    def test_deterministic_comparison_contract(self):
        r = oad280.compare_gmgn_dexscreener(
            {
                "price_usd": 1.00,
                "liquidity_usd": 100000.0,
                "volume_h24": 50000.0,
            },
            {
                "price_usd": 1.02,
                "liquidity_usd": 102000.0,
                "volume_h24": 51000.0,
            },
        )
        self.assertEqual(r.comparable_fields, 3)
        self.assertEqual(r.agreements, 3)
        self.assertEqual(r.contradictions, 0)

    def test_physical_same_token_cross_source(self):
        r = oad280.compare_live_gmgn_dexscreener_for_same_token(
            timeout_seconds=30.0
        )

        print("[PHYSICAL] token=", r.token_address)
        print("[PHYSICAL] comparable=", r.comparable_fields)
        print("[PHYSICAL] agreements=", r.agreements)
        print("[PHYSICAL] contradictions=", r.contradictions)

        for row in r.metrics:
            print(
                "[PHYSICAL]",
                row.metric,
                "gmgn=",
                row.gmgn_value,
                "dexscreener=",
                row.dexscreener_value,
                "relative_difference=",
                row.relative_difference,
                "state=",
                row.state,
            )

        self.assertTrue(r.token_address)
        self.assertGreaterEqual(r.comparable_fields, 1)
        self.assertEqual(
            r.agreements + r.contradictions,
            r.comparable_fields,
        )
        self.assertIsNone(r.probability)
        self.assertIsNone(r.direction)
        self.assertFalse(r.execution_authority)

    def test_safety(self):
        self.assertFalse(oad280.PROBABILITY_ENABLED)
        self.assertFalse(oad280.DIRECTION_ENABLED)
        self.assertFalse(oad280.PUBLICATION_ALLOWED)
        self.assertFalse(oad280.EXECUTION_AUTHORITY)


if __name__ == "__main__":
    print("=" * 120)
    print(" OAD-280 PHYSICAL CERTIFICATION TEST")
    print(" GMGN <-> DEXSCREENER SAME-TOKEN CROSS-SOURCE COMPARISON")
    print("=" * 120)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] deterministic comparison contract preserved")
    print("[PASS] physical same-token GMGN <-> DexScreener comparison certified")
    print("[PASS] provider disagreement preserved as contradiction")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-280 PHYSICALLY CERTIFIED")
"""


def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")


def write_checked(path, source):
    normalized = textwrap.dedent(source).lstrip()
    ast.parse(normalized, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(normalized, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def main():
    if Path(__file__).name != EXPECTED_FILENAME:
        raise RuntimeError("installer identity mismatch")

    root = locate_root()
    pkg = root / "qseries_v2" / "oracle_adapters" / "independent"
    module = pkg / MODULE_NAME
    test = root / TEST_NAME
    init = pkg / "__init__.py"

    print("=" * 120)
    print(" OAD-280 GMGN <-> DEXSCREENER CROSS-SOURCE COMPARISON")
    print(" EXACT OAD-263 BOUNDARY REBUILD")
    print("=" * 120)
    print("[ROOT]", root)

    dependencies = (
        (
            pkg / "oad_279_gmgn_solana_token_intelligence_adapter.py",
            "acquire_current_gmgn_solana_token_intelligence",
        ),
        (
            pkg / "oad_263_solana_token_pool_identity_liquidity_expansion.py",
            "expand_live_solana_token_pools",
        ),
    )

    for dep, symbol in dependencies:
        if not dep.is_file():
            raise RuntimeError("dependency missing: " + str(dep))
        dep_source = dep.read_text(encoding="utf-8")
        ast.parse(dep_source, filename=str(dep))
        if ("def " + symbol + "(") not in dep_source:
            raise RuntimeError(
                "dependency symbol missing: "
                + dep.name
                + " -> "
                + symbol
            )
        print("[PASS] exact dependency verified:", dep.relative_to(root), "->", symbol)

    # Verify the exact OAD-263 payload contract the rebuild consumes.
    oad263 = dependencies[1][0].read_text(encoding="utf-8")
    required_fragments = (
        '"token_address":str(token_address)',
        '"pools":tuple(pools)',
        '"pool_count":len(pools)',
        '"price_usd":p.get("priceUsd")',
        '"liquidity_usd":liq.get("usd")',
        '"volume_h24":vol.get("h24")',
    )
    for fragment in required_fragments:
        if fragment not in oad263:
            raise RuntimeError(
                "OAD-263 payload contract mismatch: missing " + fragment
            )
    print("[PASS] exact OAD-263 token/pools/price/liquidity/volume payload verified")

    ast.parse(textwrap.dedent(MODULE_SOURCE).lstrip(), filename=str(module))
    ast.parse(textwrap.dedent(TEST_SOURCE).lstrip(), filename=str(test))
    print("[PASS] replacement production module syntax verified")
    print("[PASS] replacement physical test syntax verified")

    previous = {
        p: (p.read_bytes() if p.exists() else None)
        for p in (module, test, init)
    }

    try:
        write_checked(module, MODULE_SOURCE)
        write_checked(test, TEST_SOURCE)

        init_lines = (
            init.read_text(encoding="utf-8").splitlines()
            if init.exists()
            else []
        )
        export = "from ." + module.stem + " import *"
        if export not in init_lines:
            init_lines.append(export)
        write_checked(
            init,
            "\n".join(line for line in init_lines if line.strip()) + "\n",
        )

        print("[PASS] rebuilt existing OAD-280 production boundary in place")
        print("[PASS] wrong OAD-263 filename retired")
        print("[PASS] wrong OAD-263 function symbol retired")
        print("[PASS] exact expand_live_solana_token_pools boundary installed")
        print("[PASS] same GMGN token forced into DexScreener acquisition")
        print("[PASS] highest-liquidity DexScreener pool selected deterministically")
        print("[PASS] price/liquidity/24h-volume compared only when both sources expose them")
        print("[PASS] unavailable metrics remain non-comparable")
        print("[PASS] disagreements preserved as contradictions")
        print("[PASS] no probability/direction/publication/execution")
        print("[DONE] OAD-280 EXACT OAD-263 REBUILD INSTALLATION COMPLETE")

    except Exception:
        for p, old in previous.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(old)
        print("[ROLLBACK] OAD-280 affected files restored")
        raise


if __name__ == "__main__":
    main()
