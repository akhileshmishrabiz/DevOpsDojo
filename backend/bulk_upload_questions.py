import csv
from app import create_app
from app.models import db, Topic, Question
from sqlalchemy.exc import IntegrityError

def bulk_upload_questions(csv_file_path, batch_size=100):
    app = create_app()
    
    with app.app_context():
        with open(csv_file_path, 'r') as file:
            csv_reader = csv.DictReader(file)
            questions_batch = []
            total_processed = 0
            total_success = 0
            total_failed = 0
            topics_created = 0
            
            for row in csv_reader:
                try:
                    topic_slug = row['topic_slug'].strip()
                    
                    # Find or create the topic
                    topic = Topic.query.filter_by(slug=topic_slug).first()
                    if not topic:
                        # Create a new topic with default values based on slug
                        topic_name = topic_slug.replace('-', ' ').title()
                        topic = Topic(
                            name=topic_name,
                            description=f"Questions about {topic_name}",
                            slug=topic_slug
                        )
                        db.session.add(topic)
                        db.session.commit()  # Commit immediately to get the ID
                        topics_created += 1
                        print(f"Created new topic: {topic_name} ({topic_slug})")
                    
                    # Parse options from CSV format
                    options = []
                    for i in range(1, 5):
                        option_key = f'option{i}'
                        if option_key in row and row[option_key]:
                            options.append(row[option_key])
                    
                    # If CSV has a single options column instead of option1, option2, etc.
                    if 'options' in row and not options:
                        # Try to parse options as a list
                        try:
                            import json
                            options = json.loads(row['options'])
                        except:
                            # Fallback: assume comma-separated values
                            options = [opt.strip() for opt in row['options'].split(',')]
                    
                    # Validate options
                    if len(options) != 4:
                        print(f"Error: Question must have exactly 4 options (row has {len(options)})")
                        total_failed += 1
                        continue
                    
                    # Create question object
                    question = Question(
                        topic_id=topic.id,
                        question_text=row['question_text'],
                        options=options,
                        correct_answer=int(row['correct_answer'])
                    )
                    
                    questions_batch.append(question)
                    total_processed += 1
                    
                    # Commit in batches
                    if len(questions_batch) >= batch_size:
                        try:
                            db.session.bulk_save_objects(questions_batch)
                            db.session.commit()
                            total_success += len(questions_batch)
                            print(f"Committed batch of {len(questions_batch)} questions")
                            questions_batch = []
                        except IntegrityError as e:
                            db.session.rollback()
                            print(f"Error in batch: {str(e)}")
                            total_failed += len(questions_batch)
                            questions_batch = []
                
                except Exception as e:
                    print(f"Error processing row: {str(e)}")
                    total_failed += 1
            
            # Commit any remaining questions
            if questions_batch:
                try:
                    db.session.bulk_save_objects(questions_batch)
                    db.session.commit()
                    total_success += len(questions_batch)
                except IntegrityError as e:
                    db.session.rollback()
                    print(f"Error in final batch: {str(e)}")
                    total_failed += len(questions_batch)
            
            print(f"\nUpload Summary:")
            print(f"Total Processed: {total_processed}")
            print(f"Successfully Uploaded: {total_success}")
            print(f"Failed: {total_failed}")
            print(f"Topics Created: {topics_created}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: python bulk_upload_questions.py <csv_file_path>")
        sys.exit(1)
    
    bulk_upload_questions(sys.argv[1])