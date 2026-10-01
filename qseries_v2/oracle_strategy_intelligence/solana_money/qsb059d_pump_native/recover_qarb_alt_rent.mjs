import fs from "node:fs";
import {
  AddressLookupTableProgram,
  Connection,
  Keypair,
  PublicKey,
  Transaction,
  sendAndConfirmTransaction
} from "@solana/web3.js";

const req=JSON.parse(
  fs.readFileSync(0,"utf8")
);

const connection=
  new Connection(
    req.rpc,
    "confirmed"
  );

const authority=
  Keypair.fromSecretKey(
    Uint8Array.from(
      req.secretBytes
    )
  );

const MAX_U64=
  18446744073709551615n;

const COOLDOWN=513n;

console.log(
  "[RECOVERY_WALLET]",
  authority.publicKey.toBase58()
);

for(const raw of req.alts){

  const address=
    new PublicKey(raw);

  console.log(
    "\n[ALT]",
    raw
  );

  const info=
    await connection.getAccountInfo(
      address,
      "confirmed"
    );

  if(!info){
    console.log(
      "[ALT_MISSING] already closed or absent"
    );
    continue;
  }

  console.log(
    "[ALT_LAMPORTS]",
    info.lamports,
    "SOL="+
    (info.lamports/1e9).toFixed(9)
  );

  const got=
    await connection.getAddressLookupTable(
      address,
      {
        commitment:"confirmed"
      }
    );

  const table=got.value;

  if(!table){
    console.log(
      "[HOLD] account is not readable as ALT"
    );
    continue;
  }

  const altAuthority=
    table.state.authority;

  console.log(
    "[ALT_AUTHORITY]",
    altAuthority
      ? altAuthority.toBase58()
      : "NONE"
  );

  if(
    !altAuthority ||
    !altAuthority.equals(
      authority.publicKey
    )
  ){
    console.log(
      "[HOLD] wallet is not ALT authority"
    );
    continue;
  }

  const ds=
    BigInt(
      table.state
        .deactivationSlot
        .toString()
    );

  if(ds===MAX_U64){

    console.log(
      "[ACTION] DEACTIVATE"
    );

    const ix=
      AddressLookupTableProgram
        .deactivateLookupTable({
          lookupTable:address,
          authority:
            authority.publicKey
        });

    const tx=
      new Transaction().add(ix);

    const sig=
      await sendAndConfirmTransaction(
        connection,
        tx,
        [authority],
        {
          commitment:"confirmed",
          skipPreflight:false,
          maxRetries:0
        }
      );

    console.log(
      "[DEACTIVATED]",
      sig
    );

    console.log(
      "[NEXT] cooldown required before close"
    );

    continue;
  }

  const slot=
    BigInt(
      await connection.getSlot(
        "confirmed"
      )
    );

  const eligibleAfter=
    ds+COOLDOWN;

  console.log(
    "[DEACTIVATION_SLOT]",
    ds.toString()
  );

  console.log(
    "[CURRENT_SLOT]",
    slot.toString()
  );

  if(slot<=eligibleAfter){

    console.log(
      "[COOLDOWN]",
      "remaining_slots="+
      (eligibleAfter-slot)
        .toString()
    );

    continue;
  }

  console.log(
    "[ACTION] CLOSE_AND_REFUND"
  );

  const before=
    await connection.getBalance(
      authority.publicKey,
      "confirmed"
    );

  const ix=
    AddressLookupTableProgram
      .closeLookupTable({
        lookupTable:address,
        authority:
          authority.publicKey,
        recipient:
          authority.publicKey
      });

  const tx=
    new Transaction().add(ix);

  const sig=
    await sendAndConfirmTransaction(
      connection,
      tx,
      [authority],
      {
        commitment:"confirmed",
        skipPreflight:false,
        maxRetries:0
      }
    );

  const after=
    await connection.getBalance(
      authority.publicKey,
      "confirmed"
    );

  console.log(
    "[CLOSED]",
    sig
  );

  console.log(
    "[REFUND_DELTA]",
    after-before,
    "lamports",
    "SOL="+
    ((after-before)/1e9)
      .toFixed(9)
  );
}

const finalBalance=
  await connection.getBalance(
    authority.publicKey,
    "confirmed"
  );

console.log(
  "\n[FINAL_WALLET]",
  finalBalance,
  "lamports",
  (finalBalance/1e9)
    .toFixed(9)
    +" SOL"
);
