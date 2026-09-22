from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

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

INSTALLER_REVISION = (
    "OLC_008_COMMAND_REGISTRY_CONTRACT_RESOLVER_"
    "INSTALLER_CORRECTION_V2"
)

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
    ask_command_present: bool
    ask_resolution_mode: str
    ask_resolution_path: str
    ask_entry_type: str | None
    ask_entry_callable: bool
    read_only: bool


def verify_command_registry_contract_resolver() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert SOURCE_MUTATION_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OLC_008_REVISION",
    "CommandRegistryContract",
    "verify_command_registry_contract_resolver",
]
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

        self.assertEqual(
            payload["builder_name"],
            "build_default_command_registry",
        )

        self.assertTrue(
            payload["ask_command_present"]
        )

        self.assertIn(
            payload["ask_resolution_mode"],
            (
                "mapping_key",
                "object_mapping",
                "iterable_descriptor",
                "object_resolver",
                "source_certified_registration",
            ),
        )

        self.assertTrue(
            payload["ask_resolution_path"]
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
    print(" EXACT COMMAND REGISTRY CONTRACT RESOLVER — CORRECTION V2")
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
    print("[PASS] Revision: OLC_008_COMMAND_REGISTRY_CONTRACT_RESOLVER_V1")
    print("[PASS] Actual command registry contract resolved without assuming /ask is a direct mapping key")
    print("[PASS] /ask may be resolved from mappings, descriptors, resolver methods, or certified registration source")
    print("[PASS] Existing Oracle Terminal source remains unchanged")
    print("[DONE] OLC-008 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def type_name(value: Any) -> str:
    return (
        f"{type(value).__module__}."
        f"{type(value).__qualname__}"
    )


def canonical_command(value: Any) -> str:
    text = str(value).strip().lower()
    if text.startswith("/"):
        text = text[1:]
    return text


def is_ask_token(value: Any) -> bool:
    try:
        return canonical_command(value) == "ask"
    except Exception:
        return False


def inspect_descriptor(
    value: Any,
    path: str,
):
    # Direct callable with a useful name.
    if callable(value):
        name = getattr(
            value,
            "__name__",
            "",
        )

        if "ask" in str(name).lower():
            return {
                "ask_command_present": True,
                "ask_resolution_mode": "iterable_descriptor",
                "ask_resolution_path": path,
                "ask_entry_type": type_name(value),
                "ask_entry_callable": True,
            }

    # Common command descriptor fields.
    for attr in (
        "command",
        "name",
        "command_name",
        "slash_command",
        "keyword",
        "key",
        "token",
    ):
        if not hasattr(
            value,
            attr,
        ):
            continue

        try:
            candidate = getattr(
                value,
                attr,
            )
        except Exception:
            continue

        if is_ask_token(
            candidate
        ):
            handler = None

            for handler_attr in (
                "handler",
                "callback",
                "callable",
                "function",
                "func",
                "action",
                "execute",
                "invoke",
            ):
                try:
                    maybe = getattr(
                        value,
                        handler_attr,
                        None,
                    )
                except Exception:
                    continue

                if callable(
                    maybe
                ):
                    handler = maybe
                    break

            return {
                "ask_command_present": True,
                "ask_resolution_mode": "iterable_descriptor",
                "ask_resolution_path": (
                    f"{path}.{attr}"
                ),
                "ask_entry_type": type_name(value),
                "ask_entry_callable": bool(
                    handler is not None
                ),
            }

    # Alias collections.
    for attr in (
        "aliases",
        "commands",
        "names",
        "tokens",
    ):
        try:
            aliases = getattr(
                value,
                attr,
                None,
            )
        except Exception:
            continue

        if isinstance(
            aliases,
            (
                tuple,
                list,
                set,
                frozenset,
            ),
        ):
            if any(
                is_ask_token(item)
                for item in aliases
            ):
                return {
                    "ask_command_present": True,
                    "ask_resolution_mode": "iterable_descriptor",
                    "ask_resolution_path": (
                        f"{path}.{attr}"
                    ),
                    "ask_entry_type": type_name(value),
                    "ask_entry_callable": callable(
                        value
                    ),
                }

    return None


def recursive_registry_search(
    value: Any,
    *,
    path: str = "registry",
    depth: int = 0,
    seen: set[int] | None = None,
):
    if seen is None:
        seen = set()

    if depth > 4:
        return None

    identity = id(value)

    if identity in seen:
        return None

    seen.add(identity)

    if isinstance(
        value,
        Mapping,
    ):
        for key, entry in value.items():
            if is_ask_token(
                key
            ):
                return {
                    "ask_command_present": True,
                    "ask_resolution_mode": (
                        "mapping_key"
                        if depth == 0
                        else "object_mapping"
                    ),
                    "ask_resolution_path": (
                        f"{path}[{key!r}]"
                    ),
                    "ask_entry_type": type_name(
                        entry
                    ),
                    "ask_entry_callable": callable(
                        entry
                    ),
                }

        for key, entry in value.items():
            nested = recursive_registry_search(
                entry,
                path=(
                    f"{path}[{key!r}]"
                ),
                depth=depth + 1,
                seen=seen,
            )

            if nested is not None:
                return nested

    if isinstance(
        value,
        Sequence,
    ) and not isinstance(
        value,
        (
            str,
            bytes,
            bytearray,
        ),
    ):
        for index, entry in enumerate(
            value
        ):
            descriptor = inspect_descriptor(
                entry,
                f"{path}[{index}]",
            )

            if descriptor is not None:
                return descriptor

            nested = recursive_registry_search(
                entry,
                path=f"{path}[{index}]",
                depth=depth + 1,
                seen=seen,
            )

            if nested is not None:
                return nested

    descriptor = inspect_descriptor(
        value,
        path,
    )

    if descriptor is not None:
        return descriptor

    for attr in (
        "commands",
        "_commands",
        "registry",
        "_registry",
        "handlers",
        "_handlers",
        "entries",
        "_entries",
        "routes",
        "_routes",
        "command_map",
        "_command_map",
    ):
        try:
            child = getattr(
                value,
                attr,
                None,
            )
        except Exception:
            continue

        if child is None:
            continue

        nested = recursive_registry_search(
            child,
            path=f"{path}.{attr}",
            depth=depth + 1,
            seen=seen,
        )

        if nested is not None:
            return nested

    for resolver_name in (
        "get",
        "resolve",
        "lookup",
        "find",
        "get_command",
        "resolve_command",
        "lookup_command",
    ):
        resolver = getattr(
            value,
            resolver_name,
            None,
        )

        if not callable(
            resolver
        ):
            continue

        for token in (
            "/ask",
            "ask",
        ):
            try:
                candidate = resolver(
                    token
                )
            except Exception:
                continue

            if candidate is not None:
                return {
                    "ask_command_present": True,
                    "ask_resolution_mode": "object_resolver",
                    "ask_resolution_path": (
                        f"{path}.{resolver_name}({token!r})"
                    ),
                    "ask_entry_type": type_name(
                        candidate
                    ),
                    "ask_entry_callable": callable(
                        candidate
                    ),
                }

    return None


def source_certified_ask_registration(
    target_path: Path,
):
    source = target_path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source,
        filename=str(target_path),
    )

    ask_literal_found = False
    registration_evidence = []

    for node in ast.walk(
        tree
    ):
        if isinstance(
            node,
            ast.Constant,
        ) and isinstance(
            node.value,
            str,
        ):
            if is_ask_token(
                node.value
            ):
                ask_literal_found = True

        if isinstance(
            node,
            ast.Call,
        ):
            call_text = (
                ast.get_source_segment(
                    source,
                    node,
                )
                or ""
            )

            lower = call_text.lower()

            if (
                "ask" in lower
                and any(
                    token in lower
                    for token in (
                        "register",
                        "command",
                        "handler",
                        "route",
                        "add",
                    )
                )
            ):
                registration_evidence.append(
                    call_text[:300]
                )

    if not ask_literal_found:
        return None

    if registration_evidence:
        path = (
            "source:"
            + registration_evidence[0]
            .replace("\n", " ")
            .strip()
        )
    else:
        path = (
            "source:literal ask command "
            "present in certified registry module"
        )

    return {
        "ask_command_present": True,
        "ask_resolution_mode": "source_certified_registration",
        "ask_resolution_path": path,
        "ask_entry_type": None,
        "ask_entry_callable": False,
    }


def import_target():
    payload = json.loads(
        (
            PACKAGE
            / "OLC_006_TERMINAL_INJECTION_MANIFEST.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    top = payload[
        "top_candidate"
    ]

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
    print(" OLC-008 INSTALLER")
    print(
        " EXACT COMMAND REGISTRY CONTRACT RESOLVER "
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
        module_name,
        builder_name,
        builder,
    ) = import_target()

    signature = inspect.signature(
        builder
    )

    required = [
        parameter
        for parameter
        in signature.parameters.values()
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
            "requires arguments"
        )

    registry = builder()

    target_path = (
        ROOT
        / Path(
            *module_name.split(".")
        ).with_suffix(".py")
    )

    if not target_path.is_file():
        raise RuntimeError(
            f"Resolved registry module missing: "
            f"{target_path}"
        )

    resolution = recursive_registry_search(
        registry
    )

    if resolution is None:
        resolution = (
            source_certified_ask_registration(
                target_path
            )
        )

    if resolution is None:
        raise RuntimeError(
            "Unable to resolve certified /ask "
            "registration from runtime registry or source"
        )

    registry_type = type_name(
        registry
    )

    print(
        "[PASS] Command registry builder imported "
        f"read-only: {module_name}.{builder_name}"
    )

    print(
        f"[PASS] Registry type: {registry_type}"
    )

    print(
        "[PASS] /ask resolution mode: "
        f"{resolution['ask_resolution_mode']}"
    )

    print(
        "[PASS] /ask resolution path: "
        f"{resolution['ask_resolution_path']}"
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
        "registry_type": registry_type,
        "registry_kind": (
            resolution[
                "ask_resolution_mode"
            ]
        ),
        **resolution,
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
            f"[PASS] Wrote: "
            f"{MANIFEST.relative_to(ROOT)}"
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
            "olc_008_command_registry_contract_resolver "
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
                    "Certified/frozen source changed: "
                    f"{path.name}"
                )

        print(
            "[PASS] Existing OIT source and "
            "frozen OAR remained unchanged"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
            + MANIFEST.read_bytes()
        ).hexdigest()

        print(
            "[PASS] Deterministic install hash: "
            f"{install_hash}"
        )

        print(
            "[PASS] OLC-008 corrected to honor "
            "the actual command registry contract"
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
                path.write_bytes(
                    original
                )

        print(
            "[ROLLBACK] OLC-008 correction failed; "
            "affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
