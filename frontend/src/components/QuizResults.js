import React, { useEffect, useState } from 'react';
import { analyzeQuizResults, getRecommendations } from '../services/quizAnalysisService';

function QuizResults({ userId, topic, answers, quizResult }) {
  const [loading, setLoading] = useState(true);
  const [analysis, setAnalysis] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnalysisData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Generate a temporary userId if none is provided
        const tempUserId = userId || `temp-${Date.now()}`;
        
        console.log('QuizResults component received:', {
          userId: tempUserId,
          topic,
          answers,
          quizResult
        });

        // Call the Lambda function to analyze results
        console.log('Calling analyzeQuizResults with:', {
          userId: tempUserId,
          topic,
          answers,
          correct: quizResult.correct,
          total: quizResult.total,
          score: quizResult.score
        });
        
        const analysisResult = await analyzeQuizResults(
          tempUserId,
          topic,
          answers,
          quizResult.correct,
          quizResult.total,
          quizResult.score
        );
        
        console.log('Analysis result received:', analysisResult);
        setAnalysis(analysisResult);
        
        // Get recommendations based on analysis
        console.log('Calling getRecommendations for:', tempUserId, topic);
        const recommendationsData = await getRecommendations(tempUserId, topic);
        console.log('Recommendations received:', recommendationsData);
        
        if (recommendationsData && recommendationsData.recommendations) {
          setRecommendations(recommendationsData.recommendations);
        } else {
          console.warn('Recommendations data is missing or malformed:', recommendationsData);
        }
        
      } catch (err) {
        console.error('Error getting analysis:', err);
        setError(`Failed to load advanced analysis: Error: ${err.toString()}`);
      } finally {
        setLoading(false);
      }
    };

    // Only fetch analysis if we have quiz results
    if (quizResult && quizResult.correct !== undefined && quizResult.total !== undefined) {
      fetchAnalysisData();
    } else {
      console.error('Quiz result is missing required data:', quizResult);
      setError('Invalid quiz result data');
      setLoading(false);
    }
  }, [userId, topic, answers, quizResult]);

  if (loading) {
    return (
      <div className="mt-6">
        <div className="bg-blue-50 p-4 rounded-lg">
          <p className="text-center">Analyzing your results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mt-6">
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 p-4 rounded-lg">
          <p>{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-6">
      {/* Advanced Analysis Section */}
      {analysis && (
        <div className="bg-white border rounded-lg p-6 mb-6">
          <h3 className="text-xl font-bold mb-4">Your Knowledge Analysis</h3>
          
          {analysis.strengths && analysis.strengths.length > 0 && (
            <div className="mb-4">
              <h4 className="font-bold text-green-700 mb-2">Strengths</h4>
              <ul className="list-disc pl-6">
                {analysis.strengths.map((strength, index) => (
                  <li key={index} className="text-green-700 mb-1">{strength}</li>
                ))}
              </ul>
            </div>
          )}
          
          {analysis.weaknesses && analysis.weaknesses.length > 0 && (
            <div>
              <h4 className="font-bold text-red-700 mb-2">Areas for Improvement</h4>
              <ul className="list-disc pl-6">
                {analysis.weaknesses.map((weakness, index) => (
                  <li key={index} className="text-red-700 mb-1">{weakness}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Recommendations Section */}
      {recommendations && recommendations.length > 0 && (
        <div className="bg-white border rounded-lg p-6 mb-6">
          <h3 className="text-xl font-bold mb-4">Personalized Recommendations</h3>
          <div className="space-y-4">
            {recommendations.map((recommendation, index) => (
              <div key={index} className="border-l-4 border-blue-500 pl-4 py-2">
                <h4 className="font-bold">{recommendation.title}</h4>
                <p className="text-gray-700 mb-2">{recommendation.description}</p>
                {recommendation.link && (
                  <a 
                    href={recommendation.link} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    Learn more
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default QuizResults;