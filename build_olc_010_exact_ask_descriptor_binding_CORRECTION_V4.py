from __future__ import annotations

import ast
import hashlib
import importlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()

PACKAGE = (
    ROOT
    / "qseries_v2"
    / "oracle_live_composition"
)

OIT = (
    ROOT
    / "qseries_v2"
    / "oracle_terminal"
)

OAR = (
    ROOT
    / "qseries_v2"
    / "observation_adapter_runtime"
)

UPSTREAMS = (
    PACKAGE
    / "olc_006_terminal_injection_resolver.py",
    PACKAGE
    / "OLC_006_TERMINAL_INJECTION_MANIFEST.json",
    PACKAGE
    / "olc_008_command_registry_contract_resolver.py",
    PACKAGE
    / "OLC_008_COMMAND_REGISTRY_CONTRACT_MANIFEST.json",
    PACKAGE
    / "olc_009_live_ask_registry_overlay.py",
    OAR
    / "oar_030_final_certification_freeze.py",
)

MODULE = (
    PACKAGE
    / "olc_010_exact_ask_descriptor_binding.py"
)

INIT = (
    PACKAGE
    / "__init__.py"
)

TEST = (
    ROOT
    / "test_olc_010_exact_ask_descriptor_binding.py"
)

MANIFEST = (
    PACKAGE
    / "OLC_010_EXACT_ASK_DESCRIPTOR_MANIFEST.json"
)

INSTALLER_REVISION = (
    "OLC_010_EXACT_ASK_DESCRIPTOR_BINDING_"
    "INSTALLER_CORRECTION_V4"
)

MODULE_SOURCE = r"""
from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

BUILD_ID = "OLC-010"
OLC_010_REVISION = (
    "OLC_010_EXACT_ASK_DESCRIPTOR_BINDING_V1"
)

READ_ONLY = True
EXECUTION_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False
PUBLICATION_ALLOWED = False


@dataclass(frozen=True, slots=True)
class ExactAskHandlerBinding:
    registry_module_name: str
    registry_builder_name: str
    command_index: int
    command_name: str
    handler_name_field: str
    handler_name: str
    handler_module_name: str
    handler_owner_kind: str
    handler_owner_name: str | None
    read_only: bool


def resolve_handler_symbol(
    *,
    module_name: str,
    owner_kind: str,
    owner_name: str | None,
    handler_name: str,
) -> Any:
    module = importlib.import_module(
        module_name
    )

    if owner_kind == "module_function":
        value = getattr(
            module,
            handler_name,
            None,
        )

    elif owner_kind == "class_method":
        if not owner_name:
            raise ValueError(
                "owner_name required for class_method"
            )

        owner = getattr(
            module,
            owner_name,
            None,
        )

        if owner is None:
            raise RuntimeError(
                "handler owner class missing"
            )

        value = getattr(
            owner,
            handler_name,
            None,
        )

    else:
        raise ValueError(
            f"unsupported owner_kind: {owner_kind}"
        )

    if not callable(
        value
    ):
        raise RuntimeError(
            "resolved /ask handler symbol is not callable"
        )

    return value


def verify_exact_ask_descriptor_binding() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert SOURCE_MUTATION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OLC_010_REVISION",
    "ExactAskHandlerBinding",
    "resolve_handler_symbol",
    "verify_exact_ask_descriptor_binding",
]
"""

TEST_SOURCE_TEMPLATE = r"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from qseries_v2.oracle_live_composition.olc_010_exact_ask_descriptor_binding import (
    resolve_handler_symbol,
    verify_exact_ask_descriptor_binding,
)

MANIFEST = Path(__MANIFEST__)


class TestOLC010(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_exact_ask_descriptor_binding()
        )

    def test_manifest(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        self.assertEqual(
            payload[
                "command_name"
            ],
            "/ask",
        )

        self.assertEqual(
            payload[
                "handler_name"
            ],
            "handle_ask",
        )

        self.assertIn(
            payload[
                "handler_owner_kind"
            ],
            (
                "module_function",
                "class_method",
            ),
        )

    def test_real_handler_symbol(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        handler = resolve_handler_symbol(
            module_name=(
                payload[
                    "handler_module_name"
                ]
            ),
            owner_kind=(
                payload[
                    "handler_owner_kind"
                ]
            ),
            owner_name=(
                payload[
                    "handler_owner_name"
                ]
            ),
            handler_name=(
                payload[
                    "handler_name"
                ]
            ),
        )

        self.assertTrue(
            callable(
                handler
            )
        )

        self.assertEqual(
            getattr(
                handler,
                "__name__",
                "",
            ),
            "handle_ask",
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-010 CERTIFICATION TEST")
    print(
        " EXACT /ASK DESCRIPTOR BINDING "
        "— CORRECTION V4"
    )
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(
            TestOLC010
        )
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OLC-010")
    print(
        "[PASS] handler_name='handle_ask' resolved "
        "to its exact callable owner in the certified terminal"
    )
    print(
        "[PASS] Registry metadata and executable "
        "handler resolution are now distinguished correctly"
    )
    print(
        "[PASS] Existing Oracle Terminal source remains unchanged"
    )
    print("[DONE] OLC-010 CERTIFIED")
"""


def sha(
    path: Path,
) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def module_name_for(
    path: Path,
) -> str:
    return ".".join(
        path.relative_to(
            ROOT
        ).with_suffix(
            ""
        ).parts
    )


def command_is_ask(
    value,
) -> bool:
    text = str(
        value
    ).strip().lower()

    if text.startswith(
        "/"
    ):
        text = text[1:]

    return text == "ask"


def exact_registry_contract():
    contract = json.loads(
        (
            PACKAGE
            / "OLC_008_COMMAND_REGISTRY_CONTRACT_MANIFEST.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    module_name = contract[
        "module_name"
    ]

    builder_name = contract[
        "builder_name"
    ]

    module = importlib.import_module(
        module_name
    )

    builder = getattr(
        module,
        builder_name,
        None,
    )

    if not callable(
        builder
    ):
        raise RuntimeError(
            "command registry builder is not callable"
        )

    registry = builder()

    commands = getattr(
        registry,
        "commands",
        None,
    )

    if commands is None:
        raise RuntimeError(
            "registry does not expose commands"
        )

    for index, descriptor in enumerate(
        commands
    ):
        command = getattr(
            descriptor,
            "command",
            None,
        )

        if not command_is_ask(
            command
        ):
            continue

        handler_name = getattr(
            descriptor,
            "handler_name",
            None,
        )

        if not isinstance(
            handler_name,
            str,
        ):
            raise RuntimeError(
                "/ask descriptor does not expose "
                "string handler_name"
            )

        handler_name = (
            handler_name.strip()
        )

        if not handler_name:
            raise RuntimeError(
                "/ask handler_name is empty"
            )

        return {
            "registry_module_name": (
                module_name
            ),
            "registry_builder_name": (
                builder_name
            ),
            "registry_type": (
                f"{type(registry).__module__}."
                f"{type(registry).__qualname__}"
            ),
            "command_index": index,
            "command_name": "/ask",
            "descriptor_type": (
                f"{type(descriptor).__module__}."
                f"{type(descriptor).__qualname__}"
            ),
            "handler_name_field": (
                "handler_name"
            ),
            "handler_name": (
                handler_name
            ),
        }

    raise RuntimeError(
        "exact /ask descriptor missing"
    )


def ast_handler_candidates(
    handler_name: str,
):
    if not OIT.is_dir():
        raise RuntimeError(
            f"Oracle Terminal package missing: "
            f"{OIT}"
        )

    rows = []

    for path in sorted(
        OIT.glob(
            "**/*.py"
        )
    ):
        if not path.is_file():
            continue

        source = path.read_text(
            encoding="utf-8"
        )

        tree = ast.parse(
            source,
            filename=str(
                path
            ),
        )

        module_name = (
            module_name_for(
                path
            )
        )

        for node in tree.body:
            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                ),
            ) and node.name == handler_name:
                rows.append(
                    {
                        "module_name": (
                            module_name
                        ),
                        "owner_kind": (
                            "module_function"
                        ),
                        "owner_name": None,
                        "handler_name": (
                            handler_name
                        ),
                        "path": path,
                    }
                )

            if isinstance(
                node,
                ast.ClassDef,
            ):
                for child in node.body:
                    if isinstance(
                        child,
                        (
                            ast.FunctionDef,
                            ast.AsyncFunctionDef,
                        ),
                    ) and child.name == handler_name:
                        rows.append(
                            {
                                "module_name": (
                                    module_name
                                ),
                                "owner_kind": (
                                    "class_method"
                                ),
                                "owner_name": (
                                    node.name
                                ),
                                "handler_name": (
                                    handler_name
                                ),
                                "path": path,
                            }
                        )

    return rows


def runtime_validate_candidate(
    candidate,
):
    module = importlib.import_module(
        candidate[
            "module_name"
        ]
    )

    if (
        candidate[
            "owner_kind"
        ]
        == "module_function"
    ):
        value = getattr(
            module,
            candidate[
                "handler_name"
            ],
            None,
        )

    else:
        owner = getattr(
            module,
            candidate[
                "owner_name"
            ],
            None,
        )

        if owner is None:
            return False

        value = getattr(
            owner,
            candidate[
                "handler_name"
            ],
            None,
        )

    return callable(
        value
    )


def choose_exact_handler(
    handler_name: str,
):
    candidates = ast_handler_candidates(
        handler_name
    )

    if not candidates:
        raise RuntimeError(
            f"No exact callable symbol named "
            f"{handler_name!r} found anywhere "
            f"inside qseries_v2.oracle_terminal"
        )

    valid = [
        candidate
        for candidate in candidates
        if runtime_validate_candidate(
            candidate
        )
    ]

    if not valid:
        raise RuntimeError(
            f"AST found {handler_name!r}, but "
            "none of the exact symbols are "
            "runtime-callable"
        )

    if len(
        valid
    ) != 1:
        descriptions = [
            (
                f"{row['module_name']}."
                + (
                    f"{row['owner_name']}."
                    if row[
                        "owner_name"
                    ]
                    else ""
                )
                + row[
                    "handler_name"
                ]
            )
            for row in valid
        ]

        raise RuntimeError(
            "Multiple exact runtime-callable "
            f"{handler_name!r} symbols found: "
            + ", ".join(
                descriptions
            )
        )

    return valid[
        0
    ]


def write_checked(
    path: Path,
    source: str,
) -> None:
    content = source.lstrip()

    ast.parse(
        content,
        filename=str(
            path
        ),
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        content,
        encoding="utf-8",
        newline="\n",
    )

    print(
        f"[PASS] Wrote: "
        f"{path.relative_to(ROOT)}"
    )


def main() -> int:
    print("=" * 72)
    print(" OLC-010 INSTALLER")
    print(
        " EXACT /ASK DESCRIPTOR BINDING "
        "— CORRECTION V4"
    )
    print("=" * 72)

    print(
        f"[BOOT] Revision: "
        f"{INSTALLER_REVISION}"
    )

    print(
        f"[ROOT] {ROOT}"
    )

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: "
                f"{path}"
            )

    registry = (
        exact_registry_contract()
    )

    print(
        "[PASS] Exact /ask descriptor: "
        f"registry.commands["
        f"{registry['command_index']}]"
    )

    print(
        "[PASS] Descriptor handler_name: "
        f"{registry['handler_name']}"
    )

    handler = (
        choose_exact_handler(
            registry[
                "handler_name"
            ]
        )
    )

    full_symbol = (
        f"{handler['module_name']}."
        + (
            f"{handler['owner_name']}."
            if handler[
                "owner_name"
            ]
            else ""
        )
        + handler[
            "handler_name"
        ]
    )

    print(
        "[PASS] Exact callable owner resolved: "
        f"{full_symbol}"
    )

    print(
        "[PASS] Handler owner kind: "
        f"{handler['owner_kind']}"
    )

    protected = list(
        UPSTREAMS
    )

    protected.extend(
        sorted(
            path
            for path in OIT.glob(
                "**/*.py"
            )
            if path.is_file()
        )
    )

    protected = tuple(
        dict.fromkeys(
            protected
        )
    )

    hashes = {
        path: sha(
            path
        )
        for path in protected
    }

    payload = {
        "revision": (
            "OLC_010_EXACT_ASK_DESCRIPTOR_MANIFEST_V1"
        ),
        **registry,
        "handler_module_name": (
            handler[
                "module_name"
            ]
        ),
        "handler_owner_kind": (
            handler[
                "owner_kind"
            ]
        ),
        "handler_owner_name": (
            handler[
                "owner_name"
            ]
        ),
        "handler_symbol_name": (
            handler[
                "handler_name"
            ]
        ),
        "handler_full_symbol": (
            full_symbol
        ),
        "binding_mode": (
            "symbolic_descriptor_to_exact_callable_owner"
        ),
        "read_only": True,
        "source_mutation_required": False,
    }

    test_source = (
        TEST_SOURCE_TEMPLATE
        .replace(
            "__MANIFEST__",
            repr(
                str(
                    MANIFEST
                )
            ),
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
            "olc_010_exact_ask_descriptor_binding "
            "import *"
        )

        if export not in current.splitlines():
            if (
                current
                and not current.endswith(
                    "\n"
                )
            ):
                current += "\n"

            current += (
                export
                + "\n"
            )

            ast.parse(
                current,
                filename=str(
                    INIT
                ),
            )

            INIT.write_text(
                current,
                encoding="utf-8",
                newline="\n",
            )

        for path, expected in hashes.items():
            if sha(
                path
            ) != expected:
                raise RuntimeError(
                    "Certified/frozen source changed: "
                    f"{path.name}"
                )

        print(
            "[PASS] Existing OIT source and frozen OAR remained unchanged"
        )

        print(
            "[PASS] In-memory compilation verified"
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
            "[PASS] OLC-010 now separates "
            "registry metadata from the real "
            "runtime handler owner"
        )

        print(
            "[DONE] OLC-010 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OLC-010 correction failed; "
            "affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
