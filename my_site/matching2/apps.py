from django.apps import AppConfig
import redis
import atexit

class Matching2Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'matching2'
    
    def ready(self):
        import matching2.signals
        
        # django 서버가 부팅될떄마다 redis에 저장된 키값을 모두 삭제
        def clear_redis_keys():
            redis_client = redis.Redis(host='localhost', port=6379, db=0)
            keys = redis_client.keys('asgi:group:*')
            if keys:
                redis_client.delete(*keys)
            
            print(f"Deleted keys: {keys}")

        clear_redis_keys()
        
        # 서버가 정상적으로 종료될때 clear_redis_keys 함수를 호출
        # 근데 임의로 서버를 종료하면 호출이 안됨
        atexit.register(clear_redis_keys)
            
