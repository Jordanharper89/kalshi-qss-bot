from __future__ import annotations

from pathlib import Path
import ast
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT=Path.cwd().resolve()
Q=ROOT/"qseries_v2"
OCR=Q/"oracle_continuous_reasoning"
OLF=Q/"oracle_learning_feedback"
LAUNCHER=ROOT/"run_oracle_LIVE.py"

BACKUP_ROOT=ROOT/"cleanup_backups"
STAMP=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
BACKUP=BACKUP_ROOT/f"oracle_production_baseline_{STAMP}"
MANIFEST=BACKUP/"cleanup_manifest.json"

PACKAGE_DELETE=[
    OCR/"ocr_016_intelligence_state_materializer.py",
    OCR/"ocr_017_continuous_intelligence_state_loop.py",
    OCR/"ocr_018_oracle_live_intelligence_state_binding.py",
    OCR/"ocr_019_intelligence_state_query.py",
    OCR/"ocr_020_intelligence_state_production_gate.py",
    OCR/"OCR_020_FREEZE_MANIFEST.json",
    OLF/"olf_031_exact_ticker_settlement_results.py",
    OLF/"olf_032_presettlement_price_recovery.py",
    OLF/"olf_034_physical_learning_consumption_attestation.py",
    OLF/"olf_035_learner_reasoning_lineage.py",
    OLF/"olf_036_live_learning_advancement_audit.py",
    OLF/"olf_037_learning_utilization_telemetry.py",
    OLF/"olf_038_meaningful_learning_production_gate.py",
]

ROOT_DELETE_EXACT=[
    ROOT/"run_ocr_017_continuous_intelligence_state_runtime.py",
    ROOT/"run_ocr_019_intelligence_query.py",
    ROOT/"test_ocr_016_intelligence_state_materializer.py",
    ROOT/"test_ocr_017_continuous_intelligence_state_loop.py",
    ROOT/"test_ocr_017_history_parent_recreation.py",
    ROOT/"test_ocr_017_flat_intelligence_history_storage.py",
    ROOT/"test_ocr_017_postgresql_intelligence_state_cutover.py",
    ROOT/"test_ocr_018_oracle_live_intelligence_state_binding.py",
    ROOT/"test_ocr_019_intelligence_state_query.py",
    ROOT/"test_ocr_020_intelligence_state_production_gate.py",
    ROOT/"test_olf_031_exact_ticker_settlement_result_breadth.py",
    ROOT/"test_olf_032_presettlement_price_recovery.py",
    ROOT/"test_olf_034_physical_learning_consumption_attestation.py",
    ROOT/"test_olf_035_learner_reasoning_lineage.py",
    ROOT/"test_olf_036_live_learning_advancement_audit.py",
    ROOT/"test_olf_037_learning_utilization_telemetry.py",
    ROOT/"test_olf_038_meaningful_learning_production_gate.py",
]

ROOT_GLOBS=[
    "build_ocr_016*.py","build_ocr_017*.py","build_ocr_018*.py","build_ocr_019*.py","build_ocr_020*.py",
    "build_olf_031*.py","build_olf_032*.py","build_olf_034*.py","build_olf_035*.py","build_olf_036*.py",
    "build_olf_037*.py","build_olf_038*.py",
    "build_oir_00[2-9]*.py","build_oir_01[0-5]*.py",
    "test_oir_00[2-9]*.py","test_oir_01[0-5]*.py",
]

BAD_MODULES={
    "qseries_v2.oracle_continuous_reasoning.ocr_016_intelligence_state_materializer",
    "qseries_v2.oracle_continuous_reasoning.ocr_017_continuous_intelligence_state_loop",
    "qseries_v2.oracle_continuous_reasoning.ocr_018_oracle_live_intelligence_state_binding",
    "qseries_v2.oracle_continuous_reasoning.ocr_019_intelligence_state_query",
    "qseries_v2.oracle_continuous_reasoning.ocr_020_intelligence_state_production_gate",
    "qseries_v2.oracle_learning_feedback.olf_031_exact_ticker_settlement_results",
    "qseries_v2.oracle_learning_feedback.olf_032_presettlement_price_recovery",
    "qseries_v2.oracle_learning_feedback.olf_034_physical_learning_consumption_attestation",
    "qseries_v2.oracle_learning_feedback.olf_035_learner_reasoning_lineage",
    "qseries_v2.oracle_learning_feedback.olf_036_live_learning_advancement_audit",
    "qseries_v2.oracle_learning_feedback.olf_037_learning_utilization_telemetry",
    "qseries_v2.oracle_learning_feedback.olf_038_meaningful_learning_production_gate",
}

KEEP_CHILDREN={
    "fast_lane":"run_opr_004_fast_lane_persistent_ingress.py",
    "inventory":"run_opr_004_inventory_persistent_ingress.py",
    "reasoning":"run_olf_030_breadth_aware_reasoning_runtime.py",
    "learning":"run_opr_004_learning_persistent_ingress.py",
    "coverage":"run_opr_004_coverage_persistent_ingress.py",
    "canonical_writer":"run_opr_003_persistent_single_writer_runtime.py",
    "continuity":"run_oir_001_continuity_checkpoint_daemon.py",
    "recovery":"run_oracle_background_recovery.py",
}

OCR015_VERIFY='_verify("qseries_v2.oracle_continuous_reasoning.ocr_015_production_gate","verify_ocr_015_continuous_reasoning_production_capability_gate","OCR-015")'
OCR020_VERIFY='_verify("qseries_v2.oracle_continuous_reasoning.ocr_020_intelligence_state_production_gate","verify_ocr_020_continuous_intelligence_state_production_gate","OCR-020")'

def rel(path):
    try:return str(path.relative_to(ROOT))
    except ValueError:return str(path)

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def backup_file(path):
    if not path.exists():return
    dst=BACKUP/rel(path)
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,dst)

def collect_targets():
    items=set(p for p in PACKAGE_DELETE+ROOT_DELETE_EXACT if p.exists())
    for pattern in ROOT_GLOBS:
        items.update(p for p in ROOT.glob(pattern) if p.is_file())
    return sorted(items,key=lambda p:str(p).lower())

def module_name(path):
    try:r=path.relative_to(ROOT).with_suffix("")
    except ValueError:return None
    parts=list(r.parts)
    if parts and parts[-1]=="__init__":parts=parts[:-1]
    return ".".join(parts)

def imports(path):
    try:tree=ast.parse(path.read_text(encoding="utf-8",errors="replace"))
    except Exception:return set()
    cur=module_name(path) or ""
    package=cur.rsplit(".",1)[0] if "." in cur else cur
    out=set()
    for n in ast.walk(tree):
        if isinstance(n,ast.Import):
            out.update(a.name for a in n.names)
        elif isinstance(n,ast.ImportFrom):
            base=n.module or ""
            if n.level:
                p=package.split(".") if package else []
                up=max(0,n.level-1)
                if up:p=p[:-up]
                base=".".join([*p,base] if base else p)
            if base:out.add(base)
            for a in n.names:
                if a.name!="*":out.add(base+"."+a.name if base else a.name)
    return out

def dependency_guard(targets):
    deleted={p.resolve() for p in targets if p.suffix==".py"}
    offenders=[]
    for path in Q.rglob("*.py"):
        if path.resolve() in deleted or path.name=="__init__.py":continue
        used=imports(path)
        hits=sorted(m for m in BAD_MODULES if any(i==m or i.startswith(m+".") for i in used))
        if hits:offenders.append((path,hits))
    if offenders:
        print("[ABORT] Surviving code still imports failed modules:")
        for p,h in offenders:print(" ",rel(p),"->",", ".join(h))
        raise RuntimeError("Dependency guard blocked cleanup")

def parse_children(source):
    tree=ast.parse(source)
    for n in tree.body:
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in n.targets):
            if isinstance(n.value,ast.Dict):
                d={}
                for k,v in zip(n.value.keys,n.value.values):
                    if isinstance(k,ast.Constant) and isinstance(v,ast.Constant):
                        d[str(k.value)]=str(v.value)
                return d,n
    raise RuntimeError("CHILDREN dictionary missing")

def patch_launcher(source):
    ast.parse(source)
    children,node=parse_children(source)
    for k,v in KEEP_CHILDREN.items():
        if children.get(k)!=v:
            raise RuntimeError(f"Proven child mismatch before cleanup: {k} -> {children.get(k)!r}")
    if children.get("intelligence_state")!="run_ocr_017_continuous_intelligence_state_runtime.py":
        raise RuntimeError("Expected failed intelligence_state child not found")

    body="CHILDREN={\n"+"".join(f'    "{k}":"{v}",\n' for k,v in KEEP_CHILDREN.items())+"}\n"
    lines=source.splitlines(keepends=True)
    lines[node.lineno-1:node.end_lineno]=[body]
    out="".join(lines)

    if OCR020_VERIFY in out:out=out.replace(OCR020_VERIFY,OCR015_VERIFY,1)
    elif OCR015_VERIFY not in out:raise RuntimeError("Expected OCR boot verifier not found")

    out=out.replace(
        "[PASS] OCR-001 through OCR-020 continuous reasoning + intelligence-state capability verified",
        "[PASS] OCR-001 through OCR-015 continuous reasoning capability verified",
    )
    ast.parse(out)
    final,_=parse_children(out)
    if final!=KEEP_CHILDREN:raise RuntimeError("Final child registry mismatch")
    return out

def strip_init(path,tokens):
    if not path.exists():return
    lines=[]
    for line in path.read_text(encoding="utf-8",errors="replace").splitlines():
        if any(t in line for t in tokens):continue
        lines.append(line)
    text="\n".join(lines).rstrip()+"\n"
    ast.parse(text)
    path.write_text(text,encoding="utf-8",newline="\n")

def compile_survivors():
    failures=[]
    for pkg in (OCR,OLF,Q/"oracle_scientific_reasoning",Q/"oracle_production_hardening",
                Q/"oracle_persistence_reliability",Q/"oracle_background_recovery",
                Q/"oracle_interruption_recovery",Q/"oracle_runtime_health"):
        if not pkg.is_dir():continue
        for f in pkg.rglob("*.py"):
            try:compile(f.read_text(encoding="utf-8"),str(f),"exec")
            except Exception as e:failures.append((f,e))
    if failures:
        for f,e in failures:print("[COMPILE FAIL]",rel(f),type(e).__name__,e)
        raise RuntimeError("Surviving package compile failure")

def run_gate(path,*args):
    if not path.is_file():raise RuntimeError("Missing validation command: "+rel(path))
    print("[RUN]",rel(path),*args)
    subprocess.run([sys.executable,str(path),*args],cwd=str(ROOT),check=True,timeout=120)

def restore_backup():
    for src in BACKUP.rglob("*"):
        if not src.is_file() or src==MANIFEST:continue
        dst=ROOT/src.relative_to(BACKUP)
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)

def main():
    print("="*96)
    print(" ORACLE PRODUCTION BASELINE CLEANUP")
    print(" RETIRE FAILED BRANCHES — PRESERVE PROVEN 24/7 CORE")
    print("="*96)
    print("[ROOT]",ROOT)

    if not LAUNCHER.is_file():raise RuntimeError("run_oracle_LIVE.py missing")
    targets=collect_targets()
    print(f"[PLAN] retire_files={len(targets)}")
    for p in targets:print("[RETIRE]",rel(p))

    dependency_guard(targets)

    BACKUP.mkdir(parents=True,exist_ok=True)
    touched=set(targets)|{LAUNCHER,OCR/"__init__.py",OLF/"__init__.py"}
    for p in sorted(touched,key=lambda x:str(x)):backup_file(p)

    MANIFEST.write_text(json.dumps({
        "created_at":datetime.now(timezone.utc).isoformat(),
        "operation":"Oracle Production Baseline Cleanup",
        "delete_targets":[rel(p) for p in targets],
        "pre_cleanup_hashes":{rel(p):sha256(p) for p in touched if p.exists() and p.is_file()},
        "keep_children":KEEP_CHILDREN,
        "execution_authority":False,
    },indent=2,sort_keys=True),encoding="utf-8",newline="\n")

    try:
        LAUNCHER.write_text(patch_launcher(LAUNCHER.read_text(encoding="utf-8")),encoding="utf-8",newline="\n")

        strip_init(OCR/"__init__.py",(
            "ocr_016_intelligence_state_materializer","ocr_017_continuous_intelligence_state_loop",
            "ocr_018_oracle_live_intelligence_state_binding","ocr_019_intelligence_state_query",
            "ocr_020_intelligence_state_production_gate",
        ))
        strip_init(OLF/"__init__.py",(
            "olf_031_exact_ticker_settlement_results","olf_032_presettlement_price_recovery",
            "olf_034_physical_learning_consumption_attestation","olf_035_learner_reasoning_lineage",
            "olf_036_live_learning_advancement_audit","olf_037_learning_utilization_telemetry",
            "olf_038_meaningful_learning_production_gate",
        ))

        for p in targets:
            if p.exists() and p.is_file():p.unlink()

        for child,runner in KEEP_CHILDREN.items():
            if not (ROOT/runner).is_file():
                raise RuntimeError(f"Surviving runtime child missing: {child} -> {runner}")

        compile_survivors()
        run_gate(ROOT/"test_ocr_015_continuous_reasoning_production_capability_gate.py")
        run_gate(LAUNCHER,"--check")

        final,_=parse_children(LAUNCHER.read_text(encoding="utf-8"))
        if final!=KEEP_CHILDREN:raise RuntimeError("Final launcher baseline mismatch")

    except Exception:
        print("[RESTORE] Cleanup validation failed; restoring previous repo state")
        restore_backup()
        print("[RESTORE] Restored from",BACKUP)
        raise

    print("="*96)
    print("[PASS] Failed OCR-016 through OCR-020 branch retired")
    print("[PASS] Failed OLF-031+ experimental branch retired where present")
    print("[PASS] Old OIR-002 through OIR-015 root debris retired where present")
    print("[PASS] Oracle Live restored to OCR-015 verification")
    print("[PASS] Oracle Live now contains exactly 8 proven production children")
    for k,v in KEEP_CHILDREN.items():print(f"[KEEP] {k} -> {v}")
    print("[PASS] execution_authority=FALSE")
    print("[BACKUP]",BACKUP)
    print("[DONE] ORACLE PRODUCTION BASELINE CLEANUP COMPLETE")

if __name__=="__main__":
    main()
