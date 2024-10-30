# my_app/forms.py
from django import forms
from django.utils.html import format_html
from django.conf import settings

class AdminImageWidget(forms.ClearableFileInput):
   def render(self, name, value, attrs=None, renderer=None):
        # value가 있고 이미지 파일이 존재할 때만 링크 생성
        if value and hasattr(value, "url"):
            # private-media 경로로 링크를 생성
            image_url = f"{settings.BASE_URL}/my_app/private-media/{value.name}"
            # 현재 파일명을 클릭할 수 있는 링크로 표시
            return format_html(
                'Currently: <a href="{}" target="_blank">{}</a>',
                image_url,
                value.name
            )
        return super().render(name, value, attrs, renderer)
    