from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from .serializers import RegisterSerializer, LoginSerializer, VehicleSerializer, DrivingRecordSerializer
from .models import CustomUser, Vehicle, DrivingRecord


# 회원가입 요청을 처리하는 View
class RegisterView(APIView):
    """
    회원가입 View
    사용자 데이터를 검증하고, 새로운 사용자 계정을 생성한다.
    """
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)  # 클라이언트로부터 받은 데이터를 시리얼라이저로 전달
        if serializer.is_valid():  # 데이터가 유효한지 검증
            serializer.save()  # 데이터베이스에 사용자 저장
            return Response({"message": "User registered successfully."}, status=status.HTTP_201_CREATED)  # 성공 응답 반환
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # 데이터가 유효하지 않으면 오류 반환


# 로그인 요청을 처리하는 View
class LoginView(APIView):
    """
    로그인 View
    이메일 또는 전화번호와 비밀번호를 받아 JWT 토큰을 발급한다.
    """
    def post(self, request):
        serializer = LoginSerializer(data=request.data)  # 클라이언트로부터 받은 데이터를 시리얼라이저로 전달
        if serializer.is_valid(raise_exception=True):  # 데이터 검증
            user = serializer.validated_data  # 검증된 사용자 데이터
            refresh = RefreshToken.for_user(user)  # 사용자로부터 JWT 토큰 생성
            return Response({
                'refresh': str(refresh),  # Refresh 토큰
                'access': str(refresh.access_token),  # Access 토큰
            }, status=status.HTTP_200_OK)  # 토큰과 함께 성공 응답 반환
        return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)  # 로그인 실패 시 오류 반환



# 차량 목록 및 등록 처리
class VehicleListCreateView(APIView):
    """
    GET: 전체 차량 목록 조회
    POST: 새로운 차량 등록
    """
    def get(self, request):
        vehicles = Vehicle.objects.all()  # 모든 차량 정보 가져오기
        serializer = VehicleSerializer(vehicles, many=True)  # 시리얼라이저로 데이터 직렬화
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            serializer = VehicleSerializer(data=request.data)  # 차량 등록 시리얼라이저
            if serializer.is_valid():
                if request.user.is_authenticated:  # 인증된 사용자일 경우 last_user 설정
                    serializer.save(last_user=request.user)
                else:
                    serializer.save()  # 인증되지 않은 경우 last_user를 설정하지 않음
                return Response(serializer.data, status=status.HTTP_201_CREATED)  # 성공적으로 생성된 경우 응답 반환
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # 유효하지 않은 데이터 오류 응답 반환
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  # 서버 오류 발생 시 예외 처리
        
    

# 특정 차량의 조회, 수정 및 삭제 처리
class VehicleDetailView(APIView):
    """
    GET: 특정 차량 조회
    PUT: 특정 차량 정보 수정
    DELETE: 특정 차량 삭제
    """
    def get(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)  # pk에 해당하는 차량 조회, pk는 자동으로 부여된 차량 아이디, 대충 순서대로 1, 2, 3, ...
        serializer = VehicleSerializer(vehicle)
        return Response(serializer.data)

    def put(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        serializer = VehicleSerializer(vehicle, data=request.data, partial=True)
        if serializer.is_valid():
            if request.user.is_authenticated:
                serializer.save(last_user=request.user)  # 인증된 사용자의 경우 last_user 설정
            else:
                serializer.save()  # 인증되지 않은 경우 last_user는 설정되지 않음
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        vehicle = get_object_or_404(Vehicle, pk=pk)
        vehicle.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# 차량 번호판으로 차량 정보 조회
class VehicleByLicensePlateView(APIView):
    """
    차량 번호판(license_plate_number)으로 차량 정보를 조회하는 API
    """
    def get(self, request, license_plate_number):
        # 번호판으로 차량을 조회
        vehicle = get_object_or_404(Vehicle, license_plate_number=license_plate_number)
        serializer = VehicleSerializer(vehicle)
        return Response(serializer.data, status=status.HTTP_200_OK)



# 운행 기록 목록 및 생성 처리
class DrivingRecordListCreateView(APIView):
    """
    GET: 전체 운행 기록 목록 조회
    POST: 새로운 운행 기록 생성
    """
    def get(self, request):
        records = DrivingRecord.objects.all()  # 모든 운행 기록 가져오기
        serializer = DrivingRecordSerializer(records, many=True)  # 여러 개의 운행 기록 직렬화
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = DrivingRecordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # 유효성 검사를 통과한 경우 데이터베이스에 저장
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 특정 운행 기록 조회, 수정 및 삭제 처리
class DrivingRecordDetailView(APIView):
    """
    GET: 특정 운행 기록 조회
    PUT: 특정 운행 기록 수정
    DELETE: 특정 운행 기록 삭제
    """
    def get(self, request, pk):
        record = get_object_or_404(DrivingRecord, pk=pk)  # pk로 특정 운행 기록 조회
        serializer = DrivingRecordSerializer(record)
        return Response(serializer.data)

    def put(self, request, pk):
        record = get_object_or_404(DrivingRecord, pk=pk)  # pk로 특정 운행 기록 조회
        serializer = DrivingRecordSerializer(record, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()  # 수정된 내용을 데이터베이스에 저장
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        record = get_object_or_404(DrivingRecord, pk=pk)  # pk로 특정 운행 기록 조회
        record.delete()  # 운행 기록 삭제
        return Response(status=status.HTTP_204_NO_CONTENT)