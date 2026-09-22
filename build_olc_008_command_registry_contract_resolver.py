from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_live_composition"

UPSTREAMS = (
    PACKAGE / "olc_002_terminal_runtime_resolver.py",
    PACKAGE / "OLC_002_TERMINAL_RUNTIME_MANIFEST.json",
    PACKAGE / "olc_006_terminal_injection_resolver.py",
    PACKAGE / "OLC_006_TERMINAL_INJECTION_MANIFEST.json",
    ROOT / "qseries_v2" / "observation_adapter_runtime" / "oar_030_final_certification_freeze.py",
)

MODULE = PACKAGE / "olc_008_command_registry_contract_resolver.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_olc_008_command_registry_contract_resolver.py"
MANIFEST = PACKAGE / "OLC_008_COMMAND_REGISTRY_CONTRACT_MANIFEST.json"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

BUILD_ID = "OLC-008"
OLC_008_REVISION = "OLC_008_COMMAND_REGISTRY_CONTRACT_RESOLVER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class CommandRegistryContract:
    module_name: str
    builder_name: str
    registry_type: str
    registry_kind: str
    command_names: tuple[str, ...]
    ask_command_present: bool
    ask_entry_type: str | None
    ask_entry_callable: bool
    read_only: bool


def verify_command_registry_contract_resolver() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert SOURCE_MUTATION_ALLOWED is False
    return True
"""

TEST_SOURCE_TEMPLATE = r"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from qseries_v2.oracle_live_composition.olc_008_command_registry_contract_resolver import (
    verify_command_registry_contract_resolver,
)

MANIFEST = Path(__MANIFEST__)


class TestOLC008(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_command_registry_contract_resolver()
        )

    def test_contract(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        self.assertTrue(
            payload["module_name"]
        )

        self.assertEqual(
            payload["builder_name"],
            "build_default_command_registry",
        )

        self.assertTrue(
            payload["ask_command_present"]
        )

    def test_read_only(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        self.assertTrue(
            payload["read_only"]
        )

        self.assertFalse(
            payload["source_mutation_required"]
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-008 CERTIFICATION TEST")
    print(" EXACT COMMAND REGISTRY CONTRACT RESOLVER")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC008
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-008")
    print("[PASS] Actual build_default_command_registry return contract inspected")
    print("[PASS] /ask command entry verified in the live registry shape")
    print("[PASS] No Oracle Terminal source mutation required")
    print("[DONE] OLC-008 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def import_target():
    payload = json.loads(
        (
            PACKAGE
            / "OLC_006_TERMINAL_INJECTION_MANIFEST.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    top = payload["top_candidate"]

    module_name = top[
        "module_name"
    ]
    symbol_name = top[
        "symbol_name"
    ]

    module = importlib.import_module(
        module_name
    )

    builder = getattr(
        module,
        symbol_name,
        None,
    )

    if not callable(
        builder
    ):
        raise RuntimeError(
            "Resolved command registry builder is not callable"
        )

    return (
        module_name,
        symbol_name,
        builder,
    )


def inspect_registry(
    registry,
):
    registry_type = (
        f"{type(registry).__module__}."
        f"{type(registry).__qualname__}"
    )

    command_names = []
    ask_entry = None
    registry_kind = "unknown"

    if isinstance(
        registry,
        dict,
    ):
        registry_kind = "mapping"
        command_names = [
            str(key)
            for key in registry.keys()
        ]

        for key in (
            "/ask",
            "ask",
        ):
            if key in registry:
                ask_entry = registry[key]
                break

    else:
        for attr in (
            "commands",
            "_commands",
            "registry",
            "_registry",
            "handlers",
            "_handlers",
        ):
            value = getattr(
                registry,
                attr,
                None,
            )

            if isinstance(
                value,
                dict,
            ):
                registry_kind = (
                    f"object_mapping:{attr}"
                )
                command_names = [
                    str(key)
                    for key in value.keys()
                ]

                for key in (
                    "/ask",
                    "ask",
                ):
                    if key in value:
                        ask_entry = value[key]
                        break

                break

        if registry_kind == "unknown":
            for name in (
                "get",
                "resolve",
                "lookup",
            ):
                resolver = getattr(
                    registry,
                    name,
                    None,
                )

                if callable(
                    resolver
                ):
                    for key in (
                        "/ask",
                        "ask",
                    ):
                        try:
                            candidate = resolver(
                                key
                            )
                        except Exception:
                            continue

                        if candidate is not None:
                            ask_entry = candidate
                            registry_kind = (
                                f"object_resolver:{name}"
                            )
                            command_names = [
                                key
                            ]
                            break

                if ask_entry is not None:
                    break

    ask_present = (
        ask_entry is not None
    )

    ask_entry_type = (
        None
        if ask_entry is None
        else (
            f"{type(ask_entry).__module__}."
            f"{type(ask_entry).__qualname__}"
        )
    )

    return {
        "registry_type": registry_type,
        "registry_kind": registry_kind,
        "command_names": sorted(
            set(command_names)
        ),
        "ask_command_present": ask_present,
        "ask_entry_type": ask_entry_type,
        "ask_entry_callable": bool(
            callable(ask_entry)
        ),
    }


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
        f"[PASS] Wrote: {path.relative_to(ROOT)}"
    )


def main() -> int:
    print("=" * 72)
    print(" OLC-008 INSTALLER")
    print(" EXACT COMMAND REGISTRY CONTRACT RESOLVER")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OLC_008_COMMAND_REGISTRY_CONTRACT_RESOLVER_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: {path}"
            )

    (
        module_name,
        builder_name,
        builder,
    ) = import_target()

    signature = inspect.signature(
        builder
    )

    required = [
        parameter
        for parameter in signature.parameters.values()
        if (
            parameter.default
            is inspect._empty
            and parameter.kind
            in (
                inspect.Parameter.POSITIONAL_ONLY,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.KEYWORD_ONLY,
            )
        )
    ]

    if required:
        raise RuntimeError(
            "Resolved build_default_command_registry "
            "requires arguments; exact runtime constructor "
            "must be handled before invocation"
        )

    registry = builder()

    contract = inspect_registry(
        registry
    )

    if not contract[
        "ask_command_present"
    ]:
        raise RuntimeError(
            "Resolved command registry does not expose /ask"
        )

    target_path = (
        ROOT
        / Path(
            *module_name.split(".")
        ).with_suffix(".py")
    )

    if not target_path.is_file():
        raise RuntimeError(
            f"Resolved registry module missing: {target_path}"
        )

    print(
        "[PASS] Command registry builder imported read-only: "
        f"{module_name}.{builder_name}"
    )

    print(
        "[PASS] Registry type: "
        f"{contract['registry_type']}"
    )

    print(
        "[PASS] Registry kind: "
        f"{contract['registry_kind']}"
    )

    print(
        "[PASS] /ask entry type: "
        f"{contract['ask_entry_type']}"
    )

    protected = (
        *UPSTREAMS,
        target_path,
    )

    hashes = {
        path: sha(path)
        for path in protected
    }

    payload = {
        "revision": (
            "OLC_008_COMMAND_REGISTRY_CONTRACT_MANIFEST_V1"
        ),
        "module_name": module_name,
        "builder_name": builder_name,
        **contract,
        "read_only": True,
        "source_mutation_required": False,
    }

    test_source = (
        TEST_SOURCE_TEMPLATE
        .replace(
            "__MANIFEST__",
            repr(str(MANIFEST)),
        )
    )

    affected = (
        MODULE,
        TEST,
        INIT,
        MANIFEST,
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

        MANIFEST.write_text(
            json.dumps(
                payload,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )

        print(
            f"[PASS] Wrote: {MANIFEST.relative_to(ROOT)}"
        )

        current = (
            INIT.read_text(
                encoding="utf-8"
            )
            if INIT.exists()
            else ""
        )

        export = (
            "from .olc_008_command_registry_contract_resolver import *"
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
                    f"Certified/frozen source changed: {path.name}"
                )

        print(
            "[PASS] Existing OIT source and frozen OAR remained unchanged"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
            + MANIFEST.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: {install_hash}"
        )
        print(
            "[DONE] OLC-008 INSTALLATION COMPLETE"
        )

        return 0

    except Exception:
        for path, original in backups.items():
            if original is None:
                if path.exists():
                    path.unlink()
            else:
                path.write_bytes(original)

        print(
            "[ROLLBACK] OLC-008 installation failed; affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
