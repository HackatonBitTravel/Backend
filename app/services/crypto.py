# Service de cryptographie pour signer et vérifier les tickets
# Utilise secp256k1 (Bitcoin/Lightning) au lieu de Ed25519

import json
import hashlib
from ecdsa import SigningKey, VerifyingKey, SECP256k1
from ecdsa.util import sigencode_der, sigdecode_der
from typing import Tuple

class CryptoService:
    
    @staticmethod
    def generate_keypair() -> Tuple[str, str]:
        signing_key = SigningKey.generate(curve=SECP256k1)
        verifying_key = signing_key.get_verifying_key()
        
        private_key = signing_key.to_string().hex()
        public_key = verifying_key.to_string().hex()
        
        return private_key, public_key
    
    @staticmethod
    def sign_payload(payload: dict, private_key: str) -> str:
        payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        payload_bytes = payload_json.encode('utf-8')
        
        message_hash = hashlib.sha256(payload_bytes).digest()
        
        signing_key = SigningKey.from_string(bytes.fromhex(private_key), curve=SECP256k1)
        signature = signing_key.sign_digest(message_hash, sigencode=sigencode_der)
        
        return signature.hex()
    
    @staticmethod
    def verify_signature(payload: dict, signature: str, public_key: str) -> bool:
        try:
            payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            payload_bytes = payload_json.encode('utf-8')
            
            message_hash = hashlib.sha256(payload_bytes).digest()
            
            verifying_key = VerifyingKey.from_string(bytes.fromhex(public_key), curve=SECP256k1)
            signature_bytes = bytes.fromhex(signature)
            
            verifying_key.verify_digest(signature_bytes, message_hash, sigdecode=sigdecode_der)
            return True
        except Exception as e:
            print(f"Erreur de vérification: {str(e)}")
            return False