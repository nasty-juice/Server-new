import os
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# BASE_DIR 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 개인 키 생성
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# 공개 키 생성
public_key = private_key.public_key()

# 개인 키를 PEM 형식으로 저장
pem_private_key = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption()
)

# 공개 키를 PEM 형식으로 저장
pem_public_key = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
)

key_dir = os.path.join(BASE_DIR, "keys")

os.makedirs(key_dir, exist_ok=True)

# 키 저장
with open(os.path.join(key_dir, "private_key.pem"), "wb") as f:
    f.write(pem_private_key)

with open(os.path.join(key_dir, "public_key.pem"), "wb") as f:
    f.write(pem_public_key)