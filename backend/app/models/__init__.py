from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models here
from .models import Topic, Question, WikiPage

# Make models available at package level
__all__ = ['db', 'Topic', 'Question', 'WikiPage']