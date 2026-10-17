"""Sign only an already-compiled v0 Solana transaction, simulation-only.
No network operations, no logging of private key, no sending transactions.
"""
from __future__ import annotations


def verify_and_sign(built, expected_wallet):
    from solders.transaction import VersionedTransaction
    from solders.message import to_bytes_versioned
    from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core

    if not isinstance(built, dict) or not built.get('ok'):
        raise RuntimeError('ORACLE162_INVALID_COMPILER_RESULT')
    raw = built.get('raw')
    if not isinstance(raw, (bytes, bytearray)) or not (100 <= len(raw) <= 1232):
        raise RuntimeError('ORACLE162_INVALID_RAW_PACKET')
    try:
        tx = VersionedTransaction.from_bytes(bytes(raw))
    except Exception:
        raise RuntimeError('ORACLE162_NOT_PARSEABLE_VERSIONED_TX') from None
    msg = tx.message
    if not hasattr(msg, 'address_table_lookups'):
        raise RuntimeError('ORACLE162_NOT_V0_TRANSACTION')
    header = msg.header
    n = int(header.num_required_signatures)
    if n != 1 or len(tx.signatures) != n:
        raise RuntimeError('ORACLE162_UNEXPECTED_SIGNER_COUNT:%d' % n)
    # The first static key is the payer and sole authorized signer.
    if str(msg.account_keys[0]) != str(expected_wallet):
        raise RuntimeError('ORACLE162_MESSAGE_PAYER_MISMATCH')
    signing_keypair = core.keypair()
    if str(signing_keypair.pubkey()) != str(expected_wallet):
        raise RuntimeError('ORACLE162_CREDENTIAL_SIGNER_MISMATCH')
    message_bytes = to_bytes_versioned(msg)
    # Never mutate the message, including instruction accounts, amounts or ALT indices.
    signature = signing_keypair.sign_message(message_bytes)
    signed = VersionedTransaction.populate(msg, [signature])
    verified = signed.verify_with_results()
    if len(verified) != 1 or verified[0] is not True:
        raise RuntimeError('ORACLE162_SIGNATURE_VERIFY_FAILED')
    out = bytes(signed)
    if len(out) > 1232 or len(out) < 100:
        raise RuntimeError('ORACLE162_SIGNED_PACKET_SIZE_INVALID')
    # A newly populated packet must serialize the exact same v0 message.
    if to_bytes_versioned(VersionedTransaction.from_bytes(out).message) != message_bytes:
        raise RuntimeError('ORACLE162_MESSAGE_MUTATED')
    import hashlib
    print('[ORACLE162_SIGNATURE_VALID] signers=1 verified=True bytes=%d message_sha256=%s broadcast=FALSE' %
        (len(out),hashlib.sha256(message_bytes).hexdigest()[:16]),flush=True)
    result = dict(built)
    result['raw'] = out
    result['bytes'] = len(out)
    result['oracle162_signature_verified'] = True
    return result
