from rest_framework import serializers
from .models import User

# 사용자 정보를 직렬화하는 UserSerializer 클래스
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone_number', 'device_uuid', 'company_name', 'business_registration_number',
                  'department', 'position', 'name', 'usage_distance', 'unpaid_penalties']