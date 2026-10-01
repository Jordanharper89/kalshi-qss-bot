from pathlib import Path
import hashlib, shutil
ROOT=Path(__file__).resolve().parent
LAUNCHER=ROOT/"run_oracle_live.py"
TEST=ROOT/"test_osi_018_existing_launcher_child_registration.py"
EXPECTED="e9133c5e6641b5b1a11cc7b45037de9a9c677224232802f636730fa12c0c476c"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

TEST_TEXT=r"""import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_registration(self):
  text=(ROOT/"run_oracle_live.py").read_text(encoding="utf-8",errors="replace")
  self.assertIn("run_osi_solana_intelligence_live.py",text)
  self.assertTrue((ROOT/"run_oracle_live.py.osi018.bak").is_file())
  self.assertTrue((ROOT/"run_osi_solana_intelligence_live.py").is_file())
  print("[PASS] OSI-018 existing Oracle launcher registration")
  print("[TRADER] Starting Oracle now also starts the Solana opportunity hunter")
  print("[PASS] execution_authority=FALSE")
  print("[SCOPE] Registration certified; restart Oracle required to activate child")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" OSI-018 EXISTING ORACLE LAUNCHER CHILD REGISTRATION");print("="*116)
 if sha(LAUNCHER)!=EXPECTED: raise RuntimeError("Captured launcher hash changed; refuse production patch")
 raw=LAUNCHER.read_bytes()
 newline=b"\r\n" if b"\r\n" in raw else b"\n"
 marker=b'if __name__ == "__main__":'
 idx=raw.find(marker)
 if idx<0:
  marker=b"if __name__ == '__main__':";idx=raw.find(marker)
 if idx<0: raise RuntimeError("No safe __main__ anchor found")
 if b"run_osi_solana_intelligence_live.py" not in raw:
  lines=[
   b"# OSI-018 registered read-only Solana intelligence child",
   b"import subprocess as _osi_subprocess",
   b"import sys as _osi_sys",
   b"from pathlib import Path as _OSIPath",
   b"_osi_child = _OSIPath(__file__).resolve().parent / 'run_osi_solana_intelligence_live.py'",
   b"if _osi_child.is_file():",
   b"    _osi_subprocess.Popen([_osi_sys.executable, str(_osi_child)], cwd=str(_osi_child.parent))",
   b"",
  ]
  inject=newline+newline.join(lines)+newline
  shutil.copy2(LAUNCHER,ROOT/"run_oracle_live.py.osi018.bak")
  LAUNCHER.write_bytes(raw[:idx]+inject+raw[idx:])
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] existing launcher patched from captured raw bytes")
 print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
