READ_ONLY=True;EXECUTION_AUTHORITY=False
def prediction_lines(p,entry_reference=None):
 return (
  "[ORACLE PREDICTION]",
  "Strategy: SOLANA_BUY_PRESSURE_V1",
  f"Token: {p.token_address}",
  f"Pair: {p.pair_address}",
  "Signal: BUY_PRESSURE",
  f"Frozen: {p.frozen_at}",
  f"Entry Reference: {entry_reference if entry_reference is not None else 'N/A'}",
  f"Horizon: {p.horizon_seconds}s",
  f"Target: +{p.target*100:.2f}%",
  f"Stop: -{p.stop*100:.2f}%",
  f"Assumed Friction: {p.friction_bps} bps",
  f"Prediction ID: {p.prediction_id}",
  f"Status: {p.state}",
  "Execution Authority: FALSE",
 )
def print_prediction(p,entry_reference=None,progress=print):
 for line in prediction_lines(p,entry_reference):progress(line)
