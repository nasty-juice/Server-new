from rest_framework import serializers
from django.db import transaction
from my_app.models import CustomUser
from .utils import perform_ocr, get_unknown_fields

class CustomSignupSerializer(serializers.ModelSerializer):
    student_card_image = serializers.ImageField(required=True)
    
    class Meta:
        model = CustomUser
        # fields = ('username', 'email', 'password', 'student_number', 'student_card_image', 'department')
        fields = ('username', 'email', 'password', 'student_number', 'student_card_image')
        # fields = ('username','email', 'password', 'student_number')
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        try:
            with transaction.atomic():
                
                # 사용자 생성
                user = CustomUser(
                    username=validated_data['username'],
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
                    
                #     # OCR 처리
                #     clean_dict = perform_ocr(student_card_image)
                #     print("clean dict: ", clean_dict)

                #     unknown_fields = get_unknown_fields(clean_dict)
                #     if unknown_fields:
                #         raise serializers.ValidationError(f"학생증 인식에 실패한 항목: {', '.join(unknown_fields)}")
                #     user.student_card_data = clean_dict


                # if user.student_card_data.get('student_id') != user.student_number:
                #     raise serializers.ValidationError("학번과 학생증 학번이 일치하지 않습니다.")
                
                # if user.student_card_data.get('korean_name') != user.username:
                #     raise serializers.ValidationError("이름과 학생증 이름이 일치하지 않습니다.")
                
                # if user.student_card_data.get('status') != "재학":
                #     raise serializers.ValidationError("재학생이 아닙니다.")
                
                # user.department = user.student_card_data.get('department')
                user.save()
                
            return user

        except Exception as e:
            raise serializers.ValidationError(f"An error occurred during user creation: {e}")