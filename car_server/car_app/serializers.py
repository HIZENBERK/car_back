from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

# 회원가입 시 데이터를 검증하고 사용자 생성을 처리하는 Serializer
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})  # 비밀번호 필드
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label="Confirm Password")  # 비밀번호 확인 필드

    class Meta:
        model = CustomUser
        fields = [
            'email',  # 이메일
            'phone_number',  # 전화번호
            'password',  # 비밀번호
            'password2',  # 비밀번호 확인
            'device_uuid',  # 단말기 UUID
            'company_name',  # 법인명
            'business_registration_number',  # 사업자등록번호
            'department',  # 부서
            'position',  # 직급
            'name'  # 이름
        ]
    
    # 비밀번호 검증
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})  # 비밀번호 일치 여부 확인
        try:
            validate_password(attrs['password'])  # Django 기본 비밀번호 유효성 검사
        except ValidationError as e:
            raise serializers.ValidationError({"password": e.messages})
        return attrs

    # 사용자 생성 로직
    def create(self, validated_data):
        validated_data.pop('password2')  # 비밀번호 확인 필드를 제거
        user = CustomUser(**validated_data)  # CustomUser 생성
        user.set_password(validated_data['password'])  # 비밀번호 해싱
        user.save()  # 데이터베이스에 저장
        return user


# 로그인 시 데이터를 검증하고 JWT 토큰을 반환하는 Serializer
class LoginSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()  # 이메일 또는 전화번호
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})  # 비밀번호

    # 로그인 검증 로직
    def validate(self, data):
        email_or_phone = data.get('email_or_phone')
        password = data.get('password')

        # 이메일 또는 전화번호로 사용자 조회
        user = CustomUser.objects.filter(email=email_or_phone).first() or CustomUser.objects.filter(phone_number=email_or_phone).first()

        if user and user.check_password(password):  # 비밀번호 확인
            return user  # 사용자 반환
        raise serializers.ValidationError("Invalid login credentials.")  # 로그인 실패 시 오류 발생
