import re
from django.core.exceptions import ValidationError

def validate_school_email(value):
    school_email_pattern = r'^[^@]+@mju\.ac\.kr$'
    if not re.match(school_email_pattern, value) or value.count('@') != 1:
        raise ValidationError('This email is not a valid school email address.')
    
def validate_student_card_image(value):
    pass