from rest_framework import serializers
from .models import Company, CustomUser, Notice, Vehicle, DrivingRecord, Maintenance, Expense
from django.db import transaction
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError




# 회사 정보를 처리하는 Serializer
class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = [
            'name',                      # 회사명
            'business_registration_number',  # 사업자 등록 번호
            'address'                   # 회사 주소
        ]



# 관리자 회원가입을 처리하는 Serializer
class RegisterAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})  # 비밀번호 필드
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label="Confirm Password")  # 비밀번호 확인 필드
    business_registration_number = serializers.CharField(write_only=True, required=True)  # 사업자 등록번호를 별도로 입력받음
    company_name = serializers.CharField(write_only=True, required=True)  # 회사명을 별도로 입력받음
    company_address = serializers.CharField(write_only=True, required=False)  # 회사 주소 입력 (선택적)

    class Meta:
        model = CustomUser
        fields = [
            'email',                     # 이메일
            'phone_number',              # 전화번호
            'password',                  # 비밀번호
            'password2',                 # 비밀번호 확인
            'business_registration_number',  # 사업자 등록번호
            'company_name',              # 회사명
            'company_address',           # 회사 주소 (선택적)
            'department',                # 부서명
            'position',                  # 직급
            'name'                       # 이름
        ]
        extra_kwargs = {
            'is_admin': {'default': True},  # 기본적으로 관리자로 설정
        }

    # 이메일 중복 검증
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 존재하는 이메일입니다.")
        return value

    # 전화번호 중복 검증
    def validate_phone_number(self, value):
        if CustomUser.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("이미 존재하는 전화번호입니다.")
        return value

    # 비밀번호 검증
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})  # 비밀번호 일치 여부 확인
        try:
            validate_password(attrs['password'])  # Django 기본 비밀번호 유효성 검사
        except ValidationError as e:
            raise serializers.ValidationError({"password": e.messages})
        return attrs

    @transaction.atomic  # 트랜잭션 시작
    def create(self, validated_data):
        # 회사 정보 저장 또는 조회
        business_registration_number = validated_data.pop('business_registration_number')
        company_name = validated_data.pop('company_name')
        company_address = validated_data.pop('company_address', '')

        company, created = Company.objects.get_or_create(
            business_registration_number=business_registration_number,
            defaults={'name': company_name, 'address': company_address}
        )

        try:
            # 관리자 정보 저장 시도
            validated_data.pop('password2')
            user = CustomUser(**validated_data)
            user.company = company  # 회사 정보 연결
            user.set_password(validated_data['password'])
            user.is_admin = True  # 관리자로 설정
            user.save()

            return user
        except Exception as e:
            if created:
                company.delete()  # 관리자 저장 실패 시, 새로 생성된 회사 정보 롤백
            raise serializers.ValidationError({"error": "관리자 정보 저장에 실패했습니다. 오류: " + str(e)})



# 일반 사용자 회원가입을 처리하는 Serializer
class RegisterUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'}, label="Confirm Password")
    company_name = serializers.CharField(source='company.name', read_only=True)  # 회사명만 포함 (읽기 전용)

    class Meta:
        model = CustomUser
        fields = [
            'email',                     # 이메일
            'phone_number',              # 전화번호
            'password',                  # 비밀번호
            'password2',                 # 비밀번호 확인
            'company_name',              # 회사 이름 (읽기 전용)
            'department',                # 부서명
            'position',                  # 직급
            'name'                       # 이름
        ]

    # 이메일 중복 검증
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 존재하는 이메일입니다.")
        return value

    # 전화번호 중복 검증
    def validate_phone_number(self, value):
        if CustomUser.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("이미 존재하는 전화번호입니다.")
        return value

    # 비밀번호 검증
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "비밀번호가 일치하지 않습니다."})
        try:
            validate_password(attrs['password'])  # Django 기본 비밀번호 유효성 검사
        except ValidationError as e:
            raise serializers.ValidationError({"password": e.messages})
        return attrs

    # 사용자 정보 저장
    def create(self, validated_data):
        validated_data.pop('password2')  # 비밀번호 확인 필드 제거
        request = self.context.get('request')  # 요청 객체 가져오기
        admin_user = request.user  # 현재 로그인한 관리자
        company = admin_user.company  # 관리자의 회사 정보 가져오기

        # 사용자 생성
        user = CustomUser(**validated_data)
        user.company = company  # 관리자의 회사 정보 설정
        user.is_admin = False  # 일반 사용자로 설정
        user.is_banned = False  # 사용자 차단 여부(기본 False)
        user.set_password(validated_data['password'])
        user.save()

        return user
    
    



# 사용자 정보 조회 시리얼라이저
class CustomUserSerializer(serializers.ModelSerializer):
    company = CompanySerializer()  # 회사 정보 포함
    password = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'}, label="Password")
    password2 = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'}, label="Confirm Password")

    class Meta:
        model = CustomUser
        fields = [
            'id',                       # 사용자 ID (자동 생성)
            'email',                    # 이메일
            'phone_number',             # 전화번호
            'company',                  # 회사 정보 (회사 시리얼라이저로 처리)
            'is_admin',                 # 관리자 여부
            'is_banned',                # 차단 여부
            'department',               # 부서명
            'position',                 # 직급
            'name',                     # 이름
            'usage_distance',           # 사용 거리
            'unpaid_penalties',         # 미납 과태료
            'created_at',               # 생성 일시
            'password',                 # 비밀번호 (작성 전용)
            'password2'                 # 비밀번호 확인 (작성 전용)
        ]
        read_only_fields = ['is_admin', 'created_at']  # 읽기 전용 필드 설정
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},  # 비밀번호는 작성 전용으로 설정, 필수 아님
        }

    def validate(self, attrs):
        # 비밀번호와 비밀번호 확인이 일치하는지 확인
        password = attrs.get('password')
        password2 = attrs.pop('password2', None)
        if password and password != password2:
            raise serializers.ValidationError({"password": "비밀번호가 일치하지 않습니다."})
        
        # Django 기본 비밀번호 유효성 검사
        if password:
            try:
                validate_password(password)
            except ValidationError as e:
                raise serializers.ValidationError({"password": e.messages})

        return attrs

    def update(self, instance, validated_data):
        # 비밀번호가 있으면 set_password()를 사용하여 안전하게 설정
        password = validated_data.pop('password', None)
        validated_data.pop('password2', None)  # 비밀번호 확인 필드 제거
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)  # Django 기본 메서드를 사용하여 비밀번호 해싱 후 저장
        instance.save()
        return instance






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
        raise serializers.ValidationError("로그인 정보가 올바르지 않습니다.")  # 로그인 실패 시 오류 발생



# 공지사항 Serializer
class NoticeSerializer(serializers.ModelSerializer):
    company_name = serializers.SerializerMethodField()  # 회사 이름을 반환하는 필드 추가
    created_by_name = serializers.SerializerMethodField()  # 작성자 이름을 반환하는 필드 추가
    
    class Meta:
        model = Notice  # 공지사항 모델과 연결
        fields = [  # 시리얼라이저에 포함할 필드 목록
            'id',  # 공지사항 ID (자동 생성)
            'company_name',  # 공지사항을 등록한 회사 (회사 정보)
            'title',  # 공지사항 제목
            'content',  # 공지사항 내용
            'created_at',  # 공지사항 생성 일시
            'updated_at',  # 공지사항 수정 일시
            'created_by_name'  # 공지사항 작성자 정보
        ]
        read_only_fields = [  # 읽기 전용 필드 (자동으로 설정되는 값)
            'created_at',  # 생성 일시는 자동 생성되므로 읽기 전용
            'updated_at',  # 수정 일시는 자동 갱신되므로 읽기 전용
        ]
        
    def get_company_name(self, obj):
        return obj.company.name  # 회사 이름 반환

    def get_created_by_name(self, obj):
        return obj.created_by.name  # 작성자 이름 반환



# 차량 정보를 처리하는 Serializer
class VehicleSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)  # 로그인한 사용자의 회사명 반환
    last_user = serializers.CharField(source='last_user.name', read_only=True)  # 마지막 사용자 반환
    last_used_date = serializers.DateField(read_only=True)  # 마지막 사용일 반환

    class Meta:
        model = Vehicle
        fields = [
            'id',                     # 차량 ID (자동 생성)
            'vehicle_category',        # 차량 카테고리 (내연기관, 전기차, 수소차 등)
            'vehicle_type',            # 차종 (예: K3, 아반떼 등)
            'car_registration_number', # 자동차 등록번호
            'license_plate_number',    # 차량 번호(번호판)
            'purchase_date',           # 구매 연/월/일
            'purchase_price',          # 구매 가격
            'total_mileage',           # 총 주행 거리
            'last_used_date',          # 마지막 사용일
            'last_user',               # 마지막 사용자 (자동 설정)
            'car_icon',                # 차량 아이콘 (이미지)
            'chassis_number',          # 차대 번호
            'purchase_type',           # 구매 유형 (매매, 리스, 렌트 등)
            'current_status',          # 차량 현재 상황 (가용차량, 사용불가, 삭제)
            'down_payment',            # 선수금
            'deposit',                 # 보증금
            'expiration_date',         # 만기일
            'company_name'             # 회사명 (자동 설정)
        ]
        read_only_fields = ['last_user', 'last_used_date', 'company_name']  # 마지막 사용자와 회사명은 자동으로 설정되므로 읽기 전용

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['company'] = request.user.company  # 로그인한 사용자의 회사로 자동 설정
        vehicle = Vehicle.objects.create(**validated_data)
        return vehicle



# 정비 기록을 처리하는 Serializer
class MaintenanceSerializer(serializers.ModelSerializer):
    vehicle_info = serializers.SerializerMethodField()  # 차량 정보 추가
    maintenance_type_display = serializers.CharField(source='get_maintenance_type_display', read_only=True)  # 정비 유형의 표시용 값을 반환

    class Meta:
        model = Maintenance
        fields = [
            'id',                    # 정비 기록 ID (자동 생성)
            'vehicle',               # 차량 참조
            'vehicle_info',          # 차량 정보 (추가 필드)
            'maintenance_date',      # 정비 일자
            'maintenance_type',      # 정비 유형 (코드 값)
            'maintenance_type_display',  # 정비 유형 (표시용 값)
            'maintenance_cost',      # 정비 비용
            'maintenance_description', # 정비 내용
            'created_at'             # 생성 일시
        ]
        read_only_fields = ['created_at', 'maintenance_type_display']  # 읽기 전용 필드 설정

    def get_vehicle_info(self, obj):
        return {
            "vehicle_type": obj.vehicle.vehicle_type,
            "license_plate_number": obj.vehicle.license_plate_number,
            "company": obj.vehicle.company.name if obj.vehicle.company else None
        }



# 운행 기록을 처리하는 Serializer
class DrivingRecordSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)  # 사용자 이름 추가
    vehicle_type = serializers.CharField(source='vehicle.vehicle_type', read_only=True)  # 차량 차종 추가
    vehicle_license_plate_number = serializers.CharField(source='vehicle.license_plate_number', read_only=True)  # 차량 번호판 추가

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())  # 로그인한 사용자의 계정을 자동 설정

    class Meta:
        model = DrivingRecord
        fields = [
            'id',                            # 운행 기록 ID (자동 생성)
            'vehicle',                       # 차량 참조 (직접 선택)
            'user',                          # 사용자 (로그인한 사용자로 자동 설정)
            'user_id',                       # 사용자 ID (자동 설정)
            'user_name',                     # 사용자 이름
            'vehicle_type',                  # 차량 차종
            'vehicle_license_plate_number',  # 차량 번호판
            'departure_location',            # 출발지
            'arrival_location',              # 도착지
            'departure_mileage',             # 출발 전 누적 주행거리
            'arrival_mileage',               # 도착 후 누적 주행거리
            'driving_distance',              # 운행 거리
            'departure_time',                # 출발 시간
            'arrival_time',                  # 도착 시간
            'driving_time',                  # 운행 시간
            'coordinates',                   # 주기적으로 저장된 좌표 정보
            'driving_purpose',               # 운행 목적
            'fuel_cost',                     # 유류비
            'toll_fee',                      # 통행료
            'other_costs',                   # 기타 비용
            'total_cost',                    # 합계 비용
            'created_at'                     # 생성 일시
        ]
        read_only_fields = ['driving_distance', 'driving_time', 'created_at']  # 읽기 전용 필드 설정

    def validate(self, data):
        # 출발 주행거리와 도착 주행거리가 올바른지 확인
        if data['arrival_mileage'] < data['departure_mileage']:
            raise serializers.ValidationError("도착 주행거리는 출발 주행거리보다 크거나 같아야 합니다.")
        return data

    def create(self, validated_data):
        # 운행 거리 및 운행 시간 계산
        validated_data['driving_distance'] = validated_data['arrival_mileage'] - validated_data['departure_mileage']
        validated_data['driving_time'] = validated_data['arrival_time'] - validated_data['departure_time']
        
        # 운행 기록 생성
        record = super().create(validated_data)

        # 차량의 누적 주행 거리 업데이트
        record.vehicle.total_mileage = validated_data['arrival_mileage']
        record.vehicle.save()

        # 차량의 엔진오일 필터, 에어컨 필터, 브레이크 패드, 타이어의 사용량 업데이트
        record.vehicle.update_components_usage(record)

        # 차량의 마지막 사용일과 마지막 사용자 업데이트
        record.vehicle.update_last_user_and_date(record)
        
        return record



# 지출 내역을 처리하는 Serializer
class ExpenseSerializer(serializers.ModelSerializer):
    user_info = serializers.SerializerMethodField()  # 사용자 정보 추가
    vehicle_info = serializers.SerializerMethodField()  # 차량 정보 추가

    class Meta:
        model = Expense
        fields = [
            'id',                   # 지출 내역 ID
            'expense_type',         # 지출 구분
            'expense_date',         # 지출 일자
            'status',               # 상태
            'user',                 # 사용자 (ID)
            'user_info',            # 사용자 정보 (추가 필드)
            'vehicle',              # 차량 (ID)
            'vehicle_info',         # 차량 정보 (추가 필드)
            'details',              # 지출 및 정비 상세 내용
            'payment_method',       # 결제 수단
            'amount',               # 금액
            'receipt_detail',       # 영수증 상세
            'created_at'            # 생성 일시
        ]
        read_only_fields = ['created_at']

    def get_user_info(self, obj):
        return {
            "name": obj.user.name,
            "department": obj.user.department,
            "position": obj.user.position
        }

    def get_vehicle_info(self, obj):
        if obj.vehicle:
            return {
                "vehicle_type": obj.vehicle.vehicle_type,
                "license_plate_number": obj.vehicle.license_plate_number,
                "company": obj.vehicle.company.name
            }
        return None