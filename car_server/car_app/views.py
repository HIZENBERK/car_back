from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, LoginSerializer
from .models import CustomUser

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
