from django.urls import path
from .views import RegisterView, LoginView, VehicleListCreateView, VehicleDetailView, VehicleByLicensePlateView, DrivingRecordListCreateView, DrivingRecordDetailView

# 회원가입 및 로그인 관련 URL 경로 설정
urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),  # 회원가입 경로
    path('login/', LoginView.as_view(), name='login'),  # 로그인 경로
    path('vehicles/', VehicleListCreateView.as_view(), name='vehicle-list-create'),  # 차량 등록 및 전체 목록 조회
    path('vehicles/<int:pk>/', VehicleDetailView.as_view(), name='vehicle-detail'),  # 특정 차량 조회, 수정, 삭제
    path('vehicles/license/<str:license_plate_number>/', VehicleByLicensePlateView.as_view(), name='vehicle-by-license-plate'),  # 차량 번호판으로 조회
    path('driving-records/', DrivingRecordListCreateView.as_view(), name='driving-record-list-create'),  # 운행 기록 목록 및 생성
    path('driving-records/<int:pk>/', DrivingRecordDetailView.as_view(), name='driving-record-detail'),  # 특정 운행 기록 조회, 수정, 삭제
]
