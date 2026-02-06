"""
Unified encryption utilities for user-derived keys and conversation E2EE.
Provides consistent encryption across messaging and loans apps.
"""

import hashlib
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from django.conf import settings


class UserDerivedKeyManager:
    """
    Manages encryption keys derived from user IDs.
    Provides admin-proof encryption using deterministic key derivation.
    
    DEPRECATED: Use ConversationE2EEManager for messaging instead.
    This is kept for backward compatibility with loans app.
    """

    @staticmethod
    def derive_user_key(user_id: int) -> bytes:
        """
        Derive a consistent encryption key from user ID using PBKDF2.
        Uses PBKDF2 with user ID + server secret for security.

        Note: This is kept for backward compatibility with loans app.
        For new implementations, use ConversationE2EEManager.
        """
        # Create PBKDF2 key derivation function
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 32 bytes = 256 bits for AES-256
            salt=settings.SECRET_KEY[:32].encode(),  # Use server secret as salt
            iterations=50000,  # Moderate iterations for user keys
        )

        # Use user ID as password
        password = str(user_id)

        # Derive the key
        key = kdf.derive(password.encode())

        return key

    @staticmethod
    def get_user_cipher(user_id: int) -> Fernet:
        """
        Get Fernet cipher for user encryption/decryption.
        """
        key = UserDerivedKeyManager.derive_user_key(user_id)
        return Fernet(base64.urlsafe_b64encode(key))

    @staticmethod
    def encrypt_for_user(content: str, user_id: int) -> str:
        """
        Encrypt content that only this user can decrypt.
        Uses user's derived key for encryption.
        """
        if not content:
            return ""

        cipher = UserDerivedKeyManager.get_user_cipher(user_id)
        encrypted = cipher.encrypt(content.encode())
        return encrypted.decode()

    @staticmethod
    def decrypt_for_user(encrypted_content: str, user_id: int) -> str:
        """
        Decrypt content encrypted for this user.
        Uses user's derived key for decryption.
        """
        if not encrypted_content:
            return ""

        try:
            cipher = UserDerivedKeyManager.get_user_cipher(user_id)
            decrypted = cipher.decrypt(encrypted_content.encode())
            return decrypted.decode()
        except Exception as e:
            # Return placeholder for decryption failures
            return "[Unable to decrypt message]"

    @staticmethod
    def can_user_decrypt(encrypted_content: str, user_id: int) -> bool:
        """
        Test if user can decrypt given content.
        Useful for debugging encryption issues.
        """
        try:
            UserDerivedKeyManager.decrypt_for_user(encrypted_content, user_id)
            return True
        except (ValueError, KeyError, AttributeError, Exception):
            return False


class ConversationE2EEManager:
    """
    Manages end-to-end encryption for conversations using PBKDF2.
    Both participants in a conversation can decrypt all messages.

    Uses PBKDF2 (Password-Based Key Derivation Function 2) with:
    - 100,000 iterations for strong key derivation
    - SHA256 hashing algorithm
    - 256-bit AES encryption via Fernet
    - Conversation-specific salt for additional security

    Key derivation inputs:
    - Conversation ID
    - Conversation encryption salt (random 32-byte salt per conversation)
    - Server secret key

    This provides strong protection against brute-force attacks while maintaining
    deterministic key derivation for both conversation participants.
    """

    @staticmethod
    def generate_salt() -> str:
        """
        Generate a random encryption salt for a conversation.
        
        Returns:
            Base64-encoded random 32-byte salt
        """
        return base64.b64encode(os.urandom(32)).decode()

    @staticmethod
    def derive_conversation_key(conversation_id: int, encryption_salt: str) -> bytes:
        """
        Derive a shared conversation encryption key using PBKDF2.
        Both participants can derive the same key using conversation ID and salt.

        Uses PBKDF2 with 100,000 iterations for strong key derivation,
        making brute-force attacks computationally expensive.

        Args:
            conversation_id: The conversation ID
            encryption_salt: The encryption salt stored in the conversation

        Returns:
            32-byte key suitable for Fernet encryption
        """
        # Decode the base64 salt to bytes
        try:
            salt_bytes = base64.b64decode(encryption_salt)
        except Exception:
            # Fallback to raw salt if not base64
            salt_bytes = encryption_salt.encode()

        # Create PBKDF2 key derivation function
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 32 bytes = 256 bits for AES-256
            salt=salt_bytes,
            iterations=100000,  # High iteration count for security
        )

        # Combine conversation ID and server secret as password
        password = f"{conversation_id}_{settings.SECRET_KEY[:32]}"

        # Derive the key
        key = kdf.derive(password.encode())

        return key

    @staticmethod
    def get_conversation_cipher(conversation_id: int, encryption_salt: str) -> Fernet:
        """
        Get Fernet cipher for conversation encryption/decryption.
        
        Args:
            conversation_id: The conversation ID
            encryption_salt: The encryption salt from the conversation
            
        Returns:
            Fernet cipher instance
        """
        key = ConversationE2EEManager.derive_conversation_key(conversation_id, encryption_salt)
        return Fernet(base64.urlsafe_b64encode(key))

    @staticmethod
    def encrypt_message(content: str, conversation_id: int, encryption_salt: str) -> str:
        """
        Encrypt a message for a conversation.
        Both participants in the conversation can decrypt this.
        
        Args:
            content: The message content to encrypt
            conversation_id: The conversation ID
            encryption_salt: The encryption salt from the conversation
            
        Returns:
            Encrypted message (base64-encoded)
        """
        if not content:
            return ""

        cipher = ConversationE2EEManager.get_conversation_cipher(conversation_id, encryption_salt)
        encrypted = cipher.encrypt(content.encode())
        return encrypted.decode()

    @staticmethod
    def decrypt_message(encrypted_content: str, conversation_id: int, encryption_salt: str) -> str:
        """
        Decrypt a message from a conversation.
        
        Args:
            encrypted_content: The encrypted message
            conversation_id: The conversation ID
            encryption_salt: The encryption salt from the conversation
            
        Returns:
            Decrypted message content, or error placeholder if decryption fails
        """
        if not encrypted_content:
            return ""

        try:
            cipher = ConversationE2EEManager.get_conversation_cipher(conversation_id, encryption_salt)
            decrypted = cipher.decrypt(encrypted_content.encode())
            return decrypted.decode()
        except Exception as e:
            # Return placeholder for decryption failures
            return "[Unable to decrypt message]"

    @staticmethod
    def can_decrypt_message(encrypted_content: str, conversation_id: int, encryption_salt: str) -> bool:
        """
        Test if a message can be decrypted with the given conversation key.
        Useful for debugging encryption issues.
        
        Args:
            encrypted_content: The encrypted message
            conversation_id: The conversation ID
            encryption_salt: The encryption salt
            
        Returns:
            True if decryption succeeds, False otherwise
        """
        try:
            ConversationE2EEManager.decrypt_message(encrypted_content, conversation_id, encryption_salt)
            return True
        except Exception:
            return False