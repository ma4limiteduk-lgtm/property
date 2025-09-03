import os
from dotenv import load_dotenv

load_dotenv()

RENTVINE_SUBDOMAIN = os.getenv("RENTVINE_SUBDOMAIN", "securedoorpm")
RENTVINE_API_KEY = os.getenv("RENTVINE_API_KEY")
RENTVINE_API_SECRET = os.getenv("RENTVINE_API_SECRET")