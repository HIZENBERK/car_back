from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import datetime
import uuid



# 회사 정보 모델
class Company(models.Model):
    name = models.CharField(max_length=30)  # 회사명
    business_registration_number = models.CharField(max_length=30, unique=True)  # 사업자 등록 번호 (고유값)
    address = models.CharField(max_length=50, blank=True)  # 회사 주소 (선택적)

    def __str__(self):
        return self.name  # 출력 시 회사명을 반환



# Django 기본 User 모델을 확장하여 필요한 사용자 정보 필드를 추가
class CustomUser(AbstractUser):
    username = models.CharField(max_length=255, unique=False, blank=True, null=True)  # 자동생성 필드임 실제로 사용하지 않음
    email = models.EmailField(unique=True)  # 이메일 필드를 고유값으로 설정
    phone_number = models.CharField(max_length=30, unique=True)  # 전화번호 (고유값)
    department = models.CharField(max_length=30, blank=True)  # 부서명
    position = models.CharField(max_length=30, blank=True)  # 직급
    name = models.CharField(max_length=30)  # 이름
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)  # 회사 모델과의 관계 (선택적)
    usage_distance = models.IntegerField(default=0)  # 사용 거리
    unpaid_penalties = models.IntegerField(default=0)  # 미납 과태료
    is_admin = models.BooleanField(default=False)  # 관리자 여부

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
    license_plate_number = models.CharField(max_length=10, unique=True)  # 차량 번호(번호판) 차량 등록 페이지에서 차량 등록 번호에 해당됨
    purchase_date = models.DateField()  # 구매 연/월/일
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)  # 구매 가격
    total_mileage = models.PositiveIntegerField()  # 총 주행 거리, 누적 거리 (정수, 음수 불가)
    last_used_date = models.DateField(null=True, blank=True)  # 마지막 사용일 (비어 있을 수 있음)
    last_user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)  # 마지막 사용자 CustomUser 모델 참조
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)  # 회사 정보 (Company 모델 참조)
    chassis_number = models.CharField(max_length=50, null=True, blank=True)  # 차대 번호
    purchase_type = models.CharField(max_length=20, choices=[  # 구매 유형 필드
        ('매매', '매매'),
        ('리스', '리스'),
        ('렌트', '렌트')
    ], default='매매')  # 기본값은 '매매'
    down_payment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # 선수금 (위치를 변경)
    deposit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # 보증금 (위치를 변경)
    expiration_date = models.DateField(null=True, blank=True)  # 만기일
    # 차량 등록시 등록일 정보 입력도 있는데 이는 구매 연/월/일로 임시 대체 함
    # 차량 현재 상황을 나타내는 필드 추가해야함(가용차량, 사용불가, 삭제)

    def __str__(self):
        return f'{self.vehicle_type} - {self.license_plate_number}'

"""
# 차량 정기 검사 모델
class RegularInspection(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)  # 차량 참조 (Vehicle 모델 참조)
    inspection_date = models.DateField()  # 정기 검사 만료일
    inspection_agency = models.CharField(max_length=30)  # 검사 기관
    inspection_result = models.BooleanField()  # 검사 결과 (합격/불합격)

    def __str__(self):
        return f'{self.vehicle.vehicle_type} - {self.inspection_date} 정기 검사'
"""

"""
# 차량 정기 검사 등록(게시판 느낌) 모델
정비일자
정비내용(예 : 타이어 교체)
누적주행거리
금액
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
    #json코드로 저장할 출발지 부터 도착지 까지 일정시간마다 저장할 좌표 필드 추가해야함 - 이러면 운행거리랑 생각을 해봐야 함
    
    
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