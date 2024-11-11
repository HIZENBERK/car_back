from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .serializers import RegisterAdminSerializer, RegisterUserSerializer, CustomUserSerializer, LoginSerializer, NoticeSerializer, VehicleSerializer, DrivingRecordSerializer, MaintenanceSerializer, ExpenseSerializer
from .models import Company, CustomUser, Notice, Vehicle, DrivingRecord, Maintenance, Expense
from django.db.utils import IntegrityError


# 관리자 회원가입을 처리하는 View
class RegisterAdminView(APIView):
    """
    관리자 회원가입 View
    회사 정보와 관리자의 정보를 검증한 후 새로운 관리자 계정을 생성한다.
    """
    def post(self, request):
        serializer = RegisterAdminSerializer(data=request.data)  # 클라이언트로부터 받은 데이터를 시리얼라이저로 전달
        if serializer.is_valid():  # 데이터가 유효한지 검증
            try:
                user = serializer.save()  # 관리자 정보 저장
                return Response({
                    "message": "관리자 회원가입이 성공적으로 완료되었습니다.",
                    "user": CustomUserSerializer(user).data  # 저장된 관리자 정보 반환
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
                    "error": message
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "message": "회원가입에 실패했습니다.",
            "errors": serializer.errors  # 유효성 검사 오류 반환
        }, status=status.HTTP_400_BAD_REQUEST)



# 관리자 전용 로그인 View
class AdminLoginView(APIView):
    """
    관리자 전용 로그인 View
    이메일 또는 전화번호와 비밀번호를 받아 관리자 여부를 확인하고 JWT 토큰을 발급한다.
    """
    permission_classes = [AllowAny]  # 모든 사용자에게 접근 허용
    def post(self, request):
        serializer = LoginSerializer(data=request.data)  # 클라이언트로부터 받은 데이터를 시리얼라이저로 전달
        if serializer.is_valid(raise_exception=True):  # 데이터 검증
            user = serializer.validated_data  # 검증된 사용자 데이터

            # 관리자 여부 확인
            if not user.is_admin:
                return Response({
                    "message": "관리자 전용 페이지입니다. 관리자 계정으로 로그인하세요.",
                    "error": "해당 계정은 관리자 권한이 없습니다."
                }, status=status.HTTP_403_FORBIDDEN)

            refresh = RefreshToken.for_user(user)  # 사용자로부터 JWT 토큰 생성
            user_info_serializer = CustomUserSerializer(user)  # 사용자 정보 시리얼라이저

            return Response({
                "message": "관리자 로그인이 성공적으로 완료되었습니다.",
                'refresh': str(refresh),  # Refresh 토큰
                'access': str(refresh.access_token),  # Access 토큰
                'user_info': user_info_serializer.data  # 사용자 정보 반환
            }, status=status.HTTP_200_OK)

        return Response({
            "message": "로그인에 실패했습니다.",
            "error": "유효하지 않은 자격 증명입니다. 이메일/전화번호 또는 비밀번호를 확인하세요."
        }, status=status.HTTP_400_BAD_REQUEST)



# 일반 사용자 회원가입을 처리하는 View (관리자 전용)
class RegisterUserView(APIView):
    """
    일반 사용자 회원가입 View
    관리자가 일반 사용자의 회원가입을 대신 처리한다.
    """
    def post(self, request):
        admin = request.user  # 현재 로그인한 관리자
        if not admin.is_admin:  # 관리자인지 확인
            return Response({
                "message": "관리자만 사용자를 등록할 수 있습니다."
            }, status=status.HTTP_403_FORBIDDEN)

        # 관리자 정보를 context로 전달하여 Serializer에 넘김
        serializer = RegisterUserSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                # 회사 정보는 관리자 정보에서 자동으로 추가됨
                user = serializer.save()  # 사용자 정보 저장
                return Response({
                    "message": "사용자 회원가입이 성공적으로 완료되었습니다.",
                    "user": CustomUserSerializer(user).data
                }, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                error_message = str(e)
                # 이메일 및 전화번호 중복 처리
                if 'customuser.email' in error_message:
                    message = "이미 사용 중인 이메일입니다."
                elif 'customuser.phone_number' in error_message:
                    message = "이미 사용 중인 전화번호입니다."
                else:
                    message = "데이터베이스 무결성 오류가 발생했습니다."
                return Response({
                    "message": "사용자 회원가입에 실패했습니다.",
                    "error": message
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "message": "사용자 회원가입에 실패했습니다.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)



# 회원 정보 전체 조회
class UserListView(APIView):
    """
    GET: 전체 회원 정보 조회
    """
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            # 로그인한 관리자의 회사 정보 기준으로 같은 회사의 사용자들만 가져오기
            company = request.user.company  # 로그인한 사용자의 회사 정보 가져오기
            users = CustomUser.objects.filter(company=company)  # 같은 회사의 사용자들만 필터링
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


# 특정 회원 정보 조회, 수정, 삭제 처리
class UserDetailView(APIView):
    """
    GET: 특정 회원 정보 조회
    PATCH: 특정 회원 정보 수정
    DELETE: 특정 회원 삭제
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        admin = request.user  # 현재 로그인한 관리자
        if not admin.is_admin:  # 관리자인지 확인
            return Response({
                "message": "관리자만 회원 정보를 조회할 수 있습니다."
            }, status=status.HTTP_403_FORBIDDEN)
        try:
            user = get_object_or_404(CustomUser, pk=pk)  # 회원 정보 조회
            serializer = CustomUserSerializer(user)  # 회원 정보 직렬화
            return Response({
                "message": "회원 정보 조회가 성공적으로 완료되었습니다.",
                "user": serializer.data  # 회원 정보 반환
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "message": "회원 정보 조회 중 오류가 발생했습니다.",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def patch(self, request, pk):
        admin = request.user  # 현재 로그인한 관리자
        if not admin.is_admin:  # 관리자인지 확인
            return Response({
                "message": "관리자만 사용자를 수정할 수 있습니다."
            }, status=status.HTTP_403_FORBIDDEN)
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
        admin = request.user  # 현재 로그인한 관리자
        if not admin.is_admin:  # 관리자인지 확인
            return Response({
                "message": "관리자만 사용자를 삭제할 수 있습니다."
            }, status=status.HTTP_403_FORBIDDEN)
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



# 로그인 요청을 처리하는 View (일반 사용자 전용)
class LoginView(APIView):
    """
    로그인 View
    이메일 또는 전화번호와 비밀번호를 받아 JWT 토큰을 발급한다.
    """
    def post(self, request):
        serializer = LoginSerializer(data=request.data)  # 클라이언트로부터 받은 데이터를 시리얼라이저로 전달
        if serializer.is_valid(raise_exception=True):  # 데이터 검증
            user = serializer.validated_data  # 검증된 사용자 데이터

            # JWT 토큰 생성
            refresh = RefreshToken.for_user(user)
            user_info_serializer = CustomUserSerializer(user)  # 사용자 정보 시리얼라이저

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



# 공지사항 생성 뷰 및 회사별 공지사항 조회 뷰
class NoticeListCreateView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능
    

    def post(self, request):
        # 관리자가 공지사항을 생성할 수 있도록 권한 확인
        if not request.user.is_admin:
            return Response({
                "message": "관리자만 공지사항을 생성할 수 있습니다."  # 관리자가 아닌 경우 접근 거부 메시지
            }, status=status.HTTP_403_FORBIDDEN)

        # 공지사항 데이터 유효성 검사 및 저장
        serializer = NoticeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(company=request.user.company, created_by=request.user)  # 공지사항 저장 시 회사와 작성자 정보 자동 설정
            return Response({
                "message": "공지사항이 성공적으로 생성되었습니다.",  # 성공 메시지 반환
                "notice": serializer.data  # 생성된 공지사항 데이터 반환
            }, status=status.HTTP_201_CREATED)
        return Response({
            "message": "공지사항 생성에 실패했습니다.",  # 실패 메시지 반환
            "errors": serializer.errors  # 유효성 검사 오류 반환
        }, status=status.HTTP_400_BAD_REQUEST)

# 전체 공지사항 목록 조회 뷰
class NoticeListView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능

    def get(self, request):
        # 로그인한 사용자가 속한 회사의 공지사항 전체 조회
        company = request.user.company  # 로그인한 사용자의 회사 정보 가져오기
        notices = Notice.objects.filter(company=company)  # 해당 회사의 공지사항 필터링
        data = notices.values('id', 'title', 'created_at', 'created_by__name')  # 제목, 생성일, 작성자 이름만 가져오기
        return Response({
            "message": "공지사항 목록 조회가 성공적으로 완료되었습니다.",  # 성공 메시지 반환
            "notices": list(data)  # 공지사항 목록 반환 (제목, 작성일, 작성자)
        }, status=status.HTTP_200_OK)

# 공지사항 상세 조회, 수정 및 삭제 뷰
class NoticeDetailView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능

    def get_object(self, pk, company):
        # 특정 공지사항을 가져오는 함수 (해당 회사의 공지사항인지 확인)
        try:
            return Notice.objects.get(pk=pk, company=company)  # 공지사항 ID와 회사 정보를 기준으로 조회
        except Notice.DoesNotExist:
            return None  # 공지사항이 존재하지 않는 경우 None 반환

    def get(self, request, pk):
        # 특정 공지사항 상세 조회
        notice = self.get_object(pk, request.user.company)  # 로그인한 사용자의 회사에 속한 공지사항인지 확인
        if not notice:
            return Response({
                "message": "공지사항을 찾을 수 없습니다."  # 공지사항이 없을 경우 오류 메시지 반환
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = NoticeSerializer(notice)  # 공지사항 직렬화
        return Response({
            "notice": serializer.data  # 공지사항 데이터 반환
        }, status=status.HTTP_200_OK)

    def put(self, request, pk):
        # 공지사항 수정 (관리자만 가능하며, 해당 회사의 공지사항만 수정 가능)
        if not request.user.is_admin:
            return Response({
                "message": "관리자만 공지사항을 수정할 수 있습니다."  # 관리자가 아닌 경우 접근 거부 메시지
            }, status=status.HTTP_403_FORBIDDEN)

        notice = self.get_object(pk, request.user.company)  # 로그인한 사용자의 회사에 속한 공지사항인지 확인
        if not notice:
            return Response({
                "message": "공지사항을 찾을 수 없습니다."  # 공지사항이 없을 경우 오류 메시지 반환
            }, status=status.HTTP_404_NOT_FOUND)

        # 공지사항 데이터 유효성 검사 및 수정
        serializer = NoticeSerializer(notice, data=request.data, partial=True)  # 부분 업데이트 허용
        if serializer.is_valid():
            serializer.save()  # 수정된 공지사항 저장
            return Response({
                "message": "공지사항이 성공적으로 수정되었습니다.",  # 성공 메시지 반환
                "notice": serializer.data  # 수정된 공지사항 데이터 반환
            }, status=status.HTTP_200_OK)
        return Response({
            "message": "공지사항 수정에 실패했습니다.",  # 실패 메시지 반환
            "errors": serializer.errors  # 유효성 검사 오류 반환
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        # 공지사항 삭제 (관리자만 가능하며, 해당 회사의 공지사항만 삭제 가능)
        if not request.user.is_admin:
            return Response({
                "message": "관리자만 공지사항을 삭제할 수 있습니다."  # 관리자가 아닌 경우 접근 거부 메시지
            }, status=status.HTTP_403_FORBIDDEN)

        notice = self.get_object(pk, request.user.company)  # 로그인한 사용자의 회사에 속한 공지사항인지 확인
        if not notice:
            return Response({
                "message": "공지사항을 찾을 수 없습니다."  # 공지사항이 없을 경우 오류 메시지 반환
            }, status=status.HTTP_404_NOT_FOUND)

        notice.delete()  # 공지사항 삭제
        return Response({
            "message": "공지사항이 성공적으로 삭제되었습니다."  # 성공 메시지 반환
        }, status=status.HTTP_204_NO_CONTENT)



# 차량 등록 처리
class VehicleCreateView(APIView):
    """
    POST: 새로운 차량 등록 (관리자만 가능)
    """
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능

    def post(self, request):
        if not request.user.is_admin:  # 관리자인지 확인
            return Response({
                "message": "관리자만 차량을 등록할 수 있습니다."
            }, status=status.HTTP_403_FORBIDDEN)
        try:
            serializer = VehicleSerializer(data=request.data, context={'request': request})  # 차량 등록 시리얼라이저
            if serializer.is_valid():
                vehicle = serializer.save()  # 인증된 사용자의 회사 정보와 함께 저장

                # 마지막 사용일과 마지막 사용자 정보는 운행 기록을 통해 자동으로 설정되므로 여기서 설정하지 않음

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


# 차량 목록 전체 조회
class VehicleListView(APIView):
    """
    GET: 전체 차량 목록 조회
    """
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능

    def get(self, request):
        try:
            vehicles = Vehicle.objects.filter(company=request.user.company)  # 로그인한 사용자의 회사에 소속된 차량만 가져오기
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


# 특정 차량 조회, 수정, 삭제가 가능한 API
class VehicleDetailView(APIView):
    """
    GET: 특정 차량 정보 조회
    PATCH: 특정 차량 정보 수정 (관리자만 가능)
    DELETE: 특정 차량 정보 삭제 (관리자만 가능)
    """
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능

    def get(self, request, license_plate_number):
        try:
            # 번호판으로 차량 조회
            vehicle = get_object_or_404(Vehicle, license_plate_number=license_plate_number, company=request.user.company)
            serializer = VehicleSerializer(vehicle)
            return Response({
                "vehicle": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "message": "차량 조회에 실패했습니다.",
                "error": str(e)  # 예외 메시지 반환
            }, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, license_plate_number):
        if not request.user.is_admin:  # 관리자인지 확인
            return Response({
                "message": "관리자만 차량 정보를 수정할 수 있습니다."
            }, status=status.HTTP_403_FORBIDDEN)
        try:
            # 번호판으로 차량 조회
            vehicle = get_object_or_404(Vehicle, license_plate_number=license_plate_number, company=request.user.company)
            serializer = VehicleSerializer(vehicle, data=request.data, partial=True, context={'request': request})  # 부분 업데이트 허용
            if serializer.is_valid():
                serializer.save()  # 인증된 사용자의 정보와 함께 업데이트
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
                "message": "차량 정보 수정에 실패했습니다.",
                "error": str(e)  # 예외 메시지 반환
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, license_plate_number):
        if not request.user.is_admin:  # 관리자인지 확인
            return Response({
                "message": "관리자만 차량을 삭제할 수 있습니다."
            }, status=status.HTTP_403_FORBIDDEN)
        try:
            # 번호판으로 차량 조회 후 삭제
            vehicle = get_object_or_404(Vehicle, license_plate_number=license_plate_number, company=request.user.company)
            vehicle.delete()  # 차량 삭제
            return Response({
                "message": "차량이 성공적으로 삭제되었습니다."
            }, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({
                "message": "차량 삭제에 실패했습니다.",
                "error": str(e)  # 예외 메시지 반환
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# 운행 기록 목록 및 생성 처리
class DrivingRecordListCreateView(APIView):
    """
    POST: 새로운 운행 기록 생성
    """
    def post(self, request):
        # context에 request를 추가하여 serializer에서 현재 사용자 정보에 접근 가능하도록 설정
        serializer = DrivingRecordSerializer(data=request.data, context={'request': request})
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



class DrivingRecordListView(APIView):
    """
    GET: 전체 운행 기록 목록 조회
    """
    def get(self, request):
        records = DrivingRecord.objects.all()  # 모든 운행 기록 가져오기
        serializer = DrivingRecordSerializer(records, many=True)  # 여러 개의 운행 기록 직렬화
        return Response({
            "message": "운행 기록 목록 조회가 성공적으로 완료되었습니다.",
            "records": serializer.data  # 운행 기록 목록 반환
        }, status=status.HTTP_200_OK)



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



# 정비 기록 목록 및 생성 처리
class MaintenanceListCreateView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능

    def post(self, request):
        serializer = MaintenanceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # 유효성 검사를 통과한 경우 데이터베이스에 저장
            return Response({
                "message": "정비 기록이 성공적으로 생성되었습니다.",
                "record": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "message": "정비 기록 생성에 실패했습니다.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# 정비 기록 전체 조회
class MaintenanceListView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능

    def get(self, request):
        maintenances = Maintenance.objects.filter(vehicle__company=request.user.company)  # 로그인한 사용자의 회사에 소속된 차량의 정비 기록 가져오기
        serializer = MaintenanceSerializer(maintenances, many=True)
        return Response({
            "message": "정비 기록 목록 조회가 성공적으로 완료되었습니다.",
            "records": serializer.data
        }, status=status.HTTP_200_OK)


# 특정 정비 기록 조회, 수정 및 삭제 처리
class MaintenanceDetailView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능

    def get(self, request, pk):
        maintenance = get_object_or_404(Maintenance, pk=pk, vehicle__company=request.user.company)
        serializer = MaintenanceSerializer(maintenance)
        return Response({
            "message": "정비 기록 조회가 성공적으로 완료되었습니다.",
            "record": serializer.data
        }, status=status.HTTP_200_OK)

    def put(self, request, pk):
        maintenance = get_object_or_404(Maintenance, pk=pk, vehicle__company=request.user.company)
        serializer = MaintenanceSerializer(maintenance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "정비 기록이 성공적으로 수정되었습니다.",
                "record": serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            "message": "정비 기록 수정에 실패했습니다.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        maintenance = get_object_or_404(Maintenance, pk=pk, vehicle__company=request.user.company)
        maintenance.delete()
        return Response({
            "message": "정비 기록이 성공적으로 삭제되었습니다."
        }, status=status.HTTP_204_NO_CONTENT)



# 지출 관리 목록 및 생성 처리
class ExpenseListCreateView(APIView):
    permission_classes = [IsAuthenticated]  # 인증된 사용자만 접근 가능

    def post(self, request):
        serializer = ExpenseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # 유효성 검사를 통과한 경우 데이터베이스에 저장
            return Response({
                "message": "지출 내역이 성공적으로 생성되었습니다.",
                "record": serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            "message": "지출 내역 생성에 실패했습니다.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# 지출 관리 목록 전체 조회
class ExpenseListView(APIView):
    """
    GET: 전체 지출 내역 조회
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        expenses = Expense.objects.all()
        serializer = ExpenseSerializer(expenses, many=True)
        return Response({
            "message": "지출 내역 목록 조회가 성공적으로 완료되었습니다.",
            "expenses": serializer.data
        }, status=status.HTTP_200_OK)


class ExpenseDetailView(APIView):
    """
    GET: 특정 지출 내역 조회
    PATCH: 특정 지출 내역 수정
    DELETE: 특정 지출 내역 삭제
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Expense, pk=pk)

    def get(self, request, pk):
        expense = self.get_object(pk)
        serializer = ExpenseSerializer(expense)
        return Response({
            "message": "지출 내역 조회가 성공적으로 완료되었습니다.",
            "expense": serializer.data
        }, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        expense = self.get_object(pk)
        serializer = ExpenseSerializer(expense, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "지출 내역이 성공적으로 수정되었습니다.",
                "expense": serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            "message": "지출 내역 수정에 실패했습니다.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        expense = self.get_object(pk)
        expense.delete()
        return Response({
            "message": "지출 내역이 성공적으로 삭제되었습니다."
        }, status=status.HTTP_204_NO_CONTENT)