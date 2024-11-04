from django.test import TestCase
from django.urls import reverse
from .models import CustomUser, UserGroup, MatchingQueue

class MatchingTestCase(TestCase):
    def setUp(self):
        # 임시 사용자 생성
        self.user1 = CustomUser.objects.create_user(username='testuser1', password='password123')
        self.user2 = CustomUser.objects.create_user(username='testuser2', password='password123')

    def test_start_matching_without_login(self):
        # user1을 큐에 추가
        self.client.force_login(self.user1)
        response = self.client.post(reverse('start_matching'), follow=True)
        #self.assertEqual(response.status_code, 200)  # 대기 상태 확인
        self.assertEqual(response.json().get('status'), 'waiting')  # 대기 상태 확인

        # user2를 큐에 추가
        self.client.force_login(self.user2)  # user2로 로그인
        response = self.client.post(reverse('start_matching'), follow=True)
        #self.assertEqual(response.status_code, 302)  # 리다이렉트 확인

        # 매칭 그룹이 생성되었는지 확인
        group = UserGroup.objects.first()
        self.assertIsNotNone(group)  # 그룹이 생성되었는지 확인
        self.assertIn(self.user2, group.users.all())  # user2가 그룹에 포함되어 있는지 확인

        # 큐에서 user2가 제거되었는지 확인
        #self.assertFalse(MatchingQueue.objects.filter(user=self.user2).exists())

    def tearDown(self):
        # 테스트 후 데이터 정리
        CustomUser.objects.all().delete()
        MatchingQueue.objects.all().delete()
        UserGroup.objects.all().delete()
