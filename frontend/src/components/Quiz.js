import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import API_URL from '../config/api';
import QuizResults from './QuizResults'; // Import the new component

function Quiz() {
  const { topic } = useParams();
  const navigate = useNavigate();
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  // Add user state - in a real app you'd get this from authentication
  const [userId, setUserId] = useState(null);

  useEffect(() => {
    // In a real app, get this from your authentication system
    // This is just a placeholder implementation
    const generateTempUserId = () => {
      // Generate a simple user ID from local storage or create a new one
      let id = localStorage.getItem('tempUserId');
      if (!id) {
        id = 'user_' + Math.random().toString(36).substring(2, 15);
        localStorage.setItem('tempUserId', id);
      }
      return id;
    };

    setUserId(generateTempUserId());
  }, []);

  const fetchQuiz = useCallback(async () => {
    try {
      setLoading(true);
      console.log(`Fetching quiz for topic: ${topic}`);
      const response = await fetch(`${API_URL}/api/quiz/${topic}`);
      
      if (!response.ok) {
        console.error(`Failed to fetch quiz: ${response.status} ${response.statusText}`);
        throw new Error('Failed to fetch quiz');
      }
      
      const data = await response.json();
      console.log('Fetched quiz data:', data);
      setQuiz(data);
      setAnswers({}); // Reset answers when getting new questions
      setError(null);
    } catch (err) {
      console.error('Error fetching quiz:', err);
      setError('Failed to load quiz. Please try again.');
    } finally {
      setLoading(false);
    }
  }, [topic]);

  useEffect(() => {
    fetchQuiz();
  }, [fetchQuiz]);

  const handleAnswerSelect = (questionId, answerIndex) => {
    console.log(`Selected answer for question ${questionId}: ${answerIndex}`);
    setAnswers(prev => ({
      ...prev,
      [questionId]: answerIndex
    }));
  };

  const handleSubmit = async () => {
    try {
      // Check if all questions are answered
      const answeredQuestions = Object.keys(answers).length;
      const totalQuestions = quiz.questions.length;

      console.log(`Questions answered: ${answeredQuestions}/${totalQuestions}`);
      console.log('Current answers:', answers);

      if (answeredQuestions < totalQuestions) {
        alert(`Please answer all questions (${answeredQuestions}/${totalQuestions} answered)`);
        return;
      }

      // Debug log
      console.log('Submitting answers:', {
        topic,
        answers
      });

      const response = await fetch(`${API_URL}/api/quiz/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          topic: topic,
          answers: answers
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error response from server:', errorData);
        throw new Error(errorData.error || 'Failed to submit quiz');
      }

      const data = await response.json();
      console.log('Quiz result received from API:', data);
      
      // Make sure we have all the expected data
      if (data.correct === undefined || data.total === undefined) {
        console.error('Invalid quiz result format:', data);
        throw new Error('Invalid quiz result format');
      }
      
      // Calculate exact score to ensure consistency
      const calculatedScore = (data.correct / data.total) * 100;
      console.log('Calculated raw score:', calculatedScore);
      
      // Round to 2 decimal places for display
      const roundedScore = Math.round(calculatedScore * 100) / 100;
      console.log('Rounded score for display:', roundedScore);
      
      // Create a consistent result object
      const finalResult = {
        correct: data.correct,
        total: data.total,
        score: calculatedScore,  // Store exact score for calculations
        displayScore: roundedScore  // Rounded score for display
      };
      
      console.log('Final result object:', finalResult);
      setResult(finalResult);
    } catch (err) {
      console.error('Error submitting quiz:', err);
      setError('Failed to submit quiz. Please try again.');
    }
  };

  const handleTryAgain = async () => {
    console.log('Trying another quiz');
    setResult(null);
    setAnswers({});
    await fetchQuiz();
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">Loading quiz...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
          <p>{error}</p>
          <button
            onClick={() => navigate('/')}
            className="mt-4 bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600"
          >
            Return to Home
          </button>
        </div>
      </div>
    );
  }

  if (!quiz) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">No quiz found.</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl">
      <h1 className="text-3xl font-bold mb-6">{quiz.title}</h1>
      {quiz.total_questions > quiz.selected_questions && (
        <p className="mb-4 text-gray-600">
          Showing {quiz.selected_questions} questions from a pool of {quiz.total_questions} available questions.
        </p>
      )}
      
      {!result ? (
        <div className="space-y-8">
          {quiz.questions.map((question, index) => (
            <div key={question.id} className="bg-white rounded-lg shadow-md p-6">
              <p className="text-xl mb-4">
                {index + 1}. {question.question}
              </p>
              <div className="space-y-2">
                {question.options.map((option, optionIndex) => (
                  <label
                    key={optionIndex}
                    className={`flex items-center p-3 rounded-lg cursor-pointer transition-colors ${
                      answers[question.id] === optionIndex
                        ? 'bg-blue-50 border border-blue-200'
                        : 'hover:bg-gray-50 border border-transparent'
                    }`}
                  >
                    <input
                      type="radio"
                      name={`question-${question.id}`}
                      className="mr-3"
                      checked={answers[question.id] === optionIndex}
                      onChange={() => handleAnswerSelect(question.id, optionIndex)}
                    />
                    <span>{option}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
          
          <button
            onClick={handleSubmit}
            className="w-full bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 font-medium transition-colors"
          >
            Submit Quiz
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow-md p-8">
          <h2 className="text-2xl font-bold mb-4">Quiz Results</h2>
          
          <div className="bg-blue-50 p-6 rounded-lg mb-6">
            <p className="text-4xl font-bold text-blue-600 mb-2">
              {/* Use displayScore for showing the percentage */}
              {Math.round(result.displayScore)}%
            </p>
            <p className="text-lg text-blue-800">
              You got {result.correct} out of {result.total} questions correct
            </p>
          </div>
          
          {/* Integrate the new QuizResults component */}
          <QuizResults 
            userId={userId}
            topic={topic}
            answers={answers}
            quizResult={result}
          />
          
          <div className="mt-6 space-x-4 text-center">
            <button
              onClick={handleTryAgain}
              className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 transition-colors"
            >
              Try Another Quiz
            </button>
            <button
              onClick={() => navigate('/')}
              className="bg-gray-500 text-white px-6 py-2 rounded hover:bg-gray-600 transition-colors"
            >
              Back to Home
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Quiz;