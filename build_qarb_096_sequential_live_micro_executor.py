from pathlib import Path
import py_compile

R = Path.cwd()

Q96 = R / (
    "qseries_v2/solana_live_execution/"
    "qarb_096_sequential_live_micro_executor.py"
)

TEST = R / "test_qarb_096_sequential_live_micro_executor.py"

for p in (Q96, TEST):
    if not p.is_file():
        raise SystemExit("[FAIL] missing: " + str(p))

src = Q96.read_text(encoding="utf-8")


# ============================================================
# FIX 1:
# Raw Solana JSON-RPC has no getAddressLookupTable method.
#
# Use getAccountInfo(address) to prove the ALT account exists.
# compile_v0 will resolve/use the actual ALT during v0 compile.
# ============================================================

old_saved = '''def _saved_alt(root,token):
    state=_load_alt_state(
        root
    )

    row=state[
        "tables"
    ].get(
        _alt_key(token)
    )

    if not isinstance(row,dict):
        return None

    address=row.get(
        "address"
    )

    if not address:
        return None

    try:
        got=_rpc(
            "getAddressLookupTable",
            [address]
        )

        if not isinstance(got,dict):
            return None

        if got.get("value") is None:
            return None

    except Exception:
        return None

    return address
'''

new_saved = '''def _saved_alt(root,token):
    state=_load_alt_state(
        root
    )

    row=state[
        "tables"
    ].get(
        _alt_key(token)
    )

    if not isinstance(row,dict):
        return None

    address=row.get(
        "address"
    )

    if not address:
        return None

    try:
        got=_rpc(
            "getAccountInfo",
            [
                address,
                {
                    "encoding":"base64",
                    "commitment":"confirmed"
                }
            ]
        )

        if not isinstance(got,dict):
            return None

        value=got.get("value")

        if not isinstance(value,dict):
            return None

        if not value.get("data"):
            return None

    except Exception:
        return None

    return address
'''

if old_saved not in src:
    raise SystemExit(
        "[FAIL] _saved_alt seam changed"
    )

src = src.replace(
    old_saved,
    new_saved,
    1
)


# ============================================================
# FIX 2:
# ALT activation loop also used the nonexistent raw RPC.
#
# A successfully confirmed create/extend transaction is enough
# to persist the table; then wait until:
#   - cluster slot advances beyond setup transaction slot
#   - getAccountInfo confirms the ALT account exists
#
# Use the ACTUAL confirmed tx slot, not recentSlot.
# ============================================================

old_activation = '''    alt=setup[
        "lookupTable"
    ]

    # ALT cannot be used in the exact slot in which
    # it was created/extended. Wait for the next slot.
    while time.monotonic()<deadline:

        try:
            slot=int(
                _rpc(
                    "getSlot",
                    [{
                        "commitment":
                            "confirmed"
                    }]
                )
            )

            got=_rpc(
                "getAddressLookupTable",
                [alt]
            )

            if (
                slot
                >int(
                    setup[
                        "recentSlot"
                    ]
                )
                and isinstance(
                    got,
                    dict
                )
                and got.get(
                    "value"
                ) is not None
            ):
                return {
                    "ok":True,

                    "created":True,

                    "address":
                        alt,

                    "signature":
                        signature,

                    "wallet_delta_lamports":
                        after-before,

                    "addresses":
                        len(
                            setup[
                                "addresses"
                            ]
                        ),
                }

        except Exception:
            pass

        time.sleep(0.4)

    return {
        "ok":False,

        "reason":
            "ALT_ACTIVATION_TIMEOUT",

        "hard_stop":
            True,

        "signature":
            signature,
    }
'''

new_activation = '''    alt=setup[
        "lookupTable"
    ]

    setup_slot=int(
        tx.get(
            "slot",
            0
        )
        or 0
    )

    # Address lookup tables become usable after the slot in
    # which they were created/extended. The setup transaction
    # has already been confirmed above.
    while time.monotonic()<deadline:

        try:
            slot=int(
                _rpc(
                    "getSlot",
                    [{
                        "commitment":
                            "confirmed"
                    }]
                )
            )

            got=_rpc(
                "getAccountInfo",
                [
                    alt,
                    {
                        "encoding":"base64",
                        "commitment":"confirmed"
                    }
                ]
            )

            value=(
                got.get("value")
                if isinstance(got,dict)
                else None
            )

            if (
                setup_slot>0
                and slot>setup_slot
                and isinstance(
                    value,
                    dict
                )
                and value.get("data")
            ):
                return {
                    "ok":True,

                    "created":True,

                    "address":
                        alt,

                    "signature":
                        signature,

                    "wallet_delta_lamports":
                        after-before,

                    "addresses":
                        len(
                            setup[
                                "addresses"
                            ]
                        ),
                }

        except Exception:
            pass

        time.sleep(0.4)

    # The setup transaction was confirmed already. If the ALT
    # account itself now exists, preserve it and allow the NEXT
    # scan/session to reuse it instead of blindly creating a
    # duplicate table.
    try:
        got=_rpc(
            "getAccountInfo",
            [
                alt,
                {
                    "encoding":"base64",
                    "commitment":"confirmed"
                }
            ]
        )

        if (
            isinstance(got,dict)
            and isinstance(
                got.get("value"),
                dict
            )
        ):
            return {
                "ok":True,

                "created":True,

                "address":
                    alt,

                "signature":
                    signature,

                "wallet_delta_lamports":
                    after-before,

                "addresses":
                    len(
                        setup[
                            "addresses"
                        ]
                    ),

                "activation_deferred":
                    True,
            }

    except Exception:
        pass

    return {
        "ok":False,

        "reason":
            "ALT_ACCOUNT_NOT_VISIBLE",

        "hard_stop":
            True,

        "signature":
            signature,
    }
'''

if old_activation not in src:
    raise SystemExit(
        "[FAIL] ALT activation seam changed"
    )

src = src.replace(
    old_activation,
    new_activation,
    1
)


# ============================================================
# FIX 3:
# Final print had 3 placeholders but 4 arguments.
# ============================================================

old_complete = '''    print(
        "[QARB-096] COMPLETE "
        "sends=%d confirmed=%d "
        "pre_send_rejected=%d "
        "automatic_session=TRUE"%(
            sends,
            confirmed,
            rejected,
            skipped,
        ),
        flush=True
    )
'''

new_complete = '''    print(
        "[QARB-096] COMPLETE "
        "sends=%d confirmed=%d "
        "pre_send_rejected=%d "
        "skipped=%d "
        "automatic_session=TRUE"%(
            sends,
            confirmed,
            rejected,
            skipped,
        ),
        flush=True
    )
'''

if old_complete not in src:
    raise SystemExit(
        "[FAIL] COMPLETE print seam changed"
    )

src = src.replace(
    old_complete,
    new_complete,
    1
)


# ============================================================
# FIX 4:
# If an ALT already exists from the failed-looking prior run,
# make the next scan visibly reuse it.
# ============================================================

old_apply = '''    if not alt:
        return route

    route=dict(route)

    route["base_alts"]=[
        alt
    ]
'''

new_apply = '''    if not alt:
        return route

    print(
        "[ALT_REUSE] token=%s address=%s"%(
            str(token)[:10],
            alt,
        ),
        flush=True
    )

    route=dict(route)

    route["base_alts"]=[
        alt
    ]
'''

if old_apply not in src:
    raise SystemExit(
        "[FAIL] ALT reuse seam changed"
    )

src = src.replace(
    old_apply,
    new_apply,
    1
)


Q96.write_text(
    src,
    encoding="utf-8"
)


# ============================================================
# TEST EXTENSION
# ============================================================

tests = TEST.read_text(
    encoding="utf-8"
)

needle = '''if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
'''

if needle not in tests:
    raise SystemExit(
        "[FAIL] test insertion seam missing"
    )

extra = r'''

    def test_alt_raw_rpc_uses_get_account_info(self):
        s=inspect.getsource(
            q._saved_alt
        )

        self.assertIn(
            '"getAccountInfo"',
            s
        )

        self.assertNotIn(
            '"getAddressLookupTable"',
            s
        )


    def test_alt_activation_uses_confirmed_tx_slot(self):
        s=inspect.getsource(
            q.bootstrap_micro_alt
        )

        self.assertIn(
            'tx.get(',
            s
        )

        self.assertIn(
            '"slot"',
            s
        )

        self.assertIn(
            '"getAccountInfo"',
            s
        )


    def test_alt_activation_no_fake_raw_rpc(self):
        s=inspect.getsource(
            q.bootstrap_micro_alt
        )

        self.assertNotIn(
            '"getAddressLookupTable"',
            s
        )


    def test_complete_print_four_placeholders(self):
        s=inspect.getsource(
            q.run
        )

        self.assertIn(
            "skipped=%d",
            s
        )


    def test_alt_reuse_visible(self):
        s=inspect.getsource(
            q._apply_saved_alt
        )

        self.assertIn(
            "[ALT_REUSE]",
            s
        )

'''

tests = tests.replace(
    needle,
    extra + "\n" + needle,
    1
)

TEST.write_text(
    tests,
    encoding="utf-8"
)

for p in (Q96, TEST):
    py_compile.compile(
        str(p),
        doraise=True
    )


check = Q96.read_text(
    encoding="utf-8"
)

assert '"getAddressLookupTable"' not in check
assert '"getAccountInfo"' in check
assert "[ALT_REUSE]" in check
assert "skipped=%d" in check
assert "MICRO_LAMPORTS=1_000_000" in check


print(
    "[PASS] QARB-096 ALT activation + completion repair installed"
)

print(
    "[ALT] fake raw getAddressLookupTable RPC removed"
)

print(
    "[ALT] confirmed account verified with getAccountInfo"
)

print(
    "[ALT] activation uses actual confirmed setup transaction slot"
)

print(
    "[ALT] existing table can be reused instead of recreated"
)

print(
    "[OUTPUT] COMPLETE formatting crash repaired"
)

print(
    "[CAP] exact 0.001 SOL unchanged"
)

print(
    "[PRESERVE] production 0.28/1.4 SOL sizes unchanged"
)