import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_API_KEY", 'no bot API key, load in to the environment please')
