import os
from pathlib import Path


DEFAULT_VOICE = "alloy"
DEFAULT_TONE = "친절하고 명료한 강의 톤"
DEFAULT_STYLE = "예시와 핵심 요점 중심"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 7860
DEFAULT_RUNS_DIR = Path("webio")


def load_env_file(env_path: str | Path = ".env") -> None:
    path = Path(env_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))


def require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"필수 환경변수가 없습니다: {name}")
    return value
