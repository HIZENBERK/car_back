from django.urls import path
from .views import CustomTokenObtainPairView, RegisterUserView

# 로그인과 회원가입을 위한 URL 라우팅
urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),  # 로그인 (JWT 토큰 발급)
    path('register/', RegisterUserView.as_view(), name='register_user'),  # 사용자 등록
]
