from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "observation_adapter_runtime"
UMD = ROOT / "qseries_v2" / "universal_market_discovery"

UPSTREAMS = (
    PKG / "oar_014_umd_market_correlation_handoff.py",
    PKG / "oar_016_umd_boundary_resolver.py",
    PKG / "oar_018_oi_umd_oml_integration.py",
)

TARGET_MODULE = UMD / "umd_095_market_identity.py"

MODULE = PKG / "oar_019_exact_umd_market_identity_binding.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_oar_019_exact_umd_market_identity_binding.py"

MODULE_SOURCE = r"""
from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass
from typing import Any, Callable

from .oar_014_umd_market_correlation_handoff import (
    UMDMarketCorrelationRequest,
)

BUILD_ID = "OAR-019"
OAR_019_REVISION = "OAR_019_EXACT_UMD_MARKET_IDENTITY_BINDING_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False

TARGET_MODULE = (
    "qseries_v2.universal_market_discovery."
    "umd_095_market_identity"
)
TARGET_CLASS = "CanonicalMarketIdentityResolver"

PREFERRED_METHODS = (
    "resolve",
    "resolve_market",
    "resolve_identity",
    "canonicalize",
)


@dataclass(frozen=True, slots=True)
class ExactUMDBinding:
    module_name: str
    class_name: str
    callable_name: str
    read_only: bool


class ExactUMDMarketIdentityBinding:
    read_only = True
    execution_allowed = False
    persistence_allowed = False
    publication_allowed = False

    def resolve_binding(self) -> ExactUMDBinding:
        module = importlib.import_module(
            TARGET_MODULE
        )

        target_class = getattr(
            module,
            TARGET_CLASS,
            None,
        )

        if target_class is None:
            raise RuntimeError(
                f"Certified UMD target class missing: "
                f"{TARGET_CLASS}"
            )

        if not inspect.isclass(
            target_class
        ):
            raise TypeError(
                "Certified UMD target is not a class"
            )

        callable_name = None

        for name in PREFERRED_METHODS:
            candidate = getattr(
                target_class,
                name,
                None,
            )

            if callable(candidate):
                callable_name = name
                break

        if callable_name is None:
            public = [
                name
                for name, value
                in inspect.getmembers(
                    target_class
                )
                if (
                    callable(value)
                    and not name.startswith("_")
                )
            ]

            if len(public) == 1:
                callable_name = public[0]
            else:
                raise RuntimeError(
                    "Unable to resolve exact callable "
                    "on CanonicalMarketIdentityResolver"
                )

        return ExactUMDBinding(
            module_name=TARGET_MODULE,
            class_name=TARGET_CLASS,
            callable_name=callable_name,
            read_only=True,
        )

    def validate_request(
        self,
        request: UMDMarketCorrelationRequest,
    ) -> bool:
        if not isinstance(
            request,
            UMDMarketCorrelationRequest,
        ):
            raise TypeError(
                "request must be UMDMarketCorrelationRequest"
            )

        if (
            request.market_identity_required
            is not True
        ):
            raise ValueError(
                "market identity resolution must be required"
            )

        if request.read_only is not True:
            raise ValueError(
                "UMD request must be read-only"
            )

        return True


def verify_exact_umd_market_identity_binding() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_adapter_runtime.oar_014_umd_market_correlation_handoff import (
    UMDMarketCorrelationRequest,
)
from qseries_v2.observation_adapter_runtime.oar_019_exact_umd_market_identity_binding import (
    TARGET_CLASS,
    ExactUMDMarketIdentityBinding,
    verify_exact_umd_market_identity_binding,
)

class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_exact_umd_market_identity_binding()
        )

    def test_exact_binding(self):
        binding = (
            ExactUMDMarketIdentityBinding()
            .resolve_binding()
        )

        self.assertEqual(
            binding.class_name,
            TARGET_CLASS,
        )

        self.assertTrue(
            binding.callable_name
        )

    def test_request_validation(self):
        request = UMDMarketCorrelationRequest(
            iteration_number=1,
            observation_ids=("liveobs.1",),
            provider_ids=("coinbase",),
            capability_ids=("spot_price",),
            market_identity_required=True,
            related_market_resolution_required=True,
            read_only=True,
        )

        self.assertTrue(
            ExactUMDMarketIdentityBinding()
            .validate_request(
                request
            )
        )

if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-019 CERTIFICATION TEST")
    print(" EXACT UMD MARKET IDENTITY BINDING")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-019")
    print("[PASS] Exact UMD-095 CanonicalMarketIdentityResolver boundary bound")
    print("[PASS] Certified callable resolved without modifying UMD")
    print("[PASS] UMD request validation remains read-only")
    print("[DONE] OAR-019 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def inspect_target() -> tuple[str, tuple[str, ...]]:
    if not TARGET_MODULE.is_file():
        raise RuntimeError(
            f"Certified UMD-095 module missing: "
            f"{TARGET_MODULE}"
        )

    tree = ast.parse(
        TARGET_MODULE.read_text(
            encoding="utf-8"
        ),
        filename=str(TARGET_MODULE),
    )

    target = None

    for node in tree.body:
        if (
            isinstance(node, ast.ClassDef)
            and node.name
            == "CanonicalMarketIdentityResolver"
        ):
            target = node
            break

    if target is None:
        raise RuntimeError(
            "Certified UMD-095 missing "
            "CanonicalMarketIdentityResolver"
        )

    methods = tuple(
        node.name
        for node in target.body
        if isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
        and not node.name.startswith("_")
    )

    if not methods:
        raise RuntimeError(
            "CanonicalMarketIdentityResolver "
            "has no public callable"
        )

    return target.name, methods


def write_checked(
    path: Path,
    source: str,
) -> None:
    text = source.lstrip()
    ast.parse(
        text,
        filename=str(path),
    )
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"[PASS] Wrote: "
        f"{path.relative_to(ROOT)}"
    )


def main() -> int:
    print("=" * 72)
    print(" OAR-019 INSTALLER")
    print(" EXACT UMD MARKET IDENTITY BINDING")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OAR_019_EXACT_UMD_MARKET_IDENTITY_BINDING_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: "
                f"{path}"
            )

    class_name, methods = inspect_target()

    print(
        f"[PASS] Exact UMD target verified: "
        f"{class_name}"
    )
    print(
        "[PASS] Public UMD-095 methods: "
        + ", ".join(methods)
    )

    protected = (
        *UPSTREAMS,
        TARGET_MODULE,
    )

    hashes = {
        path: sha(path)
        for path in protected
    }

    affected = (
        MODULE,
        TEST,
        INIT,
    )

    backups = {
        path: (
            path.read_bytes()
            if path.exists()
            else None
        )
        for path in affected
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
            "from ."
            "oar_019_exact_umd_market_identity_binding "
            "import *"
        )

        if export not in current.splitlines():
            if (
                current
                and not current.endswith("\n")
            ):
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
                    "Certified upstream changed: "
                    f"{path.name}"
                )

        print(
            "[PASS] Certified UMD-095 and "
            "OAR upstream remained unchanged"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            "[PASS] Deterministic install hash: "
            f"{install_hash}"
        )
        print(
            "[DONE] OAR-019 INSTALLATION COMPLETE"
        )

        return 0

    except Exception:
        for path, original in backups.items():
            if original is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(
                    original
                )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
