from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


#차계부 모델


# 사용자 생성을 관리하는 UserManager 클래스 정의
class UserManager(BaseUserManager):
    # 일반 사용자 생성 함수
    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        if not email and not phone_number:
            raise ValueError('이메일 또는 전화번호를 입력해야 합니다.')

        # 이메일 정규화
        if email:
            email = self.normalize_email(email)

        # 사용자 인스턴스 생성
        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)  # 비밀번호 해시 처리
        user.save(using=self._db)
        return user

    # 관리자(슈퍼유저) 생성 함수
    def create_superuser(self, email=None, phone_number=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email=email, phone_number=phone_number, password=password, **extra_fields)

# 사용자 모델(User) 정의
class User(AbstractBaseUser, PermissionsMixin):
    # 로그인에 사용할 필드
    email = models.EmailField(unique=True, blank=True, null=True)  # 이메일 (로그인 가능)
    phone_number = models.CharField(max_length=15, unique=True, blank=True, null=True)  # 전화번호 (로그인 가능)

    # 추가적인 사용자 정보 필드
    device_uuid = models.CharField(max_length=255, blank=True)  # 단말기 UUID
    company_name = models.CharField(max_length=255, blank=True)  # 법인명 (회사명)
    business_registration_number = models.CharField(max_length=20, blank=True)  # 사업자등록번호
    department = models.CharField(max_length=100, blank=True)  # 부서
    position = models.CharField(max_length=100, blank=True)  # 직급
    name = models.CharField(max_length=100, blank=True)  # 이름
    usage_distance = models.IntegerField(default=0)  # 사용 거리 (단위: km)
    unpaid_penalties = models.IntegerField(default=0)  # 미납 과태료 (단위: 원)

    # 사용자 상태 정보
    is_active = models.BooleanField(default=True)  # 계정 활성화 여부
    is_staff = models.BooleanField(default=False)  # 관리자 여부
    
    # groups 및 user_permissions에 관련된 필드에서 충돌 방지를 위한 related_name 설정
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='car_app_users',  # 기본 auth.User와의 충돌 방지
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='car_app_user_permissions',  # 기본 auth.User와의 충돌 방지
        blank=True
    )
    
    # UserManager를 사용하여 사용자 생성 관리
    objects = UserManager()

    # 로그인 시 사용할 필드를 설정 (이메일 또는 전화번호로 로그인 가능)
    USERNAME_FIELD = 'email'  # 기본 이메일로 로그인
    REQUIRED_FIELDS = ['phone_number']  # 필수 필드로 전화번호 설정

    def __str__(self):
        return self.email if self.email else self.phone_number  # 이메일 또는 전화번호 반환
