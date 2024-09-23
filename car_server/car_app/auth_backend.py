from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()

# 이메일 또는 전화번호로 인증하는 커스텀 백엔드
class EmailOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # 사용자가 입력한 값이 이메일 형식인지 전화번호인지 확인
        if '@' in username:
            kwargs = {'email': username}
        else:
            kwargs = {'phone_number': username}
        
        try:
            # 이메일 또는 전화번호로 사용자를 검색
            user = User.objects.get(**kwargs)
            # 비밀번호가 일치하는지 확인
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None