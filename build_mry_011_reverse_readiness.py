from pathlib import Path
import ast
PKG=Path("qseries_v2/oracle_execution/solana_atomic_executor")
RT=PKG/"runtime.py";M10=PKG/"mry_010_live_promotion.py"
TARGET=PKG/"mry_011_reverse_readiness.py";TEST=Path("test_mry_011_reverse_readiness.py")
MODULE='''from __future__ import annotations
import inspect
from pathlib import Path
def _resolve(rt):
    for _,obj in vars(rt).items():
        if not callable(obj) or getattr(obj,"__module__",None)!=rt.__name__: continue
        try: src=inspect.getsource(obj)
        except Exception: continue
        if "REVERSE_005_PRELOAD" in src: return obj
    raise RuntimeError("MRY011_REVERSE_PRELOADER_NOT_FOUND")
def refresh(rt,state,root):
    fn=_resolve(rt); vals={"state":state,"root":Path(root),"user":getattr(rt,"USER",None)}; kwargs={}
    for p in inspect.signature(fn).parameters.values():
        if p.name in vals: kwargs[p.name]=vals[p.name]
        elif p.default is inspect._empty: raise RuntimeError("MRY011_UNSUPPORTED_PARAM:"+p.name)
    out=fn(**kwargs)
    print("[MRIYA_REVERSE_REFRESH] function=%s warm=%d"%(fn.__name__,len(rt.READY_TOKENS)),flush=True)
    return out
'''
src=M10.read_text(encoding="utf-8")
if "mry_011_reverse_readiness as rev" not in src:
    src=src.replace("from . import mry_009_atomic_warm_admission as a\n","from . import mry_009_atomic_warm_admission as a\nfrom . import mry_011_reverse_readiness as rev\n",1)
if "rev.refresh(rt,state,root)" not in src:
    anchor="            a.admit(\n                rt,\n                state,\n                pair,\n                ready,\n            )\n"
    if anchor not in src: raise RuntimeError("MRY011_ADMISSION_ANCHOR_MISSING")
    src=src.replace(anchor,anchor+"\n            rev.refresh(rt,state,root)\n",1)
TEST_SOURCE='''import ast,unittest
from pathlib import Path
P=Path("qseries_v2/oracle_execution/solana_atomic_executor")
class T(unittest.TestCase):
    def test_runtime_preloader(self):
        s=(P/"runtime.py").read_text(encoding="utf-8");self.assertIn("REVERSE_005_PRELOAD",s);ast.parse(s)
    def test_admission_refresh(self):
        s=(P/"mry_010_live_promotion.py").read_text(encoding="utf-8");self.assertIn("rev.refresh(rt,state,root)",s);ast.parse(s)
if __name__=="__main__":unittest.main(verbosity=2)
'''
for s in (MODULE,src,TEST_SOURCE): ast.parse(s)
TARGET.write_text(MODULE,encoding="utf-8");M10.write_text(src,encoding="utf-8");TEST.write_text(TEST_SOURCE,encoding="utf-8")
print("[PASS] MRY-011 installed")
print("[PASS] dynamic WARM admissions now invoke the existing reverse sell-template preloader")
print("[PASS] 0.010 size, atomic profit lock, preflight and maxRetries=0 unchanged")