from __future__ import annotations
import ast, hashlib, os, textwrap
from pathlib import Path

BUILD_ID='OAD-278'
REVISION='OAD_278_GMGN_SOLANA_TRENDING_LIVE_ADAPTER_WINDOWS_UTF8_REBUILD_V1'
TITLE='GMGN SOLANA TRENDING LIVE ADAPTER — WINDOWS UTF-8 REBUILD'
EXPECTED_FILENAME='build_oad_278_gmgn_solana_trending_live_adapter_WINDOWS_UTF8_REBUILD.py'
MODULE_NAME='oad_278_gmgn_solana_trending_live_adapter.py'
TEST_NAME='test_oad_278_gmgn_solana_trending_live_adapter.py'

DEPENDENCIES={
    'qseries_v2/oracle_adapters/independent/oad_277_gmgn_production_admission_boundary.py': (
        'require_gmgn_admission',
    ),
}

MODULE_SOURCE=r'''
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import subprocess

from .oad_277_gmgn_production_admission_boundary import require_gmgn_admission

READ_ONLY = True
PROBABILITY_ENABLED = False
DIRECTION_ENABLED = False
PUBLICATION_ALLOWED = False
EXECUTION_AUTHORITY = False


@dataclass(frozen=True, slots=True)
class GMGNObservation:
    source_id: str
    provider: str
    source_class: str
    observation_type: str
    observed_at: datetime
    payload: dict
    execution_authority: bool = False


def _decode_gmgn_bytes(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if not isinstance(value, (bytes, bytearray)):
        return str(value)
    try:
        return bytes(value).decode("utf-8")
    except UnicodeDecodeError:
        return bytes(value).decode("utf-8", errors="replace")


def _json_from_stdout(value):
    text = _decode_gmgn_bytes(value).strip()
    if not text:
        raise RuntimeError("GMGN returned empty stdout")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        candidate = text[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "GMGN output contained text but no valid JSON object"
            ) from exc
    raise RuntimeError("GMGN output was not valid JSON")


def acquire_gmgn_solana_trending(interval="5m", limit=20, timeout_seconds=30.0):
    a = require_gmgn_admission()

    cmd = [
        a.cli_path,
        "market",
        "trending",
        "--chain",
        "sol",
        "--interval",
        str(interval),
        "--order-by",
        "volume",
        "--limit",
        str(int(limit)),
        "--raw",
    ]

    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=float(timeout_seconds),
        check=False,
    )

    stdout_text = _decode_gmgn_bytes(p.stdout)
    stderr_text = _decode_gmgn_bytes(p.stderr)

    if p.returncode != 0:
        detail = (stderr_text or stdout_text).strip()
        raise RuntimeError("GMGN trending failed: " + detail[:500])

    data = _json_from_stdout(p.stdout)

    if not isinstance(data, dict):
        raise RuntimeError("GMGN trending response root must be a JSON object")
    if data.get("code") != 0:
        raise RuntimeError(
            "GMGN trending returned non-success code: " + repr(data.get("code"))
        )

    return GMGNObservation(
        source_id="source.gmgn.solana.market.trending." + str(interval),
        provider="gmgn",
        source_class="market_intelligence",
        observation_type="gmgn_solana_trending",
        observed_at=datetime.now(timezone.utc),
        payload={
            "chain": "sol",
            "interval": str(interval),
            "limit": int(limit),
            "raw": data,
        },
        execution_authority=False,
    )
'''

TEST_SOURCE=r'''
import json
import unittest

from qseries_v2.oracle_adapters.independent.oad_277_gmgn_production_admission_boundary import (
    evaluate_gmgn_admission,
)
from qseries_v2.oracle_adapters.independent.oad_278_gmgn_solana_trending_live_adapter import (
    EXECUTION_AUTHORITY,
    PUBLICATION_ALLOWED,
    PROBABILITY_ENABLED,
    DIRECTION_ENABLED,
    _json_from_stdout,
    acquire_gmgn_solana_trending,
)


class T(unittest.TestCase):
    def test_utf8_parser_boundary(self):
        fixture = {
            "code": 0,
            "data": {
                "rank": [
                    {
                        "chain": "sol",
                        "address": "TEST_SOLANA_ADDRESS",
                        "symbol": "MIM",
                        "trans_name_zhcn": "神奇互联网货币",
                    }
                ]
            },
            "message": "success",
            "reason": "",
        }
        raw = json.dumps(fixture, ensure_ascii=False).encode("utf-8")
        parsed = _json_from_stdout(raw)
        self.assertEqual(parsed["code"], 0)
        self.assertEqual(
            parsed["data"]["rank"][0]["trans_name_zhcn"],
            "神奇互联网货币",
        )

    def test_physical_gmgn_solana_trending(self):
        a = evaluate_gmgn_admission()
        self.assertTrue(
            a.admitted,
            "OAD-277 GMGN production admission must be open",
        )

        r = acquire_gmgn_solana_trending(interval="1h", limit=5)
        raw = r.payload.get("raw")

        print("[PHYSICAL] source_id=", r.source_id)
        print("[PHYSICAL] provider=", r.provider)
        print("[PHYSICAL] payload_type=", type(raw).__name__)

        self.assertEqual(r.provider, "gmgn")
        self.assertEqual(r.payload["chain"], "sol")
        self.assertFalse(r.execution_authority)

        self.assertIsInstance(raw, dict)
        self.assertEqual(raw.get("code"), 0)
        self.assertEqual(raw.get("message"), "success")

        rank = ((raw.get("data") or {}).get("rank") or [])
        print("[PHYSICAL] rank_count=", len(rank))

        if rank:
            print("[PHYSICAL] first_address=", rank[0].get("address"))
            print("[PHYSICAL] first_symbol=", rank[0].get("symbol"))

        self.assertGreater(len(rank), 0)
        for row in rank:
            self.assertEqual(row.get("chain"), "sol")
            self.assertTrue(str(row.get("address") or "").strip())

    def test_read_only_safety_boundary(self):
        self.assertFalse(PROBABILITY_ENABLED)
        self.assertFalse(DIRECTION_ENABLED)
        self.assertFalse(PUBLICATION_ALLOWED)
        self.assertFalse(EXECUTION_AUTHORITY)


if __name__ == "__main__":
    print("=" * 120)
    print(" OAD-278 PHYSICAL CERTIFICATION TEST")
    print(" GMGN SOLANA TRENDING — WINDOWS UTF-8 SAFE")
    print("=" * 120)

    r = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] UTF-8 GMGN JSON decode boundary certified")
    print("[PASS] live GMGN Solana trending acquisition certified")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-278 PHYSICALLY CERTIFIED")
'''


def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")


def write_checked(path, source):
    normalized = textwrap.dedent(source).lstrip()
    ast.parse(normalized, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(normalized, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def main():
    if Path(__file__).name != EXPECTED_FILENAME:
        raise RuntimeError(
            "installer identity mismatch: expected " + EXPECTED_FILENAME
        )

    root = locate_root()
    pkg = root / "qseries_v2" / "oracle_adapters" / "independent"
    module = pkg / MODULE_NAME
    test = root / TEST_NAME
    init = pkg / "__init__.py"

    print("=" * 120)
    print(" " + BUILD_ID + " " + TITLE + " INSTALLER")
    print("=" * 120)
    print("[BOOT] Revision:", REVISION)
    print("[ROOT]", root)

    for rel, symbols in DEPENDENCIES.items():
        p = root / rel
        if not p.is_file():
            raise RuntimeError("Required dependency missing: " + rel)
        src = p.read_text(encoding="utf-8")
        for symbol in symbols:
            if ("def " + symbol + "(") not in src and ("class " + symbol) not in src:
                raise RuntimeError(
                    "Exact dependency symbol missing: " + rel + " -> " + symbol
                )
        print("[PASS] exact dependency verified:", rel)

    protected = []
    for p, label in (
        (
            root / "qseries_v2" / "oracle_production_hardening"
            / "oph_023_postgresql_single_writer_production_freeze.py",
            "Frozen OPH-023",
        ),
        (
            root / "qseries_v2" / "oracle_adapters" / "kalshi"
            / "oad_055_kalshi_production_freeze.py",
            "Frozen Kalshi OAD-055",
        ),
    ):
        if not p.is_file():
            raise RuntimeError(label + " missing: " + str(p))
        protected.append((p, hashlib.sha256(p.read_bytes()).hexdigest()))
        print("[PASS]", label, "verified")

    old = {
        p: (p.read_bytes() if p.exists() else None)
        for p in (module, test, init)
    }

    try:
        write_checked(module, MODULE_SOURCE)
        write_checked(test, TEST_SOURCE)

        lines = init.read_text(encoding="utf-8").splitlines() if init.exists() else []
        export = "from ." + module.stem + " import *"
        if export not in lines:
            lines.append(export)
        write_checked(init, "\n".join(x for x in lines if x.strip()) + "\n")

        for p, expected_hash in protected:
            if hashlib.sha256(p.read_bytes()).hexdigest() != expected_hash:
                raise RuntimeError("Frozen boundary changed: " + p.name)

        print("[PASS] rebuilt existing OAD-278 production boundary in place")
        print("[PASS] Windows cp1252 subprocess decoding removed")
        print("[PASS] GMGN stdout/stderr captured as bytes and decoded explicitly as UTF-8")
        print("[PASS] exact GMGN JSON success code enforced")
        print("[PASS] OAD-277 admission dependency preserved")
        print("[PASS] downstream GMGNObservation/acquire_gmgn_solana_trending contract preserved")
        print("[PASS] frozen production boundaries unchanged")
        print("[PASS] GMGN remains observation-only")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-278 WINDOWS UTF-8 REBUILD INSTALLATION COMPLETE")

    except Exception:
        for p, previous in old.items():
            if previous is None:
                if p.exists():
                    p.unlink()
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(previous)
        print("[ROLLBACK] OAD-278 affected files restored")
        raise


if __name__ == "__main__":
    main()
