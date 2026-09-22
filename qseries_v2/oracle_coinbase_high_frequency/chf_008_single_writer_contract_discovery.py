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
