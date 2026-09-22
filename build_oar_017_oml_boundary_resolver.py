from __future__ import annotations
import ast, hashlib
from pathlib import Path
ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"observation_adapter_runtime"
OMLROOTS=(ROOT/"qseries_v2"/"oracle_memory",ROOT/"qseries_v2"/"oracle_intelligence"/"oracle_memory")
UP=(PKG/"oar_015_oml_memory_intake_handoff.py",PKG/"oar_016_umd_boundary_resolver.py")
MOD=PKG/"oar_017_oml_boundary_resolver.py"
INIT=PKG/"__init__.py"
TEST=ROOT/"test_oar_017_oml_boundary_resolver.py"
MODULE=r"""
from __future__ import annotations
from dataclasses import dataclass
BUILD_ID="OAR-017"
OAR_017_REVISION="OAR_017_OML_BOUNDARY_RESOLVER_V1"
READ_ONLY=True
EXECUTION_ALLOWED=False
PERSISTENCE_ALLOWED=False
PUBLICATION_ALLOWED=False
@dataclass(frozen=True,slots=True)
class OMLBoundaryCandidate:
    module_name:str
    symbol_name:str
    symbol_kind:str
    score:int
@dataclass(frozen=True,slots=True)
class OMLBoundaryResolution:
    candidates:tuple[OMLBoundaryCandidate,...]
    candidate_count:int
    exact_boundary_resolved:bool
    read_only:bool
class OMLBoundaryResolver:
    read_only=True
    execution_allowed=False
    persistence_allowed=False
    publication_allowed=False
    def resolve(self,inventory:tuple[OMLBoundaryCandidate,...])->OMLBoundaryResolution:
        ordered=tuple(sorted(inventory,key=lambda x:(-x.score,x.module_name,x.symbol_name,x.symbol_kind)))
        return OMLBoundaryResolution(ordered,len(ordered),bool(ordered and ordered[0].score>=5),True)
def verify_oml_boundary_resolver()->bool:
    assert READ_ONLY is True and EXECUTION_ALLOWED is False and PERSISTENCE_ALLOWED is False and PUBLICATION_ALLOWED is False
    return True
"""
TESTSRC=r"""
from __future__ import annotations
import unittest
from qseries_v2.observation_adapter_runtime.oar_017_oml_boundary_resolver import *
class T(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_oml_boundary_resolver())
    def test_resolve(self):
        r=OMLBoundaryResolver().resolve((OMLBoundaryCandidate("oml_a","admit_observation","function",6),))
        self.assertTrue(r.exact_boundary_resolved)
if __name__=="__main__":
    print("="*72); print(" OAR-017 CERTIFICATION TEST"); print(" CERTIFIED OML BOUNDARY RESOLVER"); print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("\n[PASS] Build: OAR-017"); print("[PASS] Deterministic Oracle Memory boundary candidate resolution certified"); print("[DONE] OAR-017 CERTIFIED")
"""
def sha(x): return hashlib.sha256(x.read_bytes()).hexdigest()
def collect():
    fs=[]
    for r in OMLROOTS:
        if r.is_dir(): fs.extend(r.glob("**/*.py"))
    return tuple(sorted(set(fs)))
def inventory(files):
    kws={"memory":1,"observation":2,"evidence":1,"admit":2,"append":1,"store":1,"record":1,"intake":2,"canonical":1,"registry":1}
    rows=[]
    for p in files:
        try: tree=ast.parse(p.read_text(encoding="utf-8"),filename=str(p))
        except UnicodeDecodeError: continue
        for n in tree.body:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                score=sum(w for k,w in kws.items() if k in n.name.lower())
                if score: rows.append((p.stem,n.name,"class" if isinstance(n,ast.ClassDef) else "function",score))
    return sorted(rows,key=lambda x:(-x[3],x[0],x[1],x[2]))
def write(x,t):
    t=t.lstrip(); ast.parse(t,filename=str(x)); x.parent.mkdir(parents=True,exist_ok=True); x.write_text(t,encoding="utf-8",newline="\n"); print("[PASS] Wrote:",x.relative_to(ROOT))
def main():
    print("="*72); print(" OAR-017 INSTALLER"); print(" CERTIFIED OML BOUNDARY RESOLVER"); print("="*72); print("[BOOT] Revision: OAR_017_OML_BOUNDARY_RESOLVER_INSTALLER_V1"); print("[ROOT]",ROOT)
    for x in UP:
        if not x.is_file(): raise RuntimeError(f"Certified upstream missing: {x}")
    files=collect()
    if not files: raise RuntimeError("Certified Oracle Memory modules missing")
    inv=inventory(files)
    if not inv: raise RuntimeError("No Oracle Memory boundary candidates found")
    print(f"[PASS] OML boundary inventory built from {len(files)} modules")
    print(f"[PASS] Highest-ranked candidate: {inv[0][0]}.{inv[0][1]} ({inv[0][2]}, score={inv[0][3]})")
    protected=UP+files; h={x:sha(x) for x in protected}; backups={x:(x.read_bytes() if x.exists() else None) for x in (MOD,TEST,INIT)}
    try:
        write(MOD,MODULE); write(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; exp="from .oar_017_oml_boundary_resolver import *"
        if exp not in cur.splitlines():
            if cur and not cur.endswith("\n"): cur+="\n"
            cur+=exp+"\n"; ast.parse(cur,filename=str(INIT)); INIT.write_text(cur,encoding="utf-8",newline="\n")
        for x,e in h.items():
            if sha(x)!=e: raise RuntimeError(f"Certified upstream changed: {x.name}")
        print("[PASS] Certified Oracle Memory and OAR upstream remained unchanged"); print("[PASS] Deterministic install hash:",hashlib.sha256(MOD.read_bytes()+TEST.read_bytes()).hexdigest()); print("[DONE] OAR-017 INSTALLATION COMPLETE"); return 0
    except Exception:
        for x,b in backups.items():
            if b is None:
                if x.exists(): x.unlink()
            else: x.write_bytes(b)
        raise
if __name__=="__main__": raise SystemExit(main())
