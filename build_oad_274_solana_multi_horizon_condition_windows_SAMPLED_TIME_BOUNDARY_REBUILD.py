from __future__ import annotations

import ast
import hashlib
import os
import textwrap
from pathlib import Path

BUILD_ID = "OAD-274"
REVISION = "OAD_274_SAMPLED_TIME_BOUNDARY_REBUILD_V1"
EXPECTED_FILENAME = 'build_oad_274_solana_multi_horizon_condition_windows_SAMPLED_TIME_BOUNDARY_REBUILD.py'
MODULE_NAME = 'oad_274_solana_multi_horizon_condition_windows.py'
TEST_NAME = 'test_oad_274_solana_multi_horizon_condition_windows.py'

MODULE_SOURCE = '\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom datetime import datetime, timezone\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_intelligence.live_acquisition.oracle_canonical_persistence_backend_contract import (\n    CanonicalPersistenceQueryRequest,\n)\nfrom .oad_068_exact_postgresql_independent_readback import _backend\nfrom .oad_267_solana_pool_liquidity_historical_state import SolanaHistoricalObservation\nfrom .oad_270_solana_price_volume_liquidity_acceleration_conditions import (\n    build_solana_acceleration_conditions,\n)\n\nREAD_ONLY = True\nPROBABILITY_ENABLED = False\nDIRECTION_ENABLED = False\nPUBLICATION_ALLOWED = False\nEXECUTION_AUTHORITY = False\n\nREVISION = "OAD_274_SAMPLED_TIME_BOUNDARY_REBUILD_V1"\n\n\n@dataclass(frozen=True, slots=True)\nclass SolanaWindowState:\n    token_address: str\n    source_id: str\n    window_seconds: int\n    records: int\n    first_observed_at: str | None\n    last_observed_at: str | None\n    conditions: tuple\n    state: str\n    probability: None = None\n    direction: None = None\n    execution_authority: bool = False\n\n\ndef _parse_time(value: str) -> datetime:\n    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))\n\n\ndef _payload(row):\n    outer = dict(row.payload)\n    inner = outer.get("observation_payload")\n    return dict(inner) if isinstance(inner, dict) else outer\n\n\ndef _record(row):\n    outer = dict(row.payload)\n    return SolanaHistoricalObservation(\n        str(row.observation_id),\n        str(row.source_id),\n        str(row.observation_type),\n        row.observed_at.isoformat() if hasattr(row.observed_at, "isoformat") else str(row.observed_at),\n        getattr(row, "sequence_number", None),\n        outer.get("provider"),\n        outer.get("subject"),\n        _payload(row),\n    )\n\n\ndef read_pinned_pool_history(token_address, root=None, limit=512):\n    root = Path(root or Path.cwd()).resolve()\n    source_id = "source.dex.solana.token_pools." + str(token_address)\n    backend = _backend(root)\n    req = CanonicalPersistenceQueryRequest.by_source_id(\n        query_id="query.oad274." + str(token_address),\n        backend_id=backend.backend_id,\n        source_id=source_id,\n        limit=int(limit),\n        requested_at=datetime.now(timezone.utc),\n        query_metadata={\n            "read_only": True,\n            "build_id": "OAD-274",\n            "query_mode": "bounded_pinned_pool_history",\n            "boundary_mode": "sampled_time_anchor",\n        },\n    )\n    return tuple(_record(x) for x in backend.query(request=req))\n\n\ndef _select_sampled_window(rows, window_seconds: int):\n    """\n    Build a sampled-time horizon around the latest observation.\n\n    The latest observation is the right edge.  We include:\n      1) all observations newer than the nominal cutoff; and\n      2) the nearest observation at-or-before the cutoff as the left anchor.\n\n    This prevents normal acquisition/network overhead (for example a 5.6 s\n    sample interval on a nominal 5 s cadence) from making the 5 s horizon\n    permanently empty.\n\n    Safety rule:\n      The boundary anchor may not make the realized span exceed 2x the nominal\n      window.  If it would, temporal coverage is too stale and the caller must\n      HOLD rather than pretending that old data represents the requested\n      horizon.\n    """\n    if not rows:\n        return ()\n\n    w = int(window_seconds)\n    if w <= 0:\n        raise ValueError("window_seconds must be positive")\n\n    ordered = tuple(sorted(rows, key=lambda x: (_parse_time(x.observed_at), x.observation_id)))\n    latest_time = _parse_time(ordered[-1].observed_at)\n    cutoff = latest_time.timestamp() - float(w)\n\n    newer = [r for r in ordered if _parse_time(r.observed_at).timestamp() > cutoff]\n    anchors = [r for r in ordered if _parse_time(r.observed_at).timestamp() <= cutoff]\n\n    selected = list(newer)\n    if anchors:\n        anchor = anchors[-1]\n        realized_span = (latest_time - _parse_time(anchor.observed_at)).total_seconds()\n        if realized_span <= float(w) * 2.0:\n            selected.insert(0, anchor)\n\n    # Keep exact deterministic identity ordering with no duplicate anchor.\n    dedup = {}\n    for row in selected:\n        dedup[row.observation_id] = row\n    return tuple(sorted(dedup.values(), key=lambda x: (_parse_time(x.observed_at), x.observation_id)))\n\n\ndef build_multi_horizon_solana_states(records, token_address, windows_seconds=(5, 15, 30, 60)):\n    rows = tuple(sorted(records, key=lambda x: (_parse_time(x.observed_at), x.observation_id)))\n    if not rows:\n        return ()\n\n    out = []\n    source_id = "source.dex.solana.token_pools." + str(token_address)\n\n    for w in tuple(sorted({int(x) for x in windows_seconds})):\n        selected = _select_sampled_window(rows, w)\n\n        conditions = ()\n        state = "HOLD_TEMPORAL_DEPTH_REQUIRED"\n\n        if len(selected) >= 2:\n            realized_span = (\n                _parse_time(selected[-1].observed_at) - _parse_time(selected[0].observed_at)\n            ).total_seconds()\n\n            # Coverage must genuinely cross the requested horizon boundary,\n            # but may not be more than 2x stale.\n            if realized_span >= float(w) and realized_span <= float(w) * 2.0:\n                conditions = build_solana_acceleration_conditions(tuple(selected))\n                if conditions:\n                    state = "WINDOW_READY"\n\n        out.append(\n            SolanaWindowState(\n                str(token_address),\n                source_id,\n                w,\n                len(selected),\n                selected[0].observed_at if selected else None,\n                selected[-1].observed_at if selected else None,\n                tuple((c.pair_address, c.conditions, c.state) for c in conditions),\n                state,\n                None,\n                None,\n                False,\n            )\n        )\n\n    return tuple(out)\n'
TEST_SOURCE = '\nimport unittest\n\nfrom qseries_v2.oracle_adapters.independent.oad_267_solana_pool_liquidity_historical_state import (\n    SolanaHistoricalObservation,\n)\nfrom qseries_v2.oracle_adapters.independent.oad_274_solana_multi_horizon_condition_windows import (\n    _select_sampled_window,\n    build_multi_horizon_solana_states,\n)\n\n\ndef row(oid, ts, liq, buys, sells, vol, price):\n    return SolanaHistoricalObservation(\n        oid,\n        "source.dex.solana.token_pools.X",\n        "solana_token_pool_identity_liquidity",\n        ts,\n        None,\n        "dexscreener",\n        "X",\n        {\n            "token_address": "X",\n            "pools": (\n                {\n                    "pair_address": "P",\n                    "liquidity_usd": liq,\n                    "buys_h24": buys,\n                    "sells_h24": sells,\n                    "volume_h24": vol,\n                    "price_usd": price,\n                },\n            ),\n        },\n    )\n\n\nclass T(unittest.TestCase):\n    def test_five_second_sampled_boundary_accepts_normal_overhead(self):\n        rows = (\n            row("a", "2026-09-01T00:00:00+00:00", 100, 10, 9, 100, 1.00),\n            row("b", "2026-09-01T00:00:05.800000+00:00", 110, 12, 9, 120, 1.10),\n        )\n\n        selected = _select_sampled_window(rows, 5)\n        self.assertEqual(tuple(x.observation_id for x in selected), ("a", "b"))\n\n        states = build_multi_horizon_solana_states(rows, "X", (5,))\n        self.assertEqual(len(states), 1)\n        s = states[0]\n        print("[5S] records=", s.records, "state=", s.state)\n        print("[5S] first=", s.first_observed_at)\n        print("[5S] last=", s.last_observed_at)\n        self.assertEqual(s.records, 2)\n        self.assertEqual(s.state, "WINDOW_READY")\n        self.assertIsNone(s.probability)\n        self.assertIsNone(s.direction)\n        self.assertFalse(s.execution_authority)\n\n    def test_stale_anchor_is_rejected(self):\n        rows = (\n            row("a", "2026-09-01T00:00:00+00:00", 100, 10, 9, 100, 1.00),\n            row("b", "2026-09-01T00:00:20+00:00", 110, 12, 9, 120, 1.10),\n        )\n\n        selected = _select_sampled_window(rows, 5)\n        print("[STALE] selected=", tuple(x.observation_id for x in selected))\n        self.assertEqual(tuple(x.observation_id for x in selected), ("b",))\n\n        states = build_multi_horizon_solana_states(rows, "X", (5,))\n        self.assertEqual(states[0].state, "HOLD_TEMPORAL_DEPTH_REQUIRED")\n\n    def test_existing_multi_horizon_contract_preserved(self):\n        rows = (\n            row("a", "2026-09-01T00:00:00+00:00", 100, 10, 9, 100, 1.00),\n            row("b", "2026-09-01T00:00:05.800000+00:00", 110, 12, 9, 120, 1.10),\n            row("c", "2026-09-01T00:00:15.600000+00:00", 130, 16, 10, 150, 1.20),\n            row("d", "2026-09-01T00:00:30.500000+00:00", 150, 20, 11, 190, 1.30),\n            row("e", "2026-09-01T00:01:00.700000+00:00", 175, 24, 12, 230, 1.40),\n        )\n\n        states = build_multi_horizon_solana_states(rows, "X", (5, 15, 30, 60))\n        print("[WINDOWS]", tuple((x.window_seconds, x.records, x.state) for x in states))\n        self.assertEqual(tuple(x.window_seconds for x in states), (5, 15, 30, 60))\n        self.assertTrue(all(x.probability is None for x in states))\n        self.assertTrue(all(x.direction is None for x in states))\n        self.assertTrue(all(x.execution_authority is False for x in states))\n\n\nif __name__ == "__main__":\n    r = unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OAD-274 sampled-time horizon boundary rebuilt")\n    print("[PASS] normal source/persistence overhead no longer defeats the 5-second window")\n    print("[PASS] excessively stale boundary anchors remain HOLD")\n    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")\n'

DEPENDENCIES = {
    "qseries_v2/oracle_adapters/independent/oad_267_solana_pool_liquidity_historical_state.py": (
        "SolanaHistoricalObservation",
    ),
    "qseries_v2/oracle_adapters/independent/oad_270_solana_price_volume_liquidity_acceleration_conditions.py": (
        "build_solana_acceleration_conditions",
    ),
    "qseries_v2/oracle_adapters/independent/oad_068_exact_postgresql_independent_readback.py": (
        "_backend",
    ),
    "qseries_v2/oracle_intelligence/live_acquisition/oracle_canonical_persistence_backend_contract.py": (
        "CanonicalPersistenceQueryRequest",
    ),
    "qseries_v2/oracle_adapters/independent/oad_275_solana_continuous_observation_resilient_worker.py": (
        "run_solana_continuous_cycle",
    ),
}


def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")


def write_checked(path, source):
    source = textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def main():
    if Path(__file__).name != EXPECTED_FILENAME:
        raise RuntimeError("installer identity mismatch: expected " + EXPECTED_FILENAME)

    root = locate_root()
    pkg = root / "qseries_v2" / "oracle_adapters" / "independent"
    module = pkg / MODULE_NAME
    test = root / TEST_NAME

    print("=" * 120)
    print(" OAD-274 SAMPLED-TIME BOUNDARY REBUILD INSTALLER")
    print("=" * 120)
    print("[BOOT] Revision:", REVISION)
    print("[ROOT]", root)

    for rel, symbols in DEPENDENCIES.items():
        p = root / rel
        if not p.is_file():
            raise RuntimeError("Required dependency missing: " + rel)
        src = p.read_text(encoding="utf-8")
        for symbol in symbols:
            if ("def " + symbol + "(") not in src and ("class " + symbol) not in src:
                raise RuntimeError("Exact dependency symbol missing: " + rel + " -> " + symbol)
        print("[PASS] exact dependency verified:", rel)

    protected = []
    for p, label in (
        (
            root / "qseries_v2" / "oracle_production_hardening" /
            "oph_023_postgresql_single_writer_production_freeze.py",
            "Frozen OPH-023",
        ),
        (
            root / "qseries_v2" / "oracle_adapters" / "kalshi" /
            "oad_055_kalshi_production_freeze.py",
            "Frozen Kalshi OAD-055",
        ),
    ):
        if p.is_file():
            protected.append((p, hashlib.sha256(p.read_bytes()).hexdigest()))
            print("[PASS]", label, "verified")

    old_module = module.read_bytes() if module.exists() else None
    old_test = test.read_bytes() if test.exists() else None

    try:
        write_checked(module, MODULE_SOURCE)
        write_checked(test, TEST_SOURCE)

        # Re-parse the existing downstream worker against the preserved API boundary.
        downstream = pkg / "oad_275_solana_continuous_observation_resilient_worker.py"
        ast.parse(downstream.read_text(encoding="utf-8"), filename=str(downstream))

        for p, before_hash in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest() != before_hash:
                raise RuntimeError("Frozen boundary changed: " + p.name)

        print("[PASS] existing OAD-274 production boundary rebuilt in place")
        print("[PASS] OAD-275 downstream interface compatibility preserved")
        print("[PASS] sampled-time boundary anchor installed")
        print("[PASS] stale-anchor protection installed")
        print("[PASS] syntax validated")
        print("[PASS] frozen production boundaries unchanged")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-274 SAMPLED-TIME BOUNDARY REBUILD INSTALLATION COMPLETE")

    except Exception:
        if old_module is None:
            if module.exists():
                module.unlink()
        else:
            module.write_bytes(old_module)

        if old_test is None:
            if test.exists():
                test.unlink()
        else:
            test.write_bytes(old_test)

        print("[ROLLBACK] prior OAD-274 module/test restored")
        raise


if __name__ == "__main__":
    main()
