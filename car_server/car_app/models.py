from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import datetime
import uuid, math



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
    license_plate_number = models.CharField(max_length=10, unique=True)  # 차량 번호(번호판)
    purchase_date = models.DateField()  # 구매 연/월/일
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)  # 구매 가격
    total_mileage = models.PositiveIntegerField()  # 총 주행 거리, 누적 거리
    company = models.ForeignKey('Company', on_delete=models.CASCADE, null=True, blank=True)  # 회사 정보 (Company 모델 참조)
    chassis_number = models.CharField(max_length=50, null=True, blank=True)  # 차대 번호
    purchase_type = models.CharField(max_length=20, choices=[
        ('매매', '매매'),
        ('리스', '리스'),
        ('렌트', '렌트')
    ], default='매매')  # 구매 유형
    current_status = models.CharField(max_length=20, choices=[
        ('가용차량', '가용차량'),
        ('사용불가', '사용불가'),
        ('삭제', '삭제')
    ], default='가용차량')  # 차량 현재 상황 필드
    down_payment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # 선수금 (선택적)
    deposit = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # 보증금 (선택적)
    expiration_date = models.DateField(null=True, blank=True)  # 만기일 (선택적)
    engine_oil_filter = models.PositiveIntegerField(default=0)  # 엔진오일 필터
    aircon_filter = models.PositiveIntegerField(default=0)  # 에어컨 필터
    brake_pad = models.PositiveIntegerField(default=0)  # 브레이크 패드
    tire = models.PositiveIntegerField(default=0)  # 타이어
    last_used_date = models.DateField(null=True, blank=True)  # 마지막 사용일
    last_user = models.ForeignKey('CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='last_vehicle_user')  # 마지막 사용자

    def update_total_mileage(self):
        """
        차량의 누적 주행거리를 가장 최근 운행기록의 도착 거리로 업데이트합니다.
        """
        last_record = self.drivingrecord_set.order_by('-created_at').first()
        if last_record:
            self.total_mileage = last_record.arrival_mileage
            self.save()

    def update_components_usage(self, driving_record):
        """
        운행 기록에서 추가된 주행 거리만큼 각 부품의 사용량을 업데이트합니다.
        """
        driving_distance = driving_record.driving_distance
        self.engine_oil_filter += driving_distance
        self.aircon_filter += driving_distance
        self.brake_pad += driving_distance
        self.tire += driving_distance
        self.save()

    def reset_component_usage(self, component_type):
        """
        특정 부품의 사용량을 0으로 초기화합니다. 정비 완료 후 호출할 수 있습니다.
        """
        if component_type == 'engine_oil_filter':
            self.engine_oil_filter = 0
        elif component_type == 'aircon_filter':
            self.aircon_filter = 0
        elif component_type == 'brake_pad':
            self.brake_pad = 0
        elif component_type == 'tire':
            self.tire = 0
        else:
            raise ValueError(f"Invalid component type: {component_type}")
        self.save()

    def update_last_user_and_date(self, driving_record):
        """
        마지막 사용자를 운행 기록의 사용자로, 마지막 사용일을 운행 기록의 도착 시간으로 업데이트합니다.
        """
        self.last_user = driving_record.user
        self.last_used_date = driving_record.created_at.date()
        self.save()

    def __str__(self):
        return f'{self.vehicle_type} - {self.license_plate_number}'



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
    
    def reset_component_usage(self):
        """
        특정 부품의 사용량을 0으로 초기화합니다.
        """
        if self.maintenance_type == self.ENGINE_OIL_CHANGE:
            self.vehicle.engine_oil_filter = 0
        elif self.maintenance_type == self.AIR_FILTER_CHANGE:
            self.vehicle.aircon_filter = 0
        elif self.maintenance_type == self.BRAKE_PAD_CHANGE:
            self.vehicle.brake_pad = 0
        elif self.maintenance_type == self.TIRE_CHANGE:
            self.vehicle.tire = 0
        self.vehicle.save()

    def save(self, *args, **kwargs):
        """
        정비 기록 저장 시 부품 사용량 초기화 기능을 호출합니다.
        """
        super().save(*args, **kwargs)
        # 정비 완료 후 해당 부품의 사용량 초기화
        self.reset_component_usage()

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
    
    
    def __str__(self):
        return f'{self.vehicle_type} - {self.license_plate_number}'