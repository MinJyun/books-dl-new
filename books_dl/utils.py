"""Utility functions for encryption/decryption."""

import hashlib
import random
from urllib.parse import unquote
import re


def generate_key(url: str, download_token: str) -> bytes:
    """Generate XOR decryption key based on URL and token."""
    match = re.search(r'https://(?:[^/]+/){3}.*?(?P<rest_part>/.+)', url)
    if not match:
        raise ValueError(f"Cannot extract file path from URL: {url}")

    file_path = unquote(match.group('rest_part'))

    md5_hex = hashlib.md5(file_path.encode()).hexdigest()
    md5_chars = list(md5_hex)

    partition = 0
    for i in range(0, len(md5_chars), 4):
        chunk = ''.join(md5_chars[i:i+4])
        partition = (partition + int(chunk, 16)) % 64

    combined = f"{download_token[:partition]}{file_path}{download_token[partition:]}"
    return bytes.fromhex(hashlib.sha256(combined.encode()).hexdigest())


def decode_xor(key: bytes, encrypted_content: bytes) -> bytes:
    """Decrypt content using XOR with the given key."""
    key_len = len(key)
    result = bytearray(b ^ key[i % key_len] for i, b in enumerate(encrypted_content))

    if len(result) >= 3 and result[:3] == bytearray(b'\xef\xbb\xbf'):
        result = result[3:]

    return bytes(result)


def img_checksum() -> str:
    """Generate random checksum for image requests."""
    seed = list('0693147180559AAC')
    random.shuffle(seed)
    return ''.join(seed)
