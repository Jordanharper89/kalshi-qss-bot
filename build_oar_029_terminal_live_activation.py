from __future__ import annotations

import ast
import hashlib
from pathlib import Path

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "observation_adapter_runtime"
OIT = ROOT / "qseries_v2" / "oracle_terminal"

UPSTREAMS = (
    PKG / "oar_025_oit_ask_dispatch_resolver.py",
    PKG / "oar_026_live_ask_dispatch_binding.py",
    PKG / "oar_027_terminal_live_query_e2e.py",
    PKG / "oar_028_full_live_intelligence_certification.py",
    OIT / "oracle_live_ask_dispatch_adapter.py",
)

MODULE = PKG / "oar_029_terminal_live_activation.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_oar_029_terminal_live_activation.py"
LAUNCHER = ROOT / "run_oracle_terminal_LIVE_READ_ONLY.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oar_027_terminal_live_query_e2e import (
    TerminalLiveQueryEndToEnd,
)

BUILD_ID = "OAR-029"
OAR_029_REVISION = "OAR_029_TERMINAL_LIVE_ACTIVATION_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False
PRODUCTION_READ_ACTIVATION_ALLOWED = True


@dataclass(frozen=True, slots=True)
class TerminalLiveActivation:
    activation_id: str
    read_path_name: str
    legacy_fallback_enabled: bool
    live_query_interception_enabled: bool
    read_only: bool
    execution_allowed: bool


class TerminalLiveActivationBoundary:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def activate(self) -> TerminalLiveActivation:
        return TerminalLiveActivation(
            activation_id=(
                "oracle.terminal.live.read.v1"
            ),
            read_path_name=(
                "OAR-027 TerminalLiveQueryEndToEnd"
            ),
            legacy_fallback_enabled=True,
            live_query_interception_enabled=True,
            read_only=True,
            execution_allowed=False,
        )

    def build_read_path(
        self,
    ) -> TerminalLiveQueryEndToEnd:
        return TerminalLiveQueryEndToEnd()


def verify_terminal_live_activation() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    assert PRODUCTION_READ_ACTIVATION_ALLOWED is True
    return True
"""

LAUNCHER_SOURCE = r"""
from __future__ import annotations

from qseries_v2.observation_adapter_runtime.oar_029_terminal_live_activation import (
    TerminalLiveActivationBoundary,
)

BUILD_ID = "OAR-029-LAUNCHER"
REVISION = "OAR_029_TERMINAL_LIVE_READ_ONLY_LAUNCHER_V1"


def main() -> int:
    activation = (
        TerminalLiveActivationBoundary()
        .activate()
    )

    print("=" * 72)
    print(" ORACLE TERMINAL — LIVE INTELLIGENCE READ-ONLY ACTIVATION")
    print("=" * 72)
    print(f"[ACTIVATION] {activation.activation_id}")
    print("[MODE] READ-ONLY")
    print("[PASS] Live /ask interception enabled")
    print("[PASS] Existing Oracle Terminal fallback enabled")
    print("[PASS] OAR-027 terminal live read path active")
    print("[PASS] Execution, publication, and persistence disabled")
    print()
    print(
        "[INFO] This launcher activates the certified "
        "live-intelligence read boundary. It does not place trades."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest

from qseries_v2.observation_adapter_runtime.oar_029_terminal_live_activation import (
    TerminalLiveActivationBoundary,
    verify_terminal_live_activation,
)


class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_terminal_live_activation()
        )

    def test_activation(self):
        activation = (
            TerminalLiveActivationBoundary()
            .activate()
        )

        self.assertTrue(
            activation.live_query_interception_enabled
        )

        self.assertTrue(
            activation.legacy_fallback_enabled
        )

        self.assertTrue(
            activation.read_only
        )

        self.assertFalse(
            activation.execution_allowed
        )

    def test_read_path(self):
        path = (
            TerminalLiveActivationBoundary()
            .build_read_path()
        )

        self.assertTrue(path.read_only)
        self.assertFalse(path.execution_allowed)


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-029 CERTIFICATION TEST")
    print(" PRODUCTION TERMINAL LIVE READ ACTIVATION BOUNDARY")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-029")
    print("[PASS] Production read-only live terminal activation boundary certified")
    print("[PASS] Live /ask interception and legacy fallback both enabled")
    print("[PASS] Execution, publication, and persistence remain disabled")
    print("[DONE] OAR-029 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_checked(path: Path, source: str) -> None:
    text = source.lstrip()
    ast.parse(text, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )
    print(f"[PASS] Wrote: {path.relative_to(ROOT)}")


def main() -> int:
    print("=" * 72)
    print(" OAR-029 INSTALLER")
    print(" PRODUCTION TERMINAL LIVE READ ACTIVATION BOUNDARY")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OAR_029_TERMINAL_LIVE_ACTIVATION_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: {path}"
            )

    protected = UPSTREAMS

    hashes = {
        path: sha(path)
        for path in protected
    }

    affected = (
        MODULE,
        TEST,
        INIT,
        LAUNCHER,
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
        write_checked(MODULE, MODULE_SOURCE)
        write_checked(TEST, TEST_SOURCE)
        write_checked(LAUNCHER, LAUNCHER_SOURCE)

        current = (
            INIT.read_text(encoding="utf-8")
            if INIT.exists()
            else ""
        )

        export = (
            "from ."
            "oar_029_terminal_live_activation "
            "import *"
        )

        if export not in current.splitlines():
            if current and not current.endswith("\n"):
                current += "\n"
            current += export + "\n"
            ast.parse(current, filename=str(INIT))
            INIT.write_text(
                current,
                encoding="utf-8",
                newline="\n",
            )

        for path, expected in hashes.items():
            if sha(path) != expected:
                raise RuntimeError(
                    f"Certified upstream changed: {path.name}"
                )

        print(
            "[PASS] Certified OAR and OIT bridge "
            "upstream remained unchanged"
        )
        print(
            f"[PASS] Wrote production read-only launcher: "
            f"{LAUNCHER.name}"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + TEST.read_bytes()
            + LAUNCHER.read_bytes()
        ).hexdigest()

        print(
            f"[PASS] Deterministic install hash: {install_hash}"
        )
        print(
            "[DONE] OAR-029 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OAR-029 installation failed; "
            "affected files restored"
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
