from __future__ import annotations

import ast
import hashlib
from pathlib import Path

BUILD_ID = "OAD-005"
INSTALLER_REVISION = "OAD_005_CRYPTO_OBSERVATION_BRIDGE_INSTALLER_V1"

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "observation_adapters"
OI_PACKAGE = ROOT / "qseries_v2" / "observation_intelligence"

UPSTREAMS = (
    PACKAGE / "oad_001_adapter_foundation.py",
    PACKAGE / "oad_002_adapter_contract.py",
    PACKAGE / "oad_003_adapter_registry.py",
)

OI_FREEZE = OI_PACKAGE / "oi_final_certification_freeze.py"
OI_MANIFEST = OI_PACKAGE / "OI_FINAL_FREEZE_MANIFEST.json"

MODULE = PACKAGE / "oad_005_crypto_observation_bridge.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_oad_005_crypto_observation_bridge.py"

MODULE_SOURCE = r"""
from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from datetime import datetime, timezone
from types import ModuleType
from typing import Any, Callable, Mapping

from .oad_001_adapter_foundation import (
    build_adapter_descriptor,
)
from .oad_002_adapter_contract import (
    ObservationAdapterRequest,
    ObservationAdapterResult,
)

BUILD_ID = "OAD-005"
OAD_005_REVISION = "OAD_005_CRYPTO_OBSERVATION_BRIDGE_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
ORDER_PLACEMENT_ALLOWED = False

FROZEN_OI_MODULE = (
    "qseries_v2.observation_intelligence."
    "oi_005_public_market_data_adapter"
)

ADAPTER_ID = "adapter.crypto.observe.v1"
PROVIDER_ID = "coinbase"
SOURCE_DOMAIN = "crypto_market_data"

CAPABILITIES = (
    "market_snapshot",
    "spot_price",
)

_DISCOVERY_NAMES = (
    "observe",
    "collect",
    "acquire",
    "fetch",
    "snapshot",
    "get_spot_price",
    "get_market_snapshot",
)


def _safe_payload(value: Any) -> tuple[Mapping[str, Any], ...]:
    if value is None:
        return ()

    if isinstance(value, Mapping):
        return (dict(value),)

    if isinstance(value, (list, tuple)):
        result = []
        for item in value:
            if isinstance(item, Mapping):
                result.append(dict(item))
            elif hasattr(item, "__dict__"):
                result.append(dict(vars(item)))
            else:
                result.append({"value": item})
        return tuple(result)

    if hasattr(value, "__dict__"):
        return (dict(vars(value)),)

    return ({"value": value},)


def _resolve_callable(
    module: ModuleType,
    capability: str,
) -> Callable[..., Any]:
    preferred = []

    if capability == "spot_price":
        preferred.extend(
            (
                "get_spot_price",
                "spot_price",
                "fetch_spot_price",
                "collect_spot_price",
            )
        )
    elif capability == "market_snapshot":
        preferred.extend(
            (
                "market_snapshot",
                "fetch_market_snapshot",
                "collect_market_snapshot",
                "get_market_snapshot",
            )
        )

    preferred.extend(_DISCOVERY_NAMES)

    for name in preferred:
        candidate = getattr(module, name, None)
        if callable(candidate):
            return candidate

    for _, value in inspect.getmembers(module):
        if inspect.isclass(value):
            try:
                instance = value()
            except Exception:
                continue

            for name in preferred:
                candidate = getattr(instance, name, None)
                if callable(candidate):
                    return candidate

    raise RuntimeError(
        "Frozen OI-005 crypto adapter exposes no supported "
        f"callable for capability {capability!r}"
    )


def _invoke(
    callable_object: Callable[..., Any],
    request: ObservationAdapterRequest,
) -> Any:
    signature = inspect.signature(callable_object)
    params = signature.parameters

    aliases = {
        "request": request,
        "request_id": request.request_id,
        "subject_hint": request.subject_hint,
        "subject": request.subject_hint,
        "asset": request.subject_hint,
        "symbol": request.subject_hint,
        "capability": request.capability,
        "requested_at": request.requested_at,
        "metadata": dict(request.metadata),
    }

    kwargs = {}

    for name, parameter in params.items():
        if name in aliases:
            kwargs[name] = aliases[name]
        elif (
            parameter.default is inspect.Parameter.empty
            and parameter.kind
            not in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            )
        ):
            raise RuntimeError(
                "Frozen OI-005 callable has unsupported "
                f"required parameter: {name}"
            )

    return callable_object(**kwargs)


@dataclass(frozen=True, slots=True)
class FrozenOICryptoObservationBridge:
    descriptor = build_adapter_descriptor(
        adapter_id=ADAPTER_ID,
        provider_id=PROVIDER_ID,
        source_domain=SOURCE_DOMAIN,
        version="1",
        capabilities=CAPABILITIES,
        metadata={
            "upstream": "OI-005",
            "mode": "frozen_read_only_bridge",
        },
    )

    read_only: bool = True
    execution_allowed: bool = False
    order_placement_allowed: bool = False

    def observe(
        self,
        request: ObservationAdapterRequest,
    ) -> ObservationAdapterResult:
        if not isinstance(
            request,
            ObservationAdapterRequest,
        ):
            raise TypeError(
                "request must be ObservationAdapterRequest"
            )

        if request.capability not in self.descriptor.capabilities:
            return ObservationAdapterResult(
                request_id=request.request_id,
                adapter_id=ADAPTER_ID,
                provider_id=PROVIDER_ID,
                capability=request.capability,
                observations=(),
                observed_at=datetime.now(timezone.utc),
                success=False,
                error_code="unsupported_capability",
                read_only=True,
                execution_allowed=False,
            )

        try:
            module = importlib.import_module(
                FROZEN_OI_MODULE
            )

            callable_object = _resolve_callable(
                module,
                request.capability,
            )

            raw = _invoke(
                callable_object,
                request,
            )

            observations = _safe_payload(raw)

            return ObservationAdapterResult(
                request_id=request.request_id,
                adapter_id=ADAPTER_ID,
                provider_id=PROVIDER_ID,
                capability=request.capability,
                observations=observations,
                observed_at=datetime.now(timezone.utc),
                success=True,
                error_code=None,
                read_only=True,
                execution_allowed=False,
            )

        except Exception as exc:
            return ObservationAdapterResult(
                request_id=request.request_id,
                adapter_id=ADAPTER_ID,
                provider_id=PROVIDER_ID,
                capability=request.capability,
                observations=(),
                observed_at=datetime.now(timezone.utc),
                success=False,
                error_code=(
                    "upstream_failure:"
                    + type(exc).__name__
                ),
                read_only=True,
                execution_allowed=False,
            )


def verify_crypto_observation_bridge() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert ORDER_PLACEMENT_ALLOWED is False
    assert (
        FrozenOICryptoObservationBridge
        .descriptor
        .identity
        .provider_id
        == PROVIDER_ID
    )
    return True


__all__ = [
    "BUILD_ID",
    "OAD_005_REVISION",
    "FROZEN_OI_MODULE",
    "ADAPTER_ID",
    "PROVIDER_ID",
    "CAPABILITIES",
    "FrozenOICryptoObservationBridge",
    "verify_crypto_observation_bridge",
]
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapters.oad_002_adapter_contract import (
    build_adapter_request,
    verify_certified_adapter,
)
from qseries_v2.observation_adapters.oad_005_crypto_observation_bridge import (
    OAD_005_REVISION,
    FrozenOICryptoObservationBridge,
    verify_crypto_observation_bridge,
)

NOW = datetime(
    2026,
    8,
    11,
    20,
    0,
    tzinfo=timezone.utc,
)


class TestOAD005(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_crypto_observation_bridge()
        )

    def test_contract(self):
        adapter = FrozenOICryptoObservationBridge()
        self.assertTrue(
            verify_certified_adapter(adapter)
        )

    def test_identity(self):
        adapter = FrozenOICryptoObservationBridge()
        self.assertEqual(
            adapter.descriptor.identity.provider_id,
            "coinbase",
        )

    def test_capabilities(self):
        adapter = FrozenOICryptoObservationBridge()
        self.assertEqual(
            adapter.descriptor.capabilities,
            (
                "market_snapshot",
                "spot_price",
            ),
        )

    def test_unsupported_fails_closed(self):
        adapter = FrozenOICryptoObservationBridge()
        request = build_adapter_request(
            request_id="request.1",
            subject_hint="BTC",
            capability="place_order",
            requested_at=NOW,
        )

        result = adapter.observe(request)

        self.assertFalse(result.success)
        self.assertEqual(
            result.error_code,
            "unsupported_capability",
        )
        self.assertFalse(
            result.execution_allowed
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAD-005 CERTIFICATION TEST")
    print(" FROZEN OI CRYPTO OBSERVATION BRIDGE")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOAD005
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAD-005")
    print(f"[PASS] Revision: {OAD_005_REVISION}")
    print("[PASS] Frozen OI-005 crypto observation path bridged into OAD contract")
    print("[PASS] Spot-price and market-snapshot capabilities preserved")
    print("[PASS] Unsupported capabilities fail closed")
    print("[PASS] Execution and order placement remain disabled")
    print("[DONE] OAD-005 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_exact_oi005() -> Path:
    exact = (
        OI_PACKAGE
        / "oi_005_public_market_data_adapter.py"
    )
    if exact.is_file():
        return exact

    matches = sorted(
        OI_PACKAGE.glob("oi_005_*.py")
    )

    if len(matches) != 1:
        raise RuntimeError(
            "Unable to resolve exact frozen OI-005 module"
        )

    return matches[0]


def write_checked(path: Path, source: str) -> None:
    text = source.lstrip()
    ast.parse(text, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"[PASS] Wrote: {path.relative_to(ROOT)}")


def main() -> int:
    print("=" * 72)
    print(" OAD-005 INSTALLER")
    print(" FROZEN OI CRYPTO OBSERVATION BRIDGE")
    print("=" * 72)
    print(f"[BOOT] Revision: {INSTALLER_REVISION}")
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS + (OI_FREEZE, OI_MANIFEST):
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: {path}"
            )

    oi005 = find_exact_oi005()

    protected = UPSTREAMS + (
        OI_FREEZE,
        OI_MANIFEST,
        oi005,
    )

    hashes = {
        path: sha(path)
        for path in protected
    }

    print(
        f"[PASS] Frozen OI-005 resolved: "
        f"{oi005.name}"
    )

    affected = (MODULE, TEST, INIT)
    backups = {
        item: item.read_bytes() if item.exists() else None
        for item in affected
    }

    try:
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)

        current = (
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )

        export = (
            "from .oad_005_crypto_observation_bridge import *"
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

        for path, expected in hashes.items():
            if sha(path) != expected:
                raise RuntimeError(
                    f"Certified upstream changed: "
                    f"{path.name}"
                )

        print(
            "[PASS] Frozen OI and certified OAD upstream "
            "remained unchanged"
        )
        print("[PASS] In-memory compilation verified")

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: "
            f"{install_hash}"
        )

        print(
            "[DONE] OAD-005 INSTALLATION COMPLETE"
        )

        return 0

    except Exception:
        for item, original in backups.items():
            if original is None:
                if item.exists():
                    item.unlink()
            else:
                item.write_bytes(original)

        print(
            "[ROLLBACK] OAD-005 installation failed; "
            "affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())

