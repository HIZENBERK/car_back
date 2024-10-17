# car_back

패키지 관리
갱신
pip freeze > requirements.txt
다운
pip install -r requirements.txt


DB migrations, migrate
python manage.py makemigrations
python manage.py migrate


프론트 작업할 때 백엔드 서버 여느 법 모르시면 보세요. 순서 대로만 해주시면 됩니다.

가상환경 구동
ctrl + shift + p
python select interpreter
해당 가상환경 선택


db 모델 생성
터미널 오픈 (vscode의 경우 ctrl + `)
시작위치 : 소스트리 car_front, car_back이 존재하는 위치로 가정
cd car_back
cd car_server
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate

서버 오픈
python manage.py runserver


더미 데이터 db 삽입
서버 오픈 후 https://www.postman.com/
접속

Send An API request - New Request
Body - raw - Json
db 더미 데이터 Json코드.txt 참조하여 데이터 삽입 - Discord 파일공유란에서 다운 or 카톡에서 다운
Send

