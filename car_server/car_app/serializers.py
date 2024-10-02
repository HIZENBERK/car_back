from rest_framework import serializers
from .models import CustomUser, Vehicle, DrivingRecord
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
    
    #이메일 중복 검증
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 존재하는 이메일입니다.")
        return value
    
    #전화번호 중복 검증
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

    # 사용자 생성 로직
    def create(self, validated_data):
        validated_data.pop('password2')  # 비밀번호 확인 필드를 제거
        user = CustomUser(**validated_data)  # CustomUser 생성
        user.set_password(validated_data['password'])  # 비밀번호 해싱
        user.save()  # 데이터베이스에 저장
        return user

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id',                         # 사용자 ID(자동 생성)
            'email',                      # 이메일
            'phone_number',               # 전화번호
            'device_uuid',                # 단말기 UUID
            'company_name',               # 회사명
            'business_registration_number', # 사업자 등록 번호
            'department',                 # 부서명
            'position',                   # 직급
            'name',                       # 이름
            'usage_distance',             # 사용 거리
            'unpaid_penalties'            # 미납 과태료
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
        raise serializers.ValidationError("Invalid login credentials.")  # 로그인 실패 시 오류 발생


# 차량 정보를 처리하는 Serializer
class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            'id',               # 차량 ID (자동 생성)
            'vehicle_category',       # 차량 카테고리 (내연기관차, 전기차, 수소차 등)
            'vehicle_type',      # 차량 종류
            'car_registration_number',  # 자동차 등록번호
            'license_plate_number',  # 차량 번호(번호판)
            'purchase_date',     # 구매 연/월/일
            'purchase_price',    # 구매 가격
            'total_mileage',     # 총 주행 거리 (정수, 음수 불가)
            'last_used_date',    # 마지막 사용일 (비어 있을 수 있음)
            'last_user',         # 마지막 사용자 (CustomUser 참조)
        ]
        read_only_fields = ['last_user']  # 마지막 사용자는 자동으로 기록될 수 있음


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