from django.urls import path
from .views import RegisterAdminView, AdminLoginView, RegisterUserView, UserListView, LoginView, LogoutView, VehicleListCreateView, VehicleByLicensePlateView, DrivingRecordListCreateView, DrivingRecordDetailView

# 회원가입 및 로그인 관련 URL 경로 설정
urlpatterns = [
    
    # 관리자 관련
    path('admin/register/', RegisterAdminView.as_view(), name='admin-register'),  # 관리자 회원가입
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),  # 관리자 전용 로그인 경로
    path('admin/register-user/', RegisterUserView.as_view(), name='register-user'),  # 일반 사용자 회원가입 경로
    
    # 일반 사용자 관련
    path('users/', UserListView.as_view(), name='user-list'), # 전체 회원 정보 조회
    path('login/', LoginView.as_view(), name='login'),  # 로그인 경로
    path('logout/', LogoutView.as_view(), name='logout'),  # 로그아웃 URL 설정
    
    # 차량관련
    path('vehicles/', VehicleListCreateView.as_view(), name='vehicle-list-create'),  # 차량 등록 및 전체 목록 조회
    path('vehicles/<str:license_plate_number>/', VehicleByLicensePlateView.as_view(), name='vehicle-detail-by-license'),# 차량 번호판으로 조회, 수정, 삭제
    path('driving-records/', DrivingRecordListCreateView.as_view(), name='driving-record-list-create'),  # 운행 기록 목록 및 생성
    path('driving-records/<int:pk>/', DrivingRecordDetailView.as_view(), name='driving-record-detail'),  # 특정 운행 기록 조회, 수정, 삭제
]
