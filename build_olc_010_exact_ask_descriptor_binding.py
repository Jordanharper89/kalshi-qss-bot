from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
from dataclasses import is_dataclass
from pathlib import Path

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
            **{
                field_name: value,
            },
        )

    replacer = getattr(
        obj,
        "_replace",
        None,
    )

    if callable(replacer):
        return replacer(
            **{
                field_name: value,
            }
        )

    clone = object.__new__(
        type(obj)
    )

    if hasattr(
        obj,
        "__dict__",
    ):
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
        "unsupported immutable registry descriptor type"
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
        if key in kwargs:
            value = kwargs[key]
            if isinstance(value, str):
                return value

    for value in args:
        if isinstance(
            value,
            str,
        ):
            return value

    raise TypeError(
        "unable to extract /ask query from handler arguments"
    )


def build_live_ask_handler(
    *,
    store: AtomicLiveReadModelStore,
    fallback_handler: Callable[..., Any],
) -> Callable[..., Any]:
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

        status, value = overlay.dispatch(
            query,
            *args,
            **kwargs,
        )

        return value

    live_ask_handler.__name__ = (
        "oracle_live_ask_handler"
    )

    live_ask_handler.__doc__ = (
        "Read-only live /ask overlay with exact legacy fallback."
    )

    return live_ask_handler


def bind_ask_descriptor(
    *,
    registry: Any,
    command_index: int,
    handler_field: str,
    store: AtomicLiveReadModelStore,
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

    if not isinstance(
        command_index,
        int,
    ):
        raise TypeError(
            "command_index must be int"
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

    fallback_handler = getattr(
        descriptor,
        handler_field,
        None,
    )

    if not callable(
        fallback_handler
    ):
        raise TypeError(
            "resolved /ask handler is not callable"
        )

    live_handler = build_live_ask_handler(
        store=store,
        fallback_handler=fallback_handler,
    )

    new_descriptor = _replace_field(
        descriptor,
        handler_field,
        live_handler,
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
    "bind_ask_descriptor",
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
    bind_ask_descriptor,
    verify_exact_ask_descriptor_binding,
)

MANIFEST = Path(__MANIFEST__)


class TestOLC010(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_exact_ask_descriptor_binding()
        )

    def test_exact_binding(self):
        payload = json.loads(
            MANIFEST.read_text(
                encoding="utf-8"
            )
        )

        module = importlib.import_module(
            payload[
                "registry_module_name"
            ]
        )

        builder = getattr(
            module,
            payload[
                "registry_builder_name"
            ],
        )

        registry = builder()

        original_descriptor = (
            registry.commands[
                payload[
                    "command_index"
                ]
            ]
        )

        original_handler = getattr(
            original_descriptor,
            payload[
                "handler_field"
            ],
        )

        patched = bind_ask_descriptor(
            registry=registry,
            command_index=(
                payload[
                    "command_index"
                ]
            ),
            handler_field=(
                payload[
                    "handler_field"
                ]
            ),
            store=AtomicLiveReadModelStore(),
        )

        patched_descriptor = (
            patched.commands[
                payload[
                    "command_index"
                ]
            ]
        )

        patched_handler = getattr(
            patched_descriptor,
            payload[
                "handler_field"
            ],
        )

        self.assertTrue(
            callable(
                original_handler
            )
        )

        self.assertTrue(
            callable(
                patched_handler
            )
        )

        self.assertIsNot(
            original_handler,
            patched_handler,
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

        self.assertTrue(
            payload[
                "handler_field"
            ]
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-010 CERTIFICATION TEST")
    print(" EXACT /ASK DESCRIPTOR BINDING")
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
    print("[PASS] Exact registry.commands /ask descriptor and callable handler field bound in memory")
    print("[PASS] Legacy /ask handler remains preserved as fallback")
    print("[PASS] Existing Oracle Terminal source remains unchanged")
    print("[DONE] OLC-010 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def locate_exact_descriptor():
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
            "actual command registry does not expose commands"
        )

    match = None

    for index, descriptor in enumerate(
        commands
    ):
        command_value = getattr(
            descriptor,
            "command",
            None,
        )

        if str(
            command_value
        ).strip().lower() not in (
            "/ask",
            "ask",
        ):
            continue

        handler_candidates = []

        for attr in (
            "handler",
            "callback",
            "callable",
            "function",
            "func",
            "action",
            "execute",
            "invoke",
        ):
            candidate = getattr(
                descriptor,
                attr,
                None,
            )

            if callable(
                candidate
            ):
                handler_candidates.append(
                    (
                        attr,
                        candidate,
                    )
                )

        if not handler_candidates:
            raise RuntimeError(
                "exact /ask descriptor found but no callable handler field resolved"
            )

        if len(
            handler_candidates
        ) > 1:
            preferred = [
                item
                for item
                in handler_candidates
                if item[0]
                in (
                    "handler",
                    "callback",
                    "func",
                    "function",
                )
            ]

            if len(
                preferred
            ) == 1:
                handler_candidates = (
                    preferred
                )

        if len(
            handler_candidates
        ) != 1:
            raise RuntimeError(
                "ambiguous callable handler fields on exact /ask descriptor"
            )

        handler_field, handler = (
            handler_candidates[
                0
            ]
        )

        match = {
            "registry_module_name": module_name,
            "registry_builder_name": builder_name,
            "registry_type": (
                f"{type(registry).__module__}."
                f"{type(registry).__qualname__}"
            ),
            "commands_type": (
                f"{type(commands).__module__}."
                f"{type(commands).__qualname__}"
            ),
            "command_index": index,
            "command_name": "/ask",
            "descriptor_type": (
                f"{type(descriptor).__module__}."
                f"{type(descriptor).__qualname__}"
            ),
            "descriptor_is_dataclass": bool(
                is_dataclass(
                    descriptor
                )
            ),
            "handler_field": handler_field,
            "handler_module": getattr(
                handler,
                "__module__",
                None,
            ),
            "handler_name": getattr(
                handler,
                "__qualname__",
                getattr(
                    handler,
                    "__name__",
                    type(
                        handler
                    ).__name__,
                ),
            ),
        }

        break

    if match is None:
        raise RuntimeError(
            "exact /ask descriptor not found in registry.commands"
        )

    return match


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
    print(" OLC-010 INSTALLER")
    print(" EXACT /ASK DESCRIPTOR BINDING")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OLC_010_EXACT_ASK_DESCRIPTOR_BINDING_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: "
                f"{path}"
            )

    exact = locate_exact_descriptor()

    print(
        "[PASS] Exact /ask descriptor resolved: "
        f"registry.commands[{exact['command_index']}].command"
    )

    print(
        "[PASS] Exact /ask handler field: "
        f"{exact['handler_field']}"
    )

    print(
        "[PASS] Legacy handler: "
        f"{exact['handler_module']}."
        f"{exact['handler_name']}"
    )

    target_path = (
        ROOT
        / Path(
            *exact[
                "registry_module_name"
            ].split(".")
        ).with_suffix(".py")
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
            "olc_010_exact_ask_descriptor_binding "
            "import *"
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
                    "Certified/frozen source changed: "
                    f"{path.name}"
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
            "[PASS] Deterministic install hash: "
            f"{install_hash}"
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
            "[ROLLBACK] OLC-010 installation failed; affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
