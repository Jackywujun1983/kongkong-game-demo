"""Backend runtime configuration."""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent
DATABASE_PATH = BASE_DIR / "gamehub.sqlite3"
FRONTEND_DIR = PROJECT_DIR / "frontend"
PIC_DIR = PROJECT_DIR / "data" / "pic"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
