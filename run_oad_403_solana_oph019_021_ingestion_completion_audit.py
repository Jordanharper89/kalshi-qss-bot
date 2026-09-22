from qseries_v2.oracle_adapters.independent.oad_403_solana_oph019_021_ingestion_completion_audit import (
    audit_ingestion_completion,
    print_audit,
)

def main():
    a=audit_ingestion_completion()
    print_audit(a)

if __name__=="__main__":
    main()
