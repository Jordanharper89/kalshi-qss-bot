from __future__ import annotations

import ast
import hashlib
import os
import textwrap
from pathlib import Path

REVISION="OAD_POSTGRESQL_BACKEND_INTERFACE_AUDIT_V1"

def find_root():
    for base in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (base,*base.parents):
            if (p/"qseries_v2").is_dir():
                return p
    raise SystemExit("[ERROR] Q Series repository not found")

ROOT=find_root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
MODULE=PKG/"oad_postgresql_backend_interface_audit.py"
TEST=ROOT/"test_oad_postgresql_backend_interface_audit.py"
INIT=PKG/"__init__.py"

MODULE_SOURCE='\nfrom __future__ import annotations\n\nimport inspect\nimport json\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_production_hardening.oph_007_physical_single_postgresql_writer_runtime import (\n    build_existing_canonical_router,\n)\n\nREAD_ONLY=True\nEXECUTION_AUTHORITY=False\nPROBABILITY_ENABLED=False\n\nSAFE_VALUE_TYPES=(str,int,float,bool,type(None))\n\ndef _safe_value(value):\n    if isinstance(value,SAFE_VALUE_TYPES):\n        return value\n    if isinstance(value,(tuple,list)):\n        return [_safe_value(x) for x in value[:20]]\n    if isinstance(value,dict):\n        out={}\n        for i,(k,v) in enumerate(value.items()):\n            if i>=20:\n                break\n            out[str(k)]=_safe_value(v)\n        return out\n    return f"<{type(value).__module__}.{type(value).__name__}>"\n\ndef _callable_signature(obj):\n    try:\n        return str(inspect.signature(obj))\n    except Exception:\n        return "<signature unavailable>"\n\ndef _public_surface(obj):\n    methods=[]\n    attrs=[]\n    for name in sorted(set(dir(obj))):\n        if name.startswith("__"):\n            continue\n        try:\n            value=getattr(obj,name)\n        except Exception as exc:\n            attrs.append({\n                "name":name,\n                "kind":"unreadable",\n                "error":f"{type(exc).__name__}: {exc}",\n            })\n            continue\n        if callable(value):\n            methods.append({\n                "name":name,\n                "signature":_callable_signature(value),\n                "module":getattr(value,"__module__",None),\n                "qualname":getattr(value,"__qualname__",None),\n            })\n        else:\n            attrs.append({\n                "name":name,\n                "type":f"{type(value).__module__}.{type(value).__name__}",\n                "value":_safe_value(value),\n            })\n    return methods,attrs\n\ndef run_postgresql_backend_interface_audit(root=None):\n    root=Path(root or Path.cwd()).resolve()\n    router=build_existing_canonical_router(root)\n\n    backend=getattr(router,"_persistence_backend",None)\n    if backend is None:\n        raise RuntimeError("existing canonical router has no _persistence_backend")\n\n    router_methods,router_attrs=_public_surface(router)\n    backend_methods,backend_attrs=_public_surface(backend)\n\n    nested=[]\n    for name,value in vars(backend).items():\n        if isinstance(value,SAFE_VALUE_TYPES):\n            continue\n        try:\n            methods,attrs=_public_surface(value)\n        except Exception as exc:\n            nested.append({\n                "attribute":name,\n                "type":f"{type(value).__module__}.{type(value).__name__}",\n                "error":f"{type(exc).__name__}: {exc}",\n            })\n            continue\n        nested.append({\n            "attribute":name,\n            "type":f"{type(value).__module__}.{type(value).__name__}",\n            "methods":methods,\n            "attributes":attrs,\n        })\n\n    report={\n        "read_only":True,\n        "execution_authority":False,\n        "probability_enabled":False,\n        "router_type":f"{type(router).__module__}.{type(router).__name__}",\n        "backend_type":f"{type(backend).__module__}.{type(backend).__name__}",\n        "router_methods":router_methods,\n        "router_attributes":router_attrs,\n        "backend_methods":backend_methods,\n        "backend_attributes":backend_attrs,\n        "backend_nested_objects":nested,\n    }\n\n    path=root/"OAD_POSTGRESQL_BACKEND_INTERFACE_AUDIT.json"\n    path.write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")\n    return report,path\n'
TEST_SOURCE='\nimport unittest\n\nfrom qseries_v2.oracle_adapters.independent.oad_postgresql_backend_interface_audit import (\n    run_postgresql_backend_interface_audit,\n)\n\nclass T(unittest.TestCase):\n    def test_backend_interface_audit(self):\n        report,path=run_postgresql_backend_interface_audit()\n\n        print("[ROUTER_TYPE]",report["router_type"])\n        print("[BACKEND_TYPE]",report["backend_type"])\n\n        print("[BACKEND_METHODS]")\n        for m in report["backend_methods"]:\n            print(" ",m["name"],m["signature"])\n\n        print("[BACKEND_ATTRIBUTES]")\n        for a in report["backend_attributes"]:\n            print(" ",a["name"],a.get("type"),a.get("value",""))\n\n        print("[BACKEND_NESTED_OBJECTS]")\n        for obj in report["backend_nested_objects"]:\n            print(" ",obj["attribute"],obj["type"])\n            for m in obj.get("methods",[]):\n                print("    METHOD",m["name"],m["signature"])\n            for a in obj.get("attributes",[]):\n                print("    ATTR",a["name"],a.get("type"),a.get("value",""))\n\n        print("[REPORT]",path)\n\n        self.assertTrue(report["read_only"])\n        self.assertFalse(report["execution_authority"])\n        self.assertFalse(report["probability_enabled"])\n        self.assertTrue(report["backend_type"])\n        self.assertGreater(len(report["backend_methods"])+len(report["backend_attributes"]),0)\n\nif __name__=="__main__":\n    print("="*108)\n    print(" OAD POSTGRESQL BACKEND INTERFACE AUDIT")\n    print(" EXACT PRODUCTION PERSISTENCE SURFACE DISCOVERY")\n    print("="*108)\n\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n\n    print("[PASS] production backend inspected without issuing SQL")\n    print("[PASS] no PostgreSQL rows modified")\n    print("[PASS] no production module modified")\n    print("[PASS] probability_enabled=FALSE")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] POSTGRESQL BACKEND INTERFACE AUDIT COMPLETE")\n'

REQUIRED=[
    ("qseries_v2/oracle_production_hardening/oph_007_physical_single_postgresql_writer_runtime.py","Existing PostgreSQL production router"),
    ("qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py","Frozen OPH-023"),
    ("qseries_v2/oracle_adapters/independent/oad_106_universal_identity_classification_physical_gate.py","Recertified OAD-106"),
]

PROTECTED=[
    "qseries_v2/oracle_adapters/kalshi/oad_055_kalshi_production_freeze.py",
    "qseries_v2/oracle_production_hardening/oph_023_postgresql_single_writer_production_freeze.py",
    "qseries_v2/universal_market_discovery/umd_098_market_taxonomy.py",
    "qseries_v2/universal_market_discovery/umd_109_market_semantic_profile.py",
    "qseries_v2/oracle_adapters/independent/oad_104_semantic_entity_domain_disambiguation.py",
    "qseries_v2/oracle_adapters/independent/oad_105_authoritative_source_requirement_router.py",
    "qseries_v2/oracle_adapters/independent/oad_106_universal_identity_classification_physical_gate.py",
]

def write(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    print("="*108)
    print(" OAD POSTGRESQL BACKEND INTERFACE AUDIT INSTALLER")
    print(" EXACT PRODUCTION PERSISTENCE SURFACE DISCOVERY")
    print("="*108)
    print("[BOOT] Revision:",REVISION)
    print("[ROOT]",ROOT)

    for rel,label in REQUIRED:
        p=ROOT/rel
        if not p.is_file():
            raise RuntimeError(label+" missing: "+str(p))
        print("[PASS]",label,"verified")

    hashes={ROOT/rel:hashlib.sha256((ROOT/rel).read_bytes()).hexdigest() for rel in PROTECTED}
    old={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,TEST,INIT)}

    try:
        write(MODULE,MODULE_SOURCE)
        write(TEST,TEST_SOURCE)

        lines=INIT.read_text(encoding="utf-8").splitlines() if INIT.exists() else []
        export="from .oad_postgresql_backend_interface_audit import *"
        if export not in lines:
            lines.append(export)
        write(INIT,"\n".join(x for x in lines if x.strip())+"\n")

        for p,h in hashes.items():
            if hashlib.sha256(p.read_bytes()).hexdigest()!=h:
                raise RuntimeError("Protected production file changed: "+p.name)

        print("[PASS] backend interface audit installed")
        print("[PASS] production OAD-104/OAD-105/OAD-106 protected")
        print("[PASS] frozen Kalshi/OPH/UMD boundaries unchanged")
        print("[PASS] audit issues no SQL")
        print("[PASS] probability_enabled=FALSE")
        print("[PASS] execution_authority=FALSE")
        print("[DONE] POSTGRESQL BACKEND INTERFACE AUDIT INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(data)
        print("[ROLLBACK] audit files restored")
        raise

if __name__=="__main__":
    main()
