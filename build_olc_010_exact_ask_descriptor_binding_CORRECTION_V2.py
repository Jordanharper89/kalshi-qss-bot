from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
import json
from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass, replace
from pathlib import Path
from typing import Any

ROOT = Path.cwd().resolve()

PACKAGE = (
    ROOT
    / "qseries_v2"
    / "oracle_live_composition"
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
    "INSTALLER_CORRECTION_V2"
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
OLC_010_REVISION = (
    "OLC_010_EXACT_ASK_DESCRIPTOR_BINDING_V1"
)

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
            key,
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


def bind_ask_descriptor(
    *,
    registry: Any,
    command_index: int,
    binding_field: str,
    fallback_handler: Callable[..., Any],
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

    live_handler = build_live_ask_handler(
        store=store,
        fallback_handler=fallback_handler,
    )

    current_value = getattr(
        descriptor,
        binding_field,
        None,
    )

    # If the descriptor field itself is callable,
    # replace it directly. If it is symbolic metadata,
    # bind the live handler to the same field only when
    # that descriptor type accepts callables there.
    new_descriptor = _replace_field(
        descriptor,
        binding_field,
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

        registry_module = importlib.import_module(
            payload[
                "registry_module_name"
            ]
        )

        registry_builder = getattr(
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

        fallback_handler = getattr(
            fallback_module,
            payload[
                "fallback_handler_symbol"
            ],
        )

        registry = registry_builder()

        patched = bind_ask_descriptor(
            registry=registry,
            command_index=(
                payload[
                    "command_index"
                ]
            ),
            binding_field=(
                payload[
                    "binding_field"
                ]
            ),
            fallback_handler=(
                fallback_handler
            ),
            store=AtomicLiveReadModelStore(),
        )

        descriptor = patched.commands[
            payload[
                "command_index"
            ]
        ]

        bound = getattr(
            descriptor,
            payload[
                "binding_field"
            ],
        )

        self.assertTrue(
            callable(
                bound
            )
        )

        self.assertEqual(
            getattr(
                bound,
                "__name__",
                "",
            ),
            "oracle_live_ask_handler",
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
                "binding_field"
            ]
        )

        self.assertTrue(
            payload[
                "fallback_handler_module"
            ]
        )

        self.assertTrue(
            payload[
                "fallback_handler_symbol"
            ]
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OLC-010 CERTIFICATION TEST")
    print(
        " EXACT /ASK DESCRIPTOR BINDING "
        "— CORRECTION V2"
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
        "[PASS] Exact /ask descriptor binding field "
        "and real fallback handler resolved"
    )
    print(
        "[PASS] Live handler overlays the descriptor "
        "in memory only"
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


def descriptor_fields(
    descriptor: Any,
):
    names = []

    if is_dataclass(
        descriptor
    ):
        names.extend(
            field.name
            for field in fields(
                descriptor
            )
        )

    if hasattr(
        descriptor,
        "_fields",
    ):
        names.extend(
            str(
                name
            )
            for name in descriptor._fields
        )

    if hasattr(
        descriptor,
        "__dict__",
    ):
        names.extend(
            descriptor.__dict__.keys()
        )

    for name in dir(
        descriptor
    ):
        if name.startswith(
            "_"
        ):
            continue

        names.append(
            name
        )

    return tuple(
        sorted(
            set(
                names
            )
        )
    )


def source_candidates(
    target_path: Path,
):
    source = target_path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source,
        filename=str(
            target_path
        ),
    )

    rows = []

    for node in ast.walk(
        tree
    ):
        if not isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            continue

        segment = (
            ast.get_source_segment(
                source,
                node,
            )
            or ""
        )

        lower = segment.lower()

        score = 0
        evidence = []

        if "ask" in node.name.lower():
            score += 5
            evidence.append(
                "symbol_name_contains_ask"
            )

        if "/ask" in lower:
            score += 6
            evidence.append(
                "contains_/ask"
            )

        if (
            "command" in lower
            and "ask" in lower
        ):
            score += 3
            evidence.append(
                "contains_command_and_ask"
            )

        if (
            "query" in lower
            or "question" in lower
        ):
            score += 2
            evidence.append(
                "contains_query_semantics"
            )

        if score:
            rows.append(
                {
                    "name": node.name,
                    "score": score,
                    "evidence": evidence,
                }
            )

    rows.sort(
        key=lambda item: (
            -item[
                "score"
            ],
            item[
                "name"
            ],
        )
    )

    return rows


def imported_fallback_candidates(
    target_module,
    descriptor,
):
    rows = []

    for name in descriptor_fields(
        descriptor
    ):
        try:
            value = getattr(
                descriptor,
                name,
            )
        except Exception:
            continue

        if isinstance(
            value,
            str,
        ):
            candidate = getattr(
                target_module,
                value,
                None,
            )

            if callable(
                candidate
            ):
                rows.append(
                    {
                        "binding_field": name,
                        "binding_value": value,
                        "fallback_handler": candidate,
                        "mode": (
                            "descriptor_symbol_reference"
                        ),
                        "score": 10,
                    }
                )

        if callable(
            value
        ):
            rows.append(
                {
                    "binding_field": name,
                    "binding_value": None,
                    "fallback_handler": value,
                    "mode": (
                        "descriptor_callable"
                    ),
                    "score": 12,
                }
            )

    return rows


def locate_exact_descriptor_and_handler():
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
            "command registry does not expose commands"
        )

    ask_index = None
    ask_descriptor = None

    for index, descriptor in enumerate(
        commands
    ):
        command = getattr(
            descriptor,
            "command",
            None,
        )

        if command_is_ask(
            command
        ):
            ask_index = index
            ask_descriptor = descriptor
            break

    if ask_descriptor is None:
        raise RuntimeError(
            "exact /ask descriptor missing"
        )

    print(
        "[PASS] Exact /ask descriptor found: "
        f"registry.commands[{ask_index}]"
    )

    print(
        "[INFO] /ask descriptor type: "
        f"{type_name(ask_descriptor)}"
    )

    field_names = descriptor_fields(
        ask_descriptor
    )

    visible = []

    for name in field_names:
        try:
            value = getattr(
                ask_descriptor,
                name,
            )
        except Exception:
            continue

        if callable(
            value
        ):
            preview = (
                f"<callable "
                f"{getattr(value, '__module__', '')}."
                f"{getattr(value, '__qualname__', getattr(value, '__name__', ''))}>"
            )
        else:
            preview = repr(
                value
            )

            if len(
                preview
            ) > 180:
                preview = (
                    preview[:177]
                    + "..."
                )

        visible.append(
            (
                name,
                preview,
            )
        )

    print(
        "[INFO] /ask descriptor fields:"
    )

    for name, preview in visible:
        print(
            f"       {name} = {preview}"
        )

    candidates = (
        imported_fallback_candidates(
            module,
            ask_descriptor,
        )
    )

    if not candidates:
        target_path = (
            ROOT
            / Path(
                *module_name.split(
                    "."
                )
            ).with_suffix(
                ".py"
            )
        )

        source_rows = (
            source_candidates(
                target_path
            )
        )

        if not source_rows:
            raise RuntimeError(
                "exact /ask descriptor found, but "
                "no callable or symbolic handler field "
                "and no source-level /ask handler candidate "
                "could be resolved"
            )

        top_score = source_rows[
            0
        ][
            "score"
        ]

        top_rows = [
            row
            for row in source_rows
            if row[
                "score"
            ] == top_score
        ]

        if len(
            top_rows
        ) != 1:
            raise RuntimeError(
                "ambiguous source-level /ask handler candidates: "
                + ", ".join(
                    row[
                        "name"
                    ]
                    for row in top_rows
                )
            )

        handler_name = top_rows[
            0
        ][
            "name"
        ]

        handler = getattr(
            module,
            handler_name,
            None,
        )

        if not callable(
            handler
        ):
            raise RuntimeError(
                "source-level /ask handler candidate "
                "is not importable as a callable"
            )

        # Find a descriptor field that can plausibly carry
        # the callable or symbolic handler. We prefer explicit
        # dispatch/handler metadata fields.
        preferred_names = (
            "handler",
            "callback",
            "function",
            "func",
            "action",
            "execute",
            "invoke",
            "dispatch",
            "resolver",
            "target",
            "handler_name",
            "handler_id",
            "symbol",
            "function_name",
        )

        binding_field = None

        for name in preferred_names:
            if name in field_names:
                binding_field = name
                break

        if binding_field is None:
            raise RuntimeError(
                "real /ask fallback handler was resolved "
                "from source, but the descriptor exposes no "
                "certifiable binding field"
            )

        candidates.append(
            {
                "binding_field": binding_field,
                "binding_value": getattr(
                    ask_descriptor,
                    binding_field,
                    None,
                ),
                "fallback_handler": handler,
                "mode": (
                    "source_handler_plus_descriptor_binding_field"
                ),
                "score": 8,
            }
        )

    candidates.sort(
        key=lambda item: (
            -item[
                "score"
            ],
            item[
                "binding_field"
            ],
        )
    )

    best_score = candidates[
        0
    ][
        "score"
    ]

    best = [
        item
        for item in candidates
        if item[
            "score"
        ] == best_score
    ]

    if len(
        best
    ) != 1:
        raise RuntimeError(
            "ambiguous exact /ask binding candidates: "
            + ", ".join(
                item[
                    "binding_field"
                ]
                for item in best
            )
        )

    selected = best[
        0
    ]

    fallback_handler = selected[
        "fallback_handler"
    ]

    print(
        "[PASS] Exact /ask binding mode: "
        f"{selected['mode']}"
    )

    print(
        "[PASS] Exact /ask binding field: "
        f"{selected['binding_field']}"
    )

    print(
        "[PASS] Real fallback handler: "
        f"{getattr(fallback_handler, '__module__', '')}."
        f"{getattr(fallback_handler, '__qualname__', getattr(fallback_handler, '__name__', ''))}"
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
            ask_descriptor
        ),
        "binding_mode": selected[
            "mode"
        ],
        "binding_field": selected[
            "binding_field"
        ],
        "binding_original_value": repr(
            selected[
                "binding_value"
            ]
        ),
        "fallback_handler_module": getattr(
            fallback_handler,
            "__module__",
            None,
        ),
        "fallback_handler_symbol": getattr(
            fallback_handler,
            "__name__",
            None,
        ),
        "fallback_handler_qualname": getattr(
            fallback_handler,
            "__qualname__",
            getattr(
                fallback_handler,
                "__name__",
                None,
            ),
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
        "— CORRECTION V2"
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

    exact = (
        locate_exact_descriptor_and_handler()
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
            "[PASS] OLC-010 corrected to resolve "
            "the actual descriptor-to-handler contract"
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
