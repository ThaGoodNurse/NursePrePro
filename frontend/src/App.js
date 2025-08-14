import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Progress } from './components/ui/progress';
import { Separator } from './components/ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { BookOpen, Brain, Trophy, Target, ArrowRight, CheckCircle, XCircle, RotateCcw, RefreshCw, Eye, EyeOff, Volume2, Clock, Timer, Zap, Star, TrendingUp, Calendar } from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Spaced Repetition Quality Scale
const QUALITY_SCALE = [
  { value: 0, label: "Complete blackout", color: "bg-red-600" },
  { value: 1, label: "Incorrect with difficulty", color: "bg-red-400" },
  { value: 2, label: "Incorrect but familiar", color: "bg-orange-400" },
  { value: 3, label: "Correct with difficulty", color: "bg-yellow-400" },
  { value: 4, label: "Correct with hesitation", color: "bg-lime-400" },
  { value: 5, label: "Perfect recall", color: "bg-green-500" }
];

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
  const [quizTimer, setQuizTimer] = useState(null);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [questionStartTime, setQuestionStartTime] = useState(null);
  
  // Advanced Quiz Settings
  const [quizSettings, setQuizSettings] = useState({
    quizType: 'practice',
    timeLimit: null,
    questionCount: 10,
    difficultyLevel: 'adaptive',
    nclexCategories: []
  });
  
  // Flashcard state
  const [flashcardSets, setFlashcardSets] = useState([]);
  const [currentFlashcardSet, setCurrentFlashcardSet] = useState(null);
  const [flashcards, setFlashcards] = useState([]);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [showDefinition, setShowDefinition] = useState(false);
  const [studySession, setStudySession] = useState(null);
  const [knownCards, setKnownCards] = useState(new Set());
  const [cardStartTime, setCardStartTime] = useState(null);
  const [spacedRepetitionMode, setSpacedRepetitionMode] = useState(true);
  
  // Stats state
  const [userStats, setUserStats] = useState(null);
  const [flashcardStats, setFlashcardStats] = useState(null);
  const [competencyData, setCompetencyData] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchStudyAreas();
    fetchFlashcardSets();
    fetchUserStats();
    fetchFlashcardStats();
  }, []);

  // Timer effect for quizzes
  useEffect(() => {
    if (quizTimer && timeRemaining > 0) {
      const timer = setTimeout(() => {
        setTimeRemaining(prev => prev - 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (timeRemaining === 0 && quizTimer) {
      handleTimeUp();
    }
  }, [timeRemaining, quizTimer]);

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

  const handleTimeUp = () => {
    if (currentView === 'quiz') {
      submitQuiz(true); // Auto-submit when time is up
    }
  };

  // Advanced Quiz functions
  const startAdvancedQuiz = async (settings) => {
    setLoading(true);
    try {
      const response = await axios.post(`${BACKEND_URL}/api/quiz/start-advanced`, {
        area_id: settings.areaId,
        quiz_type: settings.quizType,
        question_count: settings.questionCount,
        time_limit: settings.timeLimit,
        difficulty_level: settings.difficultyLevel,
        nclex_categories: settings.nclexCategories
      });
      
      setCurrentQuiz({
        id: response.data.quiz_id,
        areaId: settings.areaId,
        totalQuestions: response.data.total_questions,
        areaName: studyAreas.find(area => area.id === settings.areaId)?.name || 'NCLEX Simulation',
        quizType: response.data.quiz_type,
        timeLimit: response.data.time_limit,
        adaptiveMode: response.data.adaptive_mode
      });
      
      setQuizQuestions(response.data.questions);
      setCurrentQuestionIndex(0);
      setSelectedAnswers({});
      setQuizResults(null);
      
      // Set up timer if there's a time limit
      if (response.data.time_limit) {
        setTimeRemaining(response.data.time_limit);
        setQuizTimer(true);
      }
      
      setQuestionStartTime(Date.now());
      setCurrentView('quiz');
    } catch (error) {
      console.error('Error starting advanced quiz:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectAnswer = (questionId, optionId, isMultipleResponse = false) => {
    setSelectedAnswers(prev => {
      if (isMultipleResponse) {
        const currentAnswers = prev[questionId]?.selected_option_ids || [];
        const newAnswers = currentAnswers.includes(optionId)
          ? currentAnswers.filter(id => id !== optionId)
          : [...currentAnswers, optionId];
        
        return {
          ...prev,
          [questionId]: {
            ...prev[questionId],
            selected_option_ids: newAnswers,
            time_spent: Date.now() - questionStartTime
          }
        };
      } else {
        return {
          ...prev,
          [questionId]: {
            selected_option_id: optionId,
            time_spent: Date.now() - questionStartTime
          }
        };
      }
    });
  };

  const nextQuestion = () => {
    if (currentQuestionIndex < quizQuestions.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
      setQuestionStartTime(Date.now());
    }
  };

  const previousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
      setQuestionStartTime(Date.now());
    }
  };

  const submitQuiz = async (autoSubmit = false) => {
    setLoading(true);
    try {
      const answers = Object.entries(selectedAnswers).map(([questionId, answerData]) => ({
        question_id: questionId,
        ...answerData
      }));

      const totalTimeSpent = currentQuiz.timeLimit ? currentQuiz.timeLimit - timeRemaining : null;

      const response = await axios.post(`${BACKEND_URL}/api/quiz/${currentQuiz.id}/submit-advanced`, 
        answers, 
        { params: { time_taken: totalTimeSpent } }
      );
      
      setQuizResults(response.data);
      setQuizTimer(false);
      setCurrentView('results');
      fetchUserStats();
    } catch (error) {
      console.error('Error submitting quiz:', error);
    } finally {
      setLoading(false);
    }
  };

  // Spaced Repetition Flashcard functions
  const startFlashcardStudy = async (setId, useSpacedRepetition = true) => {
    setLoading(true);
    try {
      const endpoint = useSpacedRepetition ? 'study-spaced' : 'study';
      const params = useSpacedRepetition ? { set_id: setId, max_cards: 20 } : { set_id: setId, shuffle: true };
      
      const response = await axios.post(`${BACKEND_URL}/api/flashcards/${endpoint}`, null, { params });
      
      setCurrentFlashcardSet({
        id: setId,
        name: flashcardSets.find(set => set.id === setId)?.name || 'Unknown',
        totalCards: response.data.total_cards,
        sessionType: response.data.session_type || 'normal',
        dueCardsCount: response.data.due_cards_count || 0
      });
      
      setFlashcards(response.data.flashcards);
      setStudySession({ id: response.data.session_id });
      setCurrentCardIndex(0);
      setShowDefinition(false);
      setKnownCards(new Set());
      setCardStartTime(Date.now());
      setSpacedRepetitionMode(useSpacedRepetition);
      setCurrentView('flashcards');
    } catch (error) {
      console.error('Error starting flashcard study:', error);
    } finally {
      setLoading(false);
    }
  };

  const flipCard = () => {
    setShowDefinition(!showDefinition);
    if (!showDefinition) {
      setCardStartTime(Date.now()); // Start timing when definition is shown
    }
  };

  const markCardSpacedRepetition = async (quality) => {
    if (!studySession || !flashcards[currentCardIndex]) return;
    
    const responseTime = cardStartTime ? (Date.now() - cardStartTime) / 1000 : 5;
    
    try {
      const endpoint = spacedRepetitionMode ? 'review-spaced' : 'review';
      await axios.post(`${BACKEND_URL}/api/flashcards/study/${studySession.id}/${endpoint}`, {
        card_id: flashcards[currentCardIndex].id,
        quality: quality,
        response_time: responseTime
      });
      
      if (quality >= 3) {
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
      setCardStartTime(Date.now());
    } else {
      setCurrentView('flashcard-results');
      fetchFlashcardStats();
    }
  };

  const previousCard = () => {
    if (currentCardIndex > 0) {
      setCurrentCardIndex(prev => prev - 1);
      setShowDefinition(false);
      setCardStartTime(Date.now());
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
    setQuizTimer(false);
    setTimeRemaining(0);
    setCurrentFlashcardSet(null);
    setFlashcards([]);
    setCurrentCardIndex(0);
    setShowDefinition(false);
    setStudySession(null);
    setKnownCards(new Set());
    setSpacedRepetitionMode(true);
  };

  const speakText = (text) => {
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.8;
      utterance.pitch = 1;
      speechSynthesis.speak(utterance);
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const QuizSettingsDialog = ({ areaId, areaName, onStart }) => {
    const [settings, setSettings] = useState({
      quizType: 'practice',
      timeLimit: null,
      questionCount: 10,
      difficultyLevel: 'adaptive'
    });

    const handleStart = () => {
      onStart({ ...settings, areaId });
    };

    return (
      <Dialog>
        <DialogTrigger asChild>
          <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white">
            <Zap className="mr-2 h-4 w-4" />
            Advanced Quiz
          </Button>
        </DialogTrigger>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Quiz Settings - {areaName}</DialogTitle>
            <DialogDescription>
              Configure your quiz for optimal learning
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Quiz Type</label>
              <Select value={settings.quizType} onValueChange={(value) => setSettings(prev => ({ ...prev, quizType: value }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="practice">Practice Quiz</SelectItem>
                  <SelectItem value="adaptive">Adaptive Difficulty</SelectItem>
                  <SelectItem value="timed">Timed Challenge</SelectItem>
                  <SelectItem value="nclex_simulation">NCLEX Simulation</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium">Number of Questions</label>
              <Select value={settings.questionCount.toString()} onValueChange={(value) => setSettings(prev => ({ ...prev, questionCount: parseInt(value) }))}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5">5 Questions</SelectItem>
                  <SelectItem value="10">10 Questions</SelectItem>
                  <SelectItem value="15">15 Questions</SelectItem>
                  <SelectItem value="25">25 Questions</SelectItem>
                  <SelectItem value="50">50 Questions</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {(settings.quizType === 'timed' || settings.quizType === 'nclex_simulation') && (
              <div>
                <label className="text-sm font-medium">Time Limit (minutes)</label>
                <Select value={settings.timeLimit?.toString() || ''} onValueChange={(value) => setSettings(prev => ({ ...prev, timeLimit: value ? parseInt(value) : null }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select time limit" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="15">15 minutes</SelectItem>
                    <SelectItem value="30">30 minutes</SelectItem>
                    <SelectItem value="45">45 minutes</SelectItem>
                    <SelectItem value="60">60 minutes</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}

            <Button onClick={handleStart} className="w-full">
              Start Quiz
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    );
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
            <div>
              <h1 className="text-4xl font-bold text-gray-800">NursePrep Pro™</h1>
              <p className="text-xs text-gray-500 mt-1">© 2025 NursePrep Pro. All rights reserved.</p>
            </div>
          </div>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Master NCLEX-RN with adaptive quizzes, spaced repetition flashcards, and comprehensive analytics
          </p>
          <div className="mt-4 text-xs text-gray-500">
            <p>NCLEX-RN® is a registered trademark of NCSBN. Not affiliated with NCSBN.</p>
            <p>Educational use only - Not medical advice</p>
          </div>
        </div>

        {/* Enhanced Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <Card className="bg-white shadow-md hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Total Quizzes</CardTitle>
              <Trophy className="h-4 w-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-800">{userStats?.total_quizzes || 0}</div>
              <p className="text-xs text-muted-foreground">
                +{userStats?.recent_attempts?.length || 0} this week
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white shadow-md hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Quiz Average</CardTitle>
              <Target className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-800">{userStats?.average_score || 0}%</div>
              <Progress value={userStats?.average_score || 0} className="h-1 mt-2" />
            </CardContent>
          </Card>

          <Card className="bg-white shadow-md hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Cards Studied</CardTitle>
              <BookOpen className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-800">{flashcardStats?.total_cards_studied || 0}</div>
              <p className="text-xs text-muted-foreground">
                {flashcardStats?.total_sessions || 0} sessions
              </p>
            </CardContent>
          </Card>

          <Card className="bg-white shadow-md hover:shadow-lg transition-shadow">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">Card Mastery</CardTitle>
              <Star className="h-4 w-4 text-yellow-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-800">{flashcardStats?.average_accuracy || 0}%</div>
              <Progress value={flashcardStats?.average_accuracy || 0} className="h-1 mt-2" />
            </CardContent>
          </Card>
        </div>

        {/* Tabs for Quizzes and Flashcards */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="mb-8">
          <TabsList className="grid w-full grid-cols-2 mb-8">
            <TabsTrigger value="quizzes" className="text-lg">
              <Brain className="mr-2 h-4 w-4" />
              NCLEX Practice
            </TabsTrigger>
            <TabsTrigger value="flashcards" className="text-lg">
              <BookOpen className="mr-2 h-4 w-4" />
              Medical Terminology
            </TabsTrigger>
          </TabsList>

          <TabsContent value="quizzes">
            <div className="mb-8">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-800">NCLEX-RN Study Areas</h2>
                <Badge variant="secondary" className="text-sm">
                  Adaptive Difficulty • Timed Quizzes • Performance Analytics
                </Badge>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {studyAreas.map((area) => (
                  <Card key={area.id} className="bg-white shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className={`w-4 h-4 rounded-full`} style={{ backgroundColor: area.color }}></div>
                        <div className="flex space-x-2">
                          <Badge variant="secondary">{area.question_count} questions</Badge>
                          {area.question_count > 0 && (
                            <Badge variant="outline" className="text-xs">
                              <TrendingUp className="w-3 h-3 mr-1" />
                              NCLEX
                            </Badge>
                          )}
                        </div>
                      </div>
                      <CardTitle className="text-lg font-semibold text-gray-800">{area.name}</CardTitle>
                      <CardDescription className="text-gray-600">{area.description}</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <QuizSettingsDialog 
                        areaId={area.id} 
                        areaName={area.name}
                        onStart={startAdvancedQuiz}
                      />
                      <Button 
                        variant="outline"
                        onClick={() => startAdvancedQuiz({ 
                          areaId: area.id, 
                          quizType: 'practice', 
                          questionCount: 5,
                          difficultyLevel: 'medium' 
                        })} 
                        className="w-full"
                        disabled={area.question_count === 0}
                      >
                        Quick Practice
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
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-800">Spaced Repetition Flashcards</h2>
                <Badge variant="secondary" className="text-sm">
                  <Calendar className="w-3 h-3 mr-1" />
                  SM-2 Algorithm • Due Cards Priority
                </Badge>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {flashcardSets.map((set) => (
                  <Card key={set.id} className="bg-white shadow-md hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div className={`w-4 h-4 rounded-full`} style={{ backgroundColor: set.color }}></div>
                        <div className="flex space-x-2">
                          <Badge variant="secondary">{set.card_count} cards</Badge>
                          {set.spaced_repetition_enabled && (
                            <Badge variant="outline" className="text-xs text-green-600">
                              <RefreshCw className="w-3 h-3 mr-1" />
                              SRS
                            </Badge>
                          )}
                        </div>
                      </div>
                      <CardTitle className="text-lg font-semibold text-gray-800">{set.name}</CardTitle>
                      <CardDescription className="text-gray-600">{set.description}</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-2">
                      <Button 
                        onClick={() => startFlashcardStudy(set.id, true)} 
                        className="w-full bg-green-600 hover:bg-green-700 text-white"
                        disabled={set.card_count === 0}
                      >
                        <Brain className="mr-2 h-4 w-4" />
                        Smart Review
                      </Button>
                      <Button 
                        variant="outline"
                        onClick={() => startFlashcardStudy(set.id, false)} 
                        className="w-full"
                        disabled={set.card_count === 0}
                      >
                        <BookOpen className="mr-2 h-4 w-4" />
                        Study All Cards
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

  const renderQuiz = () => {
    const currentQuestion = quizQuestions[currentQuestionIndex];
    const progress = ((currentQuestionIndex + 1) / quizQuestions.length) * 100;
    const allQuestionsAnswered = quizQuestions.every(q => selectedAnswers[q.id]);
    const isMultipleResponse = currentQuestion?.question_type === 'multiple_response';

    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-8">
        <div className="container mx-auto px-4 max-w-4xl">
          {/* Enhanced Quiz Header */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <h1 className="text-2xl font-bold text-gray-800">{currentQuiz.areaName}</h1>
                  <Badge variant="outline">{currentQuiz.quizType.replace('_', ' ')}</Badge>
                  {currentQuiz.adaptiveMode && (
                    <Badge variant="secondary" className="bg-purple-100 text-purple-700">
                      <Zap className="w-3 h-3 mr-1" />
                      Adaptive
                    </Badge>
                  )}
                </div>
                <p className="text-gray-600">Question {currentQuestionIndex + 1} of {quizQuestions.length}</p>
              </div>
              <div className="text-right">
                {quizTimer && (
                  <div className="flex items-center space-x-2 mb-2">
                    <Timer className="h-4 w-4 text-red-500" />
                    <span className={`text-lg font-mono ${timeRemaining < 300 ? 'text-red-500' : 'text-gray-700'}`}>
                      {formatTime(timeRemaining)}
                    </span>
                  </div>
                )}
                <Badge variant="outline" className="text-lg px-4 py-2">
                  {Math.round(progress)}% Complete
                </Badge>
              </div>
            </div>
            <Progress value={progress} className="h-2" />
            {quizTimer && timeRemaining < 300 && (
              <div className="mt-2 text-sm text-red-600 font-medium">
                ⚠️ Less than 5 minutes remaining!
              </div>
            )}
          </div>

          {/* Enhanced Question Card */}
          <Card className="bg-white shadow-lg mb-6">
            <CardHeader>
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center space-x-2">
                  <Badge variant="secondary">{currentQuestion.difficulty}</Badge>
                  <Badge variant="outline" className="text-xs">
                    {currentQuestion.cognitive_level}
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    {currentQuestion.nclex_category?.replace('_', ' ')}
                  </Badge>
                </div>
                <div className="flex items-center space-x-2 text-sm text-gray-500">
                  {currentQuestion.time_limit && (
                    <span className="flex items-center">
                      <Clock className="w-3 h-3 mr-1" />
                      {currentQuestion.time_limit}s
                    </span>
                  )}
                  <span>{selectedAnswers[currentQuestion.id] ? 'Answered' : 'Not answered'}</span>
                  {currentQuestion.priority_level === 'critical' && (
                    <Badge variant="destructive" className="text-xs">CRITICAL</Badge>
                  )}
                </div>
              </div>
              <CardTitle className="text-xl leading-relaxed text-gray-800 mt-4">
                {currentQuestion.question_text}
              </CardTitle>
              {isMultipleResponse && (
                <p className="text-sm text-blue-600 font-medium">
                  Select all that apply:
                </p>
              )}
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {currentQuestion.options.map((option, index) => {
                  const isSelected = isMultipleResponse 
                    ? selectedAnswers[currentQuestion.id]?.selected_option_ids?.includes(option.id)
                    : selectedAnswers[currentQuestion.id]?.selected_option_id === option.id;
                  const letter = String.fromCharCode(65 + index);
                  
                  return (
                    <button
                      key={option.id}
                      onClick={() => selectAnswer(currentQuestion.id, option.id, isMultipleResponse)}
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
                          {isMultipleResponse ? (isSelected ? '✓' : '☐') : letter}
                        </span>
                        <span className="text-base">{option.text}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Enhanced Navigation */}
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
                  onClick={() => {
                    setCurrentQuestionIndex(index);
                    setQuestionStartTime(Date.now());
                  }}
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
                onClick={() => submitQuiz(false)}
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

  const renderFlashcards = () => {
    const currentCard = flashcards[currentCardIndex];
    const progress = ((currentCardIndex + 1) / flashcards.length) * 100;
    const knownCount = knownCards.size;

    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 via-white to-blue-50 py-8">
        <div className="container mx-auto px-4 max-w-4xl">
          {/* Enhanced Flashcard Header */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="flex items-center space-x-2 mb-2">
                  <h1 className="text-2xl font-bold text-gray-800">{currentFlashcardSet.name}</h1>
                  {spacedRepetitionMode && (
                    <Badge variant="secondary" className="bg-green-100 text-green-700">
                      <RefreshCw className="w-3 h-3 mr-1" />
                      Smart Review
                    </Badge>
                  )}
                </div>
                <p className="text-gray-600">Card {currentCardIndex + 1} of {flashcards.length}</p>
                {currentFlashcardSet.dueCardsCount > 0 && (
                  <p className="text-sm text-orange-600">
                    <Calendar className="w-3 h-3 inline mr-1" />
                    {currentFlashcardSet.dueCardsCount} cards due for review
                  </p>
                )}
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

          {/* Enhanced Flashcard */}
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
                    <div className="flex items-center justify-center space-x-2 mb-6">
                      {currentCard.word_type && (
                        <Badge variant="secondary">{currentCard.word_type}</Badge>
                      )}
                      {currentCard.difficulty && (
                        <Badge variant="outline">{currentCard.difficulty}</Badge>
                      )}
                      {spacedRepetitionMode && currentCard.success_rate !== undefined && (
                        <Badge variant="outline" className="text-xs">
                          <Star className="w-3 h-3 mr-1" />
                          {Math.round(currentCard.success_rate * 100)}%
                        </Badge>
                      )}
                    </div>
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
                      <Badge variant="outline" className="mb-6">{currentCard.category}</Badge>
                    )}
                    {spacedRepetitionMode && currentCard.next_review && (
                      <div className="text-xs text-gray-500 mb-4">
                        Next review: {new Date(currentCard.next_review).toLocaleDateString()}
                      </div>
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

          {/* Enhanced Navigation and Actions */}
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
                      setCardStartTime(Date.now());
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
              <div className="space-y-4">
                {spacedRepetitionMode ? (
                  // Spaced Repetition Quality Scale
                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-3">How well did you remember this card?</p>
                    <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                      {QUALITY_SCALE.map((quality) => (
                        <Button
                          key={quality.value}
                          variant="outline"
                          size="sm"
                          onClick={() => markCardSpacedRepetition(quality.value)}
                          className={`flex flex-col h-auto p-2 text-xs hover:${quality.color} hover:text-white`}
                        >
                          <span className="font-bold">{quality.value}</span>
                          <span className="text-xs text-center leading-tight">{quality.label}</span>
                        </Button>
                      ))}
                    </div>
                  </div>
                ) : (
                  // Simple Known/Unknown
                  <div className="flex justify-center space-x-4">
                    <Button 
                      onClick={() => markCardSpacedRepetition(1)}
                      variant="outline"
                      className="border-red-200 text-red-600 hover:bg-red-50"
                    >
                      <XCircle className="mr-2 h-4 w-4" />
                      Need Review
                    </Button>
                    <Button 
                      onClick={() => markCardSpacedRepetition(4)}
                      className="bg-green-600 hover:bg-green-700 text-white"
                    >
                      <CheckCircle className="mr-2 h-4 w-4" />
                      I Know This
                    </Button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderResults = () => {
    const scoreColor = quizResults.score >= 75 ? 'text-green-600' : 'text-red-600';
    const scoreMessage = quizResults.score >= 75 ? 'Excellent! You passed!' : 'Keep studying - you can do it!';
    const isPassing = quizResults.score >= 75;
    
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 py-8">
        <div className="container mx-auto px-4 max-w-4xl">
          {/* Enhanced Results Header */}
          <Card className="bg-white shadow-lg mb-8">
            <CardHeader className="text-center">
              <div className={`text-6xl font-bold ${scoreColor} mb-2`}>
                {quizResults.score}%
              </div>
              <div className="flex items-center justify-center space-x-2 mb-2">
                {isPassing ? (
                  <CheckCircle className="h-6 w-6 text-green-500" />
                ) : (
                  <XCircle className="h-6 w-6 text-red-500" />
                )}
                <CardTitle className="text-2xl text-gray-800">
                  {scoreMessage}
                </CardTitle>
              </div>
              <CardDescription className="text-lg mb-4">
                You got {quizResults.correct_answers} out of {quizResults.total_questions} questions correct
              </CardDescription>
              
              {/* Quiz Type and Time Info */}
              <div className="flex items-center justify-center space-x-4 mb-4">
                <Badge variant="outline">{currentQuiz.quizType.replace('_', ' ')}</Badge>
                {quizResults.time_taken && (
                  <Badge variant="secondary">
                    <Timer className="w-3 h-3 mr-1" />
                    {formatTime(quizResults.time_taken)}
                  </Badge>
                )}
                {quizResults.quiz_type === 'adaptive' && (
                  <Badge variant="secondary" className="bg-purple-100 text-purple-700">
                    <Zap className="w-3 h-3 mr-1" />
                    Adaptive
                  </Badge>
                )}
              </div>
              
              <div className="mt-4">
                <Progress value={quizResults.score} className="h-3" />
              </div>
            </CardHeader>
          </Card>

          {/* NCLEX Category Performance */}
          {quizResults.nclex_performance && Object.keys(quizResults.nclex_performance).length > 0 && (
            <Card className="bg-white shadow-lg mb-6">
              <CardHeader>
                <CardTitle className="text-xl text-gray-800">NCLEX Category Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(quizResults.nclex_performance).map(([category, performance]) => (
                    <div key={category} className="p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium text-gray-800 capitalize">
                          {category.replace('_', ' ')}
                        </h4>
                        <span className={`font-bold ${performance.percentage >= 75 ? 'text-green-600' : 'text-red-600'}`}>
                          {Math.round(performance.percentage)}%
                        </span>
                      </div>
                      <div className="text-sm text-gray-600 mb-2">
                        {performance.correct}/{performance.total} correct
                      </div>
                      <Progress value={performance.percentage} className="h-2" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Enhanced Question Review */}
          <Card className="bg-white shadow-lg mb-6">
            <CardHeader>
              <CardTitle className="text-xl text-gray-800">Detailed Question Review</CardTitle>
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
                        <div className="flex items-center space-x-2 mb-2">
                          {result.is_correct ? (
                            <CheckCircle className="h-5 w-5 text-green-500" />
                          ) : (
                            <XCircle className="h-5 w-5 text-red-500" />
                          )}
                          <Badge variant="outline" className="text-xs">
                            {result.cognitive_level}
                          </Badge>
                          <Badge variant="outline" className="text-xs">
                            {result.nclex_category?.replace('_', ' ')}
                          </Badge>
                          {result.time_spent && (
                            <Badge variant="secondary" className="text-xs">
                              {Math.round(result.time_spent / 1000)}s
                            </Badge>
                          )}
                        </div>
                        
                        <h4 className="text-base font-medium text-gray-800 mb-2">
                          {result.question_text}
                        </h4>
                        
                        <div className="space-y-2">
                          <div className="flex items-start">
                            <span className="text-sm text-gray-600 mr-2">Your answer:</span>
                            <span className={`text-sm font-medium ${result.is_correct ? 'text-green-600' : 'text-red-600'}`}>
                              {result.user_answer?.selected_option_id ? 
                                result.user_answer.selected_option_text || 'Selected option' : 
                                result.user_answer?.answer_text || 'Not answered'}
                            </span>
                          </div>
                          
                          {!result.is_correct && (
                            <div className="flex items-start">
                              <span className="text-sm text-gray-600 mr-2">Correct answer:</span>
                              <span className="text-sm font-medium text-green-600">
                                {result.correct_answer?.correct_answer_text || 'Correct option'}
                              </span>
                            </div>
                          )}
                        </div>
                        
                        {(result.explanation || result.rationale) && (
                          <div className="mt-3 p-3 bg-blue-50 rounded-lg">
                            <h5 className="text-sm font-medium text-blue-800 mb-1">
                              {result.rationale ? 'Rationale:' : 'Explanation:'}
                            </h5>
                            <p className="text-sm text-blue-700">
                              {result.rationale || result.explanation}
                            </p>
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
              onClick={() => startAdvancedQuiz({ 
                areaId: currentQuiz.areaId, 
                quizType: currentQuiz.quizType,
                questionCount: currentQuiz.totalQuestions,
                difficultyLevel: 'adaptive'
              })}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              <RotateCcw className="mr-2 h-4 w-4" />
              Retake Quiz
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
                {spacedRepetitionMode ? 'Review Session Complete!' : 'Study Session Complete!'}
              </CardTitle>
              <CardDescription className="text-lg mb-4">
                You knew {knownCount} out of {totalStudied} cards
              </CardDescription>
              
              {spacedRepetitionMode && (
                <div className="flex items-center justify-center space-x-4 mb-4">
                  <Badge variant="secondary" className="bg-green-100 text-green-700">
                    <RefreshCw className="w-3 h-3 mr-1" />
                    Spaced Repetition
                  </Badge>
                  <Badge variant="outline">
                    <Star className="w-3 h-3 mr-1" />
                    Smart Algorithm
                  </Badge>
                </div>
              )}
              
              <div className="mt-4">
                <Progress value={accuracy} className="h-3" />
              </div>
            </CardHeader>
          </Card>

          <div className="flex justify-center space-x-4">
            <Button 
              onClick={() => startFlashcardStudy(currentFlashcardSet.id, spacedRepetitionMode)}
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