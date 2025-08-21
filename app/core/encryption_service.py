from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from app.core.config import settings

class EncryptionService:
    def __init__( self ):
        self.secret_key = settings.SECRET_KEY
        self.salt = b'gym_fingerprint_salt'  # Fixed salt for consistency
    
    async def generate_encryption_key( self ) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm   = hashes.SHA256(),
            length      = 32,
            salt        = self.salt,
            iterations  = 100000
        )

        return base64.urlsafe_b64encode( kdf.derive( self.secret_key.encode() ) )
    
    async def encrypt_byte_array( self, data: bytes ) -> bytes:
        key = self.generate_encryption_key()
        f   = Fernet( key )

        return f.encrypt( data )
    
    async def decrypt_byte_array( self, encrypted_data: bytes ) -> bytes:
        key = self.generate_encryption_key()
        f   = Fernet( key )

        return f.decrypt( encrypted_data )

# Global instance
encryption_service = EncryptionService()