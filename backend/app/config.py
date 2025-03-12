import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/devops_learning')
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgresadmin:YourStrongPassword123!@postgres-db.3-tier-app-eks.svc.cluster.local:5432/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = bool(int(os.getenv('FLASK_DEBUG', '0')))
