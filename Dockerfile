# 파이썬 3.10 슬림 이미지를 기반으로 사용
FROM python:3.10-slim

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 시스템 필수 패키지 및 한글 폰트 설치
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libreoffice \
    libreoffice-java-common \
    xvfb \
    poppler-utils \
    fonts-nanum \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 전체 소스 코드 복사
COPY . .

# 영상이 저장될 디렉토리 생성
RUN mkdir -p webio

# FastAPI 서버 실행 (기본 8000 포트)
EXPOSE 8000

# xvfb-run을 사용하여 GUI가 없는 환경에서도 LibreOffice가 작동하도록 설정
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
