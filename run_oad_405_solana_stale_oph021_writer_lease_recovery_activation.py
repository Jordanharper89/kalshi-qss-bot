from qseries_v2.oracle_adapters.independent.oad_405_solana_stale_oph021_writer_lease_recovery_activation import (
    recover_and_activate_exclusive_writer,
)

def main():
    x=recover_and_activate_exclusive_writer()
    print("[RECOVERY]",x)
    if x.state!="OPH021_WRITER_RECOVERED_AND_ACTIVE":
        raise SystemExit(1)

if __name__=="__main__":
    main()
