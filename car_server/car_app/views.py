from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from .serializers import RegisterSerializer, CustomUserSerializer, LoginSerializer, VehicleSerializer, DrivingRecordSerializer
from .models import CustomUser, Vehicle, DrivingRecord
from django.db.utils import IntegrityError


# 회원가입 요청을 처리하는 View
class RegisterView(APIView):
    """
    회원가입 View
    사용자 데이터를 검증하고, 새로운 사용자 계정을 생성한다.
    """
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)  # 클라이언트로부터 받은 데이터를 시리얼라이저로 전달
        if serializer.is_valid():  # 데이터가 유효한지 검증
            try:
                serializer.save()  # 데이터베이스에 사용자 저장
                return Response({
                    "message": "회원가입이 성공적으로 완료되었습니다.",
                    "user": serializer.data
                }, status=status.HTTP_201_CREATED)
            except IntegrityError as e:  # IntegrityError 처리
                error_message = str(e)
                # 중복된 필드에 대한 오류 메시지
                if 'customuser.email' in error_message:
                    message = "이미 사용 중인 이메일입니다."
                elif 'customuser.phone_number' in error_message:
                    message = "이미 사용 중인 전화번호입니다."
                else:
                    message = "데이터베이스 무결성 오류가 발생했습니다."

                return Response({
                    "message": "회원가입에 실패했습니다.",
                    "error": message  # 한글로 변환된 오류 메시지 반환
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "message": "회원가입에 실패했습니다.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

class UserListView(APIView):
    """
    GET: 전체 회원 정보 조회
    PATCH: 특정 회원 정보 수정
    DELETE: 특정 회원 삭제
    """
    def get(self, request):
        try:
            users = CustomUser.objects.all()  # 모든 사용자 정보 가져오기
            if users.exists():  # 사용자가 있는 경우
                serializer = CustomUserSerializer(users, many=True)  # 시리얼라이저로 데이터 직렬화
                return Response({
                    "message": "회원 목록 조회가 성공적으로 완료되었습니다.",
                    "users": serializer.data  # 회원 목록 반환
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": "등록된 회원이 없습니다."
                }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": "회원 목록 조회에 실패했습니다.",
                "error": str(e)  # 예외 메시지 반환
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, pk):
        """
        특정 회원 정보 수정
        """
        try:
            user = get_object_or_404(CustomUser, pk=pk)  # 회원 정보 조회
            serializer = CustomUserSerializer(user, data=request.data, partial=True)  # 부분 업데이트 허용
            if serializer.is_valid():
                serializer.save()  # 회원 정보 업데이트
                return Response({
                    "message": "회원 정보가 성공적으로 수정되었습니다.",
                    "user": serializer.data  # 수정된 회원 정보 반환
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": "회원 정보 수정에 실패했습니다.",
                    "errors": serializer.errors  # 유효성 검사 오류 반환
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "message": "회원 정보 수정 중 오류가 발생했습니다.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        """
        특정 회원 삭제
        """
        try:
            user = get_object_or_404(CustomUser, pk=pk)  # 회원 정보 조회
            user.delete()  # 회원 삭제
            return Response({
                "message": "회원이 성공적으로 삭제되었습니다."
            }, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({
                "message": "회원 삭제 중 오류가 발생했습니다.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            
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
            user_info_serializer = CustomUserSerializer(user) # 사용자 정보 시리얼라이저
            return Response({
                "message": "로그인이 성공적으로 완료되었습니다.",
                'refresh': str(refresh),  # Refresh 토큰
                'access': str(refresh.access_token),  # Access 토큰
                'user_info': user_info_serializer.data  # 사용자 정보 반환
            }, status=status.HTTP_200_OK)  # 토큰과 함께 성공 응답 반환

        return Response({
            "message": "로그인에 실패했습니다.",
            "error": "유효하지 않은 자격 증명입니다. 이메일/전화번호 또는 비밀번호를 확인하세요."
        }, status=status.HTTP_400_BAD_REQUEST)  # 로그인 실패 시 오류 반환
    


class LogoutView(APIView):
    """
    POST: 로그아웃 기능 (Refresh Token을 무효화하여 로그아웃 처리)
    """
    def post(self, request):
        try:
            # 클라이언트에서 Refresh Token을 받아 처리
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({
                    "message": "로그아웃에 실패했습니다.",
                    "error": "Refresh Token이 제공되지 않았습니다."
                }, status=status.HTTP_400_BAD_REQUEST)
                
            token = RefreshToken(refresh_token)
            # Refresh Token을 블랙리스트에 추가하여 더 이상 사용할 수 없도록 함
            token.blacklist()

            return Response({
                "message": "성공적으로 로그아웃되었습니다."
            }, status=status.HTTP_205_RESET_CONTENT)
            
        except Exception as e:
            return Response({
                "message": "로그아웃에 실패했습니다.",
                "error": "잘못된 토큰이거나 토큰 처리 중 문제가 발생했습니다."
            }, status=status.HTTP_400_BAD_REQUEST)



# 차량 목록 및 등록 처리
class VehicleListCreateView(APIView):
    """
    GET: 전체 차량 목록 조회
    POST: 새로운 차량 등록
    """
    def get(self, request):
        try:
            vehicles = Vehicle.objects.all()  # 모든 차량 정보 가져오기
            if vehicles.exists():  # 차량이 있는 경우에만 처리
                serializer = VehicleSerializer(vehicles, many=True)  # 시리얼라이저로 데이터 직렬화
                return Response({
                    "message": "차량 목록 조회가 성공적으로 완료되었습니다.",
                    "vehicles": serializer.data  # 차량 목록 반환
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "message": "차량이 존재하지 않습니다."
                }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "message": "차량 목록 조회에 실패했습니다.",
                "error": str(e)  # 예외 메시지 반환
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = VehicleSerializer(data=request.data)  # 차량 등록 시리얼라이저
            if serializer.is_valid():
                if request.user.is_authenticated:  # 인증된 사용자일 경우 last_user 설정
                    serializer.save(last_user=request.user)
                else:
                    serializer.save()  # 인증되지 않은 경우 last_user를 설정하지 않음
                return Response({
                    "message": "차량 등록이 성공적으로 완료되었습니다.",
                    "vehicle": serializer.data  # 등록된 차량 정보 반환
                }, status=status.HTTP_201_CREATED)
            return Response({
                "message": "차량 등록에 실패했습니다.",
                "errors": serializer.errors  # 유효성 검사 실패 시 오류 반환
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "message": "서버 오류가 발생했습니다.",
                "error": str(e)  # 예외 발생 시 오류 메시지 반환
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class VehicleByLicensePlateView(APIView):
    """
    차량 번호판으로 조회, 수정, 삭제가 가능한 API
    """
    def get(self, request, license_plate_number):
        try:
            # 번호판으로 차량 조회
            vehicle = get_object_or_404(Vehicle, license_plate_number=license_plate_number)
            serializer = VehicleSerializer(vehicle)
            return Response({
                "message": "차량 조회가 성공적으로 완료되었습니다.",
                "vehicle": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "message": "차량 조회에 실패했습니다.",
                "error": "요청한 번호판에 해당하는 차량을 찾을 수 없습니다."
            }, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, license_plate_number):
        try:
            vehicle = get_object_or_404(Vehicle, license_plate_number=license_plate_number)  # 번호판으로 차량 조회
            serializer = VehicleSerializer(vehicle, data=request.data, partial=True)  # 부분 업데이트 허용
            if serializer.is_valid():
                if request.user.is_authenticated:
                    serializer.save(last_user=request.user)  # 인증된 사용자의 경우 last_user 설정
                else:
                    serializer.save()  # 인증되지 않은 경우 last_user는 설정되지 않음
                return Response({
                    "message": "차량 정보가 성공적으로 수정되었습니다.",
                    "vehicle": serializer.data
                }, status=status.HTTP_200_OK)
            return Response({
                "message": "차량 정보 수정에 실패했습니다.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "message": "차량 수정에 실패했습니다.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, license_plate_number):
        try:
            vehicle = get_object_or_404(Vehicle, license_plate_number=license_plate_number)  # 번호판으로 차량 조회
            vehicle.delete()  # 차량 삭제
            return Response({
                "message": "차량이 성공적으로 삭제되었습니다."
            }, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({
                "message": "차량 삭제에 실패했습니다.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# 운행 기록 목록 및 생성 처리
class DrivingRecordListCreateView(APIView):
    """
    GET: 전체 운행 기록 목록 조회
    POST: 새로운 운행 기록 생성
    """
    def get(self, request):
        records = DrivingRecord.objects.all()  # 모든 운행 기록 가져오기
        serializer = DrivingRecordSerializer(records, many=True)  # 여러 개의 운행 기록 직렬화
        return Response({
            "message": "운행 기록 목록 조회가 성공적으로 완료되었습니다.",
            "records": serializer.data  # 운행 기록 목록 반환
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = DrivingRecordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # 유효성 검사를 통과한 경우 데이터베이스에 저장
            return Response({
                "message": "운행 기록이 성공적으로 생성되었습니다.",
                "record": serializer.data  # 생성된 운행 기록 반환
            }, status=status.HTTP_201_CREATED)
        return Response({
            "message": "운행 기록 생성에 실패했습니다.",
            "errors": serializer.errors  # 유효성 검사 오류 반환
        }, status=status.HTTP_400_BAD_REQUEST)


# 특정 운행 기록 조회, 수정 및 삭제 처리
class DrivingRecordDetailView(APIView):
    """
    GET: 특정 운행 기록 조회
    PUT: 특정 운행 기록 수정
    DELETE: 특정 운행 기록 삭제
    """
    def get(self, request, pk):
        try:
            record = get_object_or_404(DrivingRecord, pk=pk)  # pk로 특정 운행 기록 조회
            serializer = DrivingRecordSerializer(record)
            return Response({
                "message": "운행 기록 조회가 성공적으로 완료되었습니다.",
                "record": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "message": "운행 기록 조회에 실패했습니다.",
                "error": str(e)
            }, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        record = get_object_or_404(DrivingRecord, pk=pk)  # pk로 특정 운행 기록 조회
        serializer = DrivingRecordSerializer(record, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()  # 수정된 내용을 데이터베이스에 저장
            return Response({
                "message": "운행 기록이 성공적으로 수정되었습니다.",
                "record": serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            "message": "운행 기록 수정에 실패했습니다.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        record = get_object_or_404(DrivingRecord, pk=pk)  # pk로 특정 운행 기록 조회
        record.delete()  # 운행 기록 삭제
        return Response({
            "message": "운행 기록이 성공적으로 삭제되었습니다."
        }, status=status.HTTP_204_NO_CONTENT)


