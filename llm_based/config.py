import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_BASE_URL = os.environ["OPENAI_BASE_URL"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.environ["OPENAI_MODEL"]

OPENAI_MAX_TOKENS = int(os.environ["OPENAI_MAX_TOKENS"])
OPENAI_TEMPERATURE = float(os.environ["OPENAI_TEMPERATURE"])
OPENAI_TOP_P = float(os.environ["OPENAI_TOP_P"])
OPENAI_STREAM = os.environ["OPENAI_STREAM"].lower() == "true"