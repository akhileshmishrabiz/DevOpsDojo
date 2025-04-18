// src/services/quizAnalysisService.js
// This service integrates with the Lambda API Gateway endpoints

// Get the API URL from environment variables or use a default for development
// const LAMBDA_API_URL = process.env.REACT_APP_LAMBDA_API_URL;
const LAMBDA_API_URL = "https://qw3dinn13d.execute-api.ap-south-1.amazonaws.com/dev";

// Log the API URL when the service is loaded
console.log('Lambda API URL:', LAMBDA_API_URL);

/**
 * Submit quiz results for analysis
 * @param {string} userId - User identifier 
 * @param {string} topic - Quiz topic (e.g., 'docker', 'kubernetes')
 * @param {Object} answers - Object containing question IDs and selected answers
 * @param {number} correct - Number of correct answers
 * @param {number} total - Total number of questions
 * @param {number} score - Score percentage (0-100)
 * @returns {Promise} Analysis results
 */
export const analyzeQuizResults = async (userId, topic, answers, correct, total, score) => {
  try {
    if (!LAMBDA_API_URL) {
      console.error('Lambda API URL is not configured. Please check your .env file.');
      throw new Error('API URL not configured');
    }

    console.log(`Calling API: ${LAMBDA_API_URL}/analyze-results`);
    console.log('Request payload:', { userId, topic, answers, correct, total, score });
    
    const response = await fetch(`${LAMBDA_API_URL}/analyze-results`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        userId,
        topic,
        answers,
        correct,
        total,
        score
      })
    });

    // Log full response details for debugging
    console.log('API Response Status:', response.status);
    console.log('API Response Headers:', [...response.headers.entries()]);
    
    const responseText = await response.text();
    console.log('API Response Text:', responseText);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}, response: ${responseText}`);
    }

    // Try to parse the response as JSON
    try {
      const jsonResponse = JSON.parse(responseText);
      console.log('Parsed JSON response:', jsonResponse);
      return jsonResponse;
    } catch (parseError) {
      console.error('Error parsing response as JSON:', parseError);
      throw new Error('Invalid JSON response from API');
    }
  } catch (error) {
    console.error('Error analyzing quiz results:', error);
    throw error;
  }
};

/**
 * Get personalized learning recommendations based on quiz performance
 * @param {string} userId - User identifier
 * @param {string} topic - Quiz topic
 * @returns {Promise} Recommendations
 */
export const getRecommendations = async (userId, topic) => {
  try {
    if (!LAMBDA_API_URL) {
      console.error('Lambda API URL is not configured. Please check your .env file.');
      throw new Error('API URL not configured');
    }

    console.log(`Calling API: ${LAMBDA_API_URL}/get-recommendations`);
    console.log('Request payload:', { userId, topic });
    
    const response = await fetch(`${LAMBDA_API_URL}/get-recommendations`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        userId,
        topic
      })
    });

    // Log response details
    console.log('API Response Status:', response.status);
    
    const responseText = await response.text();
    console.log('API Response Text:', responseText);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}, response: ${responseText}`);
    }

    // Try to parse the response as JSON
    try {
      const jsonResponse = JSON.parse(responseText);
      console.log('Parsed JSON response:', jsonResponse);
      return jsonResponse;
    } catch (parseError) {
      console.error('Error parsing response as JSON:', parseError);
      throw new Error('Invalid JSON response from API');
    }
  } catch (error) {
    console.error('Error getting recommendations:', error);
    throw error;
  }
};

/**
 * Track user's progress across multiple quizzes
 * @param {string} userId - User identifier
 * @returns {Promise} Progress analysis
 */
export const trackProgress = async (userId) => {
  try {
    if (!LAMBDA_API_URL) {
      console.error('Lambda API URL is not configured. Please check your .env file.');
      throw new Error('API URL not configured');
    }

    console.log(`Calling API: ${LAMBDA_API_URL}/track-progress`);
    console.log('Request payload:', { userId });
    
    const response = await fetch(`${LAMBDA_API_URL}/track-progress`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        userId
      })
    });

    // Log response details
    console.log('API Response Status:', response.status);
    
    const responseText = await response.text();
    console.log('API Response Text:', responseText);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}, response: ${responseText}`);
    }

    // Try to parse the response as JSON
    try {
      const jsonResponse = JSON.parse(responseText);
      console.log('Parsed JSON response:', jsonResponse);
      return jsonResponse;
    } catch (parseError) {
      console.error('Error parsing response as JSON:', parseError);
      throw new Error('Invalid JSON response from API');
    }
  } catch (error) {
    console.error('Error tracking progress:', error);
    throw error;
  }
};