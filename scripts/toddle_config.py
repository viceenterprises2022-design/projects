import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
STATE_FILE = BASE_DIR / "sync_state.json"
LOG_DIR = BASE_DIR / "logs"

TODDLE_URL = "https://web.toddleapp.com"
TODDLE_ACCOUNT_TYPE = "family"
TODDLE_EMAIL = os.getenv("TODDLE_EMAIL", "")
TODDLE_PASSWORD = os.getenv("TODDLE_PASSWORD", "")
TODDLE_GOOGLE_EMAIL = os.getenv("TODDLE_GOOGLE_EMAIL", "")
TODDLE_GOOGLE_PASSWORD = os.getenv("TODDLE_GOOGLE_PASSWORD", "")

ACTIVE_PROFILE = "default"
NOTEBOOKLM_PROFILE = os.getenv("NOTEBOOKLM_PROFILE", "default")

NOTEBOOK_PREFIX = ""  # e.g. " - Kid Name" to append to subject names

HEADLESS = os.getenv("TODDLE_HEADLESS", "0") == "1"
DEBUG = os.getenv("TODDLE_DEBUG", "0") == "1"

SUBJECT_OVERRIDES = os.getenv("TODDLE_SUBJECTS", "")
if SUBJECT_OVERRIDES:
    ALLOWED_SUBJECTS = [s.strip() for s in SUBJECT_OVERRIDES.split(",")]
else:
    ALLOWED_SUBJECTS = None
