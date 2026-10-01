from pathlib import Path
import ast

ROOT=Path.cwd()

TEST=ROOT/"test_sae_005b_oracle020_full_size_curve.py"

if not TEST.is_file():
    raise RuntimeError(
        "SAE005B_TEST_MISSING"
    )

src=TEST.read_text(
    encoding="utf-8"
)

old='''        self.assertIn(
            'max(rows,key=lambda x:x["local_net"])',
            src.replace(
                " ",
                ""
            )
        )'''

new='''        compact="".join(
            src.split()
        )

        self.assertIn(
            'max(rows,key=lambdax:x["local_net"])',
            compact
        )'''

if old not in src:
    raise RuntimeError(
        "SAE005B_BAD_ASSERTION_NOT_FOUND"
    )

src=src.replace(
    old,
    new,
    1
)

ast.parse(src)

TEST.write_text(
    src,
    encoding="utf-8"
)

print(
    "[PASS] SAE-005C size-curve test assertion repaired"
)
print(
    "[RUNTIME] unchanged"
)
print(
    "[SELECT] max local_net already physically present"
)
print(
    "[SAE-005B] full size curve preserved"
)
print(
    "[BROADCAST] disabled"
)