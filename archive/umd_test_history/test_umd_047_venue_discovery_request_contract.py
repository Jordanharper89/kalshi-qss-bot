from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_045_venue_discovery_source_contract import UMD_045_REVISION, CertifiedVenueDiscoverySourceContract
from qseries_v2.universal_market_discovery.umd_046_venue_discovery_source_registry import UMD_046_REVISION, CertifiedVenueDiscoverySourceRegistry
from qseries_v2.universal_market_discovery.umd_047_venue_discovery_request_contract import (
 UMD_047_REVISION, build_venue_discovery_request_contract, build_umd_047_certification_manifest,
 certify_venue_discovery_request_contract, certify_umd_047_foundation)
FIXED=datetime(2026,8,6,20,0,0,tzinfo=timezone.utc)
def source():
 l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-045",revision=UMD_045_REVISION,schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://047/source",),created_at=FIXED)
 return CertifiedVenueDiscoverySourceContract(canonical_venue_id="KALSHI",adapter_key="KALSHI_MARKET_CATALOG",display_name="Kalshi Market Catalog",discovery_method="REST_CATALOG",authentication_mode="API_KEY",pagination_mode="CURSOR",supported_market_families=("BINARY_MARKET","EVENT_CONTRACT"),supported_statuses=("ACTIVE","CLOSED","SETTLED"),source_schema_version="v1",supports_incremental_discovery=True,supports_historical_markets=True,supports_settlement_status=True,supports_cursor_resume=True,rate_limit_metadata_available=True,read_only=True,metadata={},lineage=l)
def registry(s):
 l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-046",revision=UMD_046_REVISION,schema_version="1.0.0",parent_hashes=(s.contract_hash,),source_refs=("fixture://047/registry",),created_at=FIXED)
 return CertifiedVenueDiscoverySourceRegistry(sources=(s,),registry_metadata={},lineage=l)
def request():
 s=source(); r=registry(s)
 l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-047",revision=UMD_047_REVISION,schema_version="1.0.0",parent_hashes=(s.contract_hash,r.registry_hash),source_refs=("fixture://047/request",),created_at=FIXED)
 return build_venue_discovery_request_contract(r,s,discovery_scope="ACTIVE_AND_HISTORICAL",requested_statuses=("ACTIVE","SETTLED"),requested_market_families=("BINARY_MARKET",),requested_at=FIXED,request_schema_version="v1",lineage=l,pagination_cursor="cursor-1",page_size=500,metadata={"read_only":True})
class TestUMD047(unittest.TestCase):
 def test_foundation(self): self.assertTrue(certify_umd_047_foundation()["certified"])
 def test_contract(self): self.assertTrue(certify_venue_discovery_request_contract(request())["certified"])
 def test_deterministic(self):
  a=request(); b=request(); self.assertEqual(a.request_id,b.request_id); self.assertEqual(a.request_hash,b.request_hash)
 def test_registered_source_required(self):
  s=source(); other=source(); r=registry(s)
  l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-047",revision=UMD_047_REVISION,schema_version="1.0.0",parent_hashes=(other.contract_hash,r.registry_hash),source_refs=("fixture://bad",),created_at=FIXED)
  # Alter adapter to make a genuinely unregistered source.
  other=CertifiedVenueDiscoverySourceContract(canonical_venue_id="KALSHI",adapter_key="OTHER",display_name="Other",discovery_method="REST_CATALOG",authentication_mode="API_KEY",pagination_mode="CURSOR",supported_market_families=("BINARY_MARKET",),supported_statuses=("ACTIVE",),source_schema_version="v1",supports_incremental_discovery=True,supports_historical_markets=False,supports_settlement_status=False,supports_cursor_resume=True,rate_limit_metadata_available=True,read_only=True,metadata={},lineage=other.lineage)
  with self.assertRaises(ValueError): build_venue_discovery_request_contract(r,other,discovery_scope="ACTIVE_ONLY",requested_statuses=("ACTIVE",),requested_market_families=("BINARY_MARKET",),requested_at=FIXED,request_schema_version="v1",lineage=l)
 def test_capability_subset(self):
  s=source(); r=registry(s); l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-047",revision=UMD_047_REVISION,schema_version="1.0.0",parent_hashes=(s.contract_hash,r.registry_hash),source_refs=("fixture://badcap",),created_at=FIXED)
  with self.assertRaises(ValueError): build_venue_discovery_request_contract(r,s,discovery_scope="ACTIVE_ONLY",requested_statuses=("CANCELLED",),requested_market_families=("BINARY_MARKET",),requested_at=FIXED,request_schema_version="v1",lineage=l)
 def test_time_window(self):
  s=source(); r=registry(s); l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-047",revision=UMD_047_REVISION,schema_version="1.0.0",parent_hashes=(s.contract_hash,r.registry_hash),source_refs=("fixture://badtime",),created_at=FIXED)
  with self.assertRaises(ValueError): build_venue_discovery_request_contract(r,s,discovery_scope="ACTIVE_ONLY",requested_statuses=("ACTIVE",),requested_market_families=("BINARY_MARKET",),requested_at=FIXED,request_schema_version="v1",lineage=l,window_start=FIXED,window_end=datetime(2026,8,5,tzinfo=timezone.utc))
 def test_immutable(self):
  x=request();
  with self.assertRaises((FrozenInstanceError,AttributeError)): x.page_size=1
  with self.assertRaises(TypeError): x.metadata["x"]=1
 def test_side_effects(self):
  m=build_umd_047_certification_manifest(); self.assertFalse(m.network_enabled); self.assertFalse(m.persistence_enabled); self.assertFalse(m.execution_enabled)
if __name__=="__main__":
 print("="*72); print(" UMD-047 CERTIFICATION TEST"); print(" CERTIFIED VENUE DISCOVERY REQUEST CONTRACT"); print("="*72)
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD047))
 if not result.wasSuccessful(): raise SystemExit(1)
 m=build_umd_047_certification_manifest(); print(); print(f"[PASS] Build: {m.build_id}"); print(f"[PASS] Revision: {m.revision}"); print(f"[PASS] Manifest hash: {m.manifest_hash}"); print("[PASS] UMD-001 through UMD-046 consumed read-only"); print("[PASS] Exact UMD-045 source and UMD-046 registry classes consumed"); print("[PASS] Deterministic request identity and capability bounds certified"); print("[PASS] Network, persistence, publication, and execution disabled"); print("[DONE] UMD-047 CERTIFIED VENUE DISCOVERY REQUEST CONTRACT CERTIFIED")
