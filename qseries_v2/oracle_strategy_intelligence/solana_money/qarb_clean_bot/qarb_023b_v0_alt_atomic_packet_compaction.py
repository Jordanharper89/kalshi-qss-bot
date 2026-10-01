from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Iterable, Sequence

PACKET_LIMIT = 1232
execution_authority = False


@dataclass(frozen=True)
class Candidate:
    label: str
    size_bytes: int
    tx: Any
    lookup_table_count: int


@dataclass(frozen=True)
class CompactionResult:
    ok: bool
    status: str
    best: Candidate | None
    attempted: tuple[tuple[str, int], ...]
    over_by: int
    execution_authority: bool = False


def packet_size(tx: Any) -> int:
    return len(bytes(tx))


def choose_smallest(candidates: Iterable[Candidate]) -> CompactionResult:
    rows = tuple(candidates)
    if not rows:
        return CompactionResult(False, "NO_CANDIDATE", None, (), 0)
    best = min(rows, key=lambda x: x.size_bytes)
    attempted = tuple((x.label, x.size_bytes) for x in rows)
    if best.size_bytes <= PACKET_LIMIT:
        return CompactionResult(True, "PACKET_FITS", best, attempted, 0)
    return CompactionResult(
        False,
        "ATOMIC_TX_TOO_LARGE",
        best,
        attempted,
        best.size_bytes - PACKET_LIMIT,
    )


def _compile_v0(payer: Any, recent_blockhash: Any, instructions: Sequence[Any],
                lookup_tables: Sequence[Any]) -> Any:
    try:
        from solders.message import MessageV0
        from solders.signature import Signature
        from solders.transaction import VersionedTransaction
    except Exception as exc:
        raise RuntimeError("SOLDERS_REQUIRED_FOR_V0_COMPILE") from exc

    msg = MessageV0.try_compile(
        payer,
        list(instructions),
        list(lookup_tables),
        recent_blockhash,
    )
    sigs = [Signature.default() for _ in range(msg.header.num_required_signatures)]
    return VersionedTransaction.populate(msg, sigs)


def compile_best_v0(
    payer: Any,
    recent_blockhash: Any,
    instructions: Sequence[Any],
    lookup_tables: Sequence[Any],
    max_lookup_tables: int = 3,
) -> CompactionResult:
    candidates: list[Candidate] = []
    errors: list[tuple[str, int]] = []

    table_sets: list[tuple[Any, ...]] = [()]
    limit = min(max(0, int(max_lookup_tables)), len(lookup_tables))
    for n in range(1, limit + 1):
        table_sets.extend(combinations(lookup_tables, n))

    for tables in table_sets:
        label = "V0_NO_ALT" if not tables else f"V0_ALT_{len(tables)}"
        try:
            tx = _compile_v0(payer, recent_blockhash, instructions, tables)
            candidates.append(Candidate(label, packet_size(tx), tx, len(tables)))
        except Exception:
            errors.append((label, 10**9))

    result = choose_smallest(candidates)
    if result.ok or candidates:
        return result
    return CompactionResult(
        False,
        "V0_COMPILE_FAILED",
        None,
        tuple(errors),
        0,
    )


def format_result(result: CompactionResult) -> str:
    if result.best is None:
        return (
            f"[ATOMIC_PACKET] status={result.status} "
            f"limit={PACKET_LIMIT} execution_authority=FALSE"
        )
    return (
        f"[ATOMIC_PACKET] status={result.status} "
        f"candidate={result.best.label} bytes={result.best.size_bytes} "
        f"limit={PACKET_LIMIT} over_by={result.over_by} "
        f"alts={result.best.lookup_table_count} execution_authority=FALSE"
    )
