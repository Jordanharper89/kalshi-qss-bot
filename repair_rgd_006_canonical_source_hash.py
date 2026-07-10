from pathlib import Path


ROOT = Path.cwd()

MODULE = (
    ROOT
    / "qseries_v2"
    / "oracle_intelligence"
    / "market_regime_discovery_model"
    / "market_regime_pipeline_bridge.py"
)

TEST = (
    ROOT
    / "test_rgd_006_market_regime_pipeline_bridge.py"
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
    try:
        payload = _artifact_dict(
            source_result
        )
    except TypeError:
        payload = {
            "value": _stable_value(
                source_result
            )
        }

    records = _extract_records(
        source_result
    )

    if records:
        canonical_records = tuple(
            sorted(
                (
                    _stable_value(record)
                    for record in records
                ),
                key=repr,
            )
        )

        for key in (
            "records",
            "signals",
            "items",
            "observations",
            "source_records",
        ):
            if key in payload:
                payload[key] = (
                    canonical_records
                )
                break

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
def _normalize_metadata(
'''


if (
    "def _canonical_source_payload("
    not in module_text
):
    if HELPER_MARKER not in module_text:
        raise RuntimeError(
            "Could not find the RGD-006 "
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
    try:
        source_payload = _artifact_dict(
            source_result
        )
    except TypeError:
        source_payload = _stable_value(
            source_result
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
        "Could not locate the RGD-006 "
        "source payload hashing block."
    )


OLD_TEST_BLOCK = r'''
    assert result_1.status == result_2.status


def test_pipeline_bridge_metadata():
'''


NEW_TEST_BLOCK = r'''
    assert result_1.status == result_2.status

    assert (
        result_1.pipeline_hash
        == result_2.pipeline_hash
    )


def test_pipeline_bridge_metadata():
'''


if OLD_TEST_BLOCK in test_text:
    test_text = test_text.replace(
        OLD_TEST_BLOCK,
        NEW_TEST_BLOCK,
        1,
    )
elif (
    "result_1.pipeline_hash"
    not in test_text[
        test_text.find(
            "def test_pipeline_bridge_input_order_independent"
        ):
        test_text.find(
            "def test_pipeline_bridge_metadata"
        )
    ]
):
    raise RuntimeError(
        "Could not update the RGD-006 "
        "input-order test."
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
print(" RGD-006 CANONICAL HASH REPAIR")
print(" Market Regime Pipeline Bridge")
print("========================================")
print(f"[OK] Updated {MODULE}")
print(f"[OK] Updated {TEST}")
print()
print("[DONE] RGD-006 source hashing repaired")
print()
print("Run:")
print(
    "py "
    "test_rgd_006_market_regime_"
    "pipeline_bridge.py"
)
print(
    "py "
    "test_rgd_009_market_regime_"
    "subsystem_integration_gate.py"
)