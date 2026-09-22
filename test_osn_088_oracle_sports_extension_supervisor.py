from pathlib import Path
import json,hashlib
r=Path.cwd(); s=json.loads((r/'qseries_v2/oracle_source_network/state/osn088_extension_supervisor.json').read_text())
assert hashlib.sha256((r/s['base_launcher']).read_bytes()).hexdigest()==s['base_sha256']
assert s['base_mutated'] is False
assert (r/s['launcher']).exists()
print('[PASS] frozen base launcher unchanged')
print('[PASS] extension supervisor installed')
print('[PASS] OSN-088 certified')
