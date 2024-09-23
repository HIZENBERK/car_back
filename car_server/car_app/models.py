from django.contrib.auth.models import AbstractUser
from django.db import models

# Django 기본 User 모델을 확장하여 필요한 사용자 정보 필드를 추가
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)  # 이메일 필드를 고유값으로 설정
    phone_number = models.CharField(max_length=30, unique=True)  # 전화번호 (고유값)
    device_uuid = models.CharField(max_length=30)  # 단말기 UUID
    company_name = models.CharField(max_length=30)  # 회사명
    business_registration_number = models.CharField(max_length=30)  # 사업자 등록 번호
    department = models.CharField(max_length=30)  # 부서명
    position = models.CharField(max_length=30)  # 직급
    name = models.CharField(max_length=30)  # 이름
    usage_distance = models.IntegerField(default=0)  # 사용 거리
    unpaid_penalties = models.IntegerField(default=0)  # 미납 과태료

    # 로그인 필드를 이메일로 설정
    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'  # 기본 로그인 필드를 이메일로 설정
    REQUIRED_FIELDS = ['phone_number', 'name']  # 필수 필드를 지정 (전화번호와 이름)

    def __str__(self):
        return self.email  # 출력 시 이메일을 반환
