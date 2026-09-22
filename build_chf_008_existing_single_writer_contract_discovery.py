from pathlib import Path
import py_compile

ROOT=Path.cwd()
PKG=ROOT/"qseries_v2"/"oracle_coinbase_high_frequency"
assert (PKG/"chf_007_restart_checkpoint_recovery.py").exists(),"CHF-007 required"

BODY=r"""
import inspect,importlib,json
from pathlib import Path

REVISION="CHF-008"
CANDIDATES=(
    "qseries_v2.oracle_adapters.independent.oad_261_universal_expansion_source_single_writer_postgresql_persistence",
    "qseries_v2.oracle_production_hardening.oph_019_postgresql_universal_ingestion_queue",
)

def discover(root:Path):
    root=Path(root)
    report={"revision":REVISION,"modules":[]}
    for modname in CANDIDATES:
        item={"module":modname,"imported":False,"functions":[],"classes":[]}
        try:
            mod=importlib.import_module(modname)
            item["imported"]=True
            for name,obj in vars(mod).items():
                if name.startswith("_"):
                    continue
                if inspect.isfunction(obj):
                    try:
                        sig=str(inspect.signature(obj))
                    except Exception:
                        sig="?"
                    item["functions"].append({"name":name,"signature":sig})
                elif inspect.isclass(obj) and getattr(obj,"__module__",None)==modname:
                    methods=[]
                    for mn,mv in vars(obj).items():
                        if callable(mv) and not mn.startswith("_"):
                            try:
                                ms=str(inspect.signature(mv))
                            except Exception:
                                ms="?"
                            methods.append({"name":mn,"signature":ms})
                    item["classes"].append({"name":name,"methods":methods})
        except Exception as e:
            item["error"]=repr(e)
        report["modules"].append(item)
    out=root/"runtime"/"coinbase_hf"/"single_writer_contract.json"
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2),encoding="utf-8")
    return report,out
"""

TEST=r"""
from pathlib import Path
from qseries_v2.oracle_coinbase_high_frequency.chf_008_single_writer_contract_discovery import discover
report,path=discover(Path.cwd())
print("[REPORT]",path)
for module in report["modules"]:
    print("[MODULE]",module["module"],"imported=",module["imported"])
    for fn in module["functions"]:
        print("[FUNCTION]",fn["name"],fn["signature"])
    for cls in module["classes"]:
        print("[CLASS]",cls["name"])
        for method in cls["methods"]:
            print("[METHOD]",method["name"],method["signature"])
assert any(m["imported"] for m in report["modules"]),"NO_EXISTING_SINGLE_WRITER_MODULE_IMPORTABLE"
print("[PASS] CHF-008 exact existing single-writer contract discovery certified")
"""

mod=PKG/"chf_008_single_writer_contract_discovery.py"
tst=ROOT/"test_chf_008_existing_single_writer_contract_discovery.py"
mod.write_text(BODY.lstrip(),encoding="utf-8")
tst.write_text(TEST.lstrip(),encoding="utf-8")
py_compile.compile(str(mod),doraise=True)
py_compile.compile(str(tst),doraise=True)
print("[PASS] wrote",mod)
print("[PASS] wrote",tst)
print("[PASS] repository contract discovery only")
