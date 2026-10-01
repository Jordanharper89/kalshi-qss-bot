import fs from "node:fs";
import {createRequire} from "node:module";

const require=createRequire(
  import.meta.url
);

const {
  Connection,
  PublicKey
}=require("@solana/web3.js");

const {
  TOKEN_PROGRAM_ID,
  TOKEN_2022_PROGRAM_ID,
  getMint,
  getTransferFeeConfig,
  calculateEpochFee
}=require("@solana/spl-token");

const req=JSON.parse(
  fs.readFileSync(0,"utf8")
);

const connection=new Connection(
  req.rpc,
  "confirmed"
);

const mint=new PublicKey(
  req.mint
);

const gross=BigInt(
  String(req.gross)
);

try{
  const info=
    await connection.getAccountInfo(
      mint,
      "confirmed"
    );

  if(!info){
    throw new Error(
      "MINT_NOT_FOUND"
    );
  }

  if(
    info.owner.equals(
      TOKEN_PROGRAM_ID
    )
  ){
    console.log(
      JSON.stringify({
        ok:true,
        program:
          TOKEN_PROGRAM_ID.toBase58(),
        gross:gross.toString(),
        fee:"0",
        net:gross.toString()
      })
    );

    process.exit(0);
  }

  if(
    !info.owner.equals(
      TOKEN_2022_PROGRAM_ID
    )
  ){
    throw new Error(
      "UNKNOWN_TOKEN_PROGRAM:"
      +info.owner.toBase58()
    );
  }

  const m=
    await getMint(
      connection,
      mint,
      "confirmed",
      TOKEN_2022_PROGRAM_ID
    );

  const cfg=
    getTransferFeeConfig(m);

  if(!cfg){
    console.log(
      JSON.stringify({
        ok:true,
        program:
          TOKEN_2022_PROGRAM_ID.toBase58(),
        gross:gross.toString(),
        fee:"0",
        net:gross.toString()
      })
    );

    process.exit(0);
  }

  const epoch=
    await connection.getEpochInfo(
      "confirmed"
    );

  const fee=
    calculateEpochFee(
      cfg,
      BigInt(epoch.epoch),
      gross
    );

  const net=gross-fee;

  if(net<=0n){
    throw new Error(
      "NET_RECEIVED_NONPOSITIVE"
    );
  }

  console.log(
    JSON.stringify({
      ok:true,
      program:
        TOKEN_2022_PROGRAM_ID.toBase58(),
      gross:gross.toString(),
      fee:fee.toString(),
      net:net.toString()
    })
  );

}catch(e){
  console.log(
    JSON.stringify({
      ok:false,
      reason:
        e?.stack ??
        e?.message ??
        String(e)
    })
  );
}
