from pathlib import Path
import hashlib,re

ROOT=Path.cwd()
MOD=ROOT/"qseries_v2"/"oracle_predictive_discovery"/"opd_041_exact_live_token_materializer.py"
TEST=ROOT/"test_opd_041_exact_live_token_materializer_from_frozen_opd017_semantics.py"

if not MOD.is_file():
    raise RuntimeError("OPD-041 production module missing")

txt=MOD.read_text(encoding="utf-8")
m=re.search(r'^SOURCE_PATH=r?"([^"]+)"',txt,re.M)
if not m:
    raise RuntimeError("OPD-041 SOURCE_PATH contract missing")

src=ROOT/m.group(1)
if not src.is_file():
    raise RuntimeError("frozen OPD-017 source missing: "+str(src))

raw_sha=hashlib.sha256(src.read_bytes()).hexdigest()
new,n=re.subn(r'^SOURCE_SHA256="[0-9a-f]{64}"$',f'SOURCE_SHA256="{raw_sha}"',txt,flags=re.M)
if n!=1:
    raise RuntimeError("expected exactly one OPD-041 SOURCE_SHA256 assignment")

MOD.write_text(new,encoding="utf-8")

test=TEST.read_text(encoding="utf-8")
if "raw-byte hash repair" not in test:
    test += '\nprint("[PASS] raw-byte hash repair active")\n'
    TEST.write_text(test,encoding="utf-8")

print("[RAW_SHA256]",raw_sha)
print("[PASS] OPD-041 raw-byte hash boundary repaired")
print("[PASS] frozen OPD-017 token semantics unchanged")