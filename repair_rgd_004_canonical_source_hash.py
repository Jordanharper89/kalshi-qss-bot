from pathlib import Path


ROOT = Path.cwd()

MODULE = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "market_regime_discovery_model"
    / "market_regime_pipeline_gate.py"
)

TEST = (
    ROOT
    / "test_rgd_004_market_regime_pipeline_gate.py"
)


if not MODULE.exists():
    raise FileNotFoundError(
        f"Missing module: {MODULE}"
    )

if not TEST.exists():
    raise FileNotFoundError(
        f"Missing test: {TEST}"
    )


module_text = MODULE.read_text(
    encoding="utf-8"
)

test_text = TEST.read_text(
    encoding="utf-8"
)


CANONICAL_HELPER = r'''

def _canonical_source_payload(
    source_result: Any,
) -> Dict[str, Any]:
    if (
        hasattr(source_result, "as_dict")
        and callable(source_result.as_dict)
    ):
        raw_payload = source_result.as_dict()
    elif isinstance(source_result, Mapping):
        raw_payload = dict(source_result)
    else:
        raw_payload = _stable_value(
            source_result
        )

    if isinstance(raw_payload, Mapping):
        payload = {
            str(key): _stable_value(value)
            for key, value in sorted(
                raw_payload.items(),
                key=lambda item: str(
                    item[0]
                ),
            )
        }
    else:
        payload = {
            "value": _stable_value(
                raw_payload
            )
        }

    records = _extract_records(
        source_result
    )

    canonical_records = tuple(
        sorted(
            (
                _stable_value(record)
                for record in records
            ),
            key=repr,
        )
    )

    record_keys = (
        "records",
        "signals",
        "items",
        "observations",
        "source_records",
    )

    replaced = False

    for key in record_keys:
        if key in payload:
            payload[key] = canonical_records
            replaced = True
            break

    if records and not replaced:
        payload["records"] = (
            canonical_records
        )

    return {
        str(key): _stable_value(value)
        for key, value in sorted(
            payload.items(),
            key=lambda item: str(
                item[0]
            ),
        )
    }
'''


HELPER_MARKER = r'''
def _resolve_observed_at(
'''


if (
    "def _canonical_source_payload("
    not in module_text
):
    if HELPER_MARKER not in module_text:
        raise RuntimeError(
            "Could not find the RGD-004 "
            "helper insertion point."
        )

    module_text = module_text.replace(
        HELPER_MARKER,
        CANONICAL_HELPER
        + "\n\n"
        + HELPER_MARKER,
        1,
    )


OLD_SOURCE_PAYLOAD = r'''
    source_payload = (
        source_result.as_dict()
        if hasattr(
            source_result,
            "as_dict",
        )
        and callable(
            source_result.as_dict
        )
        else source_result
    )
'''


NEW_SOURCE_PAYLOAD = r'''
    source_payload = (
        _canonical_source_payload(
            source_result
        )
    )
'''


if OLD_SOURCE_PAYLOAD in module_text:
    module_text = module_text.replace(
        OLD_SOURCE_PAYLOAD,
        NEW_SOURCE_PAYLOAD,
        1,
    )
elif NEW_SOURCE_PAYLOAD not in module_text:
    raise RuntimeError(
        "Could not locate the RGD-004 "
        "source payload block."
    )


OLD_TEST_BLOCK = r'''
    assert (
        result_1.opportunity_count
        == result_2.opportunity_count
    )


def test_pipeline_gate_validation():
'''


NEW_TEST_BLOCK = r'''
    assert (
        result_1.opportunity_count
        == result_2.opportunity_count
    )

    assert (
        result_1.source_hash
        == result_2.source_hash
    )

    assert (
        result_1.gate_hash
        == result_2.gate_hash
    )

    assert result_1 == result_2


def test_pipeline_gate_validation():
'''


if OLD_TEST_BLOCK in test_text:
    test_text = test_text.replace(
        OLD_TEST_BLOCK,
        NEW_TEST_BLOCK,
        1,
    )
else:
    test_start = test_text.find(
        "def test_pipeline_gate_input_order_independent"
    )

    test_end = test_text.find(
        "def test_pipeline_gate_validation",
        test_start,
    )

    if test_start == -1 or test_end == -1:
        raise RuntimeError(
            "Could not locate the RGD-004 "
            "input-order test."
        )

    test_section = test_text[
        test_start:test_end
    ]

    if (
        "result_1.gate_hash"
        not in test_section
    ):
        raise RuntimeError(
            "Could not safely update the "
            "RGD-004 input-order test."
        )


MODULE.write_text(
    module_text,
    encoding="utf-8",
)

TEST.write_text(
    test_text,
    encoding="utf-8",
)


print("========================================")
print(" RGD-004 CANONICAL HASH REPAIR")
print(" Market Regime Pipeline Gate")
print("========================================")
print(f"[OK] Updated {MODULE}")
print(f"[OK] Updated {TEST}")
print()
print("[DONE] RGD-004 source hashing repaired")
print()
print("Run:")
print(
    "py "
    "test_rgd_004_market_regime_"
    "pipeline_gate.py"
)
print(
    "py "
    "test_rgd_005_market_regime_"
    "registry_bridge.py"
)
print(
    "py "
    "test_rgd_006_market_regime_"
    "pipeline_bridge.py"
)
print(
    "py "
    "test_rgd_007_market_regime_"
    "oos_runtime_gate.py"
)
print(
    "py "
    "test_rgd_008_market_regime_"
    "replay_ledger.py"
)
print(
    "py "
    "test_rgd_009_market_regime_"
    "subsystem_integration_gate.py"
)