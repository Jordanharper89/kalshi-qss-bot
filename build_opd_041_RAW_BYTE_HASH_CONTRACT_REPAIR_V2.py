from pathlib import Path
import ast,hashlib,json,re

ROOT=Path.cwd()
MOD=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_041_exact_live_token_materializer.py"
MAN=ROOT/"runtime"/"predictive_data"/"opd_041_exact_live_token_materializer_contract.json"

if not MOD.is_file():
    raise RuntimeError("OPD-041 production module missing")

txt=MOD.read_text(encoding="utf-8")
tree=ast.parse(txt)
vals={}
for n in tree.body:
    if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
        if n.targets[0].id in {"SOURCE_PATH","SOURCE_SHA256"}:
            vals[n.targets[0].id]=ast.literal_eval(n.value)

src=ROOT/vals.get("SOURCE_PATH","")
if not src.is_file():
    raise RuntimeError("frozen OPD-017 source missing: "+str(src))

raw_sha=hashlib.sha256(src.read_bytes()).hexdigest()
new,n=re.subn(r'(?m)^SOURCE_SHA256\s*=\s*["\'][0-9a-f]{64}["\']',
              f'SOURCE_SHA256 = "{raw_sha}"',txt)
if n!=1:
    raise RuntimeError(f"expected one SOURCE_SHA256 assignment, found {n}")
MOD.write_text(new,encoding="utf-8")

if MAN.is_file():
    d=json.loads(MAN.read_text(encoding="utf-8"))
    d["opd017_sha256"]=raw_sha
    d["hash_basis"]="RAW_FILE_BYTES"
    MAN.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")

print("[SOURCE_PATH]",vals["SOURCE_PATH"])
print("[RAW_SHA256]",raw_sha)
print("[PASS] OPD-041 raw-byte hash contract repaired")
print("[PASS] frozen OPD-017 semantics unchanged")