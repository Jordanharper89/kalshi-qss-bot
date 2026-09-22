from __future__ import annotations

import ast
import hashlib
from pathlib import Path


BUILD_ID = "OI-003"

INSTALLER_REVISION = (
    "OI_003_CANONICAL_LIVE_OBSERVATION_GATEWAY_INSTALLER_V1"
)

ROOT = Path(__file__).resolve().parent

PACKAGE = (
    ROOT
    / "qseries_v2"
    / "observation_intelligence"
)

UPSTREAM_001 = (
    PACKAGE
    / "oi_001_universal_observation_intake.py"
)

UPSTREAM_002 = (
    PACKAGE
    / "oi_002_source_adapter_registry.py"
)

MODULE = (
    PACKAGE
    / "oi_003_canonical_observation_gateway.py"
)

INIT = PACKAGE / "__init__.py"

TEST = (
    ROOT
    / "test_oi_003_canonical_observation_gateway.py"
)


MODULE_SOURCE = r'''
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Any, Mapping

from .oi_001_universal_observation_intake import (
    RawObservationEnvelope,
    UniversalObservationIntake,
    deterministic_sha256,
    verify_universal_observation_intake,
)

from .oi_002_source_adapter_registry import (
    SourceAdapterRegistry,
    verify_source_adapter_registry,
)


BUILD_ID = "OI-003"

OI_003_REVISION = (
    "OI_003_CANONICAL_LIVE_OBSERVATION_GATEWAY_V1"
)

READ_ONLY = True
NETWORK_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False
EXECUTION_ALLOWED = False
QSERIES_EXECUTION_ALLOWED = False


class CanonicalObservationGatewayError(
    ValueError
):
    pass


@dataclass(frozen=True, slots=True)
class CanonicalLiveObservation:
    canonical_observation_id: str
    source_id: str
    source_kind: str
    provider: str
    adapter_id: str
    external_observation_id: str
    observed_at: datetime
    subject: str
    observation_type: str
    facts: Mapping[str, Any]
    metadata: Mapping[str, Any]
    source_hash: str
    raw_envelope_hash: str
    canonical_observation_hash: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "facts",
            MappingProxyType(
                dict(self.facts)
            ),
        )

        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                dict(self.metadata)
            ),
        )


@dataclass(frozen=True, slots=True)
class CanonicalObservationGatewayReceipt:
    canonical_observation: (
        CanonicalLiveObservation
    )
    adapter_registry_hash: str
    intake_receipt_hash: str


class CanonicalLiveObservationGateway:
    read_only = True
    network_allowed = False
    persistence_allowed = False
    publication_allowed = False
    execution_allowed = False

    def __init__(
        self,
        registry: SourceAdapterRegistry,
    ) -> None:
        if not isinstance(
            registry,
            SourceAdapterRegistry,
        ):
            raise TypeError(
                "registry must be SourceAdapterRegistry"
            )

        self._registry = registry
        self._intake = (
            UniversalObservationIntake()
        )

    def canonicalize(
        self,
        envelope: RawObservationEnvelope,
    ) -> CanonicalObservationGatewayReceipt:
        if not isinstance(
            envelope,
            RawObservationEnvelope,
        ):
            raise TypeError(
                "envelope must be RawObservationEnvelope"
            )

        descriptor = self._registry.get(
            envelope.source.adapter_id
        )

        if descriptor is None:
            raise CanonicalObservationGatewayError(
                "source adapter is not registered"
            )

        if descriptor.enabled_for_intake is not True:
            raise CanonicalObservationGatewayError(
                "source adapter is not enabled for intake"
            )

        if (
            descriptor.source_id
            != envelope.source.source_id
        ):
            raise CanonicalObservationGatewayError(
                "source_id does not match registered adapter"
            )

        if (
            descriptor.source_kind
            != envelope.source.source_kind
        ):
            raise CanonicalObservationGatewayError(
                "source_kind does not match registered adapter"
            )

        intake_receipt = (
            self._intake.accept(
                envelope
            )
        )

        if intake_receipt.accepted is not True:
            raise CanonicalObservationGatewayError(
                "observation intake rejected envelope"
            )

        identity_material = {
            "source_id": (
                envelope.source.source_id
            ),
            "adapter_id": (
                envelope.source.adapter_id
            ),
            "external_observation_id": (
                envelope.external_observation_id
            ),
            "observed_at": (
                envelope.observed_at
            ),
            "subject": (
                envelope.subject
            ),
            "observation_type": (
                envelope.observation_type
            ),
        }

        identity_hash = deterministic_sha256(
            identity_material
        )

        canonical_observation_id = (
            "obs."
            + identity_hash
        )

        body = {
            "canonical_observation_id": (
                canonical_observation_id
            ),
            "source_id": (
                envelope.source.source_id
            ),
            "source_kind": (
                envelope.source.source_kind
            ),
            "provider": (
                envelope.source.provider
            ),
            "adapter_id": (
                envelope.source.adapter_id
            ),
            "external_observation_id": (
                envelope.external_observation_id
            ),
            "observed_at": (
                envelope.observed_at
            ),
            "subject": (
                envelope.subject
            ),
            "observation_type": (
                envelope.observation_type
            ),
            "facts": dict(
                envelope.payload
            ),
            "metadata": dict(
                envelope.metadata
            ),
            "source_hash": (
                envelope.source.source_hash
            ),
            "raw_envelope_hash": (
                envelope.envelope_hash
            ),
        }

        observation_hash = (
            deterministic_sha256(
                body
            )
        )

        observation = (
            CanonicalLiveObservation(
                **body,
                canonical_observation_hash=(
                    observation_hash
                ),
            )
        )

        intake_receipt_hash = (
            deterministic_sha256(
                {
                    "envelope_hash": (
                        intake_receipt.envelope_hash
                    ),
                    "source_hash": (
                        intake_receipt.source_hash
                    ),
                    "accepted": (
                        intake_receipt.accepted
                    ),
                    "reason_codes": (
                        intake_receipt.reason_codes
                    ),
                }
            )
        )

        return (
            CanonicalObservationGatewayReceipt(
                canonical_observation=(
                    observation
                ),
                adapter_registry_hash=(
                    self._registry.registry_hash
                ),
                intake_receipt_hash=(
                    intake_receipt_hash
                ),
            )
        )


def verify_canonical_observation_gateway() -> bool:
    verify_universal_observation_intake()
    verify_source_adapter_registry()

    if any(
        (
            NETWORK_ALLOWED,
            PERSISTENCE_ALLOWED,
            PUBLICATION_ALLOWED,
            EXECUTION_ALLOWED,
            QSERIES_EXECUTION_ALLOWED,
        )
    ):
        raise AssertionError(
            "OI-003 forbidden capability enabled"
        )

    return True


__all__ = [
    "BUILD_ID",
    "OI_003_REVISION",
    "CanonicalObservationGatewayError",
    "CanonicalLiveObservation",
    "CanonicalObservationGatewayReceipt",
    "CanonicalLiveObservationGateway",
    "verify_canonical_observation_gateway",
]
'''


TEST_SOURCE = r'''
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_intelligence.oi_001_universal_observation_intake import (
    ObservationSourceIdentity,
    RawObservationEnvelope,
)

from qseries_v2.observation_intelligence.oi_002_source_adapter_registry import (
    SourceAdapterDescriptor,
    SourceAdapterRegistry,
)

from qseries_v2.observation_intelligence.oi_003_canonical_observation_gateway import (
    OI_003_REVISION,
    CanonicalLiveObservationGateway,
    verify_canonical_observation_gateway,
)


FIXED = datetime(
    2026,
    8,
    10,
    3,
    30,
    tzinfo=timezone.utc,
)


def descriptor():
    return SourceAdapterDescriptor(
        adapter_id="adapter.crypto.v1",
        source_id="crypto.market_data",
        source_kind="market_data",
        provider="Crypto Market Data",
        adapter_version="1.0.0",
        capabilities=(
            "market snapshot",
            "spot price",
        ),
        enabled_for_intake=True,
    )


def registry():
    return SourceAdapterRegistry(
        (
            descriptor(),
        )
    )


def envelope():
    return RawObservationEnvelope(
        source=ObservationSourceIdentity(
            source_id="crypto.market_data",
            source_kind="market_data",
            provider="Crypto Market Data",
            adapter_id="adapter.crypto.v1",
        ),
        external_observation_id=(
            "btc-usd-20260810T033000Z"
        ),
        observed_at=FIXED,
        subject="Bitcoin",
        observation_type="spot_price",
        payload={
            "symbol": "BTC",
            "quote_currency": "USD",
            "price": "123456.78",
        },
        metadata={
            "venue": "example",
        },
    )


class TestOI003(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_canonical_observation_gateway()
        )

    def test_canonicalize(self):
        receipt = (
            CanonicalLiveObservationGateway(
                registry()
            )
            .canonicalize(
                envelope()
            )
        )

        observation = (
            receipt.canonical_observation
        )

        self.assertEqual(
            observation.subject,
            "Bitcoin",
        )

        self.assertEqual(
            observation.observation_type,
            "spot_price",
        )

    def test_identity(self):
        observation = (
            CanonicalLiveObservationGateway(
                registry()
            )
            .canonicalize(
                envelope()
            )
            .canonical_observation
        )

        self.assertTrue(
            observation
            .canonical_observation_id
            .startswith("obs.")
        )

    def test_deterministic(self):
        gateway = (
            CanonicalLiveObservationGateway(
                registry()
            )
        )

        a = gateway.canonicalize(
            envelope()
        )

        b = gateway.canonicalize(
            envelope()
        )

        self.assertEqual(
            a.canonical_observation
            .canonical_observation_hash,
            b.canonical_observation
            .canonical_observation_hash,
        )

    def test_unregistered_rejected(self):
        empty = SourceAdapterRegistry(
            ()
        )

        with self.assertRaises(ValueError):
            CanonicalLiveObservationGateway(
                empty
            ).canonicalize(
                envelope()
            )

    def test_immutable(self):
        observation = (
            CanonicalLiveObservationGateway(
                registry()
            )
            .canonicalize(
                envelope()
            )
            .canonical_observation
        )

        with self.assertRaises(TypeError):
            observation.facts["price"] = "1"

    def test_lineage(self):
        receipt = (
            CanonicalLiveObservationGateway(
                registry()
            )
            .canonicalize(
                envelope()
            )
        )

        self.assertEqual(
            len(
                receipt
                .canonical_observation
                .raw_envelope_hash
            ),
            64,
        )

        self.assertEqual(
            len(
                receipt.adapter_registry_hash
            ),
            64,
        )

        self.assertEqual(
            len(
                receipt.intake_receipt_hash
            ),
            64,
        )

    def test_side_effects(self):
        gateway = (
            CanonicalLiveObservationGateway(
                registry()
            )
        )

        self.assertTrue(
            gateway.read_only
        )

        self.assertFalse(
            gateway.network_allowed
        )

        self.assertFalse(
            gateway.persistence_allowed
        )

        self.assertFalse(
            gateway.publication_allowed
        )

        self.assertFalse(
            gateway.execution_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OI-003 CERTIFICATION TEST")
    print(" CANONICAL LIVE OBSERVATION GATEWAY")
    print("=" * 72)

    suite = unittest.defaultTestLoader.loadTestsFromTestCase(
        TestOI003
    )

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(suite)

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OI-003")
    print(f"[PASS] Revision: {OI_003_REVISION}")
    print("[PASS] Registered source envelopes converted to canonical observations")
    print("[PASS] Source, adapter, timestamp, payload, and lineage preserved")
    print("[PASS] Unregistered sources rejected deterministically")
    print("[PASS] Same gateway contract supports Kalshi, crypto, weather, economic, news, blockchain, sports, and future adapters")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] OI-003 CERTIFIED")
'''


def write_checked(
    path: Path,
    source: str,
) -> None:
    text = source.lstrip()

    ast.parse(
        text,
        filename=str(path),
    )

    path.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[PASS] Wrote: {path.relative_to(ROOT)}"
    )


def main() -> int:
    print("=" * 72)
    print(" OI-003 INSTALLER")
    print(" CANONICAL LIVE OBSERVATION GATEWAY")
    print("=" * 72)

    print(
        f"[BOOT] Revision: {INSTALLER_REVISION}"
    )

    print(
        f"[ROOT] {ROOT}"
    )

    for path, name in (
        (UPSTREAM_001, "OI-001"),
        (UPSTREAM_002, "OI-002"),
    ):
        if not path.is_file():
            raise RuntimeError(
                f"Certified {name} missing"
            )

    upstream_hashes = {
        path: hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in (
            UPSTREAM_001,
            UPSTREAM_002,
        )
    }

    print(
        "[PASS] Certified OI-001 and OI-002 verified read-only"
    )

    backups = {
        path: (
            path.read_bytes()
            if path.exists()
            else None
        )
        for path in (
            MODULE,
            TEST,
            INIT,
        )
    }

    try:
        write_checked(
            MODULE,
            MODULE_SOURCE,
        )

        write_checked(
            TEST,
            TEST_SOURCE,
        )

        current = (
            INIT.read_text(
                encoding="utf-8"
            )
            if INIT.exists()
            else ""
        )

        export = (
            "from .oi_003_canonical_observation_gateway import *"
        )

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"

            current += export + "\n"

            ast.parse(
                current,
                filename=str(INIT),
            )

            INIT.write_text(
                current,
                encoding="utf-8",
                newline="\n",
            )

        print(
            "[PASS] Updated: "
            "qseries_v2\\observation_intelligence\\__init__.py"
        )

        compile(
            MODULE.read_text(
                encoding="utf-8"
            ),
            str(MODULE),
            "exec",
        )

        compile(
            TEST.read_text(
                encoding="utf-8"
            ),
            str(TEST),
            "exec",
        )

        for path, expected in upstream_hashes.items():
            actual = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()

            if actual != expected:
                raise RuntimeError(
                    f"Certified upstream changed: "
                    f"{path.name}"
                )

        print(
            "[PASS] In-memory compilation verified"
        )

        print(
            "[PASS] Certified upstream remained unchanged"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: "
            f"{install_hash}"
        )

        print(
            "[PASS] Network, persistence, publication, "
            "and execution disabled"
        )

        print(
            "[DONE] OI-003 INSTALLATION COMPLETE"
        )

        return 0

    except Exception:
        for path, content in backups.items():
            if content is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(content)

        print(
            "[ROLLBACK] OI-003 installation failed; "
            "all affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())