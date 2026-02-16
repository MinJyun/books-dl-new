import hashlib
from urllib.parse import unquote
import re

def hex_to_bytes(hex_string: str):
    return [int(hex_string[i:i+2], 16) for i in range(0, len(hex_string), 2)]

def generate_key(file_path: str, download_token: str):
    """Generate XOR decryption key based on file path and token."""
    print(f"Testing path: {file_path}")
    
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

def decode_xor(key: list, encrypted_content: bytes):
    result = bytearray()
    key_len = len(key)
    
    for i, byte in enumerate(encrypted_content):
        result.append(byte ^ key[i % key_len])
    
    # Remove BOM
    if len(result) >= 3 and result[0] == 0xEF and result[1] == 0xBB and result[2] == 0xBF:
        result = result[3:]
    
    return result

def test_find_params():
    # Derived Key from KPA
    target_key_hex = "41b71db3bdbbdfc43ca7436e3a919dee58e65079774e01563b20b864d4680aec"
    target_key = hex_to_bytes(target_key_hex)
    print(f"Target Key: {target_key_hex}")

    # Candidate Tokens
    token_log = "15c626Jc0ITlbIuyMNzScx3aJevw7BqfqkrUal2+lHe/+F8lWBkErV1wVhbKHZA/PDXAuVzMg8SPbRuQJUQaYLFCvTTDAPARND2Pl4ObcluuBjjjl+u3pxL1F0J+2mqTbF9dLt8J1JIyUdGjuZVtSVKnj+v2UmIGirKAAyh3E357hIZBAWSmylagXD/puUZbzZ4zi8o2rUMLvyke2q6nVI6O4BFaMTdJhXaxmS9zlgwIqUl1RxFWR/u/nchXdD/oIOP4OIds9neHxKyC+QJK/My2dfnCG3gagkxOL9+WXKUyG/s98h+T3K8i5uk83n4oTPTdzC83jxw3sgnTjYfDflzwZWVCV8LPpsJMvQQh+THrIkwXfG+VxrrK0rjemw/Wl/B3/b3Bg7HexYS172K/0JlLeNwA8SwsRx4Pnb6OHCED8gT37oLdWj7LyADqQEFV/fUbaTxN3s70ncxxjQEGu/Vx4JMWKUXlFpthlI7oC1c1/DZiT2Ima6b1fyDGWKcZ6xVbRmKmVO2SfzM4dyFB4QZ8GG5gqGGzWpRz1s8irfmiq9nhkDyx0DSdfgA2WKcZ6xVbRmNdxhdnM6jdo8PQi6AGCQ2F+XMOdrRZ0nEovk/yAt7FWg+usm1E39MJXMT6Kjw3qZWPj8pYwbv6Pj5aZ4OMLSfxygZB67xzaDOtE7Fu+SD++zepQCXTd8N3KpoBPi7SsHn7Ri29Tol07O1Tw3ny4UcAyNeUN63d1Gxvlca6ytK41wuAh6PMJ4Fa0nbWoSvSYzqDXVCRbx3zJDvyGQJ3Dx/Nc0YQKB8w8nhAmbG+HOggz+dipKhnfqByJyFX+a3Ztv/6O/u8mGe7qtJ21qEr0mMxsWlnDOEQcp06MwmD6OLq1LIjIo7FdxJpQ9o58W3IRM2F9yssUci+GLOQzPffFmd4tk4mgD+SWscRVkf7v53IVcu7jDViLiUg=="
    token_cookie = "cf5c82UtovIrTd5HVHbrKHf3g5L4lv+Sm6S+XayoQD9Qap4XIXJJld67XmGz0tbIhlQmSsew0V1s3p7uxgXEEXw7bn5boIkU/JicfitcffJMIfWyTCpy0w7dq5JK2LlP3qOnXn6syDGY3t9tEFAxF2MgeIO2zS7P2UuOtEQOvh6uG74+n0zWBozMVYSlKX6a5448Rhu1m5WJeZMs3wQng8kq/n69uJVAhCpGM3P8/XFIN2L3VoCoZPbI6GcN4Ujhuwt2UKAkt+0Na3ChFHLb0V12FfT/XgkuY0Zk4yD/r2TVnbNhldWnQck809GqfzJnTPE9bTu4LF6jS9cM07yQ44ktXYecPk4F7HxxDXVLdIXTl5qni1roeouAhy3Z2YTg9F0evenbtWPjW/oMFUctHl2/+mrm1kqeeVuuUFR+LPCoLDmgFURy63GGxHH0KXxqRK8mG+QPi+X09Ksf35WIelC/5GqLJTb8t/qTg+XGJLSHiz0RWhJnkWarN9GuV692ZhxrPDpiVCjtBWhtvFYDg5U9SsZsv+F6zcyJN5xsN0L27yKqbTe4GafOzlgOV692ZhxrPDhaS8QKUCrNDwwshqq+/AIhOk3Jxp73kSIxmfov1VZV83wzmIto2fP1eqDLU/4CslRbeXUU94ZerRfjF3SF68tD8I8taNdQRJNVZSx7F5S5AqE+6ZMjARZ1pz+sp7wz/5gG+R7u4gl+O50qGeBME7F39+fW+houl+ta6HqLgIct0FWCCBM3SHsVF7grAGuOWvxL6P+3lpQYBAxyQ3FDsaLrRVpp5nIh5KmMcYoh6eELarok5X9rGiWZVCOrrXW+i7pA5hP9iLdhZRe4KwBrjlr2sTTJKeGqAcbCzMBDaJ+zmee5pBxj0QvL1bM68sJQ0xbPyDzAAAmaa+VGZt6ap0TPtqyvpMqCCpaAqGT2yOhnCfcC6f2lM/mQ=="
    lpk = "dce4e188647a8efa19cd006817eb955bdf639b530bba819c0a20a31cecf648c97e64b94af0110f23"
    
    tokens = [token_log, unquote(token_log), token_cookie, unquote(token_cookie), lpk]
    
    # Candidate Paths
    full_url = "https://streaming-ebook.books.com.tw/V1.0/Streaming/book/494F95/10448821/META-INF/container.xml"
    paths = [
        "/V1.0/Streaming/book/494F95/10448821/META-INF/container.xml",
        "V1.0/Streaming/book/494F95/10448821/META-INF/container.xml",
        "/Streaming/book/494F95/10448821/META-INF/container.xml",
        "Streaming/book/494F95/10448821/META-INF/container.xml",
        "/book/494F95/10448821/META-INF/container.xml",
        "book/494F95/10448821/META-INF/container.xml",
        "/book/494F95/10448821//META-INF/container.xml", # Double slash
        "book/494F95/10448821//META-INF/container.xml",
        "/494F95/10448821/META-INF/container.xml",
        "494F95/10448821/META-INF/container.xml",
        "/META-INF/container.xml",
        "META-INF/container.xml",
        "/container.xml",
        "container.xml",
        "META-INF/container.xml".lower(),
        full_url,
        full_url.replace("/META-INF", "//META-INF")
    ]

    for t_idx, t in enumerate(tokens):
        for p in paths:
            try:
                key = generate_key(p, t)
                if key == target_key:
                    print(f"🎉 FOUND! Token #{t_idx}, Path: {p}")
                    return
            except Exception:
                pass
    
    print("No match found.")

if __name__ == "__main__":
    test_find_params()
