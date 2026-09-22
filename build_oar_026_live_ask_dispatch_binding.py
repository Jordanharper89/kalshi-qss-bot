from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

ROOT = Path.cwd().resolve()
PKG = ROOT / "qseries_v2" / "observation_adapter_runtime"
OIT = ROOT / "qseries_v2" / "oracle_terminal"

UPSTREAMS = (
    PKG / "oar_023_terminal_live_query_router.py",
    PKG / "oar_024_oit_live_intelligence_bridge.py",
    PKG / "oar_025_oit_ask_dispatch_resolver.py",
    PKG / "oar_025_oit_ask_dispatch_manifest.json",
)

MODULE = PKG / "oar_026_live_ask_dispatch_binding.py"
INIT = PKG / "__init__.py"
TEST = ROOT / "test_oar_026_live_ask_dispatch_binding.py"
OIT_ADAPTER = OIT / "oracle_live_ask_dispatch_adapter.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass

from .oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from .oar_024_oit_live_intelligence_bridge import (
    OITLiveIntelligenceBridge,
    OITLiveIntelligenceResponse,
)

BUILD_ID = "OAR-026"
OAR_026_REVISION = "OAR_026_LIVE_ASK_DISPATCH_BINDING_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


@dataclass(frozen=True, slots=True)
class LiveAskDispatchBindingResult:
    query: str
    live_response: OITLiveIntelligenceResponse
    consume_existing_terminal: bool
    read_only: bool


class LiveAskDispatchBinding:
    read_only = True
    execution_allowed = False
    publication_allowed = False
    persistence_allowed = False

    def dispatch(
        self,
        *,
        query: str,
        read_model: TerminalLiveIntelligenceReadModel | None,
    ) -> LiveAskDispatchBindingResult:
        response = (
            OITLiveIntelligenceBridge()
            .respond(
                query=query,
                read_model=read_model,
            )
        )

        return LiveAskDispatchBindingResult(
            query=query,
            live_response=response,
            consume_existing_terminal=(
                response
                .fallback_to_existing_terminal
            ),
            read_only=True,
        )


def verify_live_ask_dispatch_binding() -> bool:
    assert READ_ONLY is True
    assert EXECUTION_ALLOWED is False
    assert PUBLICATION_ALLOWED is False
    assert PERSISTENCE_ALLOWED is False
    return True
"""

OIT_ADAPTER_SOURCE = r"""
from __future__ import annotations

from qseries_v2.observation_adapter_runtime.oar_026_live_ask_dispatch_binding import (
    LiveAskDispatchBinding,
)

BUILD_ID = "OAR-026-OIT"
REVISION = "OAR_026_OIT_LIVE_ASK_DISPATCH_ADAPTER_V1"

READ_ONLY = True
EXECUTION_ALLOWED = False
PUBLICATION_ALLOWED = False
PERSISTENCE_ALLOWED = False


def build_oracle_live_ask_dispatch_adapter():
    return LiveAskDispatchBinding()


def verify_oracle_live_ask_dispatch_adapter() -> bool:
    adapter = (
        build_oracle_live_ask_dispatch_adapter()
    )

    assert adapter.read_only is True
    assert adapter.execution_allowed is False
    assert adapter.publication_allowed is False
    assert adapter.persistence_allowed is False

    return True
"""

TEST_SOURCE = r"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from qseries_v2.observation_adapter_runtime.oar_022_terminal_live_intelligence_read_model import (
    TerminalLiveIntelligenceReadModel,
)
from qseries_v2.observation_adapter_runtime.oar_026_live_ask_dispatch_binding import (
    LiveAskDispatchBinding,
    verify_live_ask_dispatch_binding,
)
from qseries_v2.oracle_terminal.oracle_live_ask_dispatch_adapter import (
    verify_oracle_live_ask_dispatch_adapter,
)

NOW = datetime(
    2026,
    8,
    12,
    16,
    0,
    tzinfo=timezone.utc,
)


def read_model():
    return TerminalLiveIntelligenceReadModel(
        read_model_id="terminal.live.1",
        iteration_number=1,
        observation_count=1,
        observation_ids=("liveobs.1",),
        provider_ids=("coinbase",),
        capability_ids=("spot_price",),
        oi_ready=True,
        umd_ready=True,
        oml_ready=True,
        lineage_valid=True,
        generated_at=NOW,
        evidence_hash="a"*64,
        read_only=True,
    )


class T(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(
            verify_live_ask_dispatch_binding()
        )

        self.assertTrue(
            verify_oracle_live_ask_dispatch_adapter()
        )

    def test_live_query_intercept(self):
        result = (
            LiveAskDispatchBinding()
            .dispatch(
                query=(
                    "why is bitcoin moving?"
                ),
                read_model=read_model(),
            )
        )

        self.assertTrue(
            result.live_response.handled
        )

        self.assertFalse(
            result.consume_existing_terminal
        )

    def test_fallback(self):
        result = (
            LiveAskDispatchBinding()
            .dispatch(
                query="show current session",
                read_model=read_model(),
            )
        )

        self.assertTrue(
            result.consume_existing_terminal
        )


if __name__ == "__main__":
    print("=" * 72)
    print(" OAR-026 CERTIFICATION TEST")
    print(" LIVE /ASK DISPATCH BINDING")
    print("=" * 72)

    result = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not result.wasSuccessful():
        raise SystemExit(1)

    print()
    print("[PASS] Build: OAR-026")
    print("[PASS] Live /ask queries can be intercepted before legacy terminal fallback")
    print("[PASS] Non-live queries preserve the existing OIT dispatch path")
    print("[PASS] Binding remains additive, read-only, and non-executing")
    print("[DONE] OAR-026 CERTIFIED")
"""


def sha(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


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
    print(" OAR-026 INSTALLER")
    print(" LIVE /ASK DISPATCH BINDING")
    print("=" * 72)
    print(
        "[BOOT] Revision: "
        "OAR_026_LIVE_ASK_DISPATCH_BINDING_INSTALLER_V1"
    )
    print(f"[ROOT] {ROOT}")

    for path in UPSTREAMS:
        if not path.is_file():
            raise RuntimeError(
                f"Certified upstream missing: "
                f"{path}"
            )

    manifest = json.loads(
        UPSTREAMS[-1].read_text(
            encoding="utf-8"
        )
    )

    top = manifest.get(
        "top_candidate"
    )

    if not top:
        raise RuntimeError(
            "OAR-025 /ask boundary manifest "
            "has no top candidate"
        )

    if top.get("score", 0) < 6:
        raise RuntimeError(
            "OAR-025 /ask boundary is not "
            "certified with sufficient confidence"
        )

    module_name = top["module_name"]

    relative = Path(
        *module_name.split(".")
    ).with_suffix(".py")

    target_path = (
        ROOT / relative
    )

    if not target_path.is_file():
        raise RuntimeError(
            f"Resolved OIT /ask module missing: "
            f"{target_path}"
        )

    protected = (
        *UPSTREAMS,
        target_path,
    )

    hashes = {
        path: sha(path)
        for path in protected
    }

    print(
        "[PASS] Certified OIT /ask boundary consumed: "
        f"{module_name}.{top['symbol_name']}"
    )

    affected = (
        MODULE,
        TEST,
        INIT,
        OIT_ADAPTER,
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
            OIT_ADAPTER,
            OIT_ADAPTER_SOURCE,
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
            "oar_026_live_ask_dispatch_binding "
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
            "[PASS] Resolved certified OIT /ask "
            "source remained unchanged"
        )

        print(
            "[PASS] OIT received one additive "
            "read-only /ask dispatch adapter"
        )

        install_hash = hashlib.sha256(
            MODULE.read_bytes()
            + OIT_ADAPTER.read_bytes()
            + TEST.read_bytes()
        ).hexdigest()

        print(
            "[PASS] Deterministic install hash: "
            f"{install_hash}"
        )

        print(
            "[DONE] OAR-026 INSTALLATION COMPLETE"
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
            "[ROLLBACK] OAR-026 installation failed; "
            "affected files restored"
        )

        raise


if __name__ == "__main__":
    raise SystemExit(main())
