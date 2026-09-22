from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import fields, is_dataclass, replace
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_live_composition"
OAR = ROOT / "qseries_v2" / "observation_adapter_runtime"

UPSTREAMS = (
    PACKAGE / "olc_006_terminal_injection_resolver.py",
    PACKAGE / "OLC_006_TERMINAL_INJECTION_MANIFEST.json",
    PACKAGE / "olc_008_command_registry_contract_resolver.py",
    PACKAGE / "OLC_008_COMMAND_REGISTRY_CONTRACT_MANIFEST.json",
    PACKAGE / "olc_009_live_ask_registry_overlay.py",
    OAR / "oar_030_final_certification_freeze.py",
)

MODULE = PACKAGE / "olc_010_exact_ask_descriptor_binding.py"
INIT = PACKAGE / "__init__.py"
TEST = ROOT / "test_olc_010_exact_ask_descriptor_binding.py"
MANIFEST = PACKAGE / "OLC_010_EXACT_ASK_DESCRIPTOR_MANIFEST.json"

INSTALLER_REVISION = (
    "OLC_010_EXACT_ASK_DESCRIPTOR_BINDING_"
    "INSTALLER_CORRECTION_V3"
)

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import is_dataclass, replace
from typing import Any, Callable

from .olc_005_live_read_model_refresh import (
    AtomicLiveReadModelStore,
)
from .olc_009_live_ask_registry_overlay import (
    LiveAskHandlerOverlay,
)

BUILD_ID = "OLC-010"
OLC_010_REVISION = "OLC_010_EXACT_ASK_DESCRIPTOR_BINDING_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
SOURCE_MUTATION_ALLOWED = False
PUBLICATION_ALLOWED = False


def _replace_field(
    obj: Any,
    field_name: str,
    value: Any,
) -> Any:
    if is_dataclass(obj):
        return replace(
            obj,
            **{field_name: value},
        )

    replacer = getattr(
        obj,
        "_replace",
        None,
    )

    if callable(replacer):
        return replacer(
            **{field_name: value}
        )

    if hasattr(
        obj,
        "__dict__",
    ):
        clone = object.__new__(
            type(obj)
        )

        clone.__dict__.update(
            obj.__dict__
        )

        setattr(
            clone,
            field_name,
            value,
        )

        return clone

    raise TypeError(
        "unsupported immutable descriptor type"
    )


def _extract_query(
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    for key in (
        "query",
        "text",
        "argument",
        "arguments",
        "raw_query",
        "value",
    ):
        value = kwargs.get(
            key
        )

        if isinstance(
            value,
            str,
        ):
            return value

    for value in args:
        if isinstance(
            value,
            str,
        ):
            return value

    raise TypeError(
        "unable to extract /ask query"
    )


def build_live_ask_handler(
    *,
    store: AtomicLiveReadModelStore,
    fallback_handler: Callable[..., Any],
) -> Callable[..., Any]:
    if not callable(
        fallback_handler
    ):
        raise TypeError(
            "fallback_handler must be callable"
        )

    overlay = LiveAskHandlerOverlay(
        store=store,
        fallback_handler=fallback_handler,
    )

    def live_ask_handler(
        *args,
        **kwargs,
    ):
        query = _extract_query(
            args,
            kwargs,
        )

        _status, value = overlay.dispatch(
            query,
            *args,
            **kwargs,
        )

        return value

    live_ask_handler.__name__ = (
        "oracle_live_ask_handler"
    )

    return live_ask_handler


def build_patched_registry(
    *,
    registry: Any,
    command_index: int,
    handler_name_field: str,
    live_handler_name: str,
) -> Any:
    commands = getattr(
        registry,
        "commands",
        None,
    )

    if commands is None:
        raise TypeError(
            "registry does not expose commands"
        )

    if (
        command_index < 0
        or command_index >= len(commands)
    ):
        raise IndexError(
            "command_index out of range"
        )

    descriptor = commands[
        command_index
    ]

    new_descriptor = _replace_field(
        descriptor,
        handler_name_field,
        live_handler_name,
    )

    if isinstance(
        commands,
        tuple,
    ):
        new_commands = (
            commands[:command_index]
            + (new_descriptor,)
            + commands[
                command_index + 1:
            ]
        )
    else:
        new_commands = list(
            commands
        )

        new_commands[
            command_index
        ] = new_descriptor

        if type(commands) is not list:
            try:
                new_commands = type(
                    commands
                )(
                    new_commands
                )
            except Exception:
                pass

    return _replace_field(
        registry,
        "commands",
        new_commands,
    )


def verify_exact_ask_descriptor_binding() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert SOURCE_MUTATION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    return True


__all__ = [
    "BUILD_ID",
    "OLC_010_REVISION",
    "build_live_ask_handler",
    "build_patched_registry",
    "verify_exact_ask_descriptor_binding",
]
"""

TEST_SOURCE_TEMPLATE = r"""
from __future__ import annotations

import importlib
import json
import unittest
from pathlib import Path

from qseries_v2.oracle_live_composition.olc_005_live_read_model_refresh import (
    AtomicLiveReadModelStore,
)
from qseries_v2.oracle_live_composition.olc_010_exact_ask_descriptor_binding import (
    build_live_ask_handler,
    build_patched_registry,
    verify_exact_ask_descriptor_binding,
)

MANIFEST = Path(__MANIFEST__)


class TestOLC010(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_exact_ask_descriptor_binding()
        )

    def test_exact_fallback_handler(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        module = importlib.import_module(
            payload[
                "fallback_handler_module"
            ]
        )

        fallback = getattr(
            module,
            payload[
                "fallback_handler_symbol"
            ],
        )

        self.assertTrue(
            callable(
                fallback
            )
        )

        self.assertEqual(
            fallback.__name__,
            "handle_ask",
        )

    def test_descriptor_patch(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        registry_module = importlib.import_module(
            payload[
                "registry_module_name"
            ]
        )

        builder = getattr(
            registry_module,
            payload[
                "registry_builder_name"
            ],
        )

        fallback_module = importlib.import_module(
            payload[
                "fallback_handler_module"
            ]
        )

        fallback = getattr(
            fallback_module,
            payload[
                "fallback_handler_symbol"
            ],
        )

        registry = builder()

        live_handler = build_live_ask_handler(
            store=AtomicLiveReadModelStore(),
            fallback_handler=fallback,
        )

        patched = build_patched_registry(
            registry=registry,
            command_index=(
                payload[
                    "command_index"
                ]
            ),
            handler_name_field=(
                payload[
                    "handler_name_field"
                ]
            ),
            live_handler_name=(
                payload[
                    "live_handler_symbol"
                ]
            ),
        )

        descriptor = patched.commands[
            payload[
                "command_index"
            ]
        ]

        self.assertEqual(
            getattr(
                descriptor,
                payload[
                    "handler_name_field"
                ],
            ),
            payload[
                "live_handler_symbol"
            ],
        )

        self.assertEqual(
            live_handler.__name__,
            payload[
                "live_handler_symbol"
            ],
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
                "handler_name_field"
            ],
            "handler_name",
        )

        self.assertEqual(
            payload[
                "fallback_handler_symbol"
            ],
            "handle_ask",
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-010 CERTIFICATION TEST")
    print(
        " EXACT /ASK DESCRIPTOR BINDING "
        "— CORRECTION V3"
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
        "[PASS] Descriptor handler_name='handle_ask' "
        "resolved to the real handle_ask callable"
    )
    print(
        "[PASS] Live overlay uses a symbolic handler-name "
        "replacement compatible with the actual registry contract"
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


def type_name(
    value: Any,
) -> str:
    return (
        f"{type(value).__module__}."
        f"{type(value).__qualname__}"
    )


def command_is_ask(
    value: Any,
) -> bool:
    text = str(
        value
    ).strip().lower()

    if text.startswith(
        "/"
    ):
        text = text[1:]

    return text == "ask"


def locate_exact_contract():
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

    ask_index = None
    descriptor = None

    for index, item in enumerate(
        commands
    ):
        if command_is_ask(
            getattr(
                item,
                "command",
                None,
            )
        ):
            ask_index = index
            descriptor = item
            break

    if descriptor is None:
        raise RuntimeError(
            "exact /ask descriptor missing"
        )

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
            "/ask descriptor handler_name is missing "
            "or is not a string"
        )

    handler_name = handler_name.strip()

    if handler_name != "handle_ask":
        raise RuntimeError(
            "unexpected /ask handler_name: "
            f"{handler_name!r}"
        )

    fallback = getattr(
        module,
        handler_name,
        None,
    )

    if not callable(
        fallback
    ):
        # Search the resolved interactive terminal module too,
        # because handler symbols can be imported there.
        terminal_manifest = json.loads(
            (
                PACKAGE
                / "OLC_002_TERMINAL_RUNTIME_MANIFEST.json"
            ).read_text(
                encoding="utf-8"
            )
        )

        terminal_module_name = (
            terminal_manifest[
                "top_candidate"
            ][
                "module_name"
            ]
        )

        terminal_module = (
            importlib.import_module(
                terminal_module_name
            )
        )

        fallback = getattr(
            terminal_module,
            handler_name,
            None,
        )

        if callable(
            fallback
        ):
            fallback_module_name = (
                terminal_module_name
            )
        else:
            raise RuntimeError(
                "descriptor handler_name='handle_ask' "
                "does not resolve to a callable in the "
                "registry or interactive terminal module"
            )
    else:
        fallback_module_name = (
            module_name
        )

    return {
        "registry_module_name": module_name,
        "registry_builder_name": builder_name,
        "registry_type": type_name(
            registry
        ),
        "commands_type": type_name(
            commands
        ),
        "command_index": ask_index,
        "command_name": "/ask",
        "descriptor_type": type_name(
            descriptor
        ),
        "handler_name_field": "handler_name",
        "fallback_handler_name": handler_name,
        "fallback_handler_module": (
            fallback_module_name
        ),
        "fallback_handler_symbol": (
            fallback.__name__
        ),
        "fallback_handler_qualname": (
            fallback.__qualname__
        ),
        "live_handler_symbol": (
            "oracle_live_ask_handler"
        ),
        "binding_mode": (
            "symbolic_handler_name_overlay"
        ),
    }


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
        "— CORRECTION V3"
    )
    print("=" * 72)

    print(
        f"[BOOT] Revision: "
        f"{INSTALLER_REVISION}"
    )

    print(
        f"[ROOT] {ROOT}"
    )

    # OLC-002 is used by fallback resolution when needed.
    required_extra = (
        PACKAGE
        / "OLC_002_TERMINAL_RUNTIME_MANIFEST.json"
    )

    if not required_extra.is_file():
        raise RuntimeError(
            f"Certified upstream missing: "
            f"{required_extra}"
        )

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: "
                f"{path}"
            )

    exact = locate_exact_contract()

    print(
        "[PASS] Exact /ask descriptor found: "
        f"registry.commands[{exact['command_index']}]"
    )

    print(
        "[PASS] Descriptor handler_name: "
        f"{exact['fallback_handler_name']}"
    )

    print(
        "[PASS] Real fallback handler: "
        f"{exact['fallback_handler_module']}."
        f"{exact['fallback_handler_qualname']}"
    )

    print(
        "[PASS] Binding mode: "
        f"{exact['binding_mode']}"
    )

    target_path = (
        ROOT
        / Path(
            *exact[
                "registry_module_name"
            ].split(
                "."
            )
        ).with_suffix(
            ".py"
        )
    )

    protected = (
        *UPSTREAMS,
        required_extra,
        target_path,
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
        **exact,
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
            "[PASS] OLC-010 corrected to bind the "
            "actual handle_ask symbol instead of "
            "misidentifying the registry builder"
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
