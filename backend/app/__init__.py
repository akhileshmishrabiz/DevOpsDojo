from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from .config import Config
from .models import db
from .models.models import Topic, Question, WikiPage
from .routes import topic_bp, quiz_bp, api_bp, wiki_bp
import os

migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions

    # Check if ALLOWED_ORIGINS environment variable exists
    if os.getenv('ALLOWED_ORIGINS'):
        # Get allowed origins from environment variable
        allowed_origins = os.getenv('ALLOWED_ORIGINS').split(',')
        print(f"CORS allowing specific origins: {allowed_origins}")
        # Initialize CORS with specific origins
        CORS(app, origins=allowed_origins, supports_credentials=True)
    else:
        # Use default behavior (allow all origins) for development
        print("CORS allowing all origins (development mode)")
        CORS(app)
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    app.register_blueprint(topic_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(wiki_bp)
    app.register_blueprint(api_bp)
    
    # Health check route
    @app.route('/health', methods=['GET'])
    def health_check():
        return {"status": "healthy"}, 200
    
    return app