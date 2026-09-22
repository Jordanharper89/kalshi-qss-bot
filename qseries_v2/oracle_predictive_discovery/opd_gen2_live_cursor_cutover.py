from pathlib import Path
import json,shutil,time
execution_authority=False

def cutover(root=None):
    root=Path(root or Path.cwd()).resolve()
    rt=root/"runtime"/"predictive_data"
    spool=rt/"opd_061_live_anchor_spool.jsonl"
    cursor=rt/"opd_065_intake_cursor.json"
    freeze=rt/"opd_gen2_candidate_freeze.json"

    if not spool.exists():
        raise RuntimeError("LIVE_ANCHOR_SPOOL_MISSING")
    if not freeze.exists():
        raise RuntimeError("GEN2_FREEZE_MISSING")

    activation=float(json.loads(freeze.read_text(encoding="utf-8"))["activation_epoch"])

    old_offset=0
    if cursor.exists():
        try:
            old_offset=int(json.loads(cursor.read_text(encoding="utf-8")).get("byte_offset",0))
        except Exception:
            old_offset=0

    first_post_offset=None
    post_count=0
    total=0
    last_epoch=None

    with spool.open("r",encoding="utf-8") as f:
        while True:
            start=f.tell()
            line=f.readline()
            if not line:
                eof=f.tell()
                break
            total+=1
            try:
                a=json.loads(line)
                ep=float(a["observed_epoch"])
                last_epoch=ep
            except Exception:
                continue
            if ep>activation:
                post_count+=1
                if first_post_offset is None:
                    first_post_offset=start

    target=eof if first_post_offset is None else first_post_offset

    if target < old_offset:
        target=old_offset

    if cursor.exists():
        backup=cursor.with_name(cursor.name+".pre_gen2_live_cutover")
        if not backup.exists():
            shutil.copy2(cursor,backup)

    payload={
        "byte_offset":int(target),
        "cutover_basis":"FIRST_POST_GEN2_FREEZE_ANCHOR_OR_EOF",
        "gen2_activation_epoch":activation,
        "old_byte_offset":int(old_offset),
        "spool_eof":int(eof),
        "spool_rows_total":int(total),
        "post_freeze_anchors_present":int(post_count),
        "first_post_freeze_offset":first_post_offset,
        "last_spool_observed_epoch":last_epoch,
        "cutover_epoch":time.time(),
        "execution_authority":False,
    }
    cursor.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")

    print("="*96)
    print("ORACLE GEN2 LIVE CURSOR CUTOVER")
    print("="*96)
    print("GEN2_ACTIVATION_EPOCH=",activation)
    print("OLD_BYTE_OFFSET=",old_offset)
    print("NEW_BYTE_OFFSET=",target)
    print("SPOOL_EOF=",eof)
    print("SPOOL_ROWS_TOTAL=",total)
    print("POST_FREEZE_ANCHORS_ALREADY_PRESENT=",post_count)
    print("FIRST_POST_FREEZE_OFFSET=",first_post_offset)
    print("CURSOR_MOVED_FORWARD_ONLY=",target>=old_offset)
    print("OLD_BACKLOG_RETAINED_ON_DISK=TRUE")
    print("EXECUTION_AUTHORITY=FALSE")
    return payload

if __name__=="__main__":
    cutover()
