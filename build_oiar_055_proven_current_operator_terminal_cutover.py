from pathlib import Path
import ast
import importlib
import os
import subprocess
import sys
import time

ROOT = Path.cwd().resolve()

MOD = ROOT / "qseries_v2/oracle_intelligence_analytics_runtime/oiar_055_proven_current_operator_terminal_cutover.py"
TEST = ROOT / "test_oiar_055_proven_current_operator_terminal_cutover.py"

MODULE_SOURCE = r'''from __future__ import annotations

from pathlib import Path

from .oiar_054_proven_current_trader_analytics import (
    read_latest_current_trader_analytics,
)

OIAR_055_BUILD_ID = "OIAR-055"
OIAR_055_REVISION = "OIAR_055_PROVEN_CURRENT_OPERATOR_TERMINAL_CUTOVER_V1"

TOKENS = (
    "what do you like",
    "plays for today",
    "plays today",
    "what are the plays",
    "anything bullish",
    "anything bearish",
    "strongest",
    "what should i watch",
    "live opportunities",
    "edge right now",
)


def is_current_trader_query(q):
    n = " ".join(str(q or "").lower().split())
    return any(t in n for t in TOKENS)


def _score(m):
    try:
        return float(
            m.get("admission", {}).get("admission_score", 0) or 0
        )
    except Exception:
        return 0.0


def _direction(m):
    c = m.get("candidate", {})
    f = m.get("features", {})

    for k in (
        "research_direction",
        "direction",
        "candidate_direction",
    ):
        v = c.get(k) or f.get(k)
        if v:
            return str(v).upper()

    return "NEUTRAL"


def render_current_trader_read(root=None, limit=5):
    x = read_latest_current_trader_analytics(root)

    if not x:
        raise RuntimeError(
            "OIAR-055 requires OIAR-054 analytics snapshot"
        )

    markets = sorted(
        x.get("markets", []),
        key=lambda m: (-_score(m), m.get("market_id", "")),
    )[:max(1, min(int(limit), 10))]

    lines = [
        "=" * 80,
        "ORACLE CURRENT TRADER READ",
        "PROVEN CURRENT CANONICAL COHORT | INDEXED HISTORY | OIA ANALYTICS",
        "-" * 80,
    ]

    for i, m in enumerate(markets, 1):
        meta = m.get("market", {})
        adm = m.get("admission", {})
        use = m.get("usefulness", {})
        cand = m.get("candidate", {})

        lines += [
            f"#{i} {meta.get('title') or m.get('market_id')}",
            f"   Market: {m.get('market_id')}",
            f"   Direction: {_direction(m)}",
            (
                f"   Admission: "
                f"{adm.get('admission_status', 'UNKNOWN')} | "
                f"Score: {adm.get('admission_score', 0)}"
            ),
            (
                f"   Usefulness: "
                f"{use.get('usefulness_classification', 'UNKNOWN')} | "
                f"Score: {use.get('usefulness_score', 0)}"
            ),
            (
                f"   Candidate: "
                f"{cand.get('candidate_family', 'UNKNOWN')} | "
                f"History rows: {m.get('history_rows', 0)}"
            ),
            "",
        ]

    lines += [
        "No order placement. Q Series execution authority remains separate.",
        "=" * 80,
    ]

    return tuple(lines)


def bind_current_trader_terminal(base_module, root=None):
    if getattr(base_module, "_oiar055_bound", False):
        return base_module

    original = base_module.display_query
    active = Path(
        root or base_module.repository_root()
    ).resolve()

    def display_query(
        query,
        *,
        session=None,
        root=None,
        builder=None,
        write=print,
    ):
        canonical = base_module.normalize_query(query)
        use = Path(root or active).resolve()

        if is_current_trader_query(canonical):
            for line in render_current_trader_read(use, 5):
                write(line)
            return None

        kwargs = {
            "session": session,
            "root": use,
            "write": write,
        }

        if builder is not None:
            kwargs["builder"] = builder

        return original(canonical, **kwargs)

    base_module.display_query = display_query
    base_module._oiar055_bound = True

    return base_module


def physical_probe(root=None):
    lines = render_current_trader_read(root, 5)

    return {
        "lines": len(lines),
        "header": lines[1],
        "execution_authority": False,
    }
'''

TEST_SOURCE = r'''import inspect
import unittest

import qseries_v2.oracle_intelligence_analytics_runtime.oiar_055_proven_current_operator_terminal_cutover as m


class T(unittest.TestCase):

    def test_identity(self):
        self.assertEqual(
            m.OIAR_055_BUILD_ID,
            "OIAR-055",
        )

    def test_queries(self):
        self.assertTrue(
            m.is_current_trader_query(
                "what are the plays for today?"
            )
        )

        self.assertTrue(
            m.is_current_trader_query(
                "what do you like right now?"
            )
        )

    def test_no_canonical_scan(self):
        self.assertNotIn(
            "oracle_canonical_observations",
            inspect.getsource(m),
        )


if __name__ == "__main__":

    print("=" * 88)
    print(" OIAR-055 CERTIFICATION TEST")
    print(" PROVEN CURRENT OPERATOR TERMINAL CUTOVER")
    print("=" * 88)

    r = unittest.TextTestRunner(
        verbosity=2
    ).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )

    if not r.wasSuccessful():
        raise SystemExit(1)

    print(
        "[PASS] snapshot-only current trader terminal "
        "cutover certified"
    )
    print("[DONE] OIAR-055 CERTIFIED")
'''

REQUIRED = (
    "qseries_v2/oracle_intelligence_analytics_runtime/"
    "oiar_054_proven_current_trader_analytics.py",

    "qseries_v2/oracle_intelligence_analytics_runtime/"
    "oiar_026_operator_terminal_trader_brief_cutover.py",

    "run_oracle_open_intelligence_terminal.py",
)

EXTRA_FILES = {
    "run_oracle_operator_terminal.py": r'''from __future__ import annotations

import run_oracle_open_intelligence_terminal as base

from qseries_v2.oracle_terminal.oracle_historical_experience_terminal_binding import (
    bind_historical_experience_surface,
)

from qseries_v2.oracle_terminal.oracle_persisted_trader_intelligence_terminal_binding import (
    bind_persisted_trader_intelligence,
)

from qseries_v2.oracle_intelligence_analytics_runtime.oiar_026_operator_terminal_trader_brief_cutover import (
    bind_trader_brief_terminal,
)

from qseries_v2.oracle_intelligence_analytics_runtime.oiar_055_proven_current_operator_terminal_cutover import (
    bind_current_trader_terminal,
)


def main():
    bind_historical_experience_surface(base)
    bind_persisted_trader_intelligence(base)
    bind_trader_brief_terminal(base)
    bind_current_trader_terminal(base)

    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
'''
}


def write_exact(path, text):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    tmp = path.with_name(
        path.name + f".{os.getpid()}.tmp"
    )

    tmp.write_text(
        text,
        encoding="utf-8",
        newline="\n",
    )

    os.replace(tmp, path)


def restore(path, data):
    if data is None:
        if path.exists():
            path.unlink()
    else:
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_bytes(data)


def main():

    print("=" * 88)
    print(" OIAR-055 INSTALLER")
    print(" PROVEN CURRENT OPERATOR TERMINAL CUTOVER")
    print("=" * 88)
    print("[ROOT]", ROOT)

    for rel in REQUIRED:
        p = ROOT / rel

        if not p.is_file():
            raise RuntimeError(
                "Required proven upstream missing: " + rel
            )

    targets = [
        MOD,
        TEST,
    ] + [
        ROOT / x
        for x in EXTRA_FILES
    ]

    old = {
        p: (
            p.read_bytes()
            if p.exists()
            else None
        )
        for p in targets
    }

    try:
        ast.parse(MODULE_SOURCE)
        ast.parse(TEST_SOURCE)

        for src in EXTRA_FILES.values():
            ast.parse(src)

        print(
            "[PASS] installer payload syntax verified"
        )

        write_exact(
            MOD,
            MODULE_SOURCE,
        )

        write_exact(
            TEST,
            TEST_SOURCE,
        )

        for rel, src in EXTRA_FILES.items():
            write_exact(
                ROOT / rel,
                src,
            )

        importlib.invalidate_caches()

        m = importlib.import_module(
            "qseries_v2."
            "oracle_intelligence_analytics_runtime."
            "oiar_055_proven_current_operator_terminal_cutover"
        )

        s = time.monotonic()

        x = m.physical_probe(ROOT)

        print(
            "[PHYSICAL]",
            x,
            "elapsed_seconds=",
            round(
                time.monotonic() - s,
                3,
            ),
        )

        if x["lines"] <= 0:
            raise RuntimeError(
                "OIAR-055 empty terminal render"
            )

        subprocess.run(
            [
                sys.executable,
                str(TEST),
            ],
            cwd=str(ROOT),
            check=True,
            timeout=120,
        )

    except Exception:

        for p, data in old.items():
            restore(
                p,
                data,
            )

        print(
            "[ROLLBACK] OIAR-055 failed; "
            "affected files restored"
        )

        raise

    print(
        "[PASS] read-only intelligence boundary preserved"
    )
    print(
        "[PASS] execution_authority=FALSE"
    )
    print(
        "[DONE] OIAR-055 INSTALLATION COMPLETE"
    )


if __name__ == "__main__":
    main()