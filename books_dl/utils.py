"""Utility functions for encryption/decryption."""

import hashlib
import random
from urllib.parse import unquote
import re


def hex_to_bytes(hex_string: str) -> list[int]:
    """Convert hex string to list of byte values."""
    if not isinstance(hex_string, str):
        return []
    return [int(hex_string[i:i+2], 16) for i in range(0, len(hex_string), 2)]


def generate_key(url: str, download_token: str) -> list[int]:
    """Generate XOR decryption key based on URL and token."""
    # Extract file path from URL
    match = re.search(r'https://(?:[^/]+/){3}.*?(?P<rest_part>/.+)', url)
    if not match:
        raise ValueError(f"Cannot extract file path from URL: {url}")
    
    file_path = unquote(match.group('rest_part'))
    
    # Calculate MD5 and partition
    md5_hex = hashlib.md5(file_path.encode()).hexdigest()
    md5_chars = list(md5_hex)
    
    partition = 0
    for i in range(0, len(md5_chars), 4):
        chunk = ''.join(md5_chars[i:i+4])
        partition = (partition + int(chunk, 16)) % 64
    
    # Generate SHA256 key
    combined = f"{download_token[:partition]}{file_path}{download_token[partition:]}"
    decode_hex = hashlib.sha256(combined.encode()).hexdigest()
    
    return hex_to_bytes(decode_hex)


def decode_xor(key: list[int], encrypted_content: bytes) -> bytes:
    """Decrypt content using XOR with the given key."""
    result = bytearray()
    key_len = len(key)
    
    for i, byte in enumerate(encrypted_content):
        result.append(byte ^ key[i % key_len])
    
    # Remove BOM if present
    if len(result) >= 3 and result[0] == 0xEF and result[1] == 0xBB and result[2] == 0xBF:
        result = result[3:]
    
    return bytes(result)


def img_checksum() -> str:
    """Generate random checksum for image requests."""
    seed = list('0693147180559AAC')
    random.shuffle(seed)
    return ''.join(seed)
