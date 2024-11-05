from rest_framework import serializers
from my_app.models import CustomUser
from .utils import perform_ocr, get_unknown_fields

class CustomSignupSerializer(serializers.ModelSerializer):
    # student_card_image = serializers.ImageField(required=True)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'student_number', 'student_card_image')
        # fields = ('username','email', 'password', 'student_number')
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        # 사용자 생성
        user = CustomUser(
            username = validated_data['username'],
            email=validated_data['email'],
            student_number=validated_data['student_number']
        )
        user.set_password(validated_data['password'])
        user.save()
        
        print(user)
        # 학생증 이미지 처리
        student_card_image = validated_data.get('student_card_image')
        if student_card_image:
            new_filename = f"{user.student_number}_student_card.jpg"
            user.student_card_image.save(new_filename, student_card_image)
            
            # OCR 처리
            clean_dict = perform_ocr(student_card_image)
            print("clean dict: " , clean_dict)
            unknown_fields = get_unknown_fields(clean_dict)
            if unknown_fields:
                raise serializers.ValidationError(f"학생증 인식에 실패한 항목: {', '.join(unknown_fields)}")
            
            user.student_card_data = clean_dict
            user.save()
        
        return user