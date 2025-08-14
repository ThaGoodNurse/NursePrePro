import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Progress } from './components/ui/progress';
import { Separator } from './components/ui/separator';
import { BookOpen, Brain, Trophy, Target, ArrowRight, CheckCircle, XCircle, RotateCcw } from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [studyAreas, setStudyAreas] = useState([]);
  const [currentQuiz, setCurrentQuiz] = useState(null);
  const [quizQuestions, setQuizQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [quizResults, setQuizResults] = useState(null);
  const [userStats, setUserStats] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStudyAreas();
    fetchUserStats();
  }, []);

  const fetchStudyAreas = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/study-areas`);
      setStudyAreas(response.data.study_areas);
    } catch (error) {
      console.error('Error fetching study areas:', error);
    }
  };

  const fetchUserStats = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/stats`);
      setUserStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const startQuiz = async (areaId, questionCount = 10) => {
    setLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/quiz/start?area_id=${areaId}&question_count=${questionCount}`);
      setCurrentQuiz({
        id: response.data.quiz_id,
        areaId: areaId,
        totalQuestions: response.data.total_questions,
        areaName: studyAreas.find(area => area.id === areaId)?.name || 'Unknown'
      });
      setQuizQuestions(response.data.questions);
      setCurrentQuestionIndex(0);
      setSelectedAnswers({});
      setQuizResults(null);
      setCurrentView('quiz');
    } catch (error) {
      console.error('Error starting quiz:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectAnswer = (questionId, optionId) => {
    setSelectedAnswers(prev => ({
      ...prev,
      [questionId]: optionId
    }));
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < quizQuestions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
    }
  };

  const previousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
    }
  };

  const submitQuiz = async () => {
    setLoading(true);
    try {
      const answers = Object.entries(selectedAnswers).map(([questionId, optionId]) => ({
        question_id: questionId,
        selected_option_id: optionId
      }));

      const response = await axios.post(`${BACKEND_URL}/api/quiz/${currentQuiz.id}/submit`, answers);
      setQuizResults(response.data);
      setCurrentView('results');
      fetchUserStats(); // Refresh stats
    } catch (error) {
      console.error('Error submitting quiz:', error);
    } finally {
      setLoading(false);
    }
  };

  const resetQuiz = () => {
    setCurrentQuiz(null);
    setQuizQuestions([]);
    setCurrentQuestionIndex(0);
    setSelectedAnswers({});
    setQuizResults(null);
    setCurrentView('dashboard');
  };

  const renderDashboard = () => (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <div className="bg-blue-600 p-3 rounded-full mr-4">
              <Brain className="h-8 w-8 text-white" />
            </div>
            <h1 className="text-4xl font-bold text-gray-800">NursePrep</h1>
          </div>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Master your nursing studies with comprehensive multiple-choice practice tests
          </p>
        </div>

        {/* Stats Overview */}
        {userStats && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <Card className="bg-white shadow-md hover:shadow-lg transition-shadow">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Total Quizzes</CardTitle>
                <Trophy className="h-4 w-4 text-amber-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-800">{userStats.total_quizzes}</div>
              </CardContent>
            </Card>

            <Card className="bg-white shadow-md hover:shadow-lg transition-shadow">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Average Score</CardTitle>
                <Target className="h-4 w-4 text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-800">{userStats.average_score}%</div>
              </CardContent>
            </Card>

            <Card className="bg-white shadow-md hover:shadow-lg transition-shadow">
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">Study Areas</CardTitle>
                <BookOpen className="h-4 w-4 text-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-800">{studyAreas.length}</div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Study Areas */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Choose Your Study Area</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {studyAreas.map((area) => (
              <Card key={area.id} className="bg-white shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className={`w-4 h-4 rounded-full`} style={{ backgroundColor: area.color }}></div>
                    <Badge variant="secondary">{area.question_count} questions</Badge>
                  </div>
                  <CardTitle className="text-lg font-semibold text-gray-800">{area.name}</CardTitle>
                  <CardDescription className="text-gray-600">{area.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button 
                    onClick={() => startQuiz(area.id)} 
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                    disabled={area.question_count === 0}
                  >
                    Start Practice Test
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        {userStats && userStats.recent_attempts.length > 0 && (
          <Card className="bg-white shadow-md">
            <CardHeader>
              <CardTitle className="text-xl font-semibold text-gray-800">Recent Quiz Results</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {userStats.recent_attempts.map((attempt, index) => (
                  <div key={attempt.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div>
                      <h4 className="font-medium text-gray-800">{attempt.area_name}</h4>
                      <p className="text-sm text-gray-600">
                        {new Date(attempt.completed_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-bold" style={{ color: attempt.score >= 70 ? '#10B981' : '#EF4444' }}>
                        {attempt.score}%
                      </div>
                      <div className="text-sm text-gray-600">
                        {attempt.score >= 70 ? 'Passed' : 'Needs Review'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );

  const renderQuiz = () => {
    const currentQuestion = quizQuestions[currentQuestionIndex];
    const progress = ((currentQuestionIndex + 1) / quizQuestions.length) * 100;
    const allQuestionsAnswered = quizQuestions.every(q => selectedAnswers[q.id]);

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-8">
        <div className="container mx-auto px-4 max-w-4xl">
          {/* Quiz Header */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h1 className="text-2xl font-bold text-gray-800">{currentQuiz.areaName}</h1>
                <p className="text-gray-600">Question {currentQuestionIndex + 1} of {quizQuestions.length}</p>
              </div>
              <Badge variant="outline" className="text-lg px-4 py-2">
                {Math.round(progress)}% Complete
              </Badge>
            </div>
            <Progress value={progress} className="h-2" />
          </div>

          {/* Question Card */}
          <Card className="bg-white shadow-lg mb-6">
            <CardHeader>
              <div className="flex items-center justify-between">
                <Badge variant="secondary">{currentQuestion.difficulty}</Badge>
                <div className="text-sm text-gray-500">
                  {selectedAnswers[currentQuestion.id] ? 'Answered' : 'Not answered'}
                </div>
              </div>
              <CardTitle className="text-xl leading-relaxed text-gray-800">
                {currentQuestion.question_text}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {currentQuestion.options.map((option, index) => {
                  const isSelected = selectedAnswers[currentQuestion.id] === option.id;
                  const letter = String.fromCharCode(65 + index); // A, B, C, D
                  
                  return (
                    <button
                      key={option.id}
                      onClick={() => selectAnswer(currentQuestion.id, option.id)}
                      className={`w-full p-4 text-left rounded-lg border-2 transition-all duration-200 hover:shadow-md ${
                        isSelected 
                          ? 'border-blue-500 bg-blue-50 text-blue-800' 
                          : 'border-gray-200 bg-white hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center">
                        <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-semibold mr-3 ${
                          isSelected ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-700'
                        }`}>
                          {letter}
                        </span>
                        <span className="text-base">{option.text}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Navigation */}
          <div className="flex items-center justify-between bg-white p-6 rounded-lg shadow-md">
            <Button 
              variant="outline" 
              onClick={previousQuestion}
              disabled={currentQuestionIndex === 0}
            >
              Previous
            </Button>

            <div className="flex space-x-2">
              {quizQuestions.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentQuestionIndex(index)}
                  className={`w-8 h-8 rounded-full text-sm font-medium transition-colors ${
                    index === currentQuestionIndex
                      ? 'bg-blue-500 text-white'
                      : selectedAnswers[quizQuestions[index].id]
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {index + 1}
                </button>
              ))}
            </div>

            {currentQuestionIndex === quizQuestions.length - 1 ? (
              <Button 
                onClick={submitQuiz}
                disabled={!allQuestionsAnswered || loading}
                className="bg-green-600 hover:bg-green-700 text-white"
              >
                {loading ? 'Submitting...' : 'Submit Quiz'}
              </Button>
            ) : (
              <Button 
                onClick={nextQuestion}
                disabled={currentQuestionIndex === quizQuestions.length - 1}
              >
                Next
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderResults = () => {
    const scoreColor = quizResults.score >= 70 ? 'text-green-600' : 'text-red-600';
    const scoreMessage = quizResults.score >= 70 ? 'Great job!' : 'Keep studying!';
    
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-8">
        <div className="container mx-auto px-4 max-w-4xl">
          {/* Results Header */}
          <Card className="bg-white shadow-lg mb-8">
            <CardHeader className="text-center">
              <div className={`text-6xl font-bold ${scoreColor} mb-2`}>
                {quizResults.score}%
              </div>
              <CardTitle className="text-2xl text-gray-800 mb-2">
                {scoreMessage}
              </CardTitle>
              <CardDescription className="text-lg">
                You got {quizResults.correct_answers} out of {quizResults.total_questions} questions correct
              </CardDescription>
              <div className="mt-4">
                <Progress value={quizResults.score} className="h-3" />
              </div>
            </CardHeader>
          </Card>

          {/* Question Review */}
          <Card className="bg-white shadow-lg mb-6">
            <CardHeader>
              <CardTitle className="text-xl text-gray-800">Question Review</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {quizResults.results.map((result, index) => (
                  <div key={result.question_id} className="border-b border-gray-200 pb-6 last:border-b-0">
                    <div className="flex items-start mb-3">
                      <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 text-gray-700 text-sm font-semibold mr-3 mt-1">
                        {index + 1}
                      </span>
                      <div className="flex-1">
                        <h4 className="text-base font-medium text-gray-800 mb-2">
                          {result.question_text}
                        </h4>
                        
                        <div className="space-y-2">
                          <div className="flex items-center">
                            {result.is_correct ? (
                              <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                            ) : (
                              <XCircle className="h-5 w-5 text-red-500 mr-2" />
                            )}
                            <span className="text-sm text-gray-600">Your answer:</span>
                            <span className={`ml-2 font-medium ${result.is_correct ? 'text-green-600' : 'text-red-600'}`}>
                              {result.selected_option || 'Not answered'}
                            </span>
                          </div>
                          
                          {!result.is_correct && (
                            <div className="flex items-center">
                              <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                              <span className="text-sm text-gray-600">Correct answer:</span>
                              <span className="ml-2 font-medium text-green-600">
                                {result.correct_option}
                              </span>
                            </div>
                          )}
                        </div>
                        
                        {result.explanation && (
                          <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                            <h5 className="text-sm font-medium text-blue-800 mb-1">Explanation:</h5>
                            <p className="text-sm text-blue-700">{result.explanation}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex justify-center space-x-4">
            <Button 
              onClick={() => startQuiz(currentQuiz.areaId)}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <RotateCcw className="mr-2 h-4 w-4" />
              Try Again
            </Button>
            <Button 
              variant="outline" 
              onClick={resetQuiz}
            >
              Back to Dashboard
            </Button>
          </div>
        </div>
      </div>
    );
  };

  // Render based on current view
  if (currentView === 'quiz') {
    return renderQuiz();
  } else if (currentView === 'results') {
    return renderResults();
  } else {
    return renderDashboard();
  }
}

export default App;