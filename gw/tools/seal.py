#!/usr/bin/env python3
"""Seal a product file for the free gateway: python3 gw/tools/seal.py <in.pdf> <out.enc>
Uses the public key gw/vault/seal_pub.pem; only the gateway (GitHub Action) can open it.
Format: b"SEAL1" + 2-byte key length + RSA-OAEP(Fernet key) + Fernet(file)."""
import sys
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
pub = serialization.load_pem_public_key((Path(__file__).resolve().parents[1] / "vault/seal_pub.pem").read_bytes())
fk = Fernet.generate_key()
ek = pub.encrypt(fk, padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
data = Path(sys.argv[1]).read_bytes()
Path(sys.argv[2]).write_bytes(b"SEAL1" + len(ek).to_bytes(2, "big") + ek + Fernet(fk).encrypt(data))
print(f"sealed {len(data)} bytes -> {sys.argv[2]}")
