from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OI-007"
INSTALLER_REVISION = "OI_007_UNIVERSAL_OBSERVATION_HISTORY_FOUNDATION_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"
UPSTREAM = PACKAGE / "oi_006_live_observation_registry.py"
MODULE = PACKAGE / "oi_007_observation_history.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oi_007_observation_history.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType

from .oi_001_universal_observation_intake import deterministic_sha256
from .oi_003_canonical_observation_gateway import CanonicalLiveObservation
from .oi_006_live_observation_registry import verify_live_observation_registry

BUILD_ID = "OI-007"
OI_007_REVISION = "OI_007_UNIVERSAL_OBSERVATION_HISTORY_FOUNDATION_V1"

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


class ObservationHistoryError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ObservationHistorySeries:
    history_key: str
    observations: tuple[CanonicalLiveObservation, ...]
    history_hash: str

    def latest(self) -> CanonicalLiveObservation | None:
        return self.observations[-1] if self.observations else None

    def between(
        self,
        start_at: datetime,
        end_at: datetime,
    ) -> tuple[CanonicalLiveObservation, ...]:
        if not isinstance(start_at, datetime) or not isinstance(end_at, datetime):
            raise TypeError("start_at and end_at must be datetime")
        if start_at.tzinfo is None or end_at.tzinfo is None:
            raise ObservationHistoryError("history query timestamps must be timezone-aware")
        if end_at < start_at:
            raise ObservationHistoryError("end_at must not be before start_at")

        return tuple(
            item
            for item in self.observations
            if start_at <= item.observed_at <= end_at
        )


class UniversalObservationHistory:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False
    qseries_execution_allowed = False

    def __init__(
        self,
        observations: tuple[CanonicalLiveObservation, ...] = (),
    ) -> None:
        values = tuple(observations)

        if any(not isinstance(item, CanonicalLiveObservation) for item in values):
            raise TypeError("all observations must be CanonicalLiveObservation")

        ordered = tuple(
            sorted(
                values,
                key=lambda item: (
                    item.observed_at,
                    item.canonical_observation_id,
                ),
            )
        )

        if values != ordered:
            raise ObservationHistoryError(
                "observations must be deterministically sorted"
            )

        ids = tuple(item.canonical_observation_id for item in values)
        if len(ids) != len(set(ids)):
            raise ObservationHistoryError(
                "duplicate canonical observation id"
            )

        grouped: dict[str, list[CanonicalLiveObservation]] = {}

        for item in values:
            key = self.history_key(
                source_id=item.source_id,
                subject=item.subject,
                observation_type=item.observation_type,
            )
            grouped.setdefault(key, []).append(item)

        frozen = {
            key: tuple(items)
            for key, items in sorted(grouped.items())
        }

        self._observations = values
        self._series = MappingProxyType(frozen)

    @staticmethod
    def history_key(
        *,
        source_id: str,
        subject: str,
        observation_type: str,
    ) -> str:
        return "|".join(
            (
                str(source_id).strip().lower(),
                str(subject).strip().upper(),
                str(observation_type).strip().lower(),
            )
        )

    @property
    def observations(self) -> tuple[CanonicalLiveObservation, ...]:
        return self._observations

    @property
    def history_hash(self) -> str:
        return deterministic_sha256(
            tuple(
                item.canonical_observation_hash
                for item in self._observations
            )
        )

    def series(
        self,
        *,
        source_id: str,
        subject: str,
        observation_type: str,
    ) -> ObservationHistorySeries:
        key = self.history_key(
            source_id=source_id,
            subject=subject,
            observation_type=observation_type,
        )
        values = self._series.get(key, ())
        return ObservationHistorySeries(
            history_key=key,
            observations=values,
            history_hash=deterministic_sha256(
                {
                    "history_key": key,
                    "observation_hashes": tuple(
                        item.canonical_observation_hash
                        for item in values
                    ),
                }
            ),
        )

    def latest(
        self,
        *,
        source_id: str,
        subject: str,
        observation_type: str,
    ) -> CanonicalLiveObservation | None:
        return self.series(
            source_id=source_id,
            subject=subject,
            observation_type=observation_type,
        ).latest()


def verify_observation_history() -> bool:
    verify_live_observation_registry()

    if READ_ONLY is not True:
        raise AssertionError("OI-007 must remain read-only")

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError("OI-007 forbidden capability enabled")

    return True


__all__ = [
    "BUILD_ID",
    "OI_007_REVISION",
    "ObservationHistoryError",
    "ObservationHistorySeries",
    "UniversalObservationHistory",
    "verify_observation_history",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from qseries_v2.observation_intelligence.oi_005_public_market_data_adapter import (
    PublicMarketDataObservationAdapter,
)
from qseries_v2.observation_intelligence.oi_006_live_observation_registry import (
    default_source_registry,
)
from qseries_v2.observation_intelligence.oi_003_canonical_observation_gateway import (
    CanonicalLiveObservationGateway,
)
from qseries_v2.observation_intelligence.oi_001_universal_observation_intake import (
    ObservationSourceIdentity,
    RawObservationEnvelope,
)
from qseries_v2.observation_intelligence.oi_007_observation_history import (
    OI_007_REVISION,
    UniversalObservationHistory,
    verify_observation_history,
)


BASE = datetime(2026, 8, 10, 4, 0, tzinfo=timezone.utc)


def observation(index: int, price: str):
    source = ObservationSourceIdentity(
        source_id="coinbase.public.spot",
        source_kind="market_data",
        provider="Coinbase",
        adapter_id="adapter.coinbase.spot.v1",
    )
    envelope = RawObservationEnvelope(
        source=source,
        external_observation_id=f"BTC-USD-{index}",
        observed_at=BASE + timedelta(minutes=index),
        subject="BTC",
        observation_type="spot_price",
        payload={
            "product_id": "BTC-USD",
            "symbol": "BTC",
            "quote_currency": "USD",
            "price": price,
        },
        metadata={"venue": "coinbase"},
    )
    return CanonicalLiveObservationGateway(
        default_source_registry()
    ).canonicalize(envelope).canonical_observation


class TestOI007(unittest.TestCase):
    def setUp(self):
        self.a = observation(0, "100.0")
        self.b = observation(1, "101.0")
        self.history = UniversalObservationHistory((self.a, self.b))

    def test_foundation(self):
        self.assertTrue(verify_observation_history())

    def test_series(self):
        series = self.history.series(
            source_id="coinbase.public.spot",
            subject="btc",
            observation_type="spot_price",
        )
        self.assertEqual(series.observations, (self.a, self.b))

    def test_latest(self):
        self.assertIs(
            self.history.latest(
                source_id="coinbase.public.spot",
                subject="BTC",
                observation_type="spot_price",
            ),
            self.b,
        )

    def test_range(self):
        series = self.history.series(
            source_id="coinbase.public.spot",
            subject="BTC",
            observation_type="spot_price",
        )
        values = series.between(
            BASE,
            BASE + timedelta(seconds=30),
        )
        self.assertEqual(values, (self.a,))

    def test_deterministic(self):
        x = UniversalObservationHistory((self.a, self.b))
        y = UniversalObservationHistory((self.a, self.b))
        self.assertEqual(x.history_hash, y.history_hash)

    def test_unsorted_rejected(self):
        with self.assertRaises(ValueError):
            UniversalObservationHistory((self.b, self.a))

    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):
            UniversalObservationHistory((self.a, self.a))

    def test_side_effects(self):
        self.assertTrue(self.history.read_only)
        self.assertFalse(self.history.network_allowed)
        self.assertFalse(self.history.persistence_allowed)
        self.assertFalse(self.history.publication_allowed)
        self.assertFalse(self.history.execution_allowed)
        self.assertFalse(self.history.qseries_execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-007 CERTIFICATION TEST")
    print(" UNIVERSAL OBSERVATION HISTORY FOUNDATION")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOI007
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-007")
    print(f"[PASS] Revision: {OI_007_REVISION}")
    print("[PASS] Canonical observation history series certified")
    print("[PASS] Latest and bounded temporal queries certified")
    print("[PASS] History remains source-agnostic and category-agnostic")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-007 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_checked(path: Path, source: str) -> None:
    text = source.lstrip()
    ast.parse(text, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[PASS] Wrote: {path.relative_to(ROOT)}")


def main() -> int:
    print("=" * 72)
    print(" OI-007 INSTALLER")
    print(" UNIVERSAL OBSERVATION HISTORY FOUNDATION")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    if not UPSTREAM.is_file():
        raise RuntimeError(f"Certified OI-006 missing: {UPSTREAM}")

    upstream_hash = sha(UPSTREAM)
    print("[PASS] Certified OI-006 verified read-only")

    affected = (MODULE, TEST, INIT)
    backups = {
        path: path.read_bytes() if path.exists() else None
        for path in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export = "from .oi_007_observation_history import *"

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(current, encoding="utf-8", newline="\n")

        print("[PASS] Updated: qseries_v2\\observation_intelligence\\__init__.py")

        compile(MODULE.read_text(encoding="utf-8"), str(MODULE), "exec")
        compile(TEST.read_text(encoding="utf-8"), str(TEST), "exec")

        if sha(UPSTREAM) != upstream_hash:
            raise RuntimeError("Certified OI-006 changed during install")

        print("[PASS] In-memory compilation verified")
        print("[PASS] Certified OI-006 remained unchanged")

        install_hash = hashlib.sha256(
            MODULE.read_bytes() + TEST.read_bytes()
        ).hexdigest()

        print(f"[PASS] Deterministic install hash: {install_hash}")
        print("[PASS] Network, persistence, publication, and execution disabled")
        print("[DONE] OI-007 INSTALLATION COMPLETE")
        return 0

    except Exception:
        for path, content in backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content)

        print("[ROLLBACK] OI-007 installation failed; all affected files restored")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
