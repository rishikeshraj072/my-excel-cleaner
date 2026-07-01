import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "default-fallback-key-change-in-prod")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/excel_cms"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Ingestion performance parameters
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1000"))
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    UPLOAD_FOLDER = os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "uploads"
    )
