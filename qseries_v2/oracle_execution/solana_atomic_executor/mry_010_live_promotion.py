from __future__ import annotations
from pathlib import Path

from . import mry_007_candidate_hydrator as h
from . import mry_008_execution_readiness as r
from . import mry_009_atomic_warm_admission as a
from . import mry_011_reverse_readiness as rev

MAX_ADMISSIONS_PER_ROTATION=2

def queued(hints,state):
    have={
        str(p.token)
        for p in state.get("pairs",[])
    }

    return [
        dict(x)
        for x in (hints or [])
        if x.get("token")
        and str(x["token"]) not in have
    ]

def admit_batch(
    rt,
    root,
    state,
    hints,
    limit=MAX_ADMISSIONS_PER_ROTATION,
):
    rows=queued(
        hints,
        state,
    )

    admitted=0
    held=0

    for row in rows[
        :max(0,int(limit))
    ]:
        token=str(
            row["token"]
        )

        try:
            pair=h.hydrate_candidate(
                Path(root),
                row,
            )

            ready=r.install_forward(
                rt,
                pair,
            )

            a.admit(
                rt,
                state,
                pair,
                ready,
            )

            rev.refresh(rt,state,root)

            admitted+=1

        except Exception as exc:
            held+=1

            print(
                "[MRIYA_ADMISSION_HOLD] "
                "token=%s %s:%s"
                %(
                    token[:10],
                    type(exc).__name__,
                    str(exc)[:220],
                ),
                flush=True,
            )

    print(
        "[MRIYA_ADMISSION_BATCH] "
        "queued=%d attempted=%d "
        "admitted=%d held=%d warm=%d"
        %(
            len(rows),
            min(
                len(rows),
                max(0,int(limit)),
            ),
            admitted,
            held,
            len(rt.READY_TOKENS),
        ),
        flush=True,
    )

    return {
        "queued":len(rows),
        "admitted":admitted,
        "held":held,
    }
