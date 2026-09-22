from qseries_v2.oracle_adapters.independent.oad_404_solana_postgresql_queue_writer_live_state_audit import (
    audit_live_queue_writer_state,
    print_audit,
)

def main():
    print_audit(audit_live_queue_writer_state())

if __name__=="__main__":
    main()
