# Loads environment variables from .env and provides defaults
from dotenv import load_dotenv
import os


load_dotenv()


API_ID = int(os.getenv("API_ID", ""))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "")


MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = os.getenv("DB_NAME", "")


# Optional overrides
GROUP_DELETE_AFTER = int(os.getenv("GROUP_DELETE_AFTER", "299"))
BANNED_WORDS = [w.strip() for w in os.getenv("BANNED_WORDS", "xvideo,xxx,spam,badword,advertisement").split(",") if w.strip()]
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "40"))
PREVIEW_URL = os.getenv("PREVIEW_URL", "")


