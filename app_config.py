"""Public runtime settings.

Keep personal names, relationship wording, IDs and private service URLs out of code.
Override everything with environment variables or the admin UI.
"""
import os

AI_NAME = os.getenv("AI_NAME", "Assistant")
USER_NAME = os.getenv("USER_NAME", "User")
OWNER_ALIAS = os.getenv("OWNER_ALIAS", USER_NAME)
DEFAULT_TIMEZONE = os.getenv("APP_TIMEZONE", "Asia/Shanghai")
DEFAULT_CITY = os.getenv("DEFAULT_CITY", "")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

MEM0_USER_ID = os.getenv("MEM0_USER_ID", "default-user")
