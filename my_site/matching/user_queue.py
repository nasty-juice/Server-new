from collections import deque
import threading
from .models import UserGroup

class UserQueue:
    def __init__(self):
        self.user_queue = deque()
        self.queue_lock = threading.Lock()
        
    def start_matching(self, user_info):
        # with 문 -> 자원을 관리할때 안전하게 사용하기 위해 사용하는 것임
        # ex) 파일을 열고 사용했으면 프로세스 닫기 등등
        with self.queue_lock:
            if user_info in self.user_queue:
                print(f"User is aleady in queue : {user_info}")
            else:
                self.user_queue.append(user_info)
                print(f"User added to queue: {user_info}")

                self.match_users()  
                #if len(self.user_queue) >= 1:
                #    self.match_users()
    
    def match_users(self):
        with self.queue_lock:
            if len(self.user_queue) < 1:
                return
            
            matched_users = [self.user_queue.popleft() for _ in range(1)]
            print(f"Matched users : {matched_users}")
            
            #유저 그룹 모델 생성 => 방 생성
            user_group = UserGroup()
            #뽑은 유저들을 그룹 모델 안에 집어넣음
            for user in matched_users:
                user_group.users.add(user)
            
    
    def cancel_matching(self, user_info):
        with self.queue_lock:
            if user_info in self.user_queue:
                #큐에서 사용자 제거
                self.user_queue.remove(user_info)
                print(f"User removed : {user_info}")
            else:
                print(f"No User in Waiting List : {user_info}")
                

userQueue = UserQueue()
