from django.urls import path
from .views import RegisterAdminView, AdminLoginView, RegisterUserView, UserListView, LoginView, LogoutView, NoticeListCreateView, NoticeListView, NoticeDetailView, VehicleCreateView, VehicleListView, VehicleDetailView, DrivingRecordListCreateView, DrivingRecordDetailView

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
    
    # 공지사항 관련
    path('notices/create/', NoticeListCreateView.as_view(), name='notice-list-create'),  # 회사별 공지사항 생성
    path('notices/all/', NoticeListView.as_view(), name='notice-list'),  # 전체 공지사항 목록 조회 (로그인한 사용자의 회사에 한정)
    path('notices/<int:pk>/', NoticeDetailView.as_view(), name='notice-detail'),  # 공지사항 상세 조회, 수정, 삭제
    
    # 차량 관련
    path('vehicles/create/', VehicleCreateView.as_view(), name='vehicle-create'),  # 차량 등록
    path('vehicles/', VehicleListView.as_view(), name='vehicle-list'),  # 차량 전체 목록 조회
    path('vehicles/<str:license_plate_number>/', VehicleDetailView.as_view(), name='vehicle-detail'),  # 특정 차량 조회, 수정, 삭제
    
    # 운행 관련
    path('driving-records/', DrivingRecordListCreateView.as_view(), name='driving-record-list-create'),  # 운행 기록 목록 및 생성
    path('driving-records/<int:pk>/', DrivingRecordDetailView.as_view(), name='driving-record-detail'),  # 특정 운행 기록 조회, 수정, 삭제
]
