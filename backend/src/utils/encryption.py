"""AES-256 encryption/decryption utility using Fernet.

Fernet guarantees that a message encrypted using it cannot be
manipulated or read without the key. It uses AES-128-CBC under
the hood (via the cryptography library's Fernet implementation),
which is sufficient for OAuth token storage.
"""

import logging

from cryptography.fernet import Fernet, InvalidToken

from src.config import config

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    """Build Fernet instance from ENCRYPTION_KEY config."""
    key = config.ENCRYPTION_KEY
    if not key:
        raise RuntimeError(
            "ENCRYPTION_KEY is not set. Generate one with: "
            "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_token(plaintext: str) -> bytes:
    """Encrypt a plaintext string and return encrypted bytes.

    Args:
        plaintext: The token string to encrypt.

    Returns:
        Encrypted bytes suitable for storing in LargeBinary column.
    """
    f = _get_fernet()
    return f.encrypt(plaintext.encode("utf-8"))


def decrypt_token(ciphertext: bytes) -> str:
    """Decrypt encrypted bytes back to a plaintext string.

    Args:
        ciphertext: Encrypted bytes from encrypt_token().

    Returns:
        Original plaintext string.

    Raises:
        InvalidToken: If the ciphertext is corrupted or the key is wrong.
    """
    f = _get_fernet()
    try:
        return f.decrypt(ciphertext).decode("utf-8")
    except InvalidToken:
        logger.error("Failed to decrypt token - invalid key or corrupted data")
        raise
