from __future__ import annotations

import base64
import mimetypes
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from typing import Any, TypedDict

from openai import OpenAI
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langgraph.graph import END, START, StateGraph

from config import DEFAULT_STYLE, DEFAULT_TONE, DEFAULT_VOICE, require_env


LLM_MODEL = "gpt-4o-mini"
TTS_MODEL = "gpt-4o-mini-tts"
REQUIRED_SYSTEM_TOOLS = ("ffmpeg", "ffprobe", "soffice", "xvfb-run", "pdftoppm")


class State(TypedDict, total=False):
    pptx_path: str
    work_dir: str
    prompt: dict[str, Any]
    slides: list[dict[str, Any]]
    n_slides: int
    slide_index: int
    cur_search_context: str
    cur_page_content: str
    cur_script: str
    cur_audio: str
    cur_video: str
    cur_slide_image: str
    audios: list[str]
    videos: list[str]
    page_contents: list[str]
    scripts: list[str]
    slide_images: list[str]
    final_video: str


def ensure_runtime_requirements() -> None:
    missing_tools = [tool for tool in REQUIRED_SYSTEM_TOOLS if shutil.which(tool) is None]
    if missing_tools:
        raise RuntimeError(
            "필수 시스템 도구가 없습니다: "
            + ", ".join(missing_tools)
            + ". README의 런타임 설치 단계를 먼저 수행하세요."
        )

    require_env("OPENAI_API_KEY")
    require_env("TAVILY_API_KEY")


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def ffprobe_duration(path: str) -> float:
    out = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            path,
        ]
    ).decode().strip()
    return float(out)


def img_to_data_url(path: str) -> str:
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as file:
        encoded = base64.b64encode(file.read()).decode("utf-8")
    return f"data:{mime};base64,{encoded}"


def render_mp4(image_path: str, audio_path: str, out_mp4: str, width: int = 1920, height: int = 1080) -> None:
    duration = ffprobe_duration(audio_path)
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-i",
        image_path,
        "-i",
        audio_path,
        "-t",
        str(duration),
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        out_mp4,
    ]
    subprocess.check_call(cmd)


def export_slide_as_png(state: dict[str, Any], dpi: int = 220) -> dict[str, Any]:
    work_dir = Path(state["work_dir"]).expanduser().resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    pptx_path = Path(state["pptx_path"]).expanduser().resolve()
    if not pptx_path.exists():
        raise FileNotFoundError(f"PPTX 없음: {pptx_path}")

    page_no = int(state.get("slide_index", 0)) + 1
    out_prefix = work_dir / "slide_img"
    lo_profile = f"file:///tmp/lo_profile_{uuid.uuid4().hex}"

    env = os.environ.copy()
    env.update(
        {
            "LANG": "ko_KR.UTF-8",
            "LC_ALL": "ko_KR.UTF-8",
            "FONTCONFIG_PATH": str(Path("~/.config/fontconfig").expanduser()),
            "FONTCONFIG_FILE": str(Path("~/.config/fontconfig/fonts.conf").expanduser()),
            "HOME": str(Path("~").expanduser()),
            "XDG_CACHE_HOME": str(Path("~/.cache").expanduser()),
            "SAL_USE_VCLPLUGIN": "gen",
        }
    )

    def run_lo_convert(convert_to: str) -> subprocess.CompletedProcess[str]:
        cmd = [
            "xvfb-run",
            "-a",
            "soffice",
            "--headless",
            "--nologo",
            "--nofirststartwizard",
            "--norestore",
            f"-env:UserInstallation={lo_profile}",
            "--convert-to",
            convert_to,
            "--outdir",
            str(work_dir),
            str(pptx_path),
        ]
        return subprocess.run(cmd, capture_output=True, text=True, env=env, check=False)

    before_png = set(work_dir.glob("*.png"))
    run_lo_convert("png:impress_png_Export")
    created_png = [path for path in work_dir.glob("*.png") if path not in before_png]

    exact = [path for path in created_png if path.stem.endswith(f"-{page_no}")]
    candidate = None
    if exact:
        candidate = max(exact, key=lambda path: path.stat().st_mtime)
    elif created_png:
        candidate = max(created_png, key=lambda path: path.stat().st_mtime)

    if candidate and candidate.exists():
        state["slide_image"] = str(candidate)
        return state

    before_pdf = set(work_dir.glob("*.pdf"))
    res_pdf = run_lo_convert("pdf:impress_pdf_Export")
    target_pdf = work_dir / f"{pptx_path.stem}.pdf"
    created_pdf = [path for path in work_dir.glob("*.pdf") if path not in before_pdf]

    if target_pdf.exists():
        pdf_path = target_pdf
    elif created_pdf:
        pdf_path = max(created_pdf, key=lambda path: path.stat().st_mtime)
    else:
        raise RuntimeError(
            "PPTX -> PDF 변환 실패\n"
            f"stdout: {res_pdf.stdout}\n"
            f"stderr: {res_pdf.stderr}"
        )

    ppm_cmd = [
        "pdftoppm",
        "-f",
        str(page_no),
        "-l",
        str(page_no),
        "-png",
        "-r",
        str(dpi),
        str(pdf_path),
        str(out_prefix),
    ]
    res2 = subprocess.run(ppm_cmd, capture_output=True, text=True, env=env, check=False)

    png_path = Path(f"{out_prefix}-{page_no}.png")
    if not png_path.exists():
        raise RuntimeError(
            "PDF -> PNG 변환 실패\n"
            f"stdout: {res2.stdout}\n"
            f"stderr: {res2.stderr}"
        )

    state["slide_image"] = str(png_path)
    return state


def concat_videos_ffmpeg(video_paths: list[str], out_path: str, reencode: bool = False) -> None:
    list_path = out_path + ".txt"
    with open(list_path, "w", encoding="utf-8") as file:
        for video_path in video_paths:
            file.write(f"file '{os.path.abspath(video_path)}'\n")

    if reencode:
        cmd = [
            "ffmpeg",
            "-y",
            "-safe",
            "0",
            "-f",
            "concat",
            "-i",
            list_path,
            "-vf",
            "format=yuv420p",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            out_path,
        ]
    else:
        cmd = ["ffmpeg", "-y", "-safe", "0", "-f", "concat", "-i", list_path, "-c", "copy", out_path]

    subprocess.check_call(cmd)


def build_llm() -> ChatOpenAI:
    return ChatOpenAI(model=LLM_MODEL, temperature=0.3)


def node_parse_all(state: State) -> State:
    presentation = Presentation(state["pptx_path"])
    work_dir = state["work_dir"]
    media_dir = os.path.join(work_dir, "media")
    os.makedirs(media_dir, exist_ok=True)

    slides_out: list[dict[str, Any]] = []
    for idx, slide in enumerate(presentation.slides, start=1):
        texts: list[str] = []
        tables: list[list[list[str]]] = []
        images: list[str] = []
        title = ""

        if slide.shapes.title:
            title = clean_text(slide.shapes.title.text)

        for shape_index, shape in enumerate(slide.shapes):
            if shape.has_text_frame:
                text = "\n".join(paragraph.text for paragraph in shape.text_frame.paragraphs)
                text = clean_text(text)
                if text:
                    texts.append(text)
                    if not title and shape_index == 0:
                        title = text[:30]

            if shape.shape_type == MSO_SHAPE_TYPE.TABLE:
                table = [[clean_text(cell.text) for cell in row.cells] for row in shape.table.rows]
                tables.append(table)

            if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
                ext = shape.image.ext
                image_path = os.path.join(media_dir, f"slide{idx}_img_{shape_index}.{ext}")
                with open(image_path, "wb") as file:
                    file.write(shape.image.blob)
                images.append(image_path)

        snap_state = export_slide_as_png(
            {"pptx_path": state["pptx_path"], "work_dir": work_dir, "slide_index": idx - 1}
        )
        slides_out.append(
            {
                "index": idx,
                "title": title,
                "texts": texts,
                "tables": tables,
                "images": images,
                "snap": snap_state["slide_image"],
            }
        )

    state["slides"] = slides_out
    state["n_slides"] = len(slides_out)
    state["slide_index"] = 0
    state["page_contents"] = []
    state["scripts"] = []
    state["audios"] = []
    state["videos"] = []
    state["slide_images"] = []
    return state


def node_tool_search(state: State) -> State:
    slide = state["slides"][state["slide_index"]]
    title = slide.get("title", "")
    if not title:
        state["cur_search_context"] = "검색할 제목이 없어 검색을 수행하지 않았습니다."
        return state

    search = TavilySearch(max_results=3)
    try:
        state["cur_search_context"] = str(search.run(title))
    except Exception as exc:
        state["cur_search_context"] = f"검색 중 오류 발생: {exc}"
    return state


def node_gen_page(state: State) -> State:
    slide = state["slides"][state["slide_index"]]
    texts = slide.get("texts", [])
    tables = slide.get("tables", [])
    images = slide.get("images", [])
    snap = slide.get("snap")
    search_context = state.get("cur_search_context", "")
    prompt_config = state["prompt"]

    table_snip = ""
    if tables:
        try:
            table_snip = "\n".join(" | ".join(map(str, row)) for row in tables[0][:6])
        except Exception:
            table_snip = str(tables[0][:6])

    combined_images: list[str] = []
    if snap:
        combined_images.append(snap)
    for image in images:
        if image not in combined_images:
            combined_images.append(image)

    system_msg = SystemMessage(
        content=f"""
당신은 전문적인 AI 강사입니다.
슬라이드의 텍스트, 표, 이미지 및 검색된 외부 정보를 종합하여 슬라이드 핵심 요약을 작성하세요.

[작성 규칙]
1. 단락 구성: 반드시 4문장에서 6문장 사이의 하나의 단락으로 작성하세요.
2. 불릿 금지: 나열식 기호(-, *, •)나 숫자를 절대 사용하지 마세요.
3. 이미지 통합: 첨부된 이미지에서 보이는 시각적 특징을 요약에 포함하세요.
4. 객관성: 제공된 데이터와 검색 결과에 기반하여 사실적으로 작성하세요.
5. 요약 스타일: {prompt_config.get("style", DEFAULT_STYLE)}
""".strip()
    )

    user_text = (
        f"[슬라이드 텍스트]\n{texts if texts else '(없음)'}\n\n"
        f"[표 데이터]\n{table_snip if table_snip else '(없음)'}\n\n"
        f"[추가 검색 정보]\n{search_context if search_context else '(없음)'}"
    )
    user_content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]

    for image_path in combined_images[:3]:
        user_content.append({"type": "image_url", "image_url": {"url": img_to_data_url(image_path)}})

    response = build_llm().invoke([system_msg, HumanMessage(content=user_content)])
    state["cur_page_content"] = str(response.content).strip()
    return state


def node_gen_script(state: State) -> State:
    page_content = state.get("cur_page_content", "")
    prompt_config = state.get("prompt", {})
    work_dir = state.get("work_dir", ".")
    slide_index = state.get("slide_index", 0)
    slide_number = slide_index + 1
    n_slides = state.get("n_slides", 0)

    if slide_index == 0:
        structure = (
            "1) 인트로: 강사 인사 및 강의 전체 주제 소개\n"
            "2) 설명: 이번 슬라이드의 핵심 내용 상세 설명\n"
            "3) 전환: 다음 슬라이드 내용 예고"
        )
    elif slide_number == n_slides:
        structure = (
            "1) 연결: 이전 내용과의 연결성 언급\n"
            "2) 설명: 이번 슬라이드의 핵심 내용 상세 설명\n"
            "3) 마무리: 전체 강의 요약 및 감사 인사와 종료 멘트"
        )
    else:
        structure = (
            "1) 연결: 이전 슬라이드에서 자연스럽게 이어지는 전환 문구\n"
            "2) 설명: 이번 슬라이드의 핵심 내용 상세 설명\n"
            "3) 전환: 다음 단계나 슬라이드로 넘어가는 문장"
        )

    system_msg = SystemMessage(
        content=(
            "당신은 전문적인 대학 강의 에이전트입니다.\n"
            "슬라이드 요약을 바탕으로 60~90초 분량의 자연스러운 발표 대본을 작성하세요.\n\n"
            f"## 권장 구조\n{structure}\n\n"
            "## 핵심 규칙\n"
            "- 모든 슬라이드에서 '안녕하세요'라고 인사하지 마세요. 인사는 첫 슬라이드에서만 수행합니다.\n"
            "- 청중에게 직접 이야기하는 듯한 자연스러운 구어체(~습니다, ~해요)를 사용하세요.\n"
            "- 슬라이드 간 흐름이 끊기지 않도록 연결 문구에 신경 써주세요.\n"
            f"- 요청된 말투/톤: {prompt_config.get('tone', DEFAULT_TONE)}"
        )
    )

    response = build_llm().invoke(
        [system_msg, HumanMessage(content=[{"type": "text", "text": f"[슬라이드 요약]\n{page_content}"}])]
    )
    script = str(response.content).strip()
    script_path = os.path.join(work_dir, f"script_{slide_number}.txt")
    with open(script_path, "w", encoding="utf-8") as file:
        file.write(script)

    state["cur_script"] = script
    return state


def node_tts(state: State) -> State:
    client = OpenAI()
    slide_number = state.get("slide_index", 0) + 1
    response = client.audio.speech.create(
        model=TTS_MODEL,
        voice=state["prompt"].get("voice", DEFAULT_VOICE),
        input=state["cur_script"],
    )
    mp3_path = os.path.join(state["work_dir"], f"narration_{slide_number}.mp3")
    with open(mp3_path, "wb") as file:
        file.write(response.content)
    state["cur_audio"] = mp3_path
    return state


def node_make_video(state: State) -> State:
    slide = state["slides"][state["slide_index"]]
    slide_image = slide.get("snap")
    audio_path = state.get("cur_audio")
    slide_number = state.get("slide_index", 0) + 1
    if not slide_image:
        raise ValueError(f"Slide {slide_number}의 이미지 경로가 없습니다.")
    if not audio_path:
        raise ValueError(f"Slide {slide_number}의 오디오 경로가 없습니다.")

    output_path = os.path.join(state["work_dir"], f"slide_{slide_number}_video.mp4")
    render_mp4(slide_image, audio_path, output_path)
    state["cur_video"] = output_path
    state["cur_slide_image"] = slide_image
    return state


def node_acc_step(state: State) -> State:
    state["audios"].append(state["cur_audio"])
    state["videos"].append(state["cur_video"])
    state["slide_images"].append(state["cur_slide_image"])
    state["page_contents"].append(state["cur_page_content"])
    state["scripts"].append(state["cur_script"])
    state["slide_index"] += 1
    return state


def node_concat(state: State) -> State:
    output_path = os.path.join(state["work_dir"], "final_lecture_video.mp4")
    concat_videos_ffmpeg(state["videos"], output_path, reencode=True)
    state["final_video"] = output_path
    return state


def decide_next_step(state: State) -> str:
    return "CONTINUE" if state.get("slide_index", 0) < state.get("n_slides", 0) else "END"


def build_graph():
    builder = StateGraph(State)
    builder.add_node("parse_all", node_parse_all)
    builder.add_node("tool_search", node_tool_search)
    builder.add_node("gen_page", node_gen_page)
    builder.add_node("gen_script_ctx", node_gen_script)
    builder.add_node("tts", node_tts)
    builder.add_node("make_video", node_make_video)
    builder.add_node("acc_step", node_acc_step)
    builder.add_node("concat", node_concat)

    builder.add_edge(START, "parse_all")
    builder.add_edge("parse_all", "tool_search")
    builder.add_edge("tool_search", "gen_page")
    builder.add_edge("gen_page", "gen_script_ctx")
    builder.add_edge("gen_script_ctx", "tts")
    builder.add_edge("tts", "make_video")
    builder.add_edge("make_video", "acc_step")
    builder.add_conditional_edges("acc_step", decide_next_step, {"CONTINUE": "tool_search", "END": "concat"})
    builder.add_edge("concat", END)
    return builder.compile()


GRAPH = build_graph()


def build_initial_state(pptx_path: str, work_dir: str, tone: str | None, voice: str | None, style: str | None) -> State:
    return {
        "pptx_path": pptx_path,
        "work_dir": work_dir,
        "prompt": {
            "voice": voice or DEFAULT_VOICE,
            "tone": tone or DEFAULT_TONE,
            "style": style or DEFAULT_STYLE,
        },
    }


def run_pipeline(pptx_path: str, work_dir: str, tone: str | None = None, voice: str | None = None, style: str | None = None) -> State:
    ensure_runtime_requirements()
    state = build_initial_state(pptx_path=pptx_path, work_dir=work_dir, tone=tone, voice=voice, style=style)
    final_state = GRAPH.invoke(state)
    if not final_state.get("final_video"):
        raise RuntimeError("최종 동영상 생성에 실패했습니다.")
    return final_state
