from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
from pymongo import MongoClient
import uuid
from datetime import datetime, timedelta
import uvicorn

# Stripe integration imports
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

# Environment variables
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "nurseprep_db")
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")

if not STRIPE_API_KEY:
    print("Warning: STRIPE_API_KEY not found in environment variables")

# MongoDB setup
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

app = FastAPI(title="NursePrep API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Models
class QuestionOption(BaseModel):
    id: str
    text: str
    is_correct: Optional[bool] = False

class Question(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_text: str
    question_type: str = "multiple_choice"  # multiple_choice, multiple_response, fill_blank, hot_spot, drag_drop
    options: List[QuestionOption]
    correct_answer_id: Optional[str] = None
    correct_answer_ids: Optional[List[str]] = None  # For multiple response
    correct_answer_text: Optional[str] = None  # For fill-in-blank
    explanation: Optional[str] = None
    rationale: Optional[str] = None
    difficulty: str = "medium"  # easy, medium, hard
    cognitive_level: str = "application"  # knowledge, comprehension, application, analysis, synthesis, evaluation
    nclex_category: str = "physiological_integrity"
    nclex_subcategory: Optional[str] = None
    client_needs: Optional[str] = None
    priority_level: str = "medium"  # low, medium, high, critical
    area_id: str
    time_limit: Optional[int] = 60  # seconds
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Flashcard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    term: str
    definition: str
    pronunciation: Optional[str] = None
    word_type: Optional[str] = None  # prefix, suffix, root, term
    category: Optional[str] = None
    examples: Optional[List[str]] = None
    set_id: str
    difficulty: str = "medium"
    # Spaced Repetition Fields
    easiness_factor: float = 2.5  # SM-2 algorithm
    interval: int = 1  # days until next review
    repetitions: int = 0
    last_reviewed: Optional[datetime] = None
    next_review: Optional[datetime] = None
    review_count: int = 0
    success_rate: float = 0.0
    average_response_time: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FlashcardSet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: str
    color: str = "#3B82F6"
    card_count: int = 0
    spaced_repetition_enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FlashcardStudySession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    set_id: str
    cards_studied: List[str]  # flashcard IDs
    correct_cards: List[str]  # flashcard IDs marked as known
    session_duration: Optional[int] = None  # in seconds
    session_type: str = "normal"  # normal, spaced_repetition, review
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class NCLEXQuizAttempt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    quiz_type: str = "practice"  # practice, adaptive, timed, nclex_simulation
    questions: List[str]  # question IDs
    answers: Dict[str, Any]  # question_id -> answer data
    score: int
    total_questions: int
    time_limit: Optional[int] = None  # total time in seconds
    time_taken: Optional[int] = None  # actual time taken
    difficulty_level: float = 0.0  # adaptive difficulty
    nclex_categories_performance: Dict[str, float] = {}
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

class UserCompetency(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"  # For future user system
    area_id: str
    nclex_category: str
    competency_level: float = 0.5  # 0.0 to 1.0
    question_count: int = 0
    correct_count: int = 0
    last_updated: datetime = Field(default_factory=datetime.utcnow)

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: Optional[str] = "default_user"
    user_email: Optional[str] = None
    package_id: str
    package_name: str
    amount: float
    currency: str = "usd"
    payment_status: str = "pending"  # pending, paid, failed, expired
    checkout_status: str = "initiated"  # initiated, complete, expired
    stripe_payment_intent_id: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None

class UserSubscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "default_user"
    user_email: Optional[str] = None
    subscription_type: str  # trial, monthly, annual, lifetime
    status: str = "active"  # active, inactive, expired, cancelled
    started_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    auto_renew: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class StudyArea(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    color: str = "#3B82F6"
    question_count: int = 0

class QuizAttempt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    area_id: str
    questions: List[str]  # question IDs
    answers: Dict[str, str]  # question_id -> selected_option_id
    score: int
    total_questions: int
    started_at: datetime
    completed_at: Optional[datetime] = None

class CreateStudyAreaRequest(BaseModel):
    name: str
    description: str
    color: str = "#3B82F6"

class CreateQuestionRequest(BaseModel):
    question_text: str
    options: List[str]
    correct_answer_index: int
    explanation: Optional[str] = None
    difficulty: str = "medium"
    area_id: str

class CreateFlashcardSetRequest(BaseModel):
    name: str
    description: str
    category: str
    color: str = "#3B82F6"
    spaced_repetition_enabled: bool = True

class CreateQuestionRequest(BaseModel):
    question_text: str
    question_type: str = "multiple_choice"
    options: List[str]
    correct_answer_index: Optional[int] = None
    correct_answer_indices: Optional[List[int]] = None  # For multiple response
    correct_answer_text: Optional[str] = None  # For fill-in-blank
    explanation: Optional[str] = None
    rationale: Optional[str] = None
    difficulty: str = "medium"
    cognitive_level: str = "application"
    nclex_category: str = "physiological_integrity"
    nclex_subcategory: Optional[str] = None
    client_needs: Optional[str] = None
    priority_level: str = "medium"
    area_id: str
    time_limit: Optional[int] = 60

class CreateFlashcardRequest(BaseModel):
    term: str
    definition: str
    pronunciation: Optional[str] = None
    word_type: Optional[str] = None
    category: Optional[str] = None
    examples: Optional[List[str]] = None
    set_id: str
    difficulty: str = "medium"

class FlashcardReviewRequest(BaseModel):
    card_id: str
    quality: int  # 0-5 for SM-2 algorithm (0=total blackout, 5=perfect response)
    response_time: float  # time taken to answer in seconds

class StartQuizRequest(BaseModel):
    area_id: Optional[str] = None
    quiz_type: str = "practice"  # practice, adaptive, timed, nclex_simulation
    question_count: int = 10
    time_limit: Optional[int] = None  # total time in minutes
    difficulty_level: Optional[str] = "adaptive"  # easy, medium, hard, adaptive
    nclex_categories: Optional[List[str]] = None

class QuizAnswerRequest(BaseModel):
    question_id: str
    selected_option_id: str

# Initialize collections
study_areas_collection = db.study_areas
questions_collection = db.questions
quiz_attempts_collection = db.quiz_attempts
nclex_quiz_attempts_collection = db.nclex_quiz_attempts
user_competency_collection = db.user_competency
flashcard_sets_collection = db.flashcard_sets
flashcards_collection = db.flashcards
flashcard_sessions_collection = db.flashcard_sessions

# Spaced Repetition Algorithm (SM-2)
def calculate_next_interval(quality, easiness_factor, interval, repetitions):
    """Calculate next review interval using SM-2 algorithm"""
    if quality >= 3:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * easiness_factor)
        repetitions += 1
    else:
        repetitions = 0
        interval = 1
    
    # Update easiness factor
    easiness_factor = easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if easiness_factor < 1.3:
        easiness_factor = 1.3
    
    return interval, easiness_factor, repetitions

# Adaptive Difficulty Algorithm
def calculate_user_competency(user_performance):
    """Calculate user competency level based on recent performance"""
    if not user_performance:
        return 0.5  # neutral starting point
    
    recent_scores = user_performance[-10:]  # last 10 attempts
    weights = [i + 1 for i in range(len(recent_scores))]  # more weight to recent
    
    weighted_sum = sum(score * weight for score, weight in zip(recent_scores, weights))
    weight_sum = sum(weights)
    
    return weighted_sum / weight_sum if weight_sum > 0 else 0.5

def select_adaptive_questions(area_id, competency_level, count=10):
    """Select questions based on user competency level"""
    # Define difficulty ranges based on competency
    if competency_level < 0.3:
        difficulty_weights = {"easy": 0.7, "medium": 0.3, "hard": 0.0}
    elif competency_level < 0.7:
        difficulty_weights = {"easy": 0.2, "medium": 0.6, "hard": 0.2}
    else:
        difficulty_weights = {"easy": 0.1, "medium": 0.3, "hard": 0.6}
    
    questions = []
    for difficulty, weight in difficulty_weights.items():
        question_count = max(1, int(count * weight))
        area_questions = list(questions_collection.find(
            {"area_id": area_id, "difficulty": difficulty},
            {"_id": 0}
        ).limit(question_count))
        questions.extend(area_questions)
    
    # Fill remaining slots if needed
    if len(questions) < count:
        additional = list(questions_collection.find(
            {"area_id": area_id},
            {"_id": 0}
        ).limit(count - len(questions)))
        questions.extend(additional)
    
    return questions[:count]

@app.get("/")
async def root():
    return {"message": "NursePrep API is running"}

# Study Areas endpoints
@app.get("/api/study-areas")
async def get_study_areas():
    """Get all study areas with question counts"""
    try:
        areas = list(study_areas_collection.find({}, {"_id": 0}))
        
        # Update question counts
        for area in areas:
            count = questions_collection.count_documents({"area_id": area["id"]})
            area["question_count"] = count
            
        return {"study_areas": areas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/study-areas")
async def create_study_area(request: CreateStudyAreaRequest):
    """Create a new study area"""
    try:
        area = StudyArea(
            name=request.name,
            description=request.description,
            color=request.color
        )
        
        study_areas_collection.insert_one(area.model_dump())
        return {"message": "Study area created", "area": area}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Questions endpoints
@app.get("/api/study-areas/{area_id}/questions")
async def get_questions_by_area(area_id: str, limit: int = 10):
    """Get questions for a specific study area"""
    try:
        questions = list(questions_collection.find(
            {"area_id": area_id}, 
            {"_id": 0}
        ).limit(limit))
        
        return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/questions")
async def create_question(request: CreateQuestionRequest):
    """Create a new question"""
    try:
        # Create options with IDs
        options = [
            QuestionOption(id=str(uuid.uuid4()), text=option_text)
            for option_text in request.options
        ]
        
        # Get correct answer ID
        if request.correct_answer_index >= len(options):
            raise HTTPException(status_code=400, detail="Invalid correct answer index")
        
        correct_answer_id = options[request.correct_answer_index].id
        
        question = Question(
            question_text=request.question_text,
            options=options,
            correct_answer_id=correct_answer_id,
            explanation=request.explanation,
            difficulty=request.difficulty,
            area_id=request.area_id
        )
        
        questions_collection.insert_one(question.model_dump())
        return {"message": "Question created", "question": question}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Flashcard Sets endpoints
@app.get("/api/flashcard-sets")
async def get_flashcard_sets():
    """Get all flashcard sets with card counts"""
    try:
        sets = list(flashcard_sets_collection.find({}, {"_id": 0}))
        
        # Update card counts
        for flashcard_set in sets:
            count = flashcards_collection.count_documents({"set_id": flashcard_set["id"]})
            flashcard_set["card_count"] = count
            
        return {"flashcard_sets": sets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/flashcard-sets")
async def create_flashcard_set(request: CreateFlashcardSetRequest):
    """Create a new flashcard set"""
    try:
        flashcard_set = FlashcardSet(
            name=request.name,
            description=request.description,
            category=request.category,
            color=request.color
        )
        
        flashcard_sets_collection.insert_one(flashcard_set.model_dump())
        return {"message": "Flashcard set created", "set": flashcard_set}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Flashcards endpoints
@app.get("/api/flashcard-sets/{set_id}/flashcards")
async def get_flashcards_by_set(set_id: str, limit: int = 50):
    """Get flashcards for a specific set"""
    try:
        flashcards = list(flashcards_collection.find(
            {"set_id": set_id}, 
            {"_id": 0}
        ).limit(limit))
        
        return {"flashcards": flashcards}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/flashcards")
async def create_flashcard(request: CreateFlashcardRequest):
    """Create a new flashcard"""
    try:
        flashcard = Flashcard(
            term=request.term,
            definition=request.definition,
            pronunciation=request.pronunciation,
            word_type=request.word_type,
            category=request.category,
            examples=request.examples or [],
            set_id=request.set_id,
            difficulty=request.difficulty
        )
        
        flashcards_collection.insert_one(flashcard.model_dump())
        return {"message": "Flashcard created", "flashcard": flashcard}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Flashcard Study endpoints with Spaced Repetition
@app.post("/api/flashcards/study-spaced")
async def start_spaced_repetition_study(set_id: str, max_cards: int = 20):
    """Start a spaced repetition study session"""
    try:
        current_time = datetime.utcnow()
        
        # Get cards due for review (next_review is None or <= current_time)
        due_cards = list(flashcards_collection.find({
            "set_id": set_id,
            "$or": [
                {"next_review": {"$lte": current_time}},
                {"next_review": None}
            ]
        }, {"_id": 0}).limit(max_cards))
        
        # If not enough due cards, add some new cards
        if len(due_cards) < max_cards:
            new_cards_needed = max_cards - len(due_cards)
            new_cards = list(flashcards_collection.find({
                "set_id": set_id,
                "review_count": 0
            }, {"_id": 0}).limit(new_cards_needed))
            due_cards.extend(new_cards)
        
        if not due_cards:
            # No cards to review, get any cards from the set
            due_cards = list(flashcards_collection.find(
                {"set_id": set_id}, 
                {"_id": 0}
            ).limit(max_cards))
        
        if not due_cards:
            raise HTTPException(status_code=404, detail="No flashcards found for this set")
        
        # Sort by priority (overdue cards first, then by difficulty)
        def card_priority(card):
            if card.get("next_review"):
                days_overdue = (current_time - card["next_review"]).days
                return (-days_overdue, card.get("success_rate", 0))
            return (0, card.get("success_rate", 0))
        
        due_cards.sort(key=card_priority, reverse=True)
        
        study_session = FlashcardStudySession(
            set_id=set_id,
            cards_studied=[],
            correct_cards=[],
            session_type="spaced_repetition"
        )
        
        flashcard_sessions_collection.insert_one(study_session.model_dump())
        
        return {
            "session_id": study_session.id,
            "flashcards": due_cards,
            "total_cards": len(due_cards),
            "session_type": "spaced_repetition",
            "due_cards_count": len([c for c in due_cards if c.get("next_review") and c["next_review"] <= current_time])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/flashcards/study/{session_id}/review-spaced")
async def review_flashcard_spaced(session_id: str, review: FlashcardReviewRequest):
    """Review a flashcard with spaced repetition algorithm"""
    try:
        # Get session
        session = flashcard_sessions_collection.find_one({"id": session_id}, {"_id": 0})
        if not session:
            raise HTTPException(status_code=404, detail="Study session not found")
        
        # Get flashcard
        card = flashcards_collection.find_one({"id": review.card_id}, {"_id": 0})
        if not card:
            raise HTTPException(status_code=404, detail="Flashcard not found")
        
        # Apply SM-2 algorithm
        current_ef = card.get("easiness_factor", 2.5)
        current_interval = card.get("interval", 1)
        current_reps = card.get("repetitions", 0)
        
        new_interval, new_ef, new_reps = calculate_next_interval(
            review.quality, current_ef, current_interval, current_reps
        )
        
        # Calculate next review date
        next_review_date = datetime.utcnow() + timedelta(days=new_interval)
        
        # Update success rate and response time
        old_success_rate = card.get("success_rate", 0.0)
        old_avg_time = card.get("average_response_time", 0.0)
        review_count = card.get("review_count", 0)
        
        # New success rate (weighted average)
        success = 1.0 if review.quality >= 3 else 0.0
        new_success_rate = (old_success_rate * review_count + success) / (review_count + 1)
        
        # New average response time
        new_avg_time = (old_avg_time * review_count + review.response_time) / (review_count + 1)
        
        # Update flashcard
        flashcards_collection.update_one(
            {"id": review.card_id},
            {
                "$set": {
                    "easiness_factor": new_ef,
                    "interval": new_interval,
                    "repetitions": new_reps,
                    "last_reviewed": datetime.utcnow(),
                    "next_review": next_review_date,
                    "review_count": review_count + 1,
                    "success_rate": new_success_rate,
                    "average_response_time": new_avg_time
                }
            }
        )
        
        # Update session
        update_data = {"$addToSet": {"cards_studied": review.card_id}}
        if review.quality >= 3:  # Consider it "known" if quality is 3 or higher
            update_data["$addToSet"]["correct_cards"] = review.card_id
        
        flashcard_sessions_collection.update_one(
            {"id": session_id},
            update_data
        )
        
        return {
            "message": "Review recorded",
            "quality": review.quality,
            "next_review_in_days": new_interval,
            "next_review_date": next_review_date.isoformat(),
            "easiness_factor": new_ef,
            "success_rate": new_success_rate,
            "is_mastered": new_success_rate > 0.8 and new_interval > 30
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/flashcards/{set_id}/due-count")
async def get_due_cards_count(set_id: str):
    """Get count of cards due for review"""
    try:
        current_time = datetime.utcnow()
        
        due_count = flashcards_collection.count_documents({
            "set_id": set_id,
            "$or": [
                {"next_review": {"$lte": current_time}},
                {"next_review": None}
            ]
        })
        
        total_count = flashcards_collection.count_documents({"set_id": set_id})
        new_cards = flashcards_collection.count_documents({
            "set_id": set_id,
            "review_count": 0
        })
        
        return {
            "due_count": due_count,
            "total_count": total_count,
            "new_cards": new_cards,
            "review_cards": due_count - new_cards
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/flashcards/stats")
async def get_flashcard_stats():
    """Get flashcard study statistics"""
    try:
        # Get completed sessions
        sessions = list(flashcard_sessions_collection.find({}, {"_id": 0}))
        
        if not sessions:
            return {
                "total_sessions": 0,
                "total_cards_studied": 0,
                "average_accuracy": 0,
                "recent_sessions": []
            }
        
        total_cards_studied = sum(len(session.get("cards_studied", [])) for session in sessions)
        total_correct = sum(len(session.get("correct_cards", [])) for session in sessions)
        
        average_accuracy = (total_correct / total_cards_studied * 100) if total_cards_studied > 0 else 0
        
        # Get set names for recent sessions
        for session in sessions[-5:]:
            flashcard_set = flashcard_sets_collection.find_one(
                {"id": session["set_id"]}, 
                {"_id": 0, "name": 1}
            )
            session["set_name"] = flashcard_set["name"] if flashcard_set else "Unknown"
        
        return {
            "total_sessions": len(sessions),
            "total_cards_studied": total_cards_studied,
            "average_accuracy": round(average_accuracy, 1),
            "recent_sessions": sessions[-5:]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Quiz endpoints with advanced features
@app.post("/api/quiz/start-advanced")
async def start_advanced_quiz(request: StartQuizRequest):
    """Start an advanced quiz with adaptive difficulty, timing, and NCLEX simulation"""
    try:
        questions = []
        
        if request.quiz_type == "adaptive":
            # Get user competency for adaptive difficulty
            competency = user_competency_collection.find_one(
                {"area_id": request.area_id}, {"_id": 0}
            )
            competency_level = competency["competency_level"] if competency else 0.5
            
            questions = select_adaptive_questions(
                request.area_id, competency_level, request.question_count
            )
        
        elif request.quiz_type == "nclex_simulation":
            # NCLEX-style adaptive test
            categories = request.nclex_categories or [
                "safe_effective_care", "health_promotion", 
                "psychosocial_integrity", "physiological_integrity"
            ]
            
            questions_per_category = max(1, request.question_count // len(categories))
            for category in categories:
                cat_questions = list(questions_collection.find(
                    {"nclex_category": category},
                    {"_id": 0}
                ).limit(questions_per_category))
                questions.extend(cat_questions)
        
        elif request.quiz_type == "timed":
            # Regular timed quiz
            questions = list(questions_collection.aggregate([
                {"$match": {"area_id": request.area_id}},
                {"$sample": {"size": request.question_count}}
            ]))
        
        else:
            # Standard practice quiz
            questions = list(questions_collection.aggregate([
                {"$match": {"area_id": request.area_id}},
                {"$sample": {"size": request.question_count}}
            ]))
        
        if not questions:
            raise HTTPException(status_code=404, detail="No questions found")
        
        # Calculate total time limit
        total_time_limit = None
        if request.time_limit:
            total_time_limit = request.time_limit * 60  # convert to seconds
        elif request.quiz_type in ["timed", "nclex_simulation"]:
            # Default time limits
            total_time_limit = sum(q.get("time_limit", 60) for q in questions)
        
        quiz_attempt = NCLEXQuizAttempt(
            quiz_type=request.quiz_type,
            questions=[q["id"] for q in questions],
            answers={},
            score=0,
            total_questions=len(questions),
            time_limit=total_time_limit,
            difficulty_level=0.5
        )
        
        nclex_quiz_attempts_collection.insert_one(quiz_attempt.model_dump())
        
        # Return questions without correct answers for security
        safe_questions = []
        for q in questions:
            safe_q = {
                "id": q["id"],
                "question_text": q["question_text"],
                "question_type": q.get("question_type", "multiple_choice"),
                "options": q["options"],
                "difficulty": q["difficulty"],
                "cognitive_level": q.get("cognitive_level", "application"),
                "nclex_category": q.get("nclex_category", "physiological_integrity"),
                "time_limit": q.get("time_limit", 60)
            }
            safe_questions.append(safe_q)
        
        return {
            "quiz_id": quiz_attempt.id,
            "questions": safe_questions,
            "total_questions": len(questions),
            "quiz_type": request.quiz_type,
            "time_limit": total_time_limit,
            "adaptive_mode": request.quiz_type == "adaptive"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quiz/{quiz_id}/submit-advanced")
async def submit_advanced_quiz(quiz_id: str, answers: List[Dict[str, Any]], time_taken: Optional[int] = None):
    """Submit advanced quiz with detailed analysis"""
    try:
        # Get quiz attempt
        quiz = nclex_quiz_attempts_collection.find_one({"id": quiz_id}, {"_id": 0})
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Get questions with correct answers
        question_ids = quiz["questions"]
        questions = list(questions_collection.find(
            {"id": {"$in": question_ids}}, 
            {"_id": 0}
        ))
        
        # Analyze answers
        correct_count = 0
        results = []
        nclex_performance = {}
        answer_dict = {ans["question_id"]: ans for ans in answers}
        
        for question in questions:
            user_answer = answer_dict.get(question["id"], {})
            is_correct = False
            
            # Check answer based on question type
            if question.get("question_type") == "multiple_choice":
                is_correct = user_answer.get("selected_option_id") == question["correct_answer_id"]
            elif question.get("question_type") == "multiple_response":
                selected_ids = set(user_answer.get("selected_option_ids", []))
                correct_ids = set(question.get("correct_answer_ids", []))
                is_correct = selected_ids == correct_ids
            elif question.get("question_type") == "fill_blank":
                user_text = user_answer.get("answer_text", "").strip().lower()
                correct_text = question.get("correct_answer_text", "").strip().lower()
                is_correct = user_text == correct_text
            
            if is_correct:
                correct_count += 1
            
            # Track NCLEX category performance
            category = question.get("nclex_category", "physiological_integrity")
            if category not in nclex_performance:
                nclex_performance[category] = {"correct": 0, "total": 0}
            nclex_performance[category]["total"] += 1
            if is_correct:
                nclex_performance[category]["correct"] += 1
            
            results.append({
                "question_id": question["id"],
                "question_text": question["question_text"],
                "question_type": question.get("question_type", "multiple_choice"),
                "is_correct": is_correct,
                "user_answer": user_answer,
                "correct_answer": {
                    "correct_answer_id": question.get("correct_answer_id"),
                    "correct_answer_ids": question.get("correct_answer_ids"),
                    "correct_answer_text": question.get("correct_answer_text")
                },
                "explanation": question.get("explanation"),
                "rationale": question.get("rationale"),
                "nclex_category": category,
                "cognitive_level": question.get("cognitive_level", "application"),
                "time_spent": user_answer.get("time_spent", 0)
            })
        
        # Calculate scores and performance metrics
        score_percentage = int((correct_count / len(questions)) * 100)
        
        # Calculate NCLEX category percentages
        for category in nclex_performance:
            perf = nclex_performance[category]
            perf["percentage"] = (perf["correct"] / perf["total"]) * 100 if perf["total"] > 0 else 0
        
        # Update quiz attempt
        nclex_quiz_attempts_collection.update_one(
            {"id": quiz_id},
            {
                "$set": {
                    "answers": {ans["question_id"]: ans for ans in answers},
                    "score": score_percentage,
                    "time_taken": time_taken,
                    "nclex_categories_performance": nclex_performance,
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        # Update user competency if it's a practice or adaptive quiz
        if quiz["quiz_type"] in ["practice", "adaptive"]:
            for question in questions:
                area_id = question["area_id"]
                category = question.get("nclex_category", "physiological_integrity")
                
                # Update or create competency record
                competency = user_competency_collection.find_one({
                    "area_id": area_id, 
                    "nclex_category": category
                })
                
                if competency:
                    new_correct = competency["correct_count"]
                    new_total = competency["question_count"]
                    
                    # Add current question result
                    is_correct = any(r["is_correct"] for r in results if r["question_id"] == question["id"])
                    if is_correct:
                        new_correct += 1
                    new_total += 1
                    
                    new_competency = new_correct / new_total if new_total > 0 else 0.5
                    
                    user_competency_collection.update_one(
                        {"area_id": area_id, "nclex_category": category},
                        {
                            "$set": {
                                "competency_level": new_competency,
                                "correct_count": new_correct,
                                "question_count": new_total,
                                "last_updated": datetime.utcnow()
                            }
                        }
                    )
                else:
                    # Create new competency record
                    is_correct = any(r["is_correct"] for r in results if r["question_id"] == question["id"])
                    user_competency_collection.insert_one({
                        "id": str(uuid.uuid4()),
                        "user_id": "default_user",
                        "area_id": area_id,
                        "nclex_category": category,
                        "competency_level": 1.0 if is_correct else 0.0,
                        "question_count": 1,
                        "correct_count": 1 if is_correct else 0,
                        "last_updated": datetime.utcnow()
                    })
        
        return {
            "score": score_percentage,
            "correct_answers": correct_count,
            "total_questions": len(questions),
            "time_taken": time_taken,
            "time_limit": quiz.get("time_limit"),
            "quiz_type": quiz["quiz_type"],
            "nclex_performance": nclex_performance,
            "results": results,
            "passed": score_percentage >= 75,  # NCLEX passing threshold
            "competency_updated": quiz["quiz_type"] in ["practice", "adaptive"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_user_stats():
    """Get user statistics"""
    try:
        # Get completed quiz attempts
        attempts = list(quiz_attempts_collection.find(
            {"completed_at": {"$ne": None}},
            {"_id": 0}
        ).sort("completed_at", -1).limit(10))
        
        if not attempts:
            return {
                "total_quizzes": 0,
                "average_score": 0,
                "recent_attempts": []
            }
        
        # Calculate average score
        total_score = sum(attempt["score"] for attempt in attempts)
        average_score = total_score / len(attempts)
        
        # Get study area names for recent attempts
        for attempt in attempts:
            area = study_areas_collection.find_one(
                {"id": attempt["area_id"]}, 
                {"_id": 0, "name": 1}
            )
            attempt["area_name"] = area["name"] if area else "Unknown"
        
        return {
            "total_quizzes": len(attempts),
            "average_score": round(average_score, 1),
            "recent_attempts": attempts[:5]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Initialize sample data
@app.on_event("startup")
async def startup_event():
    """Initialize sample data if collections are empty"""
    try:
        # Create sample study areas if none exist
        if study_areas_collection.count_documents({}) == 0:
            sample_areas = [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Fundamentals of Nursing",
                    "description": "Basic nursing concepts, patient care, and safety",
                    "color": "#3B82F6",
                    "question_count": 0
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Pharmacology",
                    "description": "Drug classifications, actions, and administration",
                    "color": "#10B981",
                    "question_count": 0
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Medical-Surgical Nursing",
                    "description": "Adult health conditions and nursing interventions",
                    "color": "#8B5CF6",
                    "question_count": 0
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Maternal-Child Health",
                    "description": "Pregnancy, childbirth, and pediatric care",
                    "color": "#EC4899",
                    "question_count": 0
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Critical Care",
                    "description": "Intensive care unit nursing and life-threatening conditions",
                    "color": "#DC2626",
                    "question_count": 0
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Leadership",
                    "description": "Nursing leadership, management, and professional development",
                    "color": "#7C3AED",
                    "question_count": 0
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Oncology/Hematology",
                    "description": "Cancer care and blood disorder management",
                    "color": "#DB2777",
                    "question_count": 0
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Burn Wound Care",
                    "description": "Assessment and treatment of burn injuries",
                    "color": "#EA580C",
                    "question_count": 0
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Hospice",
                    "description": "End-of-life care and palliative nursing",
                    "color": "#6B7280",
                    "question_count": 0
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Cardiac",
                    "description": "Cardiovascular nursing and heart conditions",
                    "color": "#B91C1C",
                    "question_count": 0
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Gastrointestinal",
                    "description": "Digestive system disorders and GI nursing care",
                    "color": "#059669",
                    "question_count": 0
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Renal",
                    "description": "Kidney function, dialysis, and renal nursing",
                    "color": "#0284C7",
                    "question_count": 0
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Stem Cell",
                    "description": "Stem cell therapy and bone marrow transplant nursing",
                    "color": "#7C2D12",
                    "question_count": 0
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Transplant",
                    "description": "Organ transplantation and post-transplant care",
                    "color": "#15803D",
                    "question_count": 0
                }
            ]
            study_areas_collection.insert_many(sample_areas)
            
            # Create sample questions for Fundamentals
            fundamentals_area = sample_areas[0]
            sample_questions = [
                {
                    "id": str(uuid.uuid4()),
                    "question_text": "What is the most important action when a patient falls?",
                    "options": [
                        {"id": str(uuid.uuid4()), "text": "Help the patient up immediately"},
                        {"id": str(uuid.uuid4()), "text": "Assess the patient for injuries"},
                        {"id": str(uuid.uuid4()), "text": "Call the family"},
                        {"id": str(uuid.uuid4()), "text": "Document the incident"}
                    ],
                    "correct_answer_id": "",
                    "explanation": "Always assess for injuries first before moving the patient to prevent further harm.",
                    "difficulty": "medium",
                    "area_id": fundamentals_area["id"]
                },
                {
                    "id": str(uuid.uuid4()),
                    "question_text": "Which vital sign should be taken first in an emergency situation?",
                    "options": [
                        {"id": str(uuid.uuid4()), "text": "Temperature"},
                        {"id": str(uuid.uuid4()), "text": "Blood pressure"},
                        {"id": str(uuid.uuid4()), "text": "Respiratory rate"},
                        {"id": str(uuid.uuid4()), "text": "Pulse"}
                    ],
                    "correct_answer_id": "",
                    "explanation": "Respiratory rate is the most critical vital sign in emergencies as it indicates breathing adequacy.",
                    "difficulty": "easy",
                    "area_id": fundamentals_area["id"]
                }
            ]
            
            # Set correct answer IDs
            sample_questions[0]["correct_answer_id"] = sample_questions[0]["options"][1]["id"]
            sample_questions[1]["correct_answer_id"] = sample_questions[1]["options"][2]["id"]
            
            questions_collection.insert_many(sample_questions)
        
        # Create sample flashcard sets if none exist
        if flashcard_sets_collection.count_documents({}) == 0:
            medical_terminology_set = {
                "id": str(uuid.uuid4()),
                "name": "Medical Terminology Essentials",
                "description": "Common medical prefixes, suffixes, and root words",
                "category": "Medical Terminology",
                "color": "#059669",
                "card_count": 0
            }
            
            anatomy_set = {
                "id": str(uuid.uuid4()),
                "name": "Anatomy & Physiology Terms",
                "description": "Essential anatomical and physiological terminology",
                "category": "Anatomy",
                "color": "#7C3AED",
                "card_count": 0
            }
            
            pharmacology_set = {
                "id": str(uuid.uuid4()),
                "name": "Pharmacology Terms",
                "description": "Drug classifications and pharmacological terminology",
                "category": "Pharmacology",
                "color": "#DC2626",
                "card_count": 0
            }
            
            flashcard_sets_collection.insert_many([medical_terminology_set, anatomy_set, pharmacology_set])
            
            # Create sample flashcards for Medical Terminology
            sample_flashcards = [
                {
                    "id": str(uuid.uuid4()),
                    "term": "Tachycardia",
                    "definition": "Rapid heart rate, typically over 100 beats per minute",
                    "pronunciation": "tak-ih-KAR-dee-ah",
                    "word_type": "term",
                    "category": "Cardiovascular",
                    "examples": ["The patient presented with tachycardia and shortness of breath"],
                    "set_id": medical_terminology_set["id"],
                    "difficulty": "medium",
                    "created_at": datetime.utcnow()
                },
                {
                    "id": str(uuid.uuid4()),
                    "term": "Bradycardia",
                    "definition": "Slow heart rate, typically under 60 beats per minute",
                    "pronunciation": "brad-ih-KAR-dee-ah",
                    "word_type": "term",
                    "category": "Cardiovascular",
                    "examples": ["The athlete showed bradycardia at rest"],
                    "set_id": medical_terminology_set["id"],
                    "difficulty": "medium",
                    "created_at": datetime.utcnow()
                },
                {
                    "id": str(uuid.uuid4()),
                    "term": "Hypertension",
                    "definition": "High blood pressure, typically 140/90 mmHg or higher",
                    "pronunciation": "hahy-per-TEN-shuhn",
                    "word_type": "term",
                    "category": "Cardiovascular",
                    "examples": ["Patient has a history of hypertension requiring medication"],
                    "set_id": medical_terminology_set["id"],
                    "difficulty": "easy",
                    "created_at": datetime.utcnow()
                },
                {
                    "id": str(uuid.uuid4()),
                    "term": "Hypotension",
                    "definition": "Low blood pressure, typically below 90/60 mmHg",
                    "pronunciation": "hahy-poh-TEN-shuhn",
                    "word_type": "term",
                    "category": "Cardiovascular",
                    "examples": ["Hypotension can cause dizziness and fainting"],
                    "set_id": medical_terminology_set["id"],
                    "difficulty": "easy",
                    "created_at": datetime.utcnow()
                },
                {
                    "id": str(uuid.uuid4()),
                    "term": "Dyspnea",
                    "definition": "Difficulty breathing or shortness of breath",
                    "pronunciation": "DISP-nee-ah",
                    "word_type": "term",
                    "category": "Respiratory",
                    "examples": ["The patient complained of dyspnea on exertion"],
                    "set_id": medical_terminology_set["id"],
                    "difficulty": "medium",
                    "created_at": datetime.utcnow()
                },
                {
                    "id": str(uuid.uuid4()),
                    "term": "Apnea",
                    "definition": "Temporary cessation of breathing",
                    "pronunciation": "AP-nee-ah",
                    "word_type": "term",
                    "category": "Respiratory",
                    "examples": ["Sleep apnea is a common breathing disorder"],
                    "set_id": medical_terminology_set["id"],
                    "difficulty": "medium",
                    "created_at": datetime.utcnow()
                },
                {
                    "id": str(uuid.uuid4()),
                    "term": "Cardi/o",
                    "definition": "Heart (combining form)",
                    "pronunciation": "KAR-dee-oh",
                    "word_type": "root",
                    "category": "Root Words",
                    "examples": ["Cardiology", "Cardiomyopathy", "Electrocardiogram"],
                    "set_id": medical_terminology_set["id"],
                    "difficulty": "easy",
                    "created_at": datetime.utcnow()
                },
                {
                    "id": str(uuid.uuid4()),
                    "term": "Pneum/o",
                    "definition": "Lung, air (combining form)",
                    "pronunciation": "NEW-moh",
                    "word_type": "root",
                    "category": "Root Words",
                    "examples": ["Pneumonia", "Pneumothorax", "Pneumology"],
                    "set_id": medical_terminology_set["id"],
                    "difficulty": "medium",
                    "created_at": datetime.utcnow()
                },
                {
                    "id": str(uuid.uuid4()),
                    "term": "-itis",
                    "definition": "Inflammation (suffix)",
                    "pronunciation": "EYE-tis",
                    "word_type": "suffix",
                    "category": "Suffixes",
                    "examples": ["Arthritis", "Bronchitis", "Gastritis"],
                    "set_id": medical_terminology_set["id"],
                    "difficulty": "easy",
                    "created_at": datetime.utcnow()
                },
                {
                    "id": str(uuid.uuid4()),
                    "term": "-ectomy",
                    "definition": "Surgical removal (suffix)",
                    "pronunciation": "EK-toh-mee",
                    "word_type": "suffix",
                    "category": "Suffixes",
                    "examples": ["Appendectomy", "Tonsillectomy", "Hysterectomy"],
                    "set_id": medical_terminology_set["id"],
                    "difficulty": "medium",
                    "created_at": datetime.utcnow()
                },
                {
                    "id": str(uuid.uuid4()),
                    "term": "Pre-",
                    "definition": "Before, in front of (prefix)",
                    "pronunciation": "pree",
                    "word_type": "prefix",
                    "category": "Prefixes",
                    "examples": ["Preoperative", "Prenatal", "Premedication"],
                    "set_id": medical_terminology_set["id"],
                    "difficulty": "easy",
                    "created_at": datetime.utcnow()
                },
                {
                    "id": str(uuid.uuid4()),
                    "term": "Post-",
                    "definition": "After, behind (prefix)",
                    "pronunciation": "pohst",
                    "word_type": "prefix",
                    "category": "Prefixes",
                    "examples": ["Postoperative", "Postpartum", "Postmortem"],
                    "set_id": medical_terminology_set["id"],
                    "difficulty": "easy",
                    "created_at": datetime.utcnow()
                }
            ]
            
            flashcards_collection.insert_many(sample_flashcards)
        
        print("Sample data initialized successfully")
    except Exception as e:
        print(f"Error initializing sample data: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)