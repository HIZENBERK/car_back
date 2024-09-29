from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import datetime
import uuid

# Django 기본 User 모델을 확장하여 필요한 사용자 정보 필드를 추가
class CustomUser(AbstractUser):
    username = models.CharField(max_length=255, unique=False, blank=True, null=True)  # 자동생성 필드임 실제로 사용하지 않음
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
    
    def save(self, *args, **kwargs): #django username의 무결성 제약 조건 때문에 만든것. 실제로 사용하지 않음
        if not self.username:
            self.username = str(uuid.uuid4())[:8]  # username을 고유한 UUID로 자동 생성
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email  # 출력 시 이메일을 반환



# 차량 정보 모델
class Vehicle(models.Model):
    vehicle_category = models.CharField(max_length=10)  # 차량 카테고리 예: 내연기관, 전기차, 수소차 등
    vehicle_type = models.CharField(max_length=20)  # 차종 예: K3, 아반떼, K5, 소나타 등
    car_registration_number = models.CharField(max_length=10, unique=True)  # 자동차 등록번호
    license_plate_number = models.CharField(max_length=10, unique=True)  # 차량 번호(번호판)
    purchase_date = models.DateField()  # 구매 연/월/일
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)  # 구매 가격
    total_mileage = models.PositiveIntegerField()  # 총 주행 거리 (정수, 음수 불가)
    last_used_date = models.DateField(null=True, blank=True)  # 마지막 사용일 (비어 있을 수 있음)
    last_user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)  # 마지막 사용자 CustomUser 모델 참조
    # 차량 유형 에: 매매, 리스, 렌트 중 선택
    # 차량 현황 예 : '사용중', '사용가능', '수리중', '삭제(리스 만기 등으로 삭제 됨)'
    # 선수금 (null=True, blank=True)
    # 보증금 (null=True, blank=True)
    # 만기일 (null=True, blank=True)

    def __str__(self):
        return f'{self.vehicle_type} - {self.license_plate_number}'

"""
# 차량 정기 검사 모델
class RegularInspection(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)  # 차량 참조 (Vehicle 모델 참조)
    inspection_date = models.DateField()  # 정기 검사 날짜
    inspection_agency = models.CharField(max_length=30)  # 검사 기관
    inspection_result = models.BooleanField()  # 검사 결과 (합격/불합격)

    def __str__(self):
        return f'{self.vehicle.vehicle_type} - {self.inspection_date} 정기 검사'
"""


# 운행 기록 모델
class DrivingRecord(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE) # 차량 참조 (Vehicle 모델 참조)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE) # 사용자 참조 (CustomUser 모델 참조)
    departure_location = models.CharField(max_length=30) # 출발지
    arrival_location = models.CharField(max_length=30) # 도착지
    departure_mileage = models.PositiveIntegerField() # 출발 전 누적 주행거리
    arrival_mileage = models.PositiveIntegerField() # 도착 후 누적 주행거리
    driving_distance = models.PositiveIntegerField(editable=False) # 운행거리 (도착 후 주행거리 - 출발 전 주행거리)
    departure_time = models.DateTimeField() # 출발 시간
    arrival_time = models.DateTimeField() # 도착 시간
    driving_time = models.DurationField(editable=False) # 운행 시간 (도착 시간 - 출발 시간)
    
    # 운행 목적 Choices 설정
    COMMUTING = 'commuting'
    BUSINESS = 'business'
    NON_BUSINESS = 'non_business'
    DRIVING_PURPOSE_CHOICES = [
        (COMMUTING, '출/퇴근'),
        (BUSINESS, '일반업무'),
        (NON_BUSINESS, '비업무')
    ]
    
    # 운행 목적
    driving_purpose = models.CharField(
        max_length=20,
        choices=DRIVING_PURPOSE_CHOICES,
        default=COMMUTING
    )

    # 모델 저장 시 운행 거리 및 운행 시간 계산
    def save(self, *args, **kwargs):
        # 운행 거리 계산
        self.driving_distance = self.arrival_mileage - self.departure_mileage
        # 운행 시간 계산
        self.driving_time = self.arrival_time - self.departure_time
        super(DrivingRecord, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.name} - {self.vehicle.vehicle_type} 운행 기록'