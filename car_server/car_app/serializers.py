from rest_framework import serializers
from .models import Company, CustomUser, Notice, Vehicle, DrivingRecord
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
        user.set_password(validated_data['password'])
        user.save()

        return user



# 사용자 정보 조회 시리얼라이저
class CustomUserSerializer(serializers.ModelSerializer):
    company = CompanySerializer()  # 회사 정보 포함

    class Meta:
        model = CustomUser
        fields = [
            'id',                       # 사용자 ID (자동 생성)
            'email',                    # 이메일
            'phone_number',             # 전화번호
            'company',                  # 회사 정보 (회사 시리얼라이저로 처리)
            'is_admin',                 # 관리자 여부
            'department',               # 부서명
            'position',                 # 직급
            'name',                     # 이름
            'usage_distance',           # 사용 거리
            'unpaid_penalties'          # 미납 과태료
        ]



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
    company_name = serializers.SlugRelatedField(queryset=Company.objects.all(), slug_field='name', source='company')  # 회사명으로 연결

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
            'chassis_number',          # 차대 번호
            'purchase_type',           # 구매 유형 (매매, 리스, 렌트 등)
            'down_payment',            # 선수금
            'deposit',                 # 보증금
            'expiration_date',         # 만기일
            'company_name'             # 회사명 (작성 시 입력)
        ]
        read_only_fields = ['last_user']  # 마지막 사용자는 자동으로 설정되므로 읽기 전용

    def create(self, validated_data):
        company = validated_data.pop('company')
        vehicle = Vehicle.objects.create(**validated_data)
        vehicle.company = company
        vehicle.save()
        return vehicle



# 운행 기록을 처리하는 Serializer
class DrivingRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrivingRecord
        fields = [
            'id',                   # 운행 기록 ID (자동 생성)
            'vehicle',              # 차량 정보 (Vehicle 참조)
            'user',                 # 사용자 정보 (CustomUser 참조) 임시로 자동생성된 id를 사용
            'departure_location',    # 출발지
            'arrival_location',      # 도착지
            'departure_mileage',     # 출발 전 주행거리
            'arrival_mileage',       # 도착 후 주행거리
            'driving_distance',      # 운행 거리 (자동 계산)
            'departure_time',        # 출발 시간
            'arrival_time',          # 도착 시간
            'driving_time',          # 운행 시간 (자동 계산)
            'driving_purpose'        # 운행 목적
        ]
        read_only_fields = ['driving_distance', 'driving_time']  # 운행 거리 및 운행 시간은 자동 계산됨, 프론트에서 포맷팅 필요

    def create(self, validated_data):
        # 운행 거리를 자동으로 계산 (도착 후 주행거리 - 출발 전 주행거리)
        driving_distance = validated_data['arrival_mileage'] - validated_data['departure_mileage']
        # 운행 시간을 자동으로 계산 (도착 시간 - 출발 시간)
        driving_time = validated_data['arrival_time'] - validated_data['departure_time']

        # 새로운 DrivingRecord 객체 생성
        driving_record = DrivingRecord.objects.create(
            vehicle=validated_data['vehicle'],
            user=validated_data['user'],
            departure_location=validated_data['departure_location'],
            arrival_location=validated_data['arrival_location'],
            departure_mileage=validated_data['departure_mileage'],
            arrival_mileage=validated_data['arrival_mileage'],
            driving_distance=driving_distance,
            departure_time=validated_data['departure_time'],
            arrival_time=validated_data['arrival_time'],
            driving_time=driving_time,
            driving_purpose=validated_data['driving_purpose']
        )
        return driving_record