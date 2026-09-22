from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import ast
import json
import os
import re
from typing import Any

EXECUTION_AUTHORITY = False

KNOWN_TIMEOUT_REQUEST_IDS = (
    "221e743213c445b4b486cab2d923d0c6",
    "26b4b0ffed254ad397d537be9b4a42d0",
)

@dataclass(frozen=True, slots=True)
class QueueRequestEvidence:
    request_id: str
    paths: tuple[str, ...]
    statuses: tuple[str, ...]
    producers: tuple[str, ...]
    raw_hits: int

@dataclass(frozen=True, slots=True)
class IngestionCompletionAudit:
    oph019_functions: tuple[str, ...]
    oph021_functions: tuple[str, ...]
    oph021_classes: tuple[str, ...]
    queue_state_candidates: tuple[str, ...]
    writer_runtime_candidates: tuple[str, ...]
    request_evidence: tuple[QueueRequestEvidence, ...]
    conclusion: str
    execution_authority: bool = False

def _repo_root(root=None) -> Path:
    if root is not None:
        return Path(root).resolve()
    here = Path.cwd().resolve()
    for p in (here, *here.parents):
        if (p / "qseries_v2").is_dir():
            return p
    raise RuntimeError("repository root not found")

def _defs(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    funcs = sorted({
        n.name for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
    })
    classes = sorted({
        n.name for n in ast.walk(tree)
        if isinstance(n, ast.ClassDef)
    })
    return tuple(funcs), tuple(classes)

def _interesting_runtime_paths(root: Path):
    candidates = []
    for base in (
        root / "runtime_state",
        root / "runtime",
        root / "qseries_v2" / "oracle_production_hardening",
    ):
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            low = str(p).lower()
            if any(k in low for k in ("oph_019", "oph019", "ingestion", "queue", "postgres", "oph_021", "oph021", "writer", "lease")):
                candidates.append(p)
    return tuple(dict.fromkeys(candidates))

def _extract_statuses_and_producers(obj: Any):
    statuses=[]
    producers=[]
    def walk(x):
        if isinstance(x, dict):
            for k,v in x.items():
                lk=str(k).lower()
                if lk in {"status","state","request_status","queue_state"} and isinstance(v,(str,int,float,bool)):
                    statuses.append(str(v))
                if lk in {"producer","producer_name","source","source_kind"} and isinstance(v,(str,int,float,bool)):
                    producers.append(str(v))
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(obj)
    return tuple(dict.fromkeys(statuses)), tuple(dict.fromkeys(producers))

def _search_request(root: Path, request_id: str) -> QueueRequestEvidence:
    paths=[]
    statuses=[]
    producers=[]
    raw_hits=0

    for p in _interesting_runtime_paths(root):
        try:
            if p.stat().st_size > 64 * 1024 * 1024:
                continue
            text=p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if request_id not in text:
            continue

        raw_hits += text.count(request_id)
        paths.append(str(p.relative_to(root)))

        # Try JSON as a whole file.
        try:
            obj=json.loads(text)
            s,pr=_extract_statuses_and_producers(obj)
            statuses.extend(s)
            producers.extend(pr)
        except Exception:
            pass

        # Also inspect JSONL lines containing the request id.
        for line in text.splitlines():
            if request_id not in line:
                continue
            try:
                obj=json.loads(line)
                s,pr=_extract_statuses_and_producers(obj)
                statuses.extend(s)
                producers.extend(pr)
            except Exception:
                # Last-resort local status keywords from the exact matching line.
                up=line.upper()
                for token in ("PENDING","DONE","COMMITTED","FAILED","ERROR","PROCESSING","IN_PROGRESS"):
                    if token in up:
                        statuses.append(token)
                m=re.search(r'producer["\']?\s*[:=]\s*["\']([^"\']+)', line, re.I)
                if m:
                    producers.append(m.group(1))

    return QueueRequestEvidence(
        request_id=request_id,
        paths=tuple(dict.fromkeys(paths)),
        statuses=tuple(dict.fromkeys(statuses)),
        producers=tuple(dict.fromkeys(producers)),
        raw_hits=int(raw_hits),
    )

def audit_ingestion_completion(root=None, request_ids=KNOWN_TIMEOUT_REQUEST_IDS):
    r=_repo_root(root)

    oph019=r/"qseries_v2/oracle_production_hardening/oph_019_postgresql_universal_ingestion_queue.py"
    oph021=r/"qseries_v2/oracle_production_hardening/oph_021_exclusive_postgresql_canonical_writer.py"

    f19,c19=_defs(oph019)
    f21,c21=_defs(oph021)

    queue_candidates=[]
    writer_candidates=[]
    for p in _interesting_runtime_paths(r):
        rel=str(p.relative_to(r))
        low=rel.lower()
        if any(k in low for k in ("oph_019","oph019","ingestion","queue")):
            queue_candidates.append(rel)
        if any(k in low for k in ("oph_021","oph021","writer","lease")):
            writer_candidates.append(rel)

    evidence=tuple(_search_request(r, rid) for rid in request_ids)

    all_statuses={s.upper() for e in evidence for s in e.statuses}
    any_hits=any(e.raw_hits for e in evidence)

    if any(s in all_statuses for s in ("DONE","COMMITTED")):
        conclusion="TIMED_OUT_REQUEST_LATER_COMPLETED"
    elif "FAILED" in all_statuses or "ERROR" in all_statuses:
        conclusion="TIMED_OUT_REQUEST_FAILED"
    elif "PENDING" in all_statuses or "PROCESSING" in all_statuses or "IN_PROGRESS" in all_statuses:
        conclusion="TIMED_OUT_REQUEST_STILL_PENDING_OR_PROCESSING"
    elif any_hits:
        conclusion="REQUEST_FOUND_STATUS_UNRESOLVED"
    else:
        conclusion="REQUEST_NOT_FOUND_IN_DURABLE_RUNTIME_STATE"

    return IngestionCompletionAudit(
        oph019_functions=f19,
        oph021_functions=f21,
        oph021_classes=c21,
        queue_state_candidates=tuple(queue_candidates),
        writer_runtime_candidates=tuple(writer_candidates),
        request_evidence=evidence,
        conclusion=conclusion,
        execution_authority=False,
    )

def print_audit(audit: IngestionCompletionAudit):
    print("[OPH-019 FUNCTIONS]", audit.oph019_functions)
    print("[OPH-021 FUNCTIONS]", audit.oph021_functions)
    print("[OPH-021 CLASSES]", audit.oph021_classes)
    print("[QUEUE CANDIDATES]", audit.queue_state_candidates)
    print("[WRITER CANDIDATES]", audit.writer_runtime_candidates)
    for e in audit.request_evidence:
        print(
            "[REQUEST]",
            "id=", e.request_id,
            "hits=", e.raw_hits,
            "statuses=", e.statuses,
            "producers=", e.producers,
            "paths=", e.paths,
        )
    print("[CONCLUSION]", audit.conclusion)
    print("[BOUNDARY] execution_authority=FALSE")
