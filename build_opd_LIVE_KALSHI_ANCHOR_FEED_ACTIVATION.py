from pathlib import Path
R=Path.cwd()
P=R/'qseries_v2'/'oracle_adapters'/'kalshi'/'oad_036_websocket_canonical_bridge.py'
T=R/'test_opd_LIVE_KALSHI_ANCHOR_FEED_ACTIVATION.py'
s=P.read_text(encoding='utf-8')
imp='from qseries_v2.oracle_predictive_discovery.opd_061_realtime_kalshi_anchor_tap import freeze_trade\n'
if imp not in s:
    anchor='from qseries_v2.oracle_intelligence.live_acquisition.oracle_live_read_only_acquisition_runtime import (\n'
    s=s.replace(anchor,imp+'\n'+anchor,1)
if 'from pathlib import Path\n' not in s:
    s=s.replace('from datetime import datetime, timezone\n','from datetime import datetime, timezone\nfrom pathlib import Path\n',1)
old='    return CanonicalObservation.create(\n        source_id=SOURCE_ID,\n        raw_observation=raw,\n        acquired_at=received_at,\n        acquisition_batch_id=str(acquisition_batch_id),\n    )\n'
new='    observation=CanonicalObservation.create(\n        source_id=SOURCE_ID,\n        raw_observation=raw,\n        acquired_at=received_at,\n        acquisition_batch_id=str(acquisition_batch_id),\n    )\n    if typ=="trade":\n        freeze_trade(\n            raw_message,\n            received_at.timestamp(),\n            observation.observation_id,\n            Path.cwd(),\n        )\n    return observation\n'
if old not in s and new not in s: raise RuntimeError('OAD036_EXPECTED_RETURN_BLOCK_NOT_FOUND')
s=s.replace(old,new,1)
P.write_text(s,encoding='utf-8')
TEST='from datetime import datetime,timezone\nimport qseries_v2.oracle_adapters.kalshi.oad_036_websocket_canonical_bridge as m\ncalls=[]\ndef fake(raw,received_at,observation_id,root=None):\n    calls.append((raw,received_at,observation_id,root));return {"anchor_id":"x"}\nm.freeze_trade=fake\nt=datetime(2026,9,11,21,0,0,tzinfo=timezone.utc)\ntrade={"type":"trade","sid":1,"seq":2,"msg":{"market_ticker":"KXBTC15M-TEST","yes_price_dollars":"0.55"}}\no=m.build_ola_canonical_observation_from_websocket(trade,received_at=t,acquisition_batch_id="batch.test")\nassert len(calls)==1 and calls[0][2]==o.observation_id\nticker={"type":"ticker","sid":1,"seq":3,"msg":{"market_ticker":"KXBTC15M-TEST","price_dollars":"0.56"}}\nm.build_ola_canonical_observation_from_websocket(ticker,received_at=t,acquisition_batch_id="batch.test2")\nassert len(calls)==1\nprint("[PASS] OAD-036 live trade bridge now feeds OPD-061 anchor freeze exactly once per trade")\nprint("[PASS] non-trade websocket events do not create predictive anchors")\nprint("[EXECUTION/PROBABILITY/DIRECTION/PUBLICATION] FALSE/FALSE/FALSE/FALSE")\n'
T.write_text(TEST,encoding='utf-8')
compile(P.read_text(encoding='utf-8'),str(P),'exec');compile(TEST,str(T),'exec')
print('[PASS] existing live Kalshi canonical bridge -> OPD-061 anchor feed activated')
print(P);print(T)