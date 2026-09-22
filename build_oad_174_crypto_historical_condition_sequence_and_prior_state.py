from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_174_CRYPTO_HISTORICAL_CONDITION_SEQUENCE_AND_PRIOR_STATE_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\n\n@dataclass(frozen=True,slots=True)\nclass CryptoConditionSequence:\n    asset:str\n    source_family:str\n    metric_name:str\n    points:tuple\n    point_count:int\n\ndef _dt(v):\n    return datetime.fromisoformat(str(v).replace("Z","+00:00"))\n\ndef select_latest_prior_comparable_states(current_states,history_states):\n    grouped={}\n    for h in tuple(history_states):\n        grouped.setdefault((h.asset,h.source_family,h.metric_name),[]).append(h)\n    selected=[]\n    for c in tuple(current_states):\n        candidates=[\n            h for h in grouped.get((c.asset,c.source_family,c.metric_name),())\n            if h.observed_at is not None and c.observed_at is not None and _dt(h.observed_at)<_dt(c.observed_at)\n        ]\n        if candidates:\n            selected.append(max(candidates,key=lambda x:_dt(x.observed_at)))\n    return tuple(selected)\n\ndef build_crypto_condition_sequences(history_states,max_points_per_metric=32):\n    grouped={}\n    for h in tuple(history_states):\n        grouped.setdefault((h.asset,h.source_family,h.metric_name),[]).append(h)\n    out=[]\n    for key,rows in sorted(grouped.items()):\n        ordered=sorted(rows,key=lambda x:_dt(x.observed_at))\n        ordered=ordered[-int(max_points_per_metric):]\n        points=tuple((x.observed_at,float(x.value),x.condition) for x in ordered)\n        out.append(CryptoConditionSequence(key[0],key[1],key[2],points,len(points)))\n    return tuple(out)\n'
TEST_SOURCE='import unittest\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_174_crypto_historical_condition_sequence_and_prior_state import (\n    select_latest_prior_comparable_states,build_crypto_condition_sequences\n)\ndef s(t,v):\n    return SimpleNamespace(asset="BTC",source_family="bitcoin",metric_name="fastest_fee_rate",observed_at=t,value=v,condition="OBSERVED")\nclass T(unittest.TestCase):\n    def test_prior_and_sequence(self):\n        hist=(s("2026-08-29T00:00:00+00:00",10),s("2026-08-29T00:30:00+00:00",12))\n        cur=(s("2026-08-29T01:00:00+00:00",15),)\n        p=select_latest_prior_comparable_states(cur,hist)\n        q=build_crypto_condition_sequences(hist)\n        print("[PRIOR]",p[0].value)\n        print("[SEQUENCE_POINTS]",q[0].point_count)\n        self.assertEqual(p[0].value,12)\n        self.assertEqual(q[0].point_count,2)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-174 historical sequence and exact prior-state selection certified")\n'

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
    module=pkg/'oad_174_crypto_historical_condition_sequence_and_prior_state.py'; test=r/'test_oad_174_crypto_historical_condition_sequence_and_prior_state.py'; init=pkg/"__init__.py"
    print("="*118)
    print(" OAD-174 CRYPTO HISTORICAL CONDITION SEQUENCE AND PRIOR STATE INSTALLER")
    print("="*118)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_173_crypto_condition_recent_history_exact_readback.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_174_crypto_historical_condition_sequence_and_prior_state import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r))
        print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-174 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back")
        raise

if __name__=="__main__": main()
