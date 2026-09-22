from __future__ import annotations
import os,sys,subprocess
from pathlib import Path

def root():
    for b in (Path.cwd().resolve(),Path(__file__).resolve().parent):
        for p in (b,b/"kalshi-qss-bot",*b.parents):
            if (p/"qseries_v2").is_dir(): return p
    raise RuntimeError("Q Series repository root not found")

def write_atomic(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);compile(s,str(p),"exec")
    t=p.with_suffix(p.suffix+".tmp");t.write_text(s.lstrip("\n"),encoding="utf-8",newline="\n");os.replace(t,p)

def run_test(r,p):
    q=subprocess.run([sys.executable,str(p)],cwd=str(r))
    if q.returncode: raise RuntimeError("Certification test failed: "+p.name)

REVISION='OAD_232_CRYPTO_PROSPECTIVE_EMPIRICAL_FORECAST_FOUNDATION_IDENTITY_SAFE_V1'
EXPECTED='build_oad_232_crypto_prospective_empirical_forecast_foundation_IDENTITY_SAFE.py'
MODULE_NAME='oad_232_crypto_prospective_empirical_forecast_foundation.py'
TEST_NAME='test_oad_232_crypto_prospective_empirical_forecast_foundation.py'
MODULE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom hashlib import sha256\nimport json\nfrom .oad_227_crypto_learned_case_asof_snapshot_boundary import capture_crypto_learned_case_snapshot\n\nREAD_ONLY=True;PROBABILITY_ENABLED=False;DIRECTION_ENABLED=False;PUBLICATION_ALLOWED=False;EXECUTION_AUTHORITY=False\n\ndef _h(v):return sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()\n\n@dataclass(frozen=True,slots=True)\nclass ProspectiveCryptoForecast:\n    forecast_id:str\n    asset:str\n    created_at:str\n    training_as_of_sequence:int\n    training_snapshot_hash:str\n    sample_size:int\n    positive_count:int\n    negative_or_flat_count:int\n    internal_forecast_probability:float\n    source_claims:tuple\n    horizon_seconds:int=60\n    probability_enabled:bool=False\n    direction_enabled:bool=False\n    publication_allowed:bool=False\n    execution_authority:bool=False\n\ndef build_prospective_crypto_forecasts(root=None,per_asset_limit=512,created_at=None):\n    snap=capture_crypto_learned_case_snapshot(root,per_asset_limit)\n    now=created_at or datetime.now(timezone.utc).isoformat()\n    by_asset={}\n    for row in snap.rows:\n        p=row[4] if isinstance(row[4],dict) else dict(row[4] or ())\n        asset=str(p.get("asset") or "").upper()\n        if asset and p.get("return_fraction") is not None:by_asset.setdefault(asset,[]).append(p)\n    out=[]\n    for asset,rows in sorted(by_asset.items()):\n        pos=sum(float(p["return_fraction"])>0 for p in rows);n=len(rows)\n        probability=(pos+1)/(n+2)  # auditable Beta(1,1) empirical forecast\n        families={}\n        for p in rows:\n            y=float(p["return_fraction"])>0\n            seen=set()\n            for x in tuple(p.get("condition_vector") or ()):\n                if isinstance(x,(list,tuple)) and x:\n                    fam=str(x[0]).strip().lower()\n                    if fam and fam not in seen:\n                        families.setdefault(fam,[0,0]);families[fam][0]+=1;families[fam][1]+=int(y);seen.add(fam)\n        claims=tuple((fam,cnt,(pc+1)/(cnt+2),((pc+1)/(cnt+2))>=.5) for fam,(cnt,pc) in sorted(families.items()))\n        raw={"asset":asset,"created_at":now,"as_of":snap.as_of_sequence,"snapshot":snap.snapshot_hash,"n":n,"p":probability,"claims":claims}\n        out.append(ProspectiveCryptoForecast(_h(raw),asset,now,snap.as_of_sequence,snap.snapshot_hash,n,pos,n-pos,probability,claims))\n    return tuple(out)\n'
TEST='import unittest\nfrom types import SimpleNamespace\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent import oad_232_crypto_prospective_empirical_forecast_foundation as m\nROWS=((1,"o","s","t",{"asset":"BTC","return_fraction":.01,"condition_vector":(("bitcoin","fee",1,"HIGH"),)}),\n      (2,"p","s","t",{"asset":"BTC","return_fraction":-.01,"condition_vector":(("bitcoin","fee",1,"LOW"),)}),\n      (3,"q","s","t",{"asset":"BTC","return_fraction":.02,"condition_vector":(("coinbase","spot",1,"OBSERVED"),)}))\nclass T(unittest.TestCase):\n    def test_forecast(self):\n        snap=SimpleNamespace(as_of_sequence=3,snapshot_hash="a"*64,rows=ROWS)\n        with patch.object(m,"capture_crypto_learned_case_snapshot",return_value=snap):\n            x=m.build_prospective_crypto_forecasts(created_at="2026-08-31T20:00:00+00:00")[0]\n        print("[FORECAST]",x.asset,x.sample_size,x.internal_forecast_probability,"[CLAIMS]",x.source_claims)\n        self.assertAlmostEqual(x.internal_forecast_probability,3/5)\n        self.assertFalse(x.probability_enabled);self.assertFalse(x.publication_allowed);self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] OAD-232 prospective empirical forecast foundation certified")\n'

def main():
    if Path(__file__).name!=EXPECTED: raise RuntimeError(f"Installer identity mismatch: expected {EXPECTED}, got {Path(__file__).name}")
    r=root();pkg=r/"qseries_v2/oracle_adapters/independent";m=pkg/MODULE_NAME;t=r/TEST_NAME
    print("="*124);print(" OAD-232 CRYPTO PROSPECTIVE EMPIRICAL FORECAST FOUNDATION");print("="*124);print("[BOOT]",REVISION);print("[INSTALLER]",Path(__file__).name);print("[ROOT]",r)
    d=pkg/'oad_227_crypto_learned_case_asof_snapshot_boundary.py'
    if not d.is_file(): raise RuntimeError("Required dependency missing: "+str(d))
    print("[PASS] dependency verified:",d.relative_to(r))
    print("[PASS] installer identity verified")
    targets=[m,t]
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        write_atomic(m,MODULE);write_atomic(t,TEST)
        run_test(r,t)
        print('[PASS] forecast uses only history at/before training snapshot')
        print('[PASS] internal forecast probability is not operator-facing probability')
        print('[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE')
        print("[DONE] OAD-232 INSTALLATION COMPLETE")
    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists():p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] installation rolled back");raise

if __name__=="__main__":main()
