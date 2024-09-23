from django.urls import path
from .views import RegisterView, LoginView

# 회원가입 및 로그인 관련 URL 경로 설정
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),  # 회원가입 경로
    path('login/', LoginView.as_view(), name='login'),  # 로그인 경로
]
