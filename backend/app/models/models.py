from datetime import datetime
from . import db
import random

class Topic(db.Model):
    __tablename__ = 'topics'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    questions = db.relationship('Question', backref='topic', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.slug,
            'title': self.name,
            'description': self.description
        }

class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=False)
    correct_answer = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def shuffle_options(self):
        """Shuffle options and adjust correct answer index accordingly"""
        correct_option = self.options[self.correct_answer]
        
        options_with_indices = list(enumerate(self.options))
        random.shuffle(options_with_indices)
        
        new_options = []
        new_correct_index = None
        
        for new_index, (_, option) in enumerate(options_with_indices):
            new_options.append(option)
            if option == correct_option:
                new_correct_index = new_index
        
        return {
            'options': new_options,
            'correct_answer': new_correct_index
        }

    def to_dict(self, shuffle=True):
        if shuffle:
            shuffled = self.shuffle_options()
            return {
                'id': self.id,
                'question': self.question_text,
                'options': shuffled['options'],
                'correct_answer': shuffled['correct_answer']
            }
        return {
            'id': self.id,
            'question': self.question_text,
            'options': self.options,
            'correct_answer': self.correct_answer
        }

class WikiPage(db.Model):
    __tablename__ = 'wiki_pages'
    
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)  # e.g., "roadmap", "links", "guides"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author = db.Column(db.String(100), nullable=True)
    is_published = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'slug': self.slug,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'author': self.author,
            'is_published': self.is_published
        }