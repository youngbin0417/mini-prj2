from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

import gradio as gr

from config import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_RUNS_DIR,
    DEFAULT_STYLE,
    DEFAULT_TONE,
    DEFAULT_VOICE,
    load_env_file,
)
from pipeline import run_pipeline


VOICES = ["alloy", "aria", "verse", "shimmer", "coral", "sage", "nova", "amber"]


def make_run_dir(base_dir: Path) -> Path:
    run_dir = base_dir / f"run-{int(time.time())}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def run_pipeline_ui(pptx_file: str, tone: str, voice: str, style: str):
    if not pptx_file:
        raise gr.Error("PPTX 파일을 업로드하세요.")

    runs_dir = DEFAULT_RUNS_DIR
    runs_dir.mkdir(parents=True, exist_ok=True)
    work_dir = make_run_dir(runs_dir)
    pptx_path = work_dir / "input.pptx"
    shutil.copy(pptx_file, pptx_path)

    try:
        final_state = run_pipeline(
            pptx_path=str(pptx_path),
            work_dir=str(work_dir),
            tone=tone,
            voice=voice,
            style=style,
        )
    except Exception as exc:
        raise gr.Error(str(exc)) from exc

    video_path = final_state["final_video"]
    summary = (
        f"완료: 슬라이드 {final_state.get('n_slides', 0)}장 처리\n"
        f"작업 디렉터리: {work_dir}\n"
        f"최종 파일: {video_path}"
    )
    return video_path, video_path, summary


def build_app() -> gr.Blocks:
    with gr.Blocks(title="AI 강사 Agent") as demo:
        gr.Markdown("### PPT -> 강의영상 자동 제작")

        with gr.Row():
            inp_ppt = gr.File(label="PPTX 업로드", file_types=[".pptx"], type="filepath")
            with gr.Column():
                inp_tone = gr.Textbox(value=DEFAULT_TONE, label="강의 작성 톤")
                inp_voice = gr.Dropdown(VOICES, value=DEFAULT_VOICE, label="TTS Voice")
                inp_style = gr.Textbox(value=DEFAULT_STYLE, label="요약 스타일")

        run_btn = gr.Button("실행", variant="primary")
        out_video = gr.Video(label="최종 동영상 미리보기", interactive=False)
        out_download = gr.DownloadButton(label="동영상 다운로드")
        out_summary = gr.Textbox(label="실행 결과", interactive=False, lines=3)

        run_btn.click(
            fn=run_pipeline_ui,
            inputs=[inp_ppt, inp_tone, inp_voice, inp_style],
            outputs=[out_video, out_download, out_summary],
        )
    return demo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI 강사 Agent Gradio app")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", default=DEFAULT_PORT, type=int)
    parser.add_argument("--share", action="store_true", help="Enable Gradio share URL")
    parser.add_argument("--env-file", default=".env", help="Path to .env file")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_env_file(args.env_file)
    app = build_app()
    app.queue().launch(server_name=args.host, server_port=args.port, share=args.share)


if __name__ == "__main__":
    main()
