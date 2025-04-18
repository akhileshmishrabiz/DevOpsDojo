// quiz-analysis-lambda/index.js
const AWS = require('aws-sdk');
const dynamoDB = new AWS.DynamoDB.DocumentClient();

// Main Lambda handler function
exports.handler = async (event) => {
  try {
    console.log('Event received:', JSON.stringify(event));
    
    // Parse the incoming request
    const body = JSON.parse(event.body);
    const { userId, topic, answers, correct, total, score } = body;
    
    // Determine which operation to perform based on the API path
    const path = event.path;
    let result;
    
    if (path === '/analyze-results') {
      result = await analyzeResults(userId, topic, answers, correct, total, score);
    } else if (path === '/get-recommendations') {
      result = await getRecommendations(userId, topic);
    } else if (path === '/track-progress') {
      result = await trackProgress(userId);
    } else {
      return formatResponse(400, { error: 'Invalid endpoint' });
    }
    
    return formatResponse(200, result);
  } catch (error) {
    console.error('Error processing request:', error);
    return formatResponse(500, { error: 'Internal server error', detail: error.message });
  }
};

// Analyze quiz results and identify knowledge gaps
async function analyzeResults(userId, topic, answers, correct, total, score) {
  // Calculate strength areas and weak areas based on the answers
  const { strengths, weaknesses } = analyzeAnswerPatterns(answers);
  
  // Save results to DynamoDB for future reference
  await saveResultsToDatabase(userId, topic, answers, score, strengths, weaknesses);
  
  return {
    userId,
    topic,
    score,
    strengths,
    weaknesses,
    analysisComplete: true,
    timestamp: new Date().toISOString()
  };
}

// Get personalized recommendations based on quiz performance
async function getRecommendations(userId, topic) {
  // Get the user's historical performance from DynamoDB
  const userResults = await getUserResults(userId);
  
  // Generate personalized recommendations based on weak areas
  const recommendations = generateRecommendations(topic, userResults);
  
  return {
    userId,
    topic,
    recommendations,
    timestamp: new Date().toISOString()
  };
}

// Track user's progress over time across different quiz attempts
async function trackProgress(userId) {
  // Get all historical results for the user
  const userResults = await getUserResults(userId);
  
  // Analyze progression over time
  const progressAnalysis = analyzeProgress(userResults);
  
  return {
    userId,
    progressAnalysis,
    timestamp: new Date().toISOString()
  };
}

// Helper function to analyze answer patterns and identify strengths/weaknesses
function analyzeAnswerPatterns(answers) {
  // This is a simplified example - in reality, you'd have a more complex algorithm
  // that categorizes questions by subtopic and identifies patterns
  
  const strengths = [];
  const weaknesses = [];
  
  // Analyze the answers and categorize them
  // In a real implementation, you would parse the questions and analyze by topic area
  
  // Return dummy data for this example
  return {
    strengths: ['Containerization Basics', 'Docker Networking'],
    weaknesses: ['Docker Volumes', 'Multi-stage Builds']
  };
}

// Save quiz results to DynamoDB
async function saveResultsToDatabase(userId, topic, answers, score, strengths, weaknesses) {
  const params = {
    TableName: 'QuizResults',
    Item: {
      userId,
      quizId: `${topic}-${Date.now()}`,
      topic,
      answers,
      score,
      strengths,
      weaknesses,
      timestamp: new Date().toISOString()
    }
  };
  
  try {
    await dynamoDB.put(params).promise();
    console.log('Results saved to database successfully');
    return true;
  } catch (error) {
    console.error('Error saving to database:', error);
    // Don't throw the error to avoid breaking the overall process
    return false;
  }
}

// Get user's historical quiz results from DynamoDB
async function getUserResults(userId) {
  const params = {
    TableName: 'QuizResults',
    KeyConditionExpression: 'userId = :userId',
    ExpressionAttributeValues: {
      ':userId': userId
    },
    ScanIndexForward: false // to get results in descending order (newest first)
  };
  
  try {
    const data = await dynamoDB.query(params).promise();
    return data.Items;
  } catch (error) {
    console.error('Error fetching user results:', error);
    return [];
  }
}

// Generate recommendations based on weak areas
function generateRecommendations(topic, userResults) {
  // Get the most recent quiz result
  const latestResult = userResults[0];
  
  // Create topic-specific recommendations based on weak areas
  const recommendations = [];
  
  if (topic === 'docker') {
    if (latestResult.weaknesses.includes('Docker Volumes')) {
      recommendations.push({
        type: 'Resource',
        title: 'Docker Volumes Deep Dive',
        link: 'https://docs.docker.com/storage/volumes/',
        description: 'Official documentation on Docker volumes and persistent storage'
      });
      
      recommendations.push({
        type: 'Practice',
        title: 'Volume Management Exercise',
        description: 'Create a Docker volume and use it with multiple containers'
      });
    }
    
    if (latestResult.weaknesses.includes('Multi-stage Builds')) {
      recommendations.push({
        type: 'Resource',
        title: 'Multi-stage Builds Best Practices',
        link: 'https://docs.docker.com/build/building/multi-stage/',
        description: 'Learn how to optimize Docker images with multi-stage builds'
      });
    }
  } else if (topic === 'kubernetes') {
    // Add Kubernetes-specific recommendations
    recommendations.push({
      type: 'Resource',
      title: 'Kubernetes Pod Design Patterns',
      link: 'https://kubernetes.io/docs/concepts/workloads/pods/',
      description: 'Learn about pod design patterns in Kubernetes'
    });
  }
  
  // If no specific weaknesses were found, return general recommendations
  if (recommendations.length === 0) {
    recommendations.push({
      type: 'General',
      title: 'Continue Learning',
      description: 'You\'re doing well! Try taking our advanced quiz to challenge yourself further.'
    });
  }
  
  return recommendations;
}

// Analyze user's progress over time
function analyzeProgress(userResults) {
  // Group results by topic
  const topicResults = {};
  
  userResults.forEach(result => {
    if (!topicResults[result.topic]) {
      topicResults[result.topic] = [];
    }
    
    topicResults[result.topic].push({
      timestamp: result.timestamp,
      score: result.score
    });
  });
  
  // Calculate improvement for each topic
  const progressByTopic = {};
  
  Object.keys(topicResults).forEach(topic => {
    const results = topicResults[topic];
    results.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    if (results.length >= 2) {
      const firstScore = results[0].score;
      const latestScore = results[results.length - 1].score;
      const improvement = latestScore - firstScore;
      
      progressByTopic[topic] = {
        firstAttempt: results[0].timestamp,
        latestAttempt: results[results.length - 1].timestamp,
        attempts: results.length,
        firstScore,
        latestScore,
        improvement,
        improvementPercentage: ((improvement / firstScore) * 100).toFixed(2)
      };
    } else {
      progressByTopic[topic] = {
        firstAttempt: results[0].timestamp,
        latestAttempt: results[0].timestamp,
        attempts: 1,
        firstScore: results[0].score,
        latestScore: results[0].score,
        improvement: 0,
        improvementPercentage: '0.00'
      };
    }
  });
  
  return progressByTopic;
}

// Helper function to format Lambda response
function formatResponse(statusCode, body) {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*', // CORS header for API Gateway integration
      'Access-Control-Allow-Credentials': true
    },
    body: JSON.stringify(body)
  };
}