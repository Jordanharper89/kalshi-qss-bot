from __future__ import annotations
import ast,os,textwrap
from pathlib import Path

REVISION='OAD_169_CRYPTO_TEMPORAL_CONDITION_CHANGE_EVALUATOR_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoTemporalConditionChange:\n    asset:str\n    source_family:str\n    metric_name:str\n    previous_value:float|None\n    current_value:float\n    absolute_change:float|None\n    percent_change:float|None\n    previous_condition:str|None\n    current_condition:str\n    temporal_state:str\n    comparable_history_present:bool\n\ndef _dt(v):\n    try: return datetime.fromisoformat(str(v).replace("Z","+00:00"))\n    except Exception: return None\n\ndef evaluate_crypto_temporal_condition_changes(current_states,previous_states=()):\n    prev={}\n    for x in tuple(previous_states):\n        prev[(x.asset,x.source_family,x.metric_name)]=x\n    out=[]\n    for x in tuple(current_states):\n        p=prev.get((x.asset,x.source_family,x.metric_name))\n        if p is None:\n            out.append(CryptoTemporalConditionChange(\n                x.asset,x.source_family,x.metric_name,None,float(x.value),None,None,\n                None,x.condition,"NO_COMPARABLE_HISTORY",False\n            ))\n            continue\n        av=float(x.value)-float(p.value)\n        pc=None if float(p.value)==0 else av/abs(float(p.value))*100.0\n        if av>0: state="INCREASED"\n        elif av<0: state="DECREASED"\n        else: state="UNCHANGED"\n        out.append(CryptoTemporalConditionChange(\n            x.asset,x.source_family,x.metric_name,float(p.value),float(x.value),\n            av,pc,p.condition,x.condition,state,True\n        ))\n    return tuple(out)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_169_crypto_temporal_condition_change_evaluator import evaluate_crypto_temporal_condition_changes\ndef s(v,c="OBSERVED"):\n    return SimpleNamespace(asset="ETH",source_family="ethereum",metric_name="gas_price_wei",value=v,condition=c,observed_at=None)\nclass T(unittest.TestCase):\n    def test_change(self):\n        r=evaluate_crypto_temporal_condition_changes((s(120),),(s(100),))[0]\n        print("[TEMPORAL]",r.temporal_state,r.percent_change)\n        self.assertEqual(r.temporal_state,"INCREASED")\n        self.assertEqual(r.percent_change,20.0)\n        n=evaluate_crypto_temporal_condition_changes((s(120),),())[0]\n        self.assertEqual(n.temporal_state,"NO_COMPARABLE_HISTORY")\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-169 temporal condition change evaluator certified")\n'

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")

def write(path,source):
    source=textwrap.dedent(source).lstrip()
    ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(source,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_169_crypto_temporal_condition_change_evaluator.py'; test=r/'test_oad_169_crypto_temporal_condition_change_evaluator.py'; init=pkg/"__init__.py"
    print("="*112)
    print(" OAD-169 CRYPTO TEMPORAL CONDITION CHANGE EVALUATOR INSTALLER")
    print("="*112)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_168_crypto_condition_state_normalization.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_169_crypto_temporal_condition_change_evaluator import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-169 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__": main()
