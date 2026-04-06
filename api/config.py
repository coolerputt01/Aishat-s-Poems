import os
from dotenv import load_dotenv
from cocobase_client import CocoBaseClient

load_dotenv()

COCOBASE_API_KEY = os.getenv("COCOBASE_API_KEY")

COCOBASE_PROJECT_KEY = os.getenv("COCOBASE_PROJECT_KEY")
APP_API_KEY = os.getenv("API_KEY")

db = CocoBaseClient(
    api_key=COCOBASE_API_KEY,
    project_id=COCOBASE_PROJECT_KEY
)