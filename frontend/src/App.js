import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Progress } from './components/ui/progress';
import { Separator } from './components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { BookOpen, Brain, Trophy, Target, ArrowRight, CheckCircle, XCircle, RotateCcw, RefreshCw, Eye, EyeOff, Volume2 } from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [currentView, setCurrentView] = useState('dashboard');
  const [activeTab, setActiveTab] = useState('quizzes');
  
  // Quiz state
  const [studyAreas, setStudyAreas] = useState([]);
  const [currentQuiz, setCurrentQuiz] = useState(null);
  const [quizQuestions, setQuizQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState({});
  const [quizResults, setQuizResults] = useState(null);
  
  // Flashcard state
  const [flashcardSets, setFlashcardSets] = useState([]);
  const [currentFlashcardSet, setCurrentFlashcardSet] = useState(null);
  const [flashcards, setFlashcards] = useState([]);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [showDefinition, setShowDefinition] = useState(false);
  const [studySession, setStudySession] = useState(null);
  const [knownCards, setKnownCards] = useState(new Set());
  
  // Stats state
  const [userStats, setUserStats] = useState(null);
  const [flashcardStats, setFlashcardStats] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStudyAreas();
    fetchFlashcardSets();
    fetchUserStats();
    fetchFlashcardStats();
  }, []);

  const fetchStudyAreas = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/study-areas`);
      setStudyAreas(response.data.study_areas);
    } catch (error) {
      console.error('Error fetching study areas:', error);
    }
  };

  const fetchFlashcardSets = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/flashcard-sets`);
      setFlashcardSets(response.data.flashcard_sets);
    } catch (error) {
      console.error('Error fetching flashcard sets:', error);
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

  const fetchFlashcardStats = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/flashcards/stats`);
      setFlashcardStats(response.data);
    } catch (error) {
      console.error('Error fetching flashcard stats:', error);
    }
  };

  // Quiz functions
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
      fetchUserStats();
    } catch (error) {
      console.error('Error submitting quiz:', error);
    } finally {
      setLoading(false);
    }
  };

  // Flashcard functions
  const startFlashcardStudy = async (setId) => {
    setLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/flashcards/study?set_id=${setId}&shuffle=true`);
      setCurrentFlashcardSet({
        id: setId,
        name: flashcardSets.find(set => set.id === setId)?.name || 'Unknown',
        totalCards: response.data.total_cards
      });
      setFlashcards(response.data.flashcards);
      setStudySession({ id: response.data.session_id });
      setCurrentCardIndex(0);
      setShowDefinition(false);
      setKnownCards(new Set());
      setCurrentView('flashcards');
    } catch (error) {
      console.error('Error starting flashcard study:', error);
    } finally {
      setLoading(false);
    }
  };

  const flipCard = () => {
    setShowDefinition(!showDefinition);
  };

  const markCard = async (known) => {
    if (!studySession || !flashcards[currentCardIndex]) return;
    
    try {
      await axios.post(`${BACKEND_URL}/api/flashcards/study/${studySession.id}/review`, {
        card_id: flashcards[currentCardIndex].id,
        known: known
      });
      
      if (known) {
        setKnownCards(prev => new Set([...prev, flashcards[currentCardIndex].id]));
      }
      
      nextCard();
    } catch (error) {
      console.error('Error marking card:', error);
    }
  };

  const nextCard = () => {
    if (currentCardIndex < flashcards.length - 1) {
      setCurrentCardIndex(prev => prev + 1);
      setShowDefinition(false);
    } else {
      // End of study session
      setCurrentView('flashcard-results');
      fetchFlashcardStats();
    }
  };

  const previousCard = () => {
    if (currentCardIndex > 0) {
      setCurrentCardIndex(prev => prev - 1);
      setShowDefinition(false);
    }
  };

  const resetToMainMenu = () => {
    setCurrentView('dashboard');
    setActiveTab('quizzes');
    setCurrentQuiz(null);
    setQuizQuestions([]);
    setCurrentQuestionIndex(0);
    setSelectedAnswers({});
    setQuizResults(null);
    setCurrentFlashcardSet(null);
    setFlashcards([]);
    setCurrentCardIndex(0);
    setShowDefinition(false);
    setStudySession(null);
    setKnownCards(new Set());
  };

  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.8;
      utterance.pitch = 1;
      speechSynthesis.speak(utterance);
    }
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
            Master your nursing studies with comprehensive practice tests and medical terminology flashcards
          </p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <Card className="bg-white shadow-md hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Total Quizzes</CardTitle>
              <Trophy className="h-4 w-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-800">{userStats?.total_quizzes || 0}</div>
            </CardContent>
          </Card>

          <Card className="bg-white shadow-md hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Quiz Average</CardTitle>
              <Target className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-800">{userStats?.average_score || 0}%</div>
            </CardContent>
          </Card>

          <Card className="bg-white shadow-md hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Flashcard Sessions</CardTitle>
              <BookOpen className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-800">{flashcardStats?.total_sessions || 0}</div>
            </CardContent>
          </Card>

          <Card className="bg-white shadow-md hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Card Accuracy</CardTitle>
              <Brain className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-800">{flashcardStats?.average_accuracy || 0}%</div>
            </CardContent>
          </Card>
        </div>

        {/* Tabs for Quizzes and Flashcards */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-8">
          <TabsList className="grid w-full grid-cols-2 mb-8">
            <TabsTrigger value="quizzes" className="text-lg">Practice Quizzes</TabsTrigger>
            <TabsTrigger value="flashcards" className="text-lg">Medical Terminology</TabsTrigger>
          </TabsList>

          <TabsContent value="quizzes">
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
          </TabsContent>

          <TabsContent value="flashcards">
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">Medical Terminology Flashcards</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {flashcardSets.map((set) => (
                  <Card key={set.id} className="bg-white shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className={`w-4 h-4 rounded-full`} style={{ backgroundColor: set.color }}></div>
                        <Badge variant="secondary">{set.card_count} cards</Badge>
                      </div>
                      <CardTitle className="text-lg font-semibold text-gray-800">{set.name}</CardTitle>
                      <CardDescription className="text-gray-600">{set.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <Button 
                        onClick={() => startFlashcardStudy(set.id)} 
                        className="w-full bg-green-600 hover:bg-green-700 text-white"
                        disabled={set.card_count === 0}
                      >
                        Study Flashcards
                        <BookOpen className="ml-2 h-4 w-4" />
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );

  const renderFlashcards = () => {
    const currentCard = flashcards[currentCardIndex];
    const progress = ((currentCardIndex + 1) / flashcards.length) * 100;
    const knownCount = knownCards.size;

    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50 py-8">
        <div className="container mx-auto px-4 max-w-4xl">
          {/* Flashcard Header */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h1 className="text-2xl font-bold text-gray-800">{currentFlashcardSet.name}</h1>
                <p className="text-gray-600">Card {currentCardIndex + 1} of {flashcards.length}</p>
              </div>
              <div className="text-right">
                <Badge variant="outline" className="text-lg px-4 py-2 mb-2">
                  {Math.round(progress)}% Complete
                </Badge>
                <div className="text-sm text-gray-600">
                  Known: {knownCount} | Review: {currentCardIndex + 1 - knownCount}
                </div>
              </div>
            </div>
            <Progress value={progress} className="h-2" />
          </div>

          {/* Flashcard */}
          <div className="relative mb-6">
            <Card className={`bg-white shadow-lg min-h-96 transition-all duration-500 cursor-pointer ${showDefinition ? 'flashcard-flipped' : ''}`} onClick={flipCard}>
              <CardContent className="flex flex-col items-center justify-center h-96 p-8">
                {!showDefinition ? (
                  // Front of card - Term
                  <div className="text-center">
                    <div className="flex items-center justify-center mb-4">
                      <h2 className="text-4xl font-bold text-gray-800 mr-4">{currentCard.term}</h2>
                      {currentCard.pronunciation && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            speakText(currentCard.term);
                          }}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          <Volume2 className="h-5 w-5" />
                        </Button>
                      )}
                    </div>
                    {currentCard.pronunciation && (
                      <p className="text-lg text-gray-600 mb-4">/{currentCard.pronunciation}/</p>
                    )}
                    {currentCard.word_type && (
                      <Badge variant="secondary" className="mb-6">
                        {currentCard.word_type}
                      </Badge>
                    )}
                    <div className="flex items-center justify-center text-gray-500 mt-8">
                      <Eye className="h-5 w-5 mr-2" />
                      <span>Click to see definition</span>
                    </div>
                  </div>
                ) : (
                  // Back of card - Definition
                  <div className="text-center">
                    <h3 className="text-2xl font-semibold text-gray-800 mb-6">{currentCard.definition}</h3>
                    {currentCard.examples && currentCard.examples.length > 0 && (
                      <div className="mb-6">
                        <h4 className="text-lg font-medium text-gray-700 mb-2">Examples:</h4>
                        <ul className="text-gray-600">
                          {currentCard.examples.map((example, index) => (
                            <li key={index} className="mb-1 italic">"{example}"</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {currentCard.category && (
                      <Badge variant="outline" className="mb-6">
                        {currentCard.category}
                      </Badge>
                    )}
                    <div className="flex items-center justify-center text-gray-500">
                      <EyeOff className="h-5 w-5 mr-2" />
                      <span>Click to see term</span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Navigation and Actions */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex items-center justify-between mb-6">
              <Button 
                variant="outline" 
                onClick={previousCard}
                disabled={currentCardIndex === 0}
              >
                Previous
              </Button>

              <div className="flex space-x-2">
                {flashcards.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      setCurrentCardIndex(index);
                      setShowDefinition(false);
                    }}
                    className={`w-8 h-8 rounded-full text-sm font-medium transition-colors ${
                      index === currentCardIndex
                        ? 'bg-green-500 text-white'
                        : knownCards.has(flashcards[index].id)
                        ? 'bg-blue-500 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    {index + 1}
                  </button>
                ))}
              </div>

              <Button 
                variant="outline" 
                onClick={nextCard}
                disabled={currentCardIndex === flashcards.length - 1}
              >
                Skip
              </Button>
            </div>

            {showDefinition && (
              <div className="flex justify-center space-x-4">
                <Button 
                  onClick={() => markCard(false)}
                  variant="outline"
                  className="border-red-200 text-red-600 hover:bg-red-50"
                >
                  <XCircle className="mr-2 h-4 w-4" />
                  Need Review
                </Button>
                <Button 
                  onClick={() => markCard(true)}
                  className="bg-green-600 hover:bg-green-700 text-white"
                >
                  <CheckCircle className="mr-2 h-4 w-4" />
                  I Know This
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderFlashcardResults = () => {
    const totalStudied = currentCardIndex + 1;
    const knownCount = knownCards.size;
    const accuracy = totalStudied > 0 ? Math.round((knownCount / totalStudied) * 100) : 0;
    
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-8">
        <div className="container mx-auto px-4 max-w-4xl">
          <Card className="bg-white shadow-lg mb-8">
            <CardHeader className="text-center">
              <div className="text-6xl font-bold text-green-600 mb-2">
                {accuracy}%
              </div>
              <CardTitle className="text-2xl text-gray-800 mb-2">
                Study Session Complete!
              </CardTitle>
              <CardDescription className="text-lg">
                You knew {knownCount} out of {totalStudied} cards
              </CardDescription>
              <div className="mt-4">
                <Progress value={accuracy} className="h-3" />
              </div>
            </CardHeader>
          </Card>

          <div className="flex justify-center space-x-4">
            <Button 
              onClick={() => startFlashcardStudy(currentFlashcardSet.id)}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Study Again
            </Button>
            <Button 
              variant="outline" 
              onClick={resetToMainMenu}
            >
              Back to Dashboard
            </Button>
          </div>
        </div>
      </div>
    );
  };

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
                  const letter = String.fromCharCode(65 + index);
                  
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
              onClick={resetToMainMenu}
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
  } else if (currentView === 'flashcards') {
    return renderFlashcards();
  } else if (currentView === 'flashcard-results') {
    return renderFlashcardResults();
  } else {
    return renderDashboard();
  }
}

export default App;