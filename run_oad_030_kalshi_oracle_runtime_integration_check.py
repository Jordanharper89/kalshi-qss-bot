from qseries_v2.oracle_adapters.kalshi.oad_030_runtime_integration_gate import certify_oad_026_through_030

def main():
    c=certify_oad_026_through_030()
    print("="*72)
    print(" KALSHI → ORACLE LIVE RUNTIME INTEGRATION CHECK")
    print("="*72)
    print("[RUNTIME]",c.runtime_command)
    print("[CAPABILITY]",c.capability)
    print("[NEXT]",c.next_capability)
    print("[CERTIFIED]",c.certified)

if __name__=="__main__":
    main()
