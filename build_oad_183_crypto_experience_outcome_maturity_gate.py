from __future__ import annotations
import ast,os,textwrap
from pathlib import Path
REVISION='OAD_183_CRYPTO_EXPERIENCE_OUTCOME_MATURITY_GATE_V1'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone,timedelta\n\nREAD_ONLY=True\nPROBABILITY_ENABLED=False\nDIRECTION_ENABLED=False\nEXECUTION_AUTHORITY=False\nDEFAULT_HORIZON_SECONDS=60\n\n@dataclass(frozen=True,slots=True)\nclass CryptoExperienceMaturity:\n    experience:object\n    horizon_seconds:int\n    matures_at:str\n    evaluated_at:str\n    age_seconds:float\n    mature:bool\n    state:str\n\ndef _dt(v):\n    d=datetime.fromisoformat(str(v).replace("Z","+00:00"))\n    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)\n\ndef evaluate_crypto_experience_maturity(experience,horizon_seconds=DEFAULT_HORIZON_SECONDS,now=None):\n    horizon=int(horizon_seconds)\n    if horizon < 1: raise ValueError("outcome horizon must be at least one second")\n    start=_dt(experience.snapshot_at).astimezone(timezone.utc)\n    evaluated=(now or datetime.now(timezone.utc))\n    if evaluated.tzinfo is None: evaluated=evaluated.replace(tzinfo=timezone.utc)\n    evaluated=evaluated.astimezone(timezone.utc)\n    matures=start+timedelta(seconds=horizon)\n    age=(evaluated-start).total_seconds()\n    mature=evaluated>=matures\n    return CryptoExperienceMaturity(\n        experience,horizon,matures.isoformat(),evaluated.isoformat(),age,mature,\n        "MATURE_FOR_OUTCOME" if mature else "HOLD_HORIZON_NOT_EXPIRED"\n    )\n\ndef select_mature_crypto_experiences(records,horizon_seconds=DEFAULT_HORIZON_SECONDS,now=None,latest_per_asset=True):\n    rows=tuple(evaluate_crypto_experience_maturity(x,horizon_seconds,now) for x in tuple(records))\n    mature=tuple(x for x in rows if x.mature)\n    if not latest_per_asset: return mature\n    by_asset={}\n    for x in mature:\n        prev=by_asset.get(x.experience.asset)\n        if prev is None or _dt(x.experience.snapshot_at)>_dt(prev.experience.snapshot_at):\n            by_asset[x.experience.asset]=x\n    return tuple(by_asset[k] for k in sorted(by_asset))\n'
TEST_SOURCE='import unittest\nfrom datetime import datetime,timezone\nfrom types import SimpleNamespace\nfrom qseries_v2.oracle_adapters.independent.oad_183_crypto_experience_outcome_maturity_gate import evaluate_crypto_experience_maturity\nclass T(unittest.TestCase):\n    def test_horizon(self):\n        e=SimpleNamespace(snapshot_at="2026-08-29T02:00:00+00:00")\n        early=evaluate_crypto_experience_maturity(e,60,datetime(2026,8,29,2,0,30,tzinfo=timezone.utc))\n        mature=evaluate_crypto_experience_maturity(e,60,datetime(2026,8,29,2,1,0,tzinfo=timezone.utc))\n        print("[EARLY]",early.state)\n        print("[MATURE]",mature.state)\n        self.assertFalse(early.mature)\n        self.assertTrue(mature.mature)\nif __name__=="__main__":\n    z=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not z.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-183 future-horizon maturity gate certified")\n'
def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")
def write(path,source):
    source=textwrap.dedent(source).lstrip(); ast.parse(source,filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(source,encoding="utf-8",newline="\n"); os.replace(tmp,path)
def main():
    r=root(); pkg=r/"qseries_v2"/"oracle_adapters"/"independent"
    module=pkg/'oad_183_crypto_experience_outcome_maturity_gate.py'; test=r/'test_oad_183_crypto_experience_outcome_maturity_gate.py'; init=pkg/"__init__.py"
    print("="*118); print(" OAD-183 CRYPTO EXPERIENCE OUTCOME MATURITY GATE INSTALLER"); print("="*118)
    print("[BOOT] Revision:",REVISION); print("[ROOT]",r)
    for dep in ['oad_182_crypto_persisted_experience_exact_readback.py']:
        if not (pkg/dep).is_file(): raise RuntimeError("Required dependency missing: "+dep)
        print("[PASS] dependency verified:",dep)
    for dep in []:
        if not (r/dep).is_file(): raise RuntimeError("Required architecture dependency missing: "+dep)
        print("[PASS] architecture dependency verified:",dep)
    old={p:(p.read_bytes() if p.exists() else None) for p in (module,test,init)}
    try:
        write(module,MODULE_SOURCE); write(test,TEST_SOURCE)
        lines=init.read_text(encoding="utf-8").splitlines()
        exp="from .oad_183_crypto_experience_outcome_maturity_gate import *"
        if exp not in lines: lines.append(exp)
        write(init,"\n".join(x for x in lines if x.strip())+"\n")
        print("[PASS] module installed:",module.relative_to(r)); print("[PASS] test installed:",test.relative_to(r))
        print("[PASS] syntax validated")
        print("[PASS] read_only=TRUE probability_enabled=FALSE direction_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-183 INSTALLATION COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] installation rolled back"); raise
if __name__=="__main__": main()
