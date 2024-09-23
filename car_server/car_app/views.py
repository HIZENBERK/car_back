from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import User
from .serializers import UserSerializer

# 사용자 정보를 포함한 JWT 토큰 발급을 처리하는 커스텀 뷰
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = UserSerializer

# 사용자 등록을 처리하는 뷰
class RegisterUserView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)  # 요청 데이터를 직렬화
        if serializer.is_valid():
            user = serializer.save()  # 유효성 검증 후 사용자 저장
            return Response({"msg": "User created successfully"}, status=status.HTTP_201_CREATED)  # 성공 메시지 반환
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # 오류 발생 시 에러 반환