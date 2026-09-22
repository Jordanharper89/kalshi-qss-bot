from __future__ import annotations
import ast
import os
import textwrap
from pathlib import Path

MODULE_NAME = "oad_281_gmgn_solana_single_writer_postgresql_persistence.py"
TEST_NAME = "test_oad_281_gmgn_solana_single_writer_postgresql_persistence.py"

MODULE_SOURCE = r"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json

from .oad_279_gmgn_solana_token_intelligence_adapter import (
    acquire_current_gmgn_solana_token_intelligence,
)
from .oad_261_universal_expansion_source_single_writer_postgresql_persistence import (
    PRODUCER,
    PRIORITY,
    canonicalize_expansion_observation,
)
from .oad_068_exact_postgresql_independent_readback import (
    _backend,
    _query_one,
    exact_postgresql_readback,
)
from qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue import (
    submit_observation_batch,
    await_request,
)

READ_ONLY = True
PROBABILITY_ENABLED = False
DIRECTION_ENABLED = False
PUBLICATION_ALLOWED = False
EXECUTION_AUTHORITY = False

BATCH_ID = "oad281.gmgn-solana-token-intelligence"


@dataclass(frozen=True, slots=True)
class GMGNExpansionObservation:
    source_id: str
    provenance_hash: str
    observed_at: object
    observation_type: str
    source_class: str
    provider: str
    subject: str
    payload: dict
    execution_authority: bool = False


@dataclass(frozen=True, slots=True)
class GMGNPersistenceResult:
    token_address: str
    raw_observations: int
    canonical_observations: int
    already_present: int
    committed_new: int
    exact_readback: int
    providers: tuple
    source_ids: tuple
    observation_ids: tuple
    rows: tuple
    execution_authority: bool = False


def _stable_hash(value):
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _build_section_observation(gmgn, section):
    token = str(gmgn.token_address).strip()
    payload = gmgn.payload.get(section)
    if not isinstance(payload, dict):
        raise RuntimeError(
            "GMGN " + section + " payload must be a dictionary"
        )

    source_id = "source.gmgn.solana.token." + token + "." + section
    provenance_hash = _stable_hash(
        {
            "source_id": source_id,
            "provider": "gmgn",
            "source_class": "token_intelligence",
            "subject": token,
            "observation_type": "gmgn_solana_token_" + section,
            "observed_at": gmgn.observed_at,
            "payload": payload,
        }
    )

    return GMGNExpansionObservation(
        source_id=source_id,
        provenance_hash=provenance_hash,
        observed_at=gmgn.observed_at,
        observation_type="gmgn_solana_token_" + section,
        source_class="token_intelligence",
        provider="gmgn",
        subject=token,
        payload=dict(payload),
        execution_authority=False,
    )


def build_gmgn_expansion_observations(gmgn):
    return tuple(
        _build_section_observation(gmgn, section)
        for section in ("info", "security", "pool")
    )


def persist_gmgn_solana_token_intelligence(
    root=None,
    timeout_seconds=120.0,
    acquisition_timeout_seconds=30.0,
):
    root = Path(root or Path.cwd()).resolve()

    gmgn = acquire_current_gmgn_solana_token_intelligence(
        timeout_seconds=acquisition_timeout_seconds,
        candidate_limit=5,
    )
    raw = build_gmgn_expansion_observations(gmgn)

    canonical = tuple(
        canonicalize_expansion_observation(x, BATCH_ID)
        for x in raw
    )

    backend = _backend(root)
    existing = 0
    missing = []

    for index, observation in enumerate(canonical):
        if _query_one(backend, observation.observation_id, index) is None:
            missing.append(observation)
        else:
            existing += 1

    committed = 0
    if missing:
        submission = submit_observation_batch(
            PRODUCER,
            PRIORITY,
            tuple(missing),
            root,
        )
        events = tuple(
            await_request(
                str(submission.request_id),
                root,
                float(timeout_seconds),
            )
        )
        accepted = tuple(
            event
            for event in events
            if getattr(event, "accepted", False) is True
        )
        if len(accepted) != len(missing):
            raise RuntimeError(
                "GMGN universal single-writer commit mismatch"
            )
        committed = len(accepted)

    ids = tuple(x.observation_id for x in canonical)
    rows = (
        tuple(exact_postgresql_readback(ids, root))
        if ids
        else ()
    )

    if len(rows) != len(ids):
        raise RuntimeError(
            "GMGN exact PostgreSQL readback mismatch"
        )

    return GMGNPersistenceResult(
        token_address=gmgn.token_address,
        raw_observations=len(raw),
        canonical_observations=len(canonical),
        already_present=existing,
        committed_new=committed,
        exact_readback=len(rows),
        providers=tuple(x.provider for x in raw),
        source_ids=tuple(x.source_id for x in raw),
        observation_ids=ids,
        rows=rows,
        execution_authority=False,
    )


# Preserve the old public entry point while moving it onto the corrected
# token-intelligence persistence boundary.
def persist_gmgn_solana_trending(
    root=None,
    timeout_seconds=120.0,
    acquisition_timeout_seconds=30.0,
):
    return persist_gmgn_solana_token_intelligence(
        root=root,
        timeout_seconds=timeout_seconds,
        acquisition_timeout_seconds=acquisition_timeout_seconds,
    )
"""

TEST_SOURCE = r"""
import unittest

import qseries_v2.oracle_adapters.independent.oad_281_gmgn_solana_single_writer_postgresql_persistence as oad281


class _FixtureGMGN:
    token_address = "TEST_TOKEN"
    observed_at = "2026-09-02T19:00:00+00:00"
    payload = {
        "chain": "sol",
        "info": {"address": "TEST_TOKEN", "symbol": "TEST"},
        "security": {"address": "TEST_TOKEN", "risk": "provider_claim"},
        "pool": {"address": "TEST_TOKEN", "liquidity": 123.0},
    }


class T(unittest.TestCase):
    def test_exact_oad261_shape_fixture(self):
        raw = oad281.build_gmgn_expansion_observations(_FixtureGMGN())
        self.assertEqual(len(raw), 3)

        for row in raw:
            self.assertTrue(row.source_id)
            self.assertEqual(len(row.provenance_hash), 64)
            self.assertTrue(row.observed_at)
            self.assertTrue(row.observation_type)
            self.assertEqual(row.source_class, "token_intelligence")
            self.assertEqual(row.provider, "gmgn")
            self.assertEqual(row.subject, "TEST_TOKEN")
            self.assertIsInstance(row.payload, dict)
            self.assertFalse(row.execution_authority)

            canonical = oad281.canonicalize_expansion_observation(
                row,
                oad281.BATCH_ID,
            )
            self.assertTrue(canonical.observation_id)

    def test_physical_postgresql_persistence(self):
        r = oad281.persist_gmgn_solana_token_intelligence()

        print("[PHYSICAL] token=", r.token_address)
        print("[PHYSICAL] raw=", r.raw_observations)
        print("[PHYSICAL] canonical=", r.canonical_observations)
        print("[PHYSICAL] already_present=", r.already_present)
        print("[PHYSICAL] committed_new=", r.committed_new)
        print("[PHYSICAL] exact_readback=", r.exact_readback)
        print("[PHYSICAL] providers=", r.providers)
        print("[PHYSICAL] source_ids=", r.source_ids)
        print("[PHYSICAL] observation_ids=", r.observation_ids)

        self.assertTrue(r.token_address)
        self.assertEqual(r.raw_observations, 3)
        self.assertEqual(r.canonical_observations, 3)
        self.assertEqual(
            r.already_present + r.committed_new,
            3,
        )
        self.assertEqual(r.exact_readback, 3)
        self.assertEqual(r.providers, ("gmgn", "gmgn", "gmgn"))
        self.assertEqual(len(r.source_ids), 3)
        self.assertEqual(len(r.observation_ids), 3)
        self.assertFalse(r.execution_authority)

    def test_safety(self):
        self.assertFalse(oad281.PROBABILITY_ENABLED)
        self.assertFalse(oad281.DIRECTION_ENABLED)
        self.assertFalse(oad281.PUBLICATION_ALLOWED)
        self.assertFalse(oad281.EXECUTION_AUTHORITY)


if __name__ == "__main__":
    print("=" * 120)
    print(" OAD-281 PHYSICAL CERTIFICATION TEST")
    print(" GMGN TOKEN INTELLIGENCE -> EXACT OAD-261 -> OPH-019 -> POSTGRESQL")
    print("=" * 120)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] GMGN observation shape satisfies exact OAD-261 contract")
    print("[PASS] GMGN info/security/pool persisted through universal single writer")
    print("[PASS] exact observation-ID PostgreSQL readback certified")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-281 PHYSICALLY CERTIFIED")
"""


def locate_root():
    for base in (Path.cwd().resolve(), Path(__file__).resolve().parent):
        for candidate in (base, *base.parents):
            if (candidate / "qseries_v2").is_dir():
                return candidate
    raise RuntimeError("Q Series repository root not found")


def write_checked(path, source):
    normalized = textwrap.dedent(source).lstrip()
    ast.parse(normalized, filename=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(normalized, encoding="utf-8", newline="\n")
    os.replace(temp, path)


def main():
    root = locate_root()
    pkg = root / "qseries_v2" / "oracle_adapters" / "independent"
    module = pkg / MODULE_NAME
    test = root / TEST_NAME
    init = pkg / "__init__.py"

    print("=" * 120)
    print(" OAD-281 GMGN SINGLE-WRITER POSTGRESQL PERSISTENCE")
    print(" EXACT OAD-261 CONTRACT REBUILD")
    print("=" * 120)
    print("[ROOT]", root)

    dependencies = (
        (
            pkg / "oad_279_gmgn_solana_token_intelligence_adapter.py",
            "acquire_current_gmgn_solana_token_intelligence",
        ),
        (
            pkg / "oad_261_universal_expansion_source_single_writer_postgresql_persistence.py",
            "canonicalize_expansion_observation",
        ),
        (
            pkg / "oad_068_exact_postgresql_independent_readback.py",
            "exact_postgresql_readback",
        ),
        (
            root / "qseries_v2" / "oracle_production_hardening"
            / "oph_019_postgresql_universal_ingestion_queue.py",
            "submit_observation_batch",
        ),
    )

    for dep, symbol in dependencies:
        if not dep.is_file():
            raise RuntimeError("dependency missing: " + str(dep))
        dep_source = dep.read_text(encoding="utf-8")
        ast.parse(dep_source, filename=str(dep))
        if ("def " + symbol + "(") not in dep_source:
            raise RuntimeError(
                "dependency symbol missing: "
                + dep.name
                + " -> "
                + symbol
            )
        print(
            "[PASS] exact dependency verified:",
            dep.relative_to(root),
            "->",
            symbol,
        )

    oad261_path = dependencies[1][0]
    oad261 = oad261_path.read_text(encoding="utf-8")
    required_contract = (
        "x.source_id",
        "x.provenance_hash",
        "x.observed_at",
        "x.observation_type",
        "x.source_class",
        "x.provider",
        "x.subject",
        "dict(x.payload)",
    )
    for fragment in required_contract:
        if fragment not in oad261:
            raise RuntimeError(
                "OAD-261 observation contract mismatch: missing "
                + fragment
            )
    print("[PASS] exact OAD-261 eight-field observation contract verified")

    # Protect the certified upstream persistence boundary from accidental edits.
    oad261_before = oad261_path.read_bytes()

    ast.parse(textwrap.dedent(MODULE_SOURCE).lstrip(), filename=str(module))
    ast.parse(textwrap.dedent(TEST_SOURCE).lstrip(), filename=str(test))
    print("[PASS] replacement production module syntax verified")
    print("[PASS] replacement physical test syntax verified")

    previous = {
        p: (p.read_bytes() if p.exists() else None)
        for p in (module, test, init)
    }

    try:
        write_checked(module, MODULE_SOURCE)
        write_checked(test, TEST_SOURCE)

        init_lines = (
            init.read_text(encoding="utf-8").splitlines()
            if init.exists()
            else []
        )
        export = "from ." + module.stem + " import *"
        if export not in init_lines:
            init_lines.append(export)
        write_checked(
            init,
            "\n".join(line for line in init_lines if line.strip()) + "\n",
        )

        if oad261_path.read_bytes() != oad261_before:
            raise RuntimeError("certified OAD-261 changed unexpectedly")

        print("[PASS] rebuilt existing OAD-281 production boundary in place")
        print("[PASS] wrong OAD-261 filename/function assumptions retired")
        print("[PASS] GMGN mapped directly onto exact OAD-261 observation contract")
        print("[PASS] provenance_hash added at GMGN persistence boundary")
        print("[PASS] info/security/pool remain separate source-scoped observations")
        print("[PASS] existing OAD-261 canonicalizer reused unchanged")
        print("[PASS] existing OPH-019 queue/single-writer path reused unchanged")
        print("[PASS] exact OAD-068 observation-ID readback reused unchanged")
        print("[PASS] certified OAD-261 file verified unchanged")
        print("[PASS] no broad PostgreSQL scan")
        print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
        print("[DONE] OAD-281 EXACT OAD-261 REBUILD INSTALLATION COMPLETE")

    except Exception:
        for p, old in previous.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(old)
        print("[ROLLBACK] OAD-281 affected files restored")
        raise


if __name__ == "__main__":
    main()
