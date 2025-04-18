from flask import jsonify, request
from app.models.models import Topic, Question
from app.models import db
from . import quiz_bp
import random
import string

MAX_QUIZ_QUESTIONS = 15

@quiz_bp.route('/<topic_slug>', methods=['GET'])
def get_quiz(topic_slug):
    topic = Topic.query.filter_by(slug=topic_slug).first_or_404()
    
    # Get all questions for the topic
    all_questions = Question.query.filter_by(topic_id=topic.id).all()
    
    if not all_questions:
        return jsonify({
            'title': topic.name,
            'questions': [],
            'total_questions': 0,
            'selected_questions': 0
        })
    
    # Shuffle and limit questions
    selected_questions = random.sample(
        all_questions, 
        min(MAX_QUIZ_QUESTIONS, len(all_questions))
    )
    
    return jsonify({
        'title': topic.name,
        'questions': [q.to_dict(shuffle=False) for q in selected_questions],
        'total_questions': len(all_questions),
        'selected_questions': len(selected_questions)
    })

@quiz_bp.route('/submit', methods=['POST'])
def submit_quiz():
    data = request.get_json()
    topic_slug = data.get('topic')
    answers = data.get('answers')
    
    if not topic_slug or not answers:
        return jsonify({'error': 'Invalid submission'}), 400
        
    topic = Topic.query.filter_by(slug=topic_slug).first()
    if not topic:
        return jsonify({'error': 'Topic not found'}), 404
    
    # Get all questions that were answered
    question_ids = [int(qid) for qid in answers.keys()]
    questions = Question.query.filter(Question.id.in_(question_ids)).all()
    
    correct_count = 0
    total_questions = len(questions)
    
    for question in questions:
        submitted_answer = answers.get(str(question.id))
        if submitted_answer == question.correct_answer:
            correct_count += 1
    
    score = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    return jsonify({
        'score': score,
        'correct': correct_count,
        'total': total_questions
    })

@quiz_bp.route('/questions', methods=['GET', 'POST'])
def manage_questions():
    if request.method == 'POST':
        data = request.get_json()
        print("Received question data:", data)
        
        if not all(k in data for k in ('topic_slug', 'question_text', 'options', 'correct_answer')):
            return jsonify({'error': 'Missing required fields'}), 400
            
        # Find or create topic
        topic = Topic.query.filter_by(slug=data['topic_slug']).first()
        if not topic:
            # Create a new topic with default values based on slug
            topic_name = data['topic_slug'].replace('-', ' ').title()
            topic = Topic(
                name=topic_name,
                description=f"Questions about {topic_name}",
                slug=data['topic_slug']
            )
            db.session.add(topic)
            db.session.commit()
            
        try:
            question = Question(
                topic_id=topic.id,
                question_text=data['question_text'],
                options=data['options'],
                correct_answer=data['correct_answer']
            )
            
            db.session.add(question)
            db.session.commit()
            return jsonify(question.to_dict(shuffle=False)), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Error adding question: {str(e)}")
            return jsonify({'error': str(e)}), 400
            
    questions = Question.query.all()
    return jsonify([q.to_dict(shuffle=False) for q in questions])

@quiz_bp.route('/questions/bulk', methods=['POST'])
def bulk_upload_questions():
    if not request.is_json:
        return jsonify({'error': 'Content-Type must be application/json'}), 400
        
    questions_data = request.get_json()
    if not isinstance(questions_data, list):
        return jsonify({'error': 'Expected a list of questions'}), 400
        
    success_count = 0
    failed_count = 0
    errors = []
    valid_questions = []
    created_topics = []
    
    # First pass: Validate all questions and create topics if needed
    for index, question_data in enumerate(questions_data):
        try:
            # Skip empty rows
            if not question_data or not any(question_data.values()):
                continue

            # Validate required fields
            if not all(k in question_data for k in ('topic_slug', 'question_text', 'options', 'correct_answer')):
                failed_count += 1
                errors.append(f"Row {index + 1}: Missing required fields")
                continue

            # Validate content
            if not question_data['question_text'] or not question_data['question_text'].strip():
                failed_count += 1
                errors.append(f"Row {index + 1}: Empty question text")
                continue

            # Validate options
            if not isinstance(question_data['options'], list) or len(question_data['options']) != 4:
                failed_count += 1
                errors.append(f"Row {index + 1}: Invalid options format")
                continue

            if any(opt is None or str(opt).strip() == '' for opt in question_data['options']):
                failed_count += 1
                errors.append(f"Row {index + 1}: Empty options not allowed")
                continue

            # Validate correct_answer
            try:
                correct_answer = int(question_data['correct_answer'])
                if not 0 <= correct_answer <= 3:
                    raise ValueError("Correct answer must be between 0 and 3")
                question_data['correct_answer'] = correct_answer
            except (ValueError, TypeError):
                failed_count += 1
                errors.append(f"Row {index + 1}: Invalid correct_answer value")
                continue

            # Find or create topic
            topic_slug = question_data['topic_slug'].strip()
            topic = Topic.query.filter_by(slug=topic_slug).first()
            
            if not topic:
                # Track which topics we've created during this operation
                if topic_slug not in created_topics:
                    # Generate a nice title from the slug
                    topic_name = topic_slug.replace('-', ' ').title()
                    
                    # Create new topic
                    topic = Topic(
                        name=topic_name,
                        description=f"Questions about {topic_name}",
                        slug=topic_slug
                    )
                    db.session.add(topic)
                    created_topics.append(topic_slug)
                    print(f"Created new topic: {topic_name} ({topic_slug})")
                else:
                    # We've created this topic during this batch, but it's not committed yet
                    topic = Topic.query.filter_by(slug=topic_slug).first()

            # If all validations pass, add to valid questions
            valid_questions.append({
                'topic_id': topic.id if topic.id else None,  # Will be set after commit
                'topic_slug': topic_slug,  # Keep track of slug for topics created in this batch
                'question_text': question_data['question_text'].strip(),
                'options': [str(opt).strip() for opt in question_data['options']],
                'correct_answer': correct_answer
            })
            
        except Exception as e:
            failed_count += 1
            errors.append(f"Row {index + 1}: {str(e)}")
            continue
    
    # Commit new topics first if any were created
    if created_topics:
        try:
            db.session.commit()
            print(f"Successfully created {len(created_topics)} new topics")
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'error': 'Failed to create new topics',
                'detail': str(e),
                'errors': errors
            }), 400
    
    # Second pass: Add valid questions to database
    if valid_questions:
        try:
            for question_data in valid_questions:
                # If we were tracking by slug for new topics, get the actual topic id now
                if question_data['topic_id'] is None:
                    topic = Topic.query.filter_by(slug=question_data['topic_slug']).first()
                    question_data['topic_id'] = topic.id
                
                # Remove the temporary slug field
                if 'topic_slug' in question_data:
                    question_data.pop('topic_slug')
                
                question = Question(**question_data)
                db.session.add(question)
                success_count += 1
            
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'error': 'Failed to commit questions to database',
                'detail': str(e),
                'errors': errors
            }), 400
    
    return jsonify({
        'success': success_count,
        'failed': failed_count,
        'topics_created': len(created_topics),
        'errors': errors if errors else None
    })