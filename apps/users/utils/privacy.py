import hashlib
import secrets
from typing import Optional

def hash_email(email: str) -> str:
    """
    Hash email address for privacy preservation.
    Format: sha256:salt:hash
    """
    salt = secrets.token_hex(16)  # 32 character random salt
    salted_email = f"{salt}{email.lower().strip()}"
    hash_value = hashlib.sha256(salted_email.encode('utf-8')).hexdigest()
    return f"sha256:{salt}:{hash_value}"

def hash_phone(phone: str) -> str:
    """
    Hash phone number for privacy preservation.
    Format: sha256:salt:hash
    """
    salt = secrets.token_hex(16)
    salted_phone = f"{salt}{phone.replace(' ', '').replace('-', '').replace('+', '')}"
    hash_value = hashlib.sha256(salted_phone.encode('utf-8')).hexdigest()
    return f"sha256:{salt}:{hash_value}"

def verify_email_hash(email: str, hashed_email: str) -> bool:
    """
    Verify if a plain email matches a hashed email.
    """
    if not hashed_email.startswith("sha256:"):
        return False

    try:
        _, salt, hash_value = hashed_email.split(":")
        salted_email = f"{salt}{email.lower().strip()}"
        computed_hash = hashlib.sha256(salted_email.encode('utf-8')).hexdigest()
        return computed_hash == hash_value
    except ValueError:
        return False

def verify_phone_hash(phone: str, hashed_phone: str) -> bool:
    """
    Verify if a plain phone matches a hashed phone.
    """
    if not hashed_phone.startswith("sha256:"):
        return False

    try:
        _, salt, hash_value = hashed_phone.split(":")
        clean_phone = phone.replace(' ', '').replace('-', '').replace('+', '')
        salted_phone = f"{salt}{clean_phone}"
        computed_hash = hashlib.sha256(salted_phone.encode('utf-8')).hexdigest()
        return computed_hash == hash_value
    except ValueError:
        return False