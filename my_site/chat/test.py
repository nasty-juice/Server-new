from cryptography.fernet import Fernet

# Fernet 키 생성
key = Fernet.generate_key()
print("Key : "+key.decode())  