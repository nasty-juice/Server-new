import re
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

def validate_school_email(value):
    school_email_pattern = r'^[^@]+@mju\.ac\.kr$'
    if not re.match(school_email_pattern, value) or value.count('@') != 1:
        raise ValidationError('This email is not a valid school email address.')
    
# 이미지 확장자 유효성 검사
validate_image_extension = FileExtensionValidator(allowed_extensions=['png', 'jpg'])
