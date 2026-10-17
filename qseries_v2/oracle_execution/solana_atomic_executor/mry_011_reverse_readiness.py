def refresh(rt,state,root=None):
    fn=getattr(rt,"prebuild_sell_templates",None)
    user=getattr(rt,"USER",None)

    if not callable(fn):
        raise RuntimeError("MRY022_PREBUILD_SELL_TEMPLATES_MISSING")
    if not user:
        raise RuntimeError("MRY022_RUNTIME_USER_MISSING")

    count=fn(state,user)

    print(
        "[MRY022_REVERSE_REFRESH] "
        "sell_templates=%d direct=TRUE"
        %int(count),
        flush=True,
    )

    return int(count)
