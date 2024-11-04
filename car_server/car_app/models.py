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
    email = models.EmailField(unique=True)  # 이메일 필드를 고유값으로
    phone_number = models.CharField(max_length=30, unique=True)  # 전화번호 (고유값)
    department = models.CharField(max_length=30, blank=True)  # 부서명
    position = models.CharField(max_length=30, blank=True)  # 직급
    name = models.CharField(max_length=30)  # 이름
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True)  # 회사 모델과의 관계 (선택적)
    usage_distance = models.IntegerField(default=0)  # 사용 거리
    unpaid_penalties = models.IntegerField(default=0)  # 미납 과태료
    is_admin = models.BooleanField(default=False)  # 관리자 여부
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 일시



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



# 공지사항 모델
class Notice(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)  # 공지사항을 등록한 회사 참조
    title = models.CharField(max_length=100)  # 공지사항 제목
    content = models.TextField()  # 공지사항 내용
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 일시
    updated_at = models.DateTimeField(auto_now=True)  # 업데이트 일시
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # 공지사항 작성자 (관리자만)

    def __str__(self):
        return self.title



# 차량 정보 모델
class Vehicle(models.Model):
    vehicle_category = models.CharField(max_length=10)  # 차량 카테고리 예: 내연기관, 전기차, 수소차 등
    vehicle_type = models.CharField(max_length=20)  # 차종 예: K3, 아반떼, K5, 소나타 등
    car_registration_number = models.CharField(max_length=10, unique=True)  # 자동차 등록번호
    license_plate_number = models.CharField(max_length=10, unique=True)  # 차량 번호(번호판) 차량 등록 페이지에서 차량 등록 번호에 해당됨
    purchase_date = models.DateField()  # 구매 연/월/일
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)  # 구매 가격
    total_mileage = models.PositiveIntegerField()  # 총 주행 거리, 누적 거리 (정수, 음수 불가)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True)  # 회사 정보 (Company 모델 참조)
    chassis_number = models.CharField(max_length=50, null=True, blank=True)  # 차대 번호 Vehicle identification number로 바꿔야함
    purchase_type = models.CharField(max_length=20, choices=[  # 구매 유형 필드
        ('매매', '매매'),
        ('리스', '리스'),
        ('렌트', '렌트')
    ], default='매매')  # 기본값은 '매매'
    current_status = models.CharField(max_length=20, choices=[
        ('가용차량', '가용차량'),
        ('사용불가', '사용불가'),
        ('삭제', '삭제')
    ], default='가용차량')  # 차량 현재 상황 필드
    down_payment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # 선수금 (선택적)
    deposit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # 보증금 (선택적)
    expiration_date = models.DateField(null=True, blank=True)  # 만기일 (선택적)
    
    @property #마지막 사용자를 최신 운행기록을 기준으로 가져오기
    def last_user(self):
        last_record = self.drivingrecord_set.order_by('-arrival_time').first()
        if last_record:
            return last_record.user
        return None

    def __str__(self):
        return f'{self.vehicle_type} - {self.license_plate_number}'

    def __str__(self):
        return f'{self.vehicle_type} - {self.license_plate_number}'



    # 모델 저장 시 운행 거리 및 운행 시간 계산
    def save(self, *args, **kwargs):
        from .models import Vehicle # 임포트 순환 참조 방지를 위해 함수 내부에서 임포트
        # 출발 전 누적 주행거리를 차량 모델의 누적 거리에서 가져오기
        if not self.pk:  # 새로운 운행 기록일 경우에만 설정
            self.departure_mileage = self.vehicle.total_mileage
    
        # 운행 거리 계산
        self.driving_distance = self.arrival_mileage - self.departure_mileage
        # 운행 시간 계산
        self.driving_time = self.arrival_time - self.departure_time

        # 도착 후 누적 주행거리를 차량 정보에 저장
        self.vehicle.total_mileage = self.arrival_mileage
        self.vehicle.save()
    
        super(DrivingRecord, self).save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.name} - {self.vehicle.vehicle_type} 운행 기록'



# 정비 기록 모델
class Maintenance(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)  # 차량 참조 (Vehicle 모델 참조)
    maintenance_date = models.DateField()  # 정비 일자
    
    # 정비 유형 Choices 설정
    ENGINE_OIL_CHANGE = 'engine_oil_change'
    AIR_FILTER_CHANGE = 'air_filter_change'
    BRAKE_PAD_CHANGE = 'brake_pad_change'
    TIRE_CHANGE = 'tire_change'
    OTHER = 'other'
    MAINTENANCE_TYPE_CHOICES = [
        (ENGINE_OIL_CHANGE, '엔진 오일 교체'),
        (AIR_FILTER_CHANGE, '에어컨 필터 교체'),
        (BRAKE_PAD_CHANGE, '브레이크 패드 교체'),
        (TIRE_CHANGE, '타이어 교체'),
        (OTHER, '기타')
    ]
    
    maintenance_type = models.CharField(
        max_length=20,
        choices=MAINTENANCE_TYPE_CHOICES,
        default=OTHER
    )  # 정비 유형
    maintenance_cost = models.DecimalField(max_digits=10, decimal_places=2)  # 정비 비용
    maintenance_description = models.TextField()  # 정비 내용
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 일시

    def __str__(self):
        return f'{self.vehicle.vehicle_type} - {self.maintenance_type} 정비 기록'



# 지출 관리 모델
class Expense(models.Model):
    EXPENSE = 'expense'
    MAINTENANCE = 'maintenance'
    EXPENSE_TYPE_CHOICES = [
        (EXPENSE, '지출'),
        (MAINTENANCE, '정비')
    ]
    
    APPROVED = 'approved'
    PENDING = 'pending'
    REJECTED = 'rejected'
    STATUS_CHOICES = [
        (APPROVED, '승인'),
        (PENDING, '대기'),
        (REJECTED, '반려')
    ]
    
    expense_type = models.CharField(
        max_length=20,
        choices=EXPENSE_TYPE_CHOICES,
        default=EXPENSE
    )  # 구분
    expense_date = models.DateField()  # 지출 일자
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING
    )  # 상태
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # 사용자 (커스텀 유저 참조)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)  # 차량 (선택적)
    details = models.TextField()  # 상세내용
    payment_method = models.CharField(max_length=50)  # 결제수단
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # 금액
    receipt_detail = models.FileField(upload_to='receipts/', null=True, blank=True)  # 영수증 상세 (첨부파일)
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 일시

    def __str__(self):
        return f'{self.get_expense_type_display()} - {self.amount}원 지출 내역'




# 운행 기록 모델
class DrivingRecord(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)  # 차량 참조 (Vehicle 모델 참조)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)  # 사용자 참조 (CustomUser 모델 참조)
    departure_location = models.CharField(max_length=30)  # 출발지
    arrival_location = models.CharField(max_length=30)  # 도착지
    departure_mileage = models.PositiveIntegerField()  # 출발 전 누적 주행거리 차량 정보에서 가져 옴
    arrival_mileage = models.PositiveIntegerField()  # 도착 후 누적 주행거리 차량 정보에 저장 함
    driving_distance = models.PositiveIntegerField(editable=False)  # 운행거리 (도착 후 주행거리 - 출발 전 주행거리)
    departure_time = models.DateTimeField()  # 출발 시간
    arrival_time = models.DateTimeField()  # 도착 시간
    driving_time = models.DurationField(editable=False)  # 운행 시간 (도착 시간 - 출발 시간)
    coordinates = models.JSONField()  # 차량 이동 중 주기적으로 저장된 좌표 정보
    created_at = models.DateTimeField(auto_now_add=True)  # 생성 일시

    # 운행 중 발생한 정비 기록
    maintenances = models.ManyToManyField(Maintenance, blank=True)  # 운행 중 발생한 정비 기록 (Many to Many)

    # 운행 중 발생한 지출 내역
    expenses = models.ManyToManyField(Expense, blank=True)  # 운행 중 발생한 지출 내역 (Many to Many)

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