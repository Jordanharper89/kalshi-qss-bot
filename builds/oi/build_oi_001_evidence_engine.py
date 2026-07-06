"""
build_oi_001_evidence_engine.py
OI-001 Evidence Engine Installer
"""

from pathlib import Path
from datetime import datetime

ROOT = Path.cwd()
OI = ROOT / "qseries_v2" / "oi"

def backup(path):
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = path.with_suffix(path.suffix + f".bak_{stamp}")
        bak.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")

def write(path,text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup(path)
    path.write_text(text, encoding="utf-8")
    print(f"[OK] Wrote {path.relative_to(ROOT)}")

engine = """from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Evidence:
    source: str
    category: str
    value: dict
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

class EvidenceEngine:
    def __init__(self):
        self._items=[]

    def add(self,evidence):
        self._items.append(evidence)

    def all(self):
        return list(self._items)

evidence_engine = EvidenceEngine()
"""

test = """from qseries_v2.oi.evidence_engine import Evidence, evidence_engine

evidence_engine.add(Evidence(
    source="unit_test",
    category="market",
    value={"edge":5.2}
))

assert len(evidence_engine.all())==1
print("[PASS] OI-001 Evidence Engine")
"""

print("="*40)
print(" OI-001 INSTALLER")
print(" Evidence Engine")
print("="*40)

write(OI/"__init__.py","from .evidence_engine import evidence_engine, EvidenceEngine, Evidence\n")
write(OI/"evidence_engine.py",engine)
write(ROOT/"test_oi_001_evidence_engine.py",test)

print("\n[DONE] OI-001 installed")
print("Run:")
print("python test_oi_001_evidence_engine.py")
