
from __future__ import annotations
import ast, os, subprocess, sys, textwrap
from pathlib import Path

REVISION="OAD_110_111_EXACT_REPOSITORY_REBUILD"

def root():
    p=Path.cwd().resolve()
    if not (p/"qseries_v2").is_dir():
        raise RuntimeError("Run from Q Series repository root")
    return p

def write(path, src):
    src=textwrap.dedent(src).lstrip()
    ast.parse(src, filename=str(path))
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(src,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

ROOT=root()
PKG=ROOT/"qseries_v2"/"oracle_adapters"/"independent"
M061=PKG/"oad_061_independent_to_canonical_bridge.py"
M107=PKG/"oad_107_authoritative_sports_source_foundation.py"
M108=PKG/"oad_108_official_mlb_source_adapter.py"
M109=PKG/"oad_109_official_nhl_source_adapter.py"
M110=PKG/"oad_110_authoritative_sports_canonical_bridge.py"
M111=PKG/"oad_111_authoritative_sports_physical_acquisition_gate.py"
T110=ROOT/"test_oad_110_authoritative_sports_canonical_bridge.py"
T111=ROOT/"test_oad_111_authoritative_sports_physical_acquisition_gate.py"

S110='\nfrom __future__ import annotations\n\nfrom qseries_v2.oracle_adapters.independent.oad_061_independent_to_canonical_bridge import (\n    canonicalize_independent_observation,\n)\n\nREAD_ONLY = True\nEXECUTION_AUTHORITY = False\nPROBABILITY_ENABLED = False\n\ndef canonicalize_authoritative_sports_observation(observation, acquisition_batch_id):\n    if getattr(observation, "source_class", None) != "authoritative_real_world":\n        raise ValueError("authoritative_real_world source required")\n    if getattr(observation, "independent_evidence", None) is not True:\n        raise ValueError("independent evidence required")\n    if getattr(observation, "execution_authority", None) is not False:\n        raise ValueError("execution authority must remain false")\n    return canonicalize_independent_observation(observation, acquisition_batch_id)\n\ndef bridge_contract_record():\n    return {\n        "module": "qseries_v2.oracle_adapters.independent.oad_061_independent_to_canonical_bridge",\n        "callable": "canonicalize_independent_observation",\n        "read_only": True,\n        "execution_authority": False,\n        "probability_enabled": False,\n    }\n'; S111='\nfrom __future__ import annotations\n\nfrom datetime import datetime, timezone\nfrom uuid import uuid4\n\nfrom .oad_108_official_mlb_source_adapter import fetch_mlb_schedule\nfrom .oad_109_official_nhl_source_adapter import fetch_nhl_schedule\nfrom .oad_110_authoritative_sports_canonical_bridge import (\n    canonicalize_authoritative_sports_observation,\n    bridge_contract_record,\n)\n\nREAD_ONLY = True\nEXECUTION_AUTHORITY = False\nPROBABILITY_ENABLED = False\n\ndef run_physical_gate(timeout_seconds=20):\n    today = datetime.now(timezone.utc).date().isoformat()\n    mlb = fetch_mlb_schedule(date=today, timeout_seconds=timeout_seconds)\n    nhl = fetch_nhl_schedule(date=today, timeout_seconds=timeout_seconds)\n    observations = tuple(mlb) + tuple(nhl)\n\n    batch_id = "oad111-" + uuid4().hex\n    canonical = tuple(\n        canonicalize_authoritative_sports_observation(o, batch_id)\n        for o in observations\n    )\n    bridge = bridge_contract_record()\n\n    return {\n        "read_only": True,\n        "execution_authority": False,\n        "probability_enabled": False,\n        "providers": tuple(sorted({o.provider for o in observations})),\n        "baseball_observations": len(mlb),\n        "hockey_observations": len(nhl),\n        "total_observations": len(observations),\n        "canonical_observations": len(canonical),\n        "bridge_module": bridge["module"],\n        "bridge_callable": bridge["callable"],\n        "observations": observations,\n        "canonical": canonical,\n    }\n'; ST110='\nimport unittest\nfrom qseries_v2.oracle_adapters.independent.oad_107_authoritative_sports_source_foundation import build_observation\nfrom qseries_v2.oracle_adapters.independent.oad_110_authoritative_sports_canonical_bridge import (\n    canonicalize_authoritative_sports_observation, bridge_contract_record\n)\n\nclass T(unittest.TestCase):\n    def test_exact_existing_bridge(self):\n        o = build_observation(\n            source_id="mlb:test:1", provider="statsapi.mlb.com", sport_family="baseball",\n            observation_type="official_game_schedule_state", subject="A at B",\n            observed_at="2026-08-28T12:00:00+00:00",\n            source_url="https://statsapi.mlb.com/api/v1/schedule?sportId=1",\n            payload={"gamePk": 1},\n        )\n        c = canonicalize_authoritative_sports_observation(o, "oad110-test")\n        r = bridge_contract_record()\n        print("[BRIDGE_MODULE]", r["module"])\n        print("[BRIDGE_CALLABLE]", r["callable"])\n        print("[CANONICAL_SOURCE_ID]", c.source_id)\n        self.assertEqual(r["callable"], "canonicalize_independent_observation")\n        self.assertEqual(c.source_id, "source.independent."+o.source_id)\n        self.assertFalse(r["execution_authority"])\n        self.assertFalse(r["probability_enabled"])\n\nif __name__ == "__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-110 exact repository bridge certified")\n'; ST111='\nimport unittest\nfrom unittest.mock import patch\nfrom qseries_v2.oracle_adapters.independent.oad_107_authoritative_sports_source_foundation import build_observation\nfrom qseries_v2.oracle_adapters.independent.oad_111_authoritative_sports_physical_acquisition_gate import run_physical_gate\n\ndef obs(source_id, provider, family):\n    return build_observation(\n        source_id=source_id, provider=provider, sport_family=family,\n        observation_type="official_game_schedule_state", subject="A at B",\n        observed_at="2026-08-28T12:00:00+00:00",\n        source_url="https://official.example/test", payload={"id": source_id},\n    )\n\nclass T(unittest.TestCase):\n    def test_gate_contract_without_network(self):\n        with patch("qseries_v2.oracle_adapters.independent.oad_111_authoritative_sports_physical_acquisition_gate.fetch_mlb_schedule",\n                   return_value=(obs("mlb:1","statsapi.mlb.com","baseball"),)), \\\n             patch("qseries_v2.oracle_adapters.independent.oad_111_authoritative_sports_physical_acquisition_gate.fetch_nhl_schedule",\n                   return_value=(obs("nhl:1","api-web.nhle.com","hockey"),)):\n            r=run_physical_gate(timeout_seconds=1)\n        print("[TOTAL_OBSERVATIONS]",r["total_observations"])\n        print("[CANONICAL_OBSERVATIONS]",r["canonical_observations"])\n        print("[BRIDGE_MODULE]",r["bridge_module"])\n        print("[BRIDGE_CALLABLE]",r["bridge_callable"])\n        self.assertEqual(r["total_observations"],2)\n        self.assertEqual(r["canonical_observations"],2)\n        self.assertTrue(r["read_only"])\n        self.assertFalse(r["execution_authority"])\n        self.assertFalse(r["probability_enabled"])\n\nif __name__ == "__main__":\n    x=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not x.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OAD-111 exact bridge integration certified")\n    print("[NOTE] production run_physical_gate remains physical MLB+NHL network acquisition")\n'

def main():
    print("="*112)
    print(" OAD-110/111 EXACT CURRENT-REPOSITORY REBUILD")
    print("="*112)
    print("[BOOT]",REVISION)
    for p in (M061,M107,M108,M109):
        if not p.is_file(): raise RuntimeError("Required current-repo dependency missing: "+str(p))
        print("[PASS] exact dependency:",p.name)

    # Verify the exact OAD-061 symbols from the current repository source without importing the broken package.
    tree=ast.parse(M061.read_text(encoding="utf-8"))
    names={n.name for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
    if "canonicalize_independent_observation" not in names:
        raise RuntimeError("Exact OAD-061 canonicalize_independent_observation contract missing")
    print("[PASS] exact OAD-061 canonical bridge symbol verified from source")

    targets=(M110,M111,T110,T111)
    old={p:(p.read_bytes() if p.exists() else None) for p in targets}
    try:
        # Replace both broken boundary files before importing the package.
        write(M110,S110); write(M111,S111); write(T110,ST110); write(T111,ST111)
        print("[PASS] OAD-110 and OAD-111 replaced before package import")

        for test in (T110,T111):
            proc=subprocess.run([sys.executable,str(test)],cwd=str(ROOT),text=True,capture_output=True)
            print(proc.stdout.rstrip())
            if proc.returncode:
                print(proc.stderr.rstrip())
                raise RuntimeError(test.name+" failed in installer self-test")
        print("[PASS] installer self-tested both modules in fresh Python processes")
        print("[PASS] no guessed bridge discovery remains")
        print("[PASS] read_only=TRUE probability_enabled=FALSE execution_authority=FALSE")
        print("[DONE] OAD-110/111 EXACT REPOSITORY REBUILD COMPLETE")
    except Exception:
        for p,data in old.items():
            if data is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(data)
        print("[ROLLBACK] previous OAD-110/111 boundary restored")
        raise

if __name__=="__main__":
    main()
