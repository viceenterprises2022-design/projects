import base64
import json
import gzip
import zlib
import requests

# Let's test imports of cryptography or pycryptodome
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    print("cryptography library is available")
    has_cryptography = True
except ImportError:
    print("cryptography library is NOT available")
    has_cryptography = False

try:
    from Crypto.Cipher import AES
    print("pycryptodome/pycrypto library is available")
    has_pycryptodome = True
except ImportError:
    print("pycryptodome/pycrypto library is NOT available")
    has_pycryptodome = False

# Fetch data first
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://cryptopanic.com/",
    "Origin": "https://cryptopanic.com",
})

print("Fetching CSRF token...")
session.get("https://cryptopanic.com/")
csrf_token = session.cookies.get("csrftoken")
print("CSRF Token:", csrf_token)

url = "https://cryptopanic.com/web-api/posts/"
headers = {"X-CSRFToken": csrf_token}
data = {"filters": json.dumps({})}
r = session.post(url, headers=headers, data=data)
res = r.json()
encrypted_data = res["s"]

# Key derivation: (t + CSRF_TOKEN).substring(0, 16)
# t = "news"
key_str = ("news" + csrf_token)[:16]
print("Key String (16 chars):", key_str)
key_bytes = key_str.encode("utf-8")
iv_bytes = key_bytes

ciphertext = base64.b64decode(encrypted_data)

decrypted_bytes = None
if has_cryptography:
    cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv_bytes), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_bytes = decryptor.update(ciphertext) + decryptor.finalize()
elif has_pycryptodome:
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
    decrypted_bytes = cipher.decrypt(ciphertext)

if decrypted_bytes:
    print("Decrypted raw bytes length:", len(decrypted_bytes))
    print("Decrypted prefix:", decrypted_bytes[:50])
    
    # Now ungzip
    # Let's try zlib/gzip decompress
    try:
        # CryptoJS ZeroPadding leaves zeros at the end. gzip might fail if there's trailing junk,
        # but let's try standard gzip decompress or zlib decompress with gzip header.
        # We can also clean trailing zeros.
        # Wait, zlib decompressing gzip data:
        decompressed = zlib.decompress(decrypted_bytes, 16 + zlib.MAX_WBITS)
        print("Decompressed text length:", len(decompressed))
        # Let's parse JSON
        posts_data = json.loads(decompressed.decode("utf-8"))
        print("Successfully parsed posts JSON!")
        print("Keys in posts JSON:", posts_data.keys() if isinstance(posts_data, dict) else "List of posts")
        if isinstance(posts_data, dict):
            # Print keys
            # Let's print the first post
            print("First item keys:", posts_data.get("k", []))
            print("First item values:", posts_data.get("l", [[]])[0])
        else:
            print("First post:", posts_data[0])
    except Exception as e:
        print("Decompression or JSON parsing failed:", e)
else:
    print("No decryption library available to test!")
