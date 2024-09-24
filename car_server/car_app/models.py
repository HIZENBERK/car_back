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



# 차량 정보 모델
class Vehicle(models.Model):
    vehicle_type = models.CharField(max_length=20)  # 차종 예: 세단, SUV, 트럭 등
    car_registration_number = models.CharField(max_length=10, unique=True)  # 자동차 등록번호
    license_plate_number = models.CharField(max_length=10, unique=True)  # 차량 번호(번호판)
    purchase_date = models.DateField()  # 구매 연/월/일
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)  # 구매 가격
    total_mileage = models.PositiveIntegerField()  # 총 주행 거리 (정수, 음수 불가)
    last_used_date = models.DateField(null=True, blank=True)  # 마지막 사용일 (비어 있을 수 있음)
    last_user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)  # 마지막 사용자 CustomUser 모델 참조

    def __str__(self):
        return f'{self.vehicle_type} - {self.license_plate_number}'

"""
# 운행 정보 모델
class DrivingRecord(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)  # 차량 정보 참조
    driver = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # 운전자 정보 참조
    start_date = models.DateTimeField()  # 운행 시작 시간
    end_date = models.DateTimeField()  # 운행 종료 시간
    start_mileage = models.PositiveIntegerField()  # 운행 시작 주행 거리
    end_mileage = models.PositiveIntegerField()  # 운행 종료 주행 거리
    distance = models.PositiveIntegerField()  # 운행 거리
    penalty = models.IntegerField(default=0)  # 과태료 (미납 시 증가)

    def __str__(self):
        return f'{self.vehicle} - {self.driver} - {self.start_date}'
"""