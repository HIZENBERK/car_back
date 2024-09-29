from django.urls import path
from .views import RegisterView, UserListView, LoginView, LogoutView, VehicleListCreateView, VehicleByLicensePlateView, DrivingRecordListCreateView, DrivingRecordDetailView

# 회원가입 및 로그인 관련 URL 경로 설정
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),  # 회원가입 경로
    path('users/', UserListView.as_view(), name='user-list'), # 전체 회원 정보 조회
    path('login/', LoginView.as_view(), name='login'),  # 로그인 경로
    path('logout/', LogoutView.as_view(), name='logout'),  # 로그아웃 URL 설정
    path('vehicles/', VehicleListCreateView.as_view(), name='vehicle-list-create'),  # 차량 등록 및 전체 목록 조회
    path('vehicles/<str:license_plate_number>/', VehicleByLicensePlateView.as_view(), name='vehicle-detail-by-license'),# 차량 번호판으로 조회, 수정, 삭제를 처리하는 API 엔드포인트
    path('driving-records/', DrivingRecordListCreateView.as_view(), name='driving-record-list-create'),  # 운행 기록 목록 및 생성
    path('driving-records/<int:pk>/', DrivingRecordDetailView.as_view(), name='driving-record-detail'),  # 특정 운행 기록 조회, 수정, 삭제
]
