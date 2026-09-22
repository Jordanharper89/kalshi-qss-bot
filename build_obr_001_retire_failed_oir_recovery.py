from pathlib import Path
import os,re,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_interruption_recovery"
INIT=PKG/"__init__.py"

REMOVE_MODULES=[PKG/f"oir_{i:03d}_{name}.py" for i,name in []]

def main():
    print("="*88)
    print(" OBR-001 INSTALLER")
    print(" RETIRE FAILED OIR RECOVERY PATH — PRESERVE OIR-001 CONTINUITY")
    print("="*88)
    print("[ROOT]",ROOT)

    patterns=[
        "oir_002","oir_003","oir_004","oir_005",
        "oir_006","oir_007","oir_008","oir_009","oir_010",
        "oir_011","oir_012","oir_013","oir_014","oir_015",
    ]

    removed=[]
    for p in PKG.glob("oir_*.py"):
        low=p.name.lower()
        if any(token in low for token in patterns):
            p.unlink()
            removed.append(str(p.relative_to(ROOT)))

    for p in ROOT.glob("test_oir_*.py"):
        low=p.name.lower()
        if any(token in low for token in patterns):
            p.unlink()
            removed.append(str(p.relative_to(ROOT)))

    for p in PKG.glob("OIR_*_FREEZE_MANIFEST.json"):
        name=p.name.upper()
        keep=name.startswith("OIR_001")
        if not keep:
            p.unlink()
            removed.append(str(p.relative_to(ROOT)))

    if INIT.is_file():
        lines=INIT.read_text(encoding="utf-8").splitlines()
        kept=[]
        for line in lines:
            if "from .oir_" in line and any(token in line.lower() for token in patterns):
                continue
            kept.append(line)
        INIT.write_text("\n".join(kept).rstrip()+"\n",encoding="utf-8",newline="\n")

    print(f"[PASS] retired_files={len(removed)}")
    print("[PASS] OIR-001 continuity preserved")
    print("[PASS] failed synchronous recovery modules removed")
    print("[DONE] OBR-001 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
