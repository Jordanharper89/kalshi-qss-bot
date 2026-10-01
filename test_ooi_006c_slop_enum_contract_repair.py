import copy
import importlib
import json
from types import SimpleNamespace

MODULE = "qseries_v2.oracle_strategy_intelligence.oracle_opportunity_intelligence.ooi_006_slop_universal_opportunity_materializer"
CANONICAL = "qseries_v2.oracle_intelligence.universal_opportunity_model.universal_opportunity"

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def main():
    m = importlib.import_module(MODULE)
    c = importlib.import_module(CANONICAL)
    require(m.EXECUTION_AUTHORITY is False, 'execution authority changed')
    source = SimpleNamespace(prediction_id='P1', token_address='T1',
        pair_address='PAIR1', frozen_at='2026-09-17T00:00:00Z',
        conditions={'order_flow': 'BUY_PRESSURE'}, horizon_seconds=60,
        target=.10, stop=-.05, friction_bps=200)
    original = copy.deepcopy(vars(source))
    a = m.materialize_slop(source)
    b = m.materialize_slop(copy.deepcopy(source))
    require(isinstance(a, c.UniversalOpportunity), 'not canonical UniversalOpportunity')
    for name, cls, member in (
        ('opportunity_type', c.OpportunityType, 'UNKNOWN'),
        ('direction', c.OpportunityDirection, 'BUY'),
        ('status', c.OpportunityStatus, 'NEW'),
        ('risk_level', c.RiskLevel, 'UNKNOWN')):
        value = getattr(a, name)
        require(isinstance(value, cls) and value is getattr(cls, member), name + ' enum mismatch')
    require(a.read_only is True, 'read_only changed')
    require(a.metadata['execution_authority'] is False, 'metadata authority changed')
    for name in ('frozen_at', 'conditions', 'horizon_seconds', 'target', 'stop', 'friction_bps'):
        require(a.metadata[name] == original[name], 'frozen thesis changed: ' + name)
    require('P1' in a.supporting_prediction_ids, 'prediction lineage missing')
    require(vars(source) == original, 'source mutated')
    fp = a.fingerprint()
    require(isinstance(fp, str) and bool(fp.strip()), 'empty/non-string fingerprint')
    require(fp == a.fingerprint() == b.fingerprint(), 'fingerprint is not repeatable')
    require(a.opportunity_id == b.opportunity_id, 'identity is not repeatable')
    encoded = a.to_dict()
    require(isinstance(encoded, dict), 'to_dict contract failed')
    json.dumps(encoded, sort_keys=True, allow_nan=False)
    require(a.metadata['conditions']['order_flow'] == 'BUY_PRESSURE', 'BUY_PRESSURE lost')
    print('[PASS] canonical enums and direct fingerprint() certification')
    print('[PASS] deterministic identity, serialization, source immutability, prediction lineage')
    print('[PASS] frozen BUY_PRESSURE / 60 seconds / +10% / -5% / 200 bps')
    print('[PASS] OOI-006C read_only=True execution_authority=FALSE')

if __name__ == '__main__':
    main()
