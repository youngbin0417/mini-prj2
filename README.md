# AI Teacher Web App

Colab 노트북에 들어 있던 AI 강사 Agent 파이프라인을 일반 Python + Gradio 앱으로 분리한 버전입니다.

## Files

- `app.py`: Gradio 웹앱 엔트리포인트
- `pipeline.py`: PPT 파싱, 검색, 요약, 스크립트, TTS, 비디오 합성 파이프라인
- `config.py`: 기본값과 `.env` 로더
- `requirements.txt`: Python 의존성

## Runtime Prerequisites

WSL/Linux 기준으로 아래 시스템 도구가 필요합니다.

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg libreoffice poppler-utils xvfb
```

현재 파이프라인은 아래 바이너리를 사용합니다.

- `ffmpeg`, `ffprobe`
- `soffice`
- `xvfb-run`
- `pdftoppm`

## Python Setup

```bash
cd /mnt/c/Users/User/Downloads/ai_teacher_webapp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` 또는 셸 환경변수에 아래 키가 필요합니다.

- `OPENAI_API_KEY`
- `TAVILY_API_KEY`

## Run

로컬 실행:

```bash
python3 app.py
```

공개 URL이 필요한 경우:

```bash
python3 app.py --share
```

기본 주소는 `http://0.0.0.0:7860` 입니다.

## Current Flow

1. PPTX 업로드
2. `python-pptx`로 텍스트/표/내장 이미지 추출
3. LibreOffice + `pdftoppm`로 슬라이드 PNG 생성
4. Tavily 검색으로 슬라이드 제목 기반 외부 정보 보강
5. `gpt-4o-mini`로 슬라이드 설명문 생성
6. `gpt-4o-mini`로 발표 스크립트 생성
7. `gpt-4o-mini-tts`로 슬라이드별 mp3 생성
8. `ffmpeg`로 슬라이드별 mp4 생성
9. `ffmpeg concat`으로 최종 강의 영상 생성

## Notes

- 노트북의 `google.colab`, `files.upload`, `drive.mount`, `IPython.display` 의존성은 제거했습니다.
- 작업 결과는 `webio/run-<timestamp>` 아래에 저장됩니다.
- 런타임 도구가 없거나 API 키가 없으면 앱에서 즉시 오류를 반환합니다.
