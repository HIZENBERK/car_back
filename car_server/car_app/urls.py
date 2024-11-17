from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import RegisterAdminView, AdminLoginView, RegisterUserView, UserListView, UserDetailView, LoginView, LogoutView, NoticeListCreateView, NoticeListView, NoticeDetailView, VehicleCreateView, VehicleListView, VehicleDetailView, DrivingRecordListCreateView, DrivingRecordListView, DrivingRecordDetailView, MaintenanceListCreateView, MaintenanceListView, MaintenanceDetailView, ExpenseListCreateView,ExpenseListView, ExpenseDetailView

# 회원가입 및 로그인 관련 URL 경로 설정
urlpatterns = [
    
    # 관리자 관련
    path('admin/register/', RegisterAdminView.as_view(), name='admin-register'),  # 관리자 회원가입
    path('admin/login/', AdminLoginView.as_view(), name='admin-login'),  # 관리자 전용 로그인 경로
    path('admin/register-user/', RegisterUserView.as_view(), name='register-user'),  # 일반 사용자 회원가입 경로
    
    # 일반 사용자 관련
    path('users/', UserListView.as_view(), name='user-list'), # 전체 회원 정보 조회
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),  # 특정 회원 정보 조회, 수정, 삭제
    path('login/', LoginView.as_view(), name='login'),  # 로그인 경로
    path('logout/', LogoutView.as_view(), name='logout'),  # 로그아웃 URL 설정
    
    # 공지사항 관련
    path('notices/create/', NoticeListCreateView.as_view(), name='notice-list-create'),  # 회사별 공지사항 생성
    path('notices/all/', NoticeListView.as_view(), name='notice-list'),  # 전체 공지사항 목록 조회 (로그인한 사용자의 회사에 한정)
    path('notices/<int:pk>/', NoticeDetailView.as_view(), name='notice-detail'),  # 공지사항 상세 조회, 수정, 삭제
    
    # 차량 관련
    path('vehicles/create/', VehicleCreateView.as_view(), name='vehicle-create'),  # 차량 등록
    path('vehicles/', VehicleListView.as_view(), name='vehicle-list'),  # 차량 전체 목록 조회
    path('vehicles/<int:vehicle_id>/', VehicleDetailView.as_view(), name='vehicle-detail'),  # 특정 차량 조회, 수정, 삭제

    
    # 정비 관련
    path('maintenances/create/', MaintenanceListCreateView.as_view(), name='maintenance-list-create'),  # 정비 기록 생성
    path('maintenances/', MaintenanceListView.as_view(), name='maintenance-list'),  # 전체 정비 기록 조회
    path('maintenances/<int:pk>/', MaintenanceDetailView.as_view(), name='maintenance-detail'),  # 특정 정비 기록 조회, 수정, 삭제
    
    # 지출 관련
    #path('expenses/create/', ExpenseListCreateView.as_view(), name='expense-list-create'), # 지출 내역 생성
    path('expenses/', ExpenseListView.as_view(), name='expense-list'), # 지출 내역 목록 및 생성
    path('expenses/<int:pk>/', ExpenseDetailView.as_view(), name='expense-detail'), # 특정 지출 내역 조회, 수정, 삭제
    
    # 운행 관련
    path('driving-records/create/', DrivingRecordListCreateView.as_view(), name='driving-record-list-create'),  # 운행 기록 생성
    path('driving-records/', DrivingRecordListView.as_view(), name='driving-record-list'),  # 전체 운행 기록 조회
    path('driving-records/<int:pk>/', DrivingRecordDetailView.as_view(), name='driving-record-detail'),  # 특정 운행 기록 조회, 수정, 삭제
]

# DEBUG 모드에서만 미디어 파일을 서빙하도록 설정
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
