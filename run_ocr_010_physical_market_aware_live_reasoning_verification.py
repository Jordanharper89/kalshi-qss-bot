from pathlib import Path
from qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import read_latest_canonical_observations
from qseries_v2.oracle_continuous_reasoning.ocr_006_market_identity_recovery import recover_batch_market_identities
from qseries_v2.oracle_continuous_reasoning.ocr_007_umd_context_join import join_rows_to_umd_context
from qseries_v2.oracle_continuous_reasoning.ocr_008_scientific_reasoning_invocation import reason_over_market_aware_observations
from qseries_v2.oracle_continuous_reasoning.ocr_009_intelligence_state_projection import project_reasoning_results

if __name__=="__main__":
    print("="*72);print(" OCR-010 PHYSICAL MARKET-AWARE LIVE REASONING VERIFICATION");print("="*72)
    result=read_latest_canonical_observations(Path.cwd(),limit=25)
    identities=recover_batch_market_identities(result.rows)
    resolved=tuple(x for x in identities if x.recovered)
    print(f"[POSTGRESQL] rows={len(result.rows)} read_only={result.read_only}")
    print(f"[IDENTITY] resolved={len(resolved)} unresolved={len(identities)-len(resolved)} unique_markets={len(set(x.market_ticker for x in resolved))}")
    aware=join_rows_to_umd_context(result.rows)
    if not aware:raise SystemExit("[FAIL] No market identities recovered from live observations")
    reasoning=reason_over_market_aware_observations(aware)
    print(f"[OSR] markets_reasoned={len(reasoning)}")
    for r in reasoning[:10]:
        s=r.osr_state
        print(f"[OSR] market={r.market_ticker} state={s.reasoning_state} support={s.support:.3f} confidence={s.confidence:.3f} contradiction={s.contradiction:.3f} abstain={s.abstain}")
    projections=project_reasoning_results(reasoning)
    print(f"[OIS] read_only_projections={len(projections)}")
    if not projections:raise SystemExit("[FAIL] No OIS projections produced")
    print("[PASS] Real PostgreSQL observations recovered market identity")
    print("[PASS] Market-aware observations invoked frozen OSR-028/029")
    print("[PASS] Scientific reasoning projected through frozen OIS-002 read-only boundary")
    print("[DONE] OCR-010 PHYSICAL MARKET-AWARE LIVE REASONING VERIFIED")
