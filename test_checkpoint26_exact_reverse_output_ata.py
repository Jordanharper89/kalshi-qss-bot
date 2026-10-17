import unittest

from qseries_v2.oracle_execution.solana_atomic_executor import checkpoint26_dlmm_output_ata_readiness as c


def account(pubkey,signer=False,writable=False):
    return {
        "pubkey":pubkey,
        "isSigner":signer,
        "isWritable":writable,
    }


class T(unittest.TestCase):
    def test_create_idempotent_shape(self):
        ix=c._create_idempotent_ix("USER","ATA","MINT","TOKEN")
        self.assertEqual(ix["programId"],c.ATA_PROGRAM)
        self.assertEqual(ix["data"],"AQ==")
        self.assertEqual(ix["accounts"][1]["pubkey"],"ATA")
        self.assertEqual(ix["accounts"][3]["pubkey"],"MINT")
        self.assertEqual(ix["accounts"][5]["pubkey"],"TOKEN")

    def test_insert_is_before_dlmm(self):
        dlmm={
            "programId":c.DLMM_PROGRAM,
            "accounts":[
                account("A0"),account("A1"),account("A2"),
                account("A3"),account("A4"),account("DEST",writable=True),
            ],
            "data":"AA==",
        }
        out=c._inject_before_dlmm(
            [{"programId":"PRE","accounts":[],"data":""},dlmm,
             {"programId":"POST","accounts":[],"data":""}],
            c._create_idempotent_ix("USER","DEST","MINT","TOKEN"),
            "DEST",
        )
        programs=[x["programId"] for x in out]
        self.assertLess(programs.index(c.ATA_PROGRAM),programs.index(c.DLMM_PROGRAM))

    def test_existing_exact_create_not_duplicated(self):
        create=c._create_idempotent_ix("USER","DEST","MINT","TOKEN")
        dlmm={
            "programId":c.DLMM_PROGRAM,
            "accounts":[
                account("A0"),account("A1"),account("A2"),
                account("A3"),account("A4"),account("DEST",writable=True),
            ],
            "data":"AA==",
        }
        out=c._inject_before_dlmm([create,dlmm],create,"DEST")
        self.assertEqual(
            sum(x.get("programId")==c.ATA_PROGRAM for x in out),
            1,
        )

    def test_dlmm_account5_is_source_of_truth(self):
        route={
            "meteora_ix":{
                "programId":c.DLMM_PROGRAM,
                "accounts":[
                    account("A0"),account("A1"),account("A2"),
                    account("A3"),account("A4"),account("DEST"),
                ],
                "data":"AA==",
            },
            "original_candidates":[],
        }
        ix=c._exact_dlmm_ix(route)
        self.assertEqual(ix["accounts"][5]["pubkey"],"DEST")

    def test_no_send_transaction(self):
        from pathlib import Path
        source=Path(c.__file__).read_text(encoding="utf-8")
        self.assertNotIn("sendTransaction",source)
        self.assertIn("[BROADCAST] disabled",source)


if __name__=="__main__":
    unittest.main(verbosity=2)
