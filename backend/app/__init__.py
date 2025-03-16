from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from .config import Config
from .models import db
from .models.models import Topic, Question
from .routes import topic_bp, quiz_bp, api_bp 

migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    # CORS(app)
     CORS(app, origins=["https://akhileshmishra.tech", "http://akhileshmishra.tech", 
                        "http://www.akhileshmishra.tech",
                       # Include your ALB DNS for testing
                       "k8s-3tierapp-3tierapp-6901451c13-1079726941.eu-west-1.elb.amazonaws.com"])
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    app.register_blueprint(topic_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(api_bp) 
    return app
