from __future__ import annotations
import ast, os, textwrap
from pathlib import Path

EXPECTED_FILENAME = "build_oad_279_gmgn_solana_token_intelligence_adapter_TEST_IMPORT_REBUILD.py"
TEST_NAME = "test_oad_279_gmgn_solana_token_intelligence_adapter.py"

TEST_SOURCE = r"""
import unittest

import qseries_v2.oracle_adapters.independent.oad_279_gmgn_solana_token_intelligence_adapter as oad279


class T(unittest.TestCase):
    def test_direct_resource_shape(self):
        d = {"address": "TEST", "symbol": "T"}
        self.assertIs(oad279._token_resource(d), d)

    def test_envelope_shape(self):
        d = {"code": 0, "message": "success", "data": {"address": "TEST"}}
        self.assertEqual(oad279._token_resource(d)["address"], "TEST")

    def test_physical_current_token_intelligence(self):
        r = oad279.acquire_current_gmgn_solana_token_intelligence(
            timeout_seconds=30.0,
            candidate_limit=5,
        )

        print("[PHYSICAL] token=", r.token_address)
        print("[PHYSICAL] provider=", r.provider)

        for section in ("info", "security", "pool"):
            d = r.payload[section]
            resource = oad279._token_resource(d)
            print(
                "[PHYSICAL]",
                section,
                "raw_type=",
                type(d).__name__,
                "resource_type=",
                type(resource).__name__,
            )
            self.assertIsInstance(d, (dict, list))
            self.assertIsInstance(resource, (dict, list))

        self.assertEqual(r.provider, "gmgn")
        self.assertEqual(r.payload.get("chain"), "sol")
        self.assertTrue(r.token_address)
        self.assertFalse(r.execution_authority)

    def test_safety(self):
        self.assertFalse(oad279.PROBABILITY_ENABLED)
        self.assertFalse(oad279.DIRECTION_ENABLED)
        self.assertFalse(oad279.PUBLICATION_ALLOWED)
        self.assertFalse(oad279.EXECUTION_AUTHORITY)


if __name__ == "__main__":
    print("=" * 120)
    print(" OAD-279 PHYSICAL CERTIFICATION TEST")
    print(" GMGN SOLANA TOKEN INTELLIGENCE — EXPLICIT MODULE IMPORT")
    print("=" * 120)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] direct-resource raw JSON contract certified")
    print("[PASS] envelope raw JSON contract certified")
    print("[PASS] live GMGN token info/security/pool intelligence certified")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-279 PHYSICALLY CERTIFIED")
"""


def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for p in (base, *base.parents):
            if (p / "qseries_v2").is_dir():
                return p
    raise RuntimeError("Q Series repository root not found")


def write_checked(path, source):
    source = textwrap.dedent(source).lstrip()
    ast.parse(source, filename=str(path))
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(source, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def main():
    if Path(__file__).name != EXPECTED_FILENAME:
        raise RuntimeError("installer identity mismatch")

    root = locate_root()
    module = (
        root / "qseries_v2" / "oracle_adapters" / "independent"
        / "oad_279_gmgn_solana_token_intelligence_adapter.py"
    )
    test = root / TEST_NAME

    print("=" * 120)
    print(" OAD-279 TEST IMPORT REBUILD INSTALLER")
    print("=" * 120)
    print("[ROOT]", root)

    if not module.is_file():
        raise RuntimeError("OAD-279 production module missing")

    src = module.read_text(encoding="utf-8")
    required = (
        "_token_resource",
        "acquire_current_gmgn_solana_token_intelligence",
    )
    for symbol in required:
        if ("def " + symbol + "(") not in src:
            raise RuntimeError("OAD-279 production symbol missing: " + symbol)
        print("[PASS] exact production symbol verified:", symbol)

    # Compile both the installed production module source and replacement test
    # before touching the repository.
    ast.parse(src, filename=str(module))
    ast.parse(textwrap.dedent(TEST_SOURCE).lstrip(), filename=str(test))
    print("[PASS] production module syntax verified")
    print("[PASS] replacement physical test syntax verified")

    previous = test.read_bytes() if test.exists() else None
    try:
        write_checked(test, TEST_SOURCE)
        installed = test.read_text(encoding="utf-8")
        if "import qseries_v2.oracle_adapters.independent.oad_279_gmgn_solana_token_intelligence_adapter as oad279" not in installed:
            raise RuntimeError("explicit module import not installed")
        if "oad279._token_resource" not in installed:
            raise RuntimeError("private helper not referenced through module namespace")

        print("[PASS] defective wildcard/private-helper test import retired")
        print("[PASS] explicit OAD-279 module import installed")
        print("[PASS] _token_resource resolved through oad279 module namespace")
        print("[PASS] OAD-279 production module left unchanged")
        print("[PASS] ready for physical rerun")
        print("[DONE] OAD-279 TEST IMPORT REBUILD INSTALLATION COMPLETE")
    except Exception:
        if previous is None:
            if test.exists():
                test.unlink()
        else:
            test.write_bytes(previous)
        print("[ROLLBACK] prior OAD-279 test restored")
        raise


if __name__ == "__main__":
    main()
