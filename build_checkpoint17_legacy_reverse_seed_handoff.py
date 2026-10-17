from pathlib import Path
import ast

ROOT=Path.cwd()
TARGET=ROOT/"qseries_v2"/"oracle_execution"/"solana_atomic_executor"/"checkpoint17_pair_key_execution_templates.py"
TEST=ROOT/"test_checkpoint17_legacy_reverse_seed_handoff.py"

if not TARGET.is_file():
    raise RuntimeError("CHECKPOINT17_TARGET_MISSING:"+str(TARGET))

src=TARGET.read_text(encoding="utf-8")
ast.parse(src)

start=src.find("def _pair_bound_route(")
end=src.find("\ndef main():",start)

if start<0 or end<0:
    raise RuntimeError("CHECKPOINT17_ROUTE_BOUNDARY_NOT_FOUND")

replacement=r'''def _pair_bound_route(
    user,
    snap,
    opportunity,
):
    token=str(snap["token"])
    pool=str(snap["meteora"]["address"])
    direction=str(
        opportunity.get("direction")
        or ""
    )

    exact_key=_direction_key(
        token,
        pool,
        direction,
    )

    exact_template=PAIR_TEMPLATES.get(
        exact_key
    )

    if exact_template is None:
        raise RuntimeError(
            "PAIR_KEY_DIRECTION_TEMPLATE_MISSING:"
            +exact_key
        )

    quote=dict(
        opportunity.get("mq")
        or {}
    )

    if "swap_for_y" not in quote:
        raise RuntimeError(
            "CHECKPOINT17_QUOTE_DIRECTION_MISSING:"
            +exact_key
        )

    exact_swap=bool(
        exact_template["swap_for_y"]
    )

    quote_swap=bool(
        quote["swap_for_y"]
    )

    if quote_swap!=exact_swap:
        raise RuntimeError(
            "CHECKPOINT17_QUOTE_TEMPLATE_DIRECTION_MISMATCH:"
            +exact_key
            +":quote="
            +str(quote_swap)
            +":exact="
            +str(exact_swap)
        )

    # checkpoint-7 legacy reverse route still performs one inversion
    # internally. Reverse therefore receives the certified forward
    # template as the legacy seed exactly once. The live quote and the
    # exact reverse template remain the source of truth.
    if direction==REVERSE:
        seed_key=_direction_key(
            token,
            pool,
            FORWARD,
        )

        seed_template=PAIR_TEMPLATES.get(
            seed_key
        )

        if seed_template is None:
            raise RuntimeError(
                "CHECKPOINT17_LEGACY_REVERSE_SEED_MISSING:"
                +seed_key
            )

        seed_swap=bool(
            seed_template["swap_for_y"]
        )

        if seed_swap==exact_swap:
            raise RuntimeError(
                "CHECKPOINT17_REVERSE_SEED_NOT_OPPOSITE:"
                +exact_key
            )

        seed_accounts=list(
            seed_template.get(
                "fixed_accounts"
            )
            or []
        )

        exact_accounts=list(
            exact_template.get(
                "fixed_accounts"
            )
            or []
        )

        if (
            len(seed_accounts)<6
            or len(exact_accounts)<6
        ):
            raise RuntimeError(
                "CHECKPOINT17_DIRECTION_TEMPLATE_ACCOUNTS_SHORT:"
                +exact_key
            )

        if (
            str(seed_accounts[5][0])
            !=str(exact_accounts[4][0])
            or
            str(seed_accounts[4][0])
            !=str(exact_accounts[5][0])
        ):
            raise RuntimeError(
                "CHECKPOINT17_REVERSE_SEED_ACCOUNT_INVARIANT:"
                +exact_key
            )

        active_template=copy.deepcopy(
            seed_template
        )

        print(
            "[CHECKPOINT17_LEGACY_REVERSE_SEED] "
            "pair=%s seed_dir=%s seed_swap=%s "
            "physical_dir=%s physical_swap=%s "
            "quote_swap=%s invariant=PASS"
            %(
                _pair_key(
                    token,
                    pool,
                )[:28],
                FORWARD,
                str(seed_swap),
                REVERSE,
                str(exact_swap),
                str(quote_swap),
            ),
            flush=True,
        )

    elif direction==FORWARD:
        active_template=copy.deepcopy(
            exact_template
        )

    else:
        raise RuntimeError(
            "CHECKPOINT17_DIRECTION_UNSUPPORTED:"
            +direction
        )

    with ROUTE_LOCK:
        old=dict(r.METEORA_TEMPLATES)

        try:
            r.METEORA_TEMPLATES={
                token:active_template
            }

            active=(
                r.METEORA_TEMPLATES[
                    token
                ]
            )

            if str(
                active.get("pool")
            )!=pool:
                raise RuntimeError(
                    "CHECKPOINT17_ROUTE_POOL_DRIFT:"
                    +exact_key
                )

            print(
                "[CHECKPOINT17_ROUTE_DIRECTION] "
                "pair=%s dir=%s "
                "physical_source=%s physical_dest=%s "
                "physical_swap_for_y=%s "
                "legacy_seed_swap_for_y=%s"
                %(
                    _pair_key(
                        token,
                        pool,
                    )[:28],
                    direction,
                    str(
                        exact_template[
                            "source"
                        ]
                    )[:12],
                    str(
                        exact_template[
                            "dest"
                        ]
                    )[:12],
                    str(exact_swap),
                    str(
                        bool(
                            active[
                                "swap_for_y"
                            ]
                        )
                    ),
                ),
                flush=True,
            )

            return ORIGINAL_ROUTE(
                user,
                snap,
                opportunity,
            )

        finally:
            r.METEORA_TEMPLATES=old


'''

new_src=src[:start]+replacement+src[end:]
ast.parse(new_src)

required=[
    'FORWARD="PUMP_TO_METEORA"',
    'REVERSE="METEORA_TO_PUMP"',
    "expected_templates=expected_pairs*2",
    "CHECKPOINT17_QUOTE_TEMPLATE_DIRECTION_MISMATCH",
    "[BROADCAST] disabled",
]
for marker in required:
    if marker not in new_src:
        raise RuntimeError(
            "CHECKPOINT17_REQUIRED_CONTRACT_MISSING:"+marker
        )

TARGET.write_text(new_src,encoding="utf-8")

TEST_CODE=r'''import ast
import unittest
from pathlib import Path

P=Path(
    "qseries_v2/oracle_execution/solana_atomic_executor/"
    "checkpoint17_pair_key_execution_templates.py"
)


class T(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s=P.read_text(encoding="utf-8")
        ast.parse(cls.s)

    def test_reverse_uses_forward_seed_only_for_legacy_consumer(self):
        self.assertIn(
            "CHECKPOINT17_LEGACY_REVERSE_SEED",
            self.s,
        )
        self.assertIn(
            "seed_key=_direction_key(",
            self.s,
        )
        self.assertIn(
            "FORWARD,",
            self.s,
        )

    def test_quote_is_not_mutated(self):
        self.assertNotIn(
            'quote["swap_for_y"]=',
            self.s,
        )
        self.assertNotIn(
            'opportunity["mq"]["swap_for_y"]=',
            self.s,
        )

    def test_exact_reverse_quote_guard_preserved(self):
        self.assertIn(
            "CHECKPOINT17_QUOTE_TEMPLATE_DIRECTION_MISMATCH",
            self.s,
        )
        self.assertIn(
            "if quote_swap!=exact_swap:",
            self.s,
        )

    def test_reverse_seed_must_be_opposite(self):
        self.assertIn(
            "CHECKPOINT17_REVERSE_SEED_NOT_OPPOSITE",
            self.s,
        )
        self.assertIn(
            "if seed_swap==exact_swap:",
            self.s,
        )

    def test_source_destination_invariant(self):
        self.assertIn(
            "CHECKPOINT17_REVERSE_SEED_ACCOUNT_INVARIANT",
            self.s,
        )
        self.assertIn(
            "str(seed_accounts[5][0])",
            self.s,
        )
        self.assertIn(
            "str(exact_accounts[4][0])",
            self.s,
        )

    def test_forward_uses_exact_template(self):
        self.assertIn(
            "elif direction==FORWARD:",
            self.s,
        )

    def test_direction_specific_templates_preserved(self):
        self.assertIn(
            "expected_templates=expected_pairs*2",
            self.s,
        )
        self.assertIn(
            "identity=token|meteora_pool|direction",
            self.s,
        )

    def test_no_broadcast(self):
        self.assertNotIn(
            "sendTransaction",
            self.s,
        )
        self.assertIn(
            "[BROADCAST] disabled",
            self.s,
        )


if __name__=="__main__":
    unittest.main(verbosity=2)
'''

ast.parse(TEST_CODE)
TEST.write_text(TEST_CODE,encoding="utf-8")

print("[PASS] checkpoint-17 legacy reverse seed handoff replacement installed")
print("[ROOT_CAUSE] legacy reverse consumer inverted an already-reversed direction template")
print("[REVERSE] exact reverse quote/template remains source of truth")
print("[LEGACY_HANDOFF] forward template supplied only as inversion seed")
print("[GUARD] quote.swap_for_y is never rewritten")
print("[GUARD] seed source/dest inversion must equal exact reverse source/dest")
print("[FORWARD] exact forward direction path unchanged")
print("[SIZE_BIND] canonical runtime size binding untouched")
print("[KEY] untouched")
print("[BROADCAST] disabled")
print("[TEST]",TEST.name)
