from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model #현재 프로젝트에서 사용중인 User 모델을 가져옴
from rest_framework.authtoken.models import Token
from urllib.parse import parse_qs #쿼리 문자열을 파싱하기 위한 함수

User = get_user_model()

class TokenAuthMiddleware(BaseMiddleware):
    #WebSocket 연결 시 호출됨
    async def __call__(self, scope, receive, send):
        # 쿼리 문자열에서 토큰 추출
        query_string = scope['query_string'].decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]
        
        if token:
            try:
                # Token을 사용하여 사용자 인증
                user = await self.get_user(token)
                scope['user'] = user
            except Token.DoesNotExist:
                scope['user'] = AnonymousUser()
                print(f'Token not found: {token}')
            except Exception as e:
                # 기타 예외 처리
                scope['user'] = AnonymousUser()
                print(f"Token authentication error: {e}")
        else:
            # 토큰이 없을 때 슈퍼 계정을 인증
            user = await self.get_superuser()
            scope['user'] = user if user else AnonymousUser()

        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, token_key):
        try:
            token = Token.objects.get(key=token_key)
            return token.user
        except Token.DoesNotExist:
            return AnonymousUser()
    
    @database_sync_to_async
    def get_superuser(self):
        try:
            return User.objects.filter(is_superuser=True).first()
        except User.DoesNotExist:
            return AnonymousUser()