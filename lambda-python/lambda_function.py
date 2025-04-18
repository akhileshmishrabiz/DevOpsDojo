# lambda_function.py
import json
import boto3
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'QuizResults'))

def lambda_handler(event, context):
    """Main Lambda handler function"""
    try:
        print(f"Event received: {json.dumps(event)}")
        
        # Parse the incoming request
        body = json.loads(event['body'])
        user_id = body.get('userId')
        topic = body.get('topic')
        
        # Determine which operation to perform based on the API path
        path = event['path']
        
        if path == '/analyze-results':
            answers = body.get('answers')
            correct = body.get('correct')
            total = body.get('total')
            score = body.get('score')
            result = analyze_results(user_id, topic, answers, correct, total, score)
        elif path == '/get-recommendations':
            result = get_recommendations(user_id, topic)
        elif path == '/track-progress':
            result = track_progress(user_id)
        else:
            return format_response(400, {'error': 'Invalid endpoint'})
        
        return format_response(200, result)
    
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return format_response(500, {'error': 'Internal server error', 'detail': str(e)})

def analyze_results(user_id: str, topic: str, answers: Dict, correct: int, total: int, score: float) -> Dict:
    """Analyze quiz results and identify knowledge gaps"""
    # Calculate strength areas and weak areas based on the answers
    analysis = analyze_answer_patterns(answers)
    
    # Save results to DynamoDB for future reference
    save_results_to_database(user_id, topic, answers, score, analysis['strengths'], analysis['weaknesses'])
    
    return {
        'userId': user_id,
        'topic': topic,
        'score': score,
        'strengths': analysis['strengths'],
        'weaknesses': analysis['weaknesses'],
        'analysisComplete': True,
        'timestamp': datetime.now().isoformat()
    }

def get_recommendations(user_id: str, topic: str) -> Dict:
    """Get personalized recommendations based on quiz performance"""
    # Get the user's historical performance from DynamoDB
    user_results = get_user_results(user_id)
    
    # Generate personalized recommendations based on weak areas
    recommendations = generate_recommendations(topic, user_results)
    
    return {
        'userId': user_id,
        'topic': topic,
        'recommendations': recommendations,
        'timestamp': datetime.now().isoformat()
    }

def track_progress(user_id: str) -> Dict:
    """Track user's progress over time across different quiz attempts"""
    # Get all historical results for the user
    user_results = get_user_results(user_id)
    
    # Analyze progression over time
    progress_analysis = analyze_progress(user_results)
    
    return {
        'userId': user_id,
        'progressAnalysis': progress_analysis,
        'timestamp': datetime.now().isoformat()
    }

def analyze_answer_patterns(answers: Dict) -> Dict:
    """Helper function to analyze answer patterns and identify strengths/weaknesses"""
    # This is a simplified example - in reality, you'd have a more complex algorithm
    # that categorizes questions by subtopic and identifies patterns
    
    # For this example, return some dummy data
    # In production, this would analyze actual answers
    return {
        'strengths': ['Containerization Basics', 'Docker Networking'],
        'weaknesses': ['Docker Volumes', 'Multi-stage Builds']
    }

def save_results_to_database(user_id: str, topic: str, answers: Dict, 
                           score: float, strengths: List[str], weaknesses: List[str]) -> bool:
    """Save quiz results to DynamoDB"""
    try:
        table.put_item(
            Item={
                'userId': user_id,
                'quizId': f"{topic}-{int(datetime.now().timestamp() * 1000)}",
                'topic': topic,
                'answers': answers,
                'score': score,
                'strengths': strengths,
                'weaknesses': weaknesses,
                'timestamp': datetime.now().isoformat()
            }
        )
        print('Results saved to database successfully')
        return True
    except Exception as e:
        print(f'Error saving to database: {str(e)}')
        # Don't throw the error to avoid breaking the overall process
        return False

def get_user_results(user_id: str) -> List[Dict]:
    """Get user's historical quiz results from DynamoDB"""
    try:
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('userId').eq(user_id),
            ScanIndexForward=False  # to get results in descending order (newest first)
        )
        return response.get('Items', [])
    except Exception as e:
        print(f'Error fetching user results: {str(e)}')
        return []

def generate_recommendations(topic: str, user_results: List[Dict]) -> List[Dict]:
    """Generate recommendations based on weak areas"""
    # For this example, return some dummy recommendations
    # In production, this would analyze actual user performance
    recommendations = []
    
    if topic == 'docker':
        recommendations.append({
            'type': 'Resource',
            'title': 'Docker Volumes Deep Dive',
            'link': 'https://docs.docker.com/storage/volumes/',
            'description': 'Official documentation on Docker volumes and persistent storage'
        })
        
        recommendations.append({
            'type': 'Practice',
            'title': 'Volume Management Exercise',
            'description': 'Create a Docker volume and use it with multiple containers'
        })
    elif topic == 'kubernetes':
        recommendations.append({
            'type': 'Resource',
            'title': 'Kubernetes Pod Design Patterns',
            'link': 'https://kubernetes.io/docs/concepts/workloads/pods/',
            'description': 'Learn about pod design patterns in Kubernetes'
        })
    
    return recommendations

def analyze_progress(user_results: List[Dict]) -> Dict:
    """Analyze user's progress over time"""
    # Group results by topic
    topic_results = {}
    
    for result in user_results:
        topic = result.get('topic')
        if topic not in topic_results:
            topic_results[topic] = []
        
        topic_results[topic].append({
            'timestamp': result.get('timestamp'),
            'score': result.get('score')
        })
    
    # Calculate improvement for each topic
    progress_by_topic = {}
    
    for topic, results in topic_results.items():
        # Sort by timestamp (oldest first)
        results.sort(key=lambda x: x['timestamp'])
        
        if len(results) >= 2:
            first_score = results[0]['score']
            latest_score = results[-1]['score']
            improvement = latest_score - first_score
            
            progress_by_topic[topic] = {
                'firstAttempt': results[0]['timestamp'],
                'latestAttempt': results[-1]['timestamp'],
                'attempts': len(results),
                'firstScore': first_score,
                'latestScore': latest_score,
                'improvement': improvement,
                'improvementPercentage': f"{(improvement / first_score * 100):.2f}" if first_score > 0 else "0.00"
            }
        elif len(results) == 1:
            progress_by_topic[topic] = {
                'firstAttempt': results[0]['timestamp'],
                'latestAttempt': results[0]['timestamp'],
                'attempts': 1,
                'firstScore': results[0]['score'],
                'latestScore': results[0]['score'],
                'improvement': 0,
                'improvementPercentage': "0.00"
            }
    
    return progress_by_topic

def format_response(status_code: int, body: Dict) -> Dict:
    """Helper function to format Lambda response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # CORS header for API Gateway integration
            'Access-Control-Allow-Credentials': True
        },
        'body': json.dumps(body)
    }