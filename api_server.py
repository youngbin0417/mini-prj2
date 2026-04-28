import os
import uuid
import threading
import shutil
from typing import Dict, Any
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from pipeline import run_pipeline
from config import (
    DEFAULT_RUNS_DIR,
    DEFAULT_TONE,
    DEFAULT_VOICE,
    DEFAULT_STYLE,
    load_env_file,
)

# 환경 변수 로드
load_env_file()

app = FastAPI(title="AI Instructor API", version="1.0.0")

# CORS 설정 (프론트엔드와 통신을 위해 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 배포 환경에서는 Vercel 도메인으로 변경하는 것을 권장합니다. 예: ["https://my-vercel-app.vercel.app"]
    allow_credentials=False, # allow_origins=["*"]와 allow_credentials=True는 함께 사용할 수 없습니다.
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 (생성된 영상 다운로드용)
DEFAULT_RUNS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/runs", StaticFiles(directory=str(DEFAULT_RUNS_DIR)), name="runs")

# 인메모리 작업 저장소 (실제 서비스에서는 DB나 Redis 추천)
jobs: Dict[str, Dict[str, Any]] = {}

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    message: str
    video_url: str | None = None
    created_at: float

def process_pipeline_task(job_id: str, pptx_path: Path, work_dir: Path, tone: str, voice: str, style: str):
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["message"] = "강의 영상을 제작 중입니다..."
        
        final_state = run_pipeline(
            pptx_path=str(pptx_path),
            work_dir=str(work_dir),
            tone=tone,
            voice=voice,
            style=style
        )
        
        video_path = final_state.get("final_video")
        if video_path and os.path.exists(video_path):
            # 최종 영상을 webio/ 폴더 바로 아래로 이동 (job_id.mp4 이름으로)
            final_video_name = f"{job_id}.mp4"
            dest_path = DEFAULT_RUNS_DIR / final_video_name
            shutil.move(video_path, dest_path)
            
            # 작업 디렉토리(원본 PPT, 이미지, 오디오 등) 전체 삭제
            shutil.rmtree(work_dir, ignore_errors=True)
            
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 1.0
            jobs[job_id]["message"] = "영상 제작이 완료되었습니다. (임시 파일 삭제 완료)"
            jobs[job_id]["video_url"] = f"/runs/{final_video_name}"
        else:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["message"] = "영상 파일 생성에 실패했습니다."
            
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"오류 발생: {str(e)}"
        print(f"Error in job {job_id}: {str(e)}")
        # 실패하더라도 찌꺼기 파일이 남지 않도록 삭제 (디버깅이 필요하다면 주석 처리 가능)
        # shutil.rmtree(work_dir, ignore_errors=True)

@app.post("/api/jobs")
async def create_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    tone: str = DEFAULT_TONE,
    voice: str = DEFAULT_VOICE,
    style: str = DEFAULT_STYLE
):
    if not file.filename.endswith(".pptx"):
        raise HTTPException(status_code=400, detail="PPTX 파일만 업로드 가능합니다.")

    job_id = str(uuid.uuid4())
    work_dir = DEFAULT_RUNS_DIR / f"run-{job_id}"
    work_dir.mkdir(parents=True, exist_ok=True)
    
    pptx_path = work_dir / "input.pptx"
    with open(pptx_path, "wb") as buffer:
        buffer.write(await file.read())

    import time
    jobs[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 0.0,
        "message": "작업을 준비 중입니다...",
        "video_url": None,
        "created_at": time.time(),
        "filename": file.filename
    }

    background_tasks.add_task(
        process_pipeline_task, 
        job_id, pptx_path, work_dir, tone, voice, style
    )

    return {"job_id": job_id}

@app.get("/api/jobs")
async def list_jobs():
    return sorted(jobs.values(), key=lambda x: x["created_at"], reverse=True)

@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    return jobs[job_id]

@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")
    
    # 딕셔너리에서 제거
    del jobs[job_id]
    
    # 관련된 파일/폴더 삭제
    work_dir = DEFAULT_RUNS_DIR / f"run-{job_id}"
    video_path = DEFAULT_RUNS_DIR / f"{job_id}.mp4"
    
    shutil.rmtree(work_dir, ignore_errors=True)
    if video_path.exists():
        video_path.unlink(missing_ok=True)
        
    return {"message": "삭제되었습니다."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
