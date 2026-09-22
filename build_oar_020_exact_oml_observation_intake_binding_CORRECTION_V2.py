from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "observation_adapter_runtime"

OML_ROOTS = (
    ROOT / "qseries_v2" / "oracle_memory",
    ROOT / "qseries_v2" / "oracle_intelligence" / "oracle_memory",
)

UPSTREAMS = (
    PKG / "oar_015_oml_memory_intake_handoff.py",
    PKG / "oar_017_oml_boundary_resolver.py",
    PKG / "oar_019_exact_umd_market_identity_binding.py",
)

MODULE = PKG / "oar_020_exact_oml_observation_intake_binding.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_oar_020_exact_oml_observation_intake_binding.py"

TARGET_CLASS = (
    "OracleMemoryCertifiedMarketBehavior"
    "ObservationIntakeBinding"
)

INSTALLER_REVISION = (
    "OAR_020_EXACT_OML_OBSERVATION_INTAKE_BINDING_"
    "INSTALLER_CORRECTION_V2"
)

MODULE_SOURCE = r"""
from __future__ import annotations

import importlib
import inspect
from dataclasses import dataclass

from .oar_015_oml_memory_intake_handoff import (
    OMLMemoryIntakeRequest,
)

BUILD_ID = "OAR-020"
OAR_020_REVISION = (
    "OAR_020_EXACT_OML_OBSERVATION_INTAKE_BINDING_V1"
)

READ_ONLY = True
EXECUTION_ALLOWED = False
PERSISTENCE_ALLOWED = False
PUBLICATION_ALLOWED = False

TARGET_CLASS = (
    "OracleMemoryCertifiedMarketBehavior"
    "ObservationIntakeBinding"
)

PREFERRED_METHODS = (
    "bind",
    "build",
    "admit",
    "intake",
    "consume",
    "project",
)


@dataclass(frozen=True, slots=True)
class ExactOMLBinding:
    module_name: str
    class_name: str
    binding_mode: str
    callable_name: str
    public_methods: tuple[str, ...]
    read_only: bool


class ExactOMLObservationIntakeBinding:
    read_only = True
    execution_allowed = False
    persistence_allowed = False
    publication_allowed = False

    def resolve_binding(
        self,
        module_name: str,
    ) -> ExactOMLBinding:
        module = importlib.import_module(
            module_name
        )

        target_class = getattr(
            module,
            TARGET_CLASS,
            None,
        )

        if target_class is None:
            raise RuntimeError(
                "Certified OML target class missing"
            )

        if not inspect.isclass(
            target_class
        ):
            raise TypeError(
                "Certified OML target is not a class"
            )

        public_methods = tuple(
            sorted(
                name
                for name, value
                in inspect.getmembers(
                    target_class
                )
                if (
                    callable(value)
                    and not name.startswith("_")
                )
            )
        )

        callable_name = None

        for name in PREFERRED_METHODS:
            if name in public_methods:
                callable_name = name
                break

        if callable_name is not None:
            binding_mode = "public_method"
        else:
            # The certified OML object can legitimately be a pure
            # immutable binding/data contract with no public methods.
            # In that case the exact class constructor itself is the
            # certified boundary. Do not invent a method or mutate OML.
            binding_mode = "constructor_contract"
            callable_name = "__init__"

        return ExactOMLBinding(
            module_name=module_name,
            class_name=TARGET_CLASS,
            binding_mode=binding_mode,
            callable_name=callable_name,
            public_methods=public_methods,
            read_only=True,
        )

    def validate_request(
        self,
        request: OMLMemoryIntakeRequest,
    ) -> bool:
        if not isinstance(
            request,
            OMLMemoryIntakeRequest,
        ):
            raise TypeError(
                "request must be OMLMemoryIntakeRequest"
            )

        if (
            request
            .requires_market_identity_resolution
            is not True
        ):
            raise ValueError(
                "market identity resolution required"
            )

        if (
            request
            .requires_evidence_lineage_preservation
            is not True
        ):
            raise ValueError(
                "evidence lineage preservation required"
            )

        if (
            request
            .requires_contradiction_preservation
            is not True
        ):
            raise ValueError(
                "contradiction preservation required"
            )

        if request.read_only is not True:
            raise ValueError(
                "OML request must be read-only"
            )

        return True


def verify_exact_oml_observation_intake_binding() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OAR_020_REVISION",
    "TARGET_CLASS",
    "ExactOMLBinding",
    "ExactOMLObservationIntakeBinding",
    "verify_exact_oml_observation_intake_binding",
]
"""

TEST_SOURCE_TEMPLATE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_adapter_runtime.oar_015_oml_memory_intake_handoff import (
    OMLMemoryIntakeRequest,
)
from qseries_v2.observation_adapter_runtime.oar_020_exact_oml_observation_intake_binding import (
    TARGET_CLASS,
    ExactOMLObservationIntakeBinding,
    verify_exact_oml_observation_intake_binding,
)

TARGET_MODULE = __TARGET_MODULE__
EXPECTED_BINDING_MODE = __EXPECTED_BINDING_MODE__


class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_exact_oml_observation_intake_binding()
        )

    def test_exact_binding(self):
        binding = (
            ExactOMLObservationIntakeBinding()
            .resolve_binding(
                TARGET_MODULE
            )
        )

        self.assertEqual(
            binding.class_name,
            TARGET_CLASS,
        )

        self.assertEqual(
            binding.binding_mode,
            EXPECTED_BINDING_MODE,
        )

        if EXPECTED_BINDING_MODE == "constructor_contract":
            self.assertEqual(
                binding.callable_name,
                "__init__",
            )
            self.assertEqual(
                binding.public_methods,
                (),
            )
        else:
            self.assertTrue(
                binding.callable_name
            )

    def test_request_validation(self):
        request = OMLMemoryIntakeRequest(
            iteration_number=1,
            observation_ids=("liveobs.1",),
            observation_hashes=("a"*64,),
            provider_ids=("coinbase",),
            requires_market_identity_resolution=True,
            requires_evidence_lineage_preservation=True,
            requires_contradiction_preservation=True,
            read_only=True,
        )

        self.assertTrue(
            ExactOMLObservationIntakeBinding()
            .validate_request(
                request
            )
        )

    def test_side_effects(self):
        binding = ExactOMLObservationIntakeBinding()

        self.assertTrue(binding.read_only)
        self.assertFalse(binding.execution_allowed)
        self.assertFalse(binding.persistence_allowed)
        self.assertFalse(binding.publication_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-020 CERTIFICATION TEST")
    print(" EXACT OML OBSERVATION INTAKE BINDING — CORRECTION V2")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-020")
    print("[PASS] Revision: OAR_020_EXACT_OML_OBSERVATION_INTAKE_BINDING_V1")
    print("[PASS] Exact certified Oracle Memory observation-intake class boundary bound")
    print("[PASS] Pure constructor/data-contract bindings are accepted without inventing public methods")
    print("[PASS] OML source remains unchanged; persistence remains disabled")
    print("[DONE] OAR-020 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def locate_target():
    matches = []

    for root in OML_ROOTS:
        if not root.is_dir():
            continue

        for path in root.glob("**/*.py"):
            try:
                source = path.read_text(
                    encoding="utf-8"
                )
            except UnicodeDecodeError:
                continue

            tree = ast.parse(
                source,
                filename=str(path),
            )

            for node in tree.body:
                if (
                    isinstance(
                        node,
                        ast.ClassDef,
                    )
                    and node.name
                    == TARGET_CLASS
                ):
                    public_methods = tuple(
                        child.name
                        for child in node.body
                        if isinstance(
                            child,
                            (
                                ast.FunctionDef,
                                ast.AsyncFunctionDef,
                            ),
                        )
                        and not child.name.startswith("_")
                    )

                    matches.append(
                        (
                            path,
                            node,
                            public_methods,
                        )
                    )

    if len(matches) != 1:
        raise RuntimeError(
            "Expected exactly one certified OML "
            "observation intake target, found "
            f"{len(matches)}"
        )

    return matches[0]


def module_name_for(
    path: Path,
) -> str:
    relative = path.relative_to(
        ROOT
    ).with_suffix("")

    return ".".join(
        relative.parts
    )


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
    print(" OAR-020 INSTALLER")
    print(
        " EXACT OML OBSERVATION INTAKE BINDING "
        "— CORRECTION V2"
    )
    print("=" * 72)
    print(
        f"[BOOT] Revision: {INSTALLER_REVISION}"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: "
                f"{path}"
            )

    (
        target_path,
        target_node,
        public_methods,
    ) = locate_target()

    target_module = module_name_for(
        target_path
    )

    preferred = (
        "bind",
        "build",
        "admit",
        "intake",
        "consume",
        "project",
    )

    matched = tuple(
        name
        for name in preferred
        if name in public_methods
    )

    binding_mode = (
        "public_method"
        if matched
        else "constructor_contract"
    )

    print(
        "[PASS] Exact OML target verified: "
        f"{target_module}.{TARGET_CLASS}"
    )

    if public_methods:
        print(
            "[PASS] Public OML intake methods: "
            + ", ".join(public_methods)
        )
    else:
        print(
            "[PASS] Certified OML target is a "
            "pure constructor/data binding contract"
        )
        print(
            "[PASS] No public method is required "
            "or invented"
        )

    protected = (
        *UPSTREAMS,
        target_path,
    )

    hashes = {
        path: sha(path)
        for path in protected
    }

    test_source = (
        TEST_SOURCE_TEMPLATE
        .replace(
            "__TARGET_MODULE__",
            repr(target_module),
        )
        .replace(
            "__EXPECTED_BINDING_MODE__",
            repr(binding_mode),
        )
    )

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
            test_source,
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
            "oar_020_exact_oml_observation_intake_binding "
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
            "[PASS] Certified OML target and "
            "OAR upstream remained unchanged"
        )
        print(
            "[PASS] In-memory compilation verified"
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
            "[PASS] OAR-020 corrected to honor the "
            "actual certified OML class contract"
        )
        print(
            "[DONE] OAR-020 INSTALLATION COMPLETE"
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

        print(
            "[ROLLBACK] OAR-020 correction failed; "
            "affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
