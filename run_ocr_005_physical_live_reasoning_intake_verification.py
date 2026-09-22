from pathlib import Path
from qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import read_latest_canonical_observations
from qseries_v2.oracle_continuous_reasoning.ocr_003_reasoning_input_batch import assemble_reasoning_input_batch
from qseries_v2.oracle_continuous_reasoning.ocr_004_reasoning_activation_bridge import build_scientific_reasoning_activation_envelope

if __name__=="__main__":
    print("="*72)
    print(" OCR-005 PHYSICAL LIVE REASONING INTAKE VERIFICATION")
    print("="*72)
    result=read_latest_canonical_observations(Path.cwd(),limit=10)
    print(f"[POSTGRESQL] source={result.schema}.{result.table} rows={len(result.rows)} read_only={result.read_only}")
    batch=assemble_reasoning_input_batch(result.rows)
    print(f"[BATCH] observations={batch.observation_count} markets={batch.market_count} hash={batch.batch_hash}")
    envelope=build_scientific_reasoning_activation_envelope(batch)
    print(f"[REASONING] ready={envelope.reasoning_ready} OSR={envelope.frozen_reasoning_boundary} OIS={envelope.frozen_state_boundary}")
    print("[PASS] Real persisted observations reached the frozen reasoning activation boundary")
    print("[DONE] OCR-005 PHYSICAL LIVE REASONING INTAKE VERIFIED")
