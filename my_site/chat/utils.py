from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
import os
from my_site.settings import BASE_DIR

#개인 키 불러오기
private_key_path = os.path.join(BASE_DIR, "keys", "private_key.pem")
with open(private_key_path, "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(),password=None)
#공개 키 불러오기
public_key_path = os.path.join(BASE_DIR, "keys", "public_key.pem")
with open(public_key_path, "rb") as f:
    public_key = serialization.load_pem_public_key(f.read())
    
#채팅방에 입장해 있는 모든 유저 데이터 확인
def check_all_user_in_chatroom(chat_room):
    users = chat_room.users.all()
    userInfo = []
    for user in users:
        userInfo.append({
            'user_name' : user.username,
            'user_number' : user.student_number,
            'user_temperature' : str(user.temperature)
        })
    return userInfo

#채팅방에 있는 기존 대화 텍스트 불러오기(복호화)
def get_db_chatroom_messages(chatroom):
    messages = chatroom.messages.all().order_by('created_at')
    decrypted_messages = []
    
    for message in messages:
        try:
            if message.is_system:
                decrypted_messages.append({
                    'user_name' : "SYSTEM",
                    'message' : decrypt_message(message.message),
                    'timestamp' : message.created_at.isoformat()
                })
                continue
            
            decrypted_messages.append({
                'user_name' : message.user.username,
                'message' : decrypt_message(message.message),
                'timestamp' : message.created_at.isoformat()
            })
        except Exception as e:
            print(f"메시지 복호화 실패: {e}")

    return decrypted_messages
     
     
#텍스트 암호화
def encrypt_message(message):
    try:
        encrypted_message = public_key.encrypt(
            str(message).encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted_message
    except Exception as e:
        print(f"메시지 암호화 실패: {e}")
        return None

#텍스트 복호화
def decrypt_message(encrypted_message):
    try:
        decrypted_message = private_key.decrypt(
            encrypted_message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        ).decode()
        return decrypted_message
    
    except Exception as e:
        print(f"메시지 복호화 실패: {e}")
        return None