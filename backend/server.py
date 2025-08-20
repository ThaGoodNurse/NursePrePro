from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import uuid
from datetime import datetime, timedelta
import uvicorn

# Stripe integration imports
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

# Environment variables
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")

if not STRIPE_API_KEY:
    print("Warning: STRIPE_API_KEY not found in environment variables")

app = FastAPI(title="NursePrep API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== IN-MEMORY DATA STORAGE =====
# This replaces the database - you can replace this with your own database later

# In-memory storage dictionaries
users_db = {}
study_areas_db = {}
questions_db = {}
flashcards_db = {}
user_progress_db = {}
flashcard_progress_db = {}
subscriptions_db = {}

# ===== PYDANTIC MODELS =====
class QuestionOption(BaseModel):
    id: str
    text: str
    is_correct: Optional[bool] = False

class Question(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_text: str
    question_type: str = "multiple_choice"
    options: List[QuestionOption]
    correct_answer_id: Optional[str] = None
    correct_answer_ids: Optional[List[str]] = None
    explanation: Optional[str] = None
    difficulty_level: int = 2
    nclex_category: Optional[str] = None

class StudyArea(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    color: str
    icon: str
    question_count: int = 0

class Flashcard(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    set_name: str
    term: str
    definition: str
    pronunciation: Optional[str] = None

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    subscription_tier: str = "free"
    subscription_status: str = "inactive"
    stripe_customer_id: Optional[str] = None
    trial_end_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)

class UserProgress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    study_area_id: str
    questions_attempted: int = 0
    questions_correct: int = 0
    quiz_sessions: List[Dict] = Field(default_factory=list)
    last_activity: datetime = Field(default_factory=datetime.now)

class FlashcardProgress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    flashcard_id: str
    ease_factor: float = 2.5
    repetitions: int = 0
    interval_days: int = 1
    next_review_date: datetime = Field(default_factory=datetime.now)
    status: str = "new"

class QuizSubmission(BaseModel):
    study_area_id: str
    answers: List[Dict[str, Any]]
    time_spent: Optional[int] = None

class FlashcardReview(BaseModel):
    flashcard_id: str
    difficulty: str  # "easy", "good", "hard"

# ===== STRIPE MODELS =====
class SubscriptionPlan(BaseModel):
    id: str
    name: str
    description: str
    price: float
    interval: str
    features: List[str]

class Subscription(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    stripe_subscription_id: Optional[str] = None
    status: str = "inactive"
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False

# ===== SAMPLE DATA INITIALIZATION =====
def initialize_sample_data():
    """Initialize the app with sample data"""
    
    # Study Areas
    study_areas = [
        {
            "id": "fundamentals",
            "name": "Fundamentals of Nursing",
            "description": "Basic nursing concepts, patient care, and safety",
            "color": "blue",
            "icon": "stethoscope",
            "question_count": 4
        },
        {
            "id": "pharmacology", 
            "name": "Pharmacology",
            "description": "Drug classifications, actions, and administration",
            "color": "green",
            "icon": "pill",
            "question_count": 0
        },
        {
            "id": "med-surg",
            "name": "Medical-Surgical Nursing", 
            "description": "Adult health conditions and nursing interventions",
            "color": "purple",
            "icon": "hospital",
            "question_count": 0
        }
    ]
    
    for area_data in study_areas:
        study_areas_db[area_data["id"]] = StudyArea(**area_data)
    
    # Sample Questions
    sample_questions = [
        {
            "id": "q1",
            "question_text": "What is the most important principle when administering medications?",
            "question_type": "multiple_choice",
            "options": [
                {"id": "a", "text": "Speed of administration", "is_correct": False},
                {"id": "b", "text": "Patient identification and verification", "is_correct": True},
                {"id": "c", "text": "Cost of medication", "is_correct": False},
                {"id": "d", "text": "Time of day", "is_correct": False}
            ],
            "correct_answer_id": "b",
            "explanation": "Patient identification and verification (Right Patient) is the most critical safety principle to prevent medication errors.",
            "difficulty_level": 2,
            "nclex_category": "Safe and Effective Care Environment"
        },
        {
            "id": "q2", 
            "question_text": "Which vital sign should be assessed first in a patient experiencing chest pain?",
            "question_type": "multiple_choice",
            "options": [
                {"id": "a", "text": "Temperature", "is_correct": False},
                {"id": "b", "text": "Blood pressure", "is_correct": True},
                {"id": "c", "text": "Respiratory rate", "is_correct": False},
                {"id": "d", "text": "Pulse oximetry", "is_correct": False}
            ],
            "correct_answer_id": "b",
            "explanation": "Blood pressure should be assessed first as chest pain may indicate cardiac compromise affecting circulation.",
            "difficulty_level": 3,
            "nclex_category": "Physiological Integrity"
        }
    ]
    
    for q_data in sample_questions:
        questions_db[q_data["id"]] = Question(**q_data)
    
    # Sample Flashcards
    sample_flashcards = [
        {
            "id": "f1",
            "set_name": "Medical Terminology Essentials",
            "term": "Tachycardia",
            "definition": "Rapid heart rate, typically over 100 beats per minute",
            "pronunciation": "tak-i-KAR-dee-ah"
        },
        {
            "id": "f2",
            "set_name": "Medical Terminology Essentials", 
            "term": "Bradycardia",
            "definition": "Slow heart rate, typically under 60 beats per minute",
            "pronunciation": "brad-i-KAR-dee-ah"
        }
    ]
    
    for f_data in sample_flashcards:
        flashcards_db[f_data["id"]] = Flashcard(**f_data)

# ===== API ENDPOINTS =====

@app.get("/")
async def root():
    return {"message": "NursePrep Pro API - Database Free Version", "status": "running"}

# Study Areas Endpoints
@app.get("/api/study-areas", response_model=List[StudyArea])
async def get_study_areas():
    return list(study_areas_db.values())

@app.get("/api/study-areas/{area_id}/questions", response_model=List[Question])
async def get_questions_by_area(area_id: str):
    # Filter questions by study area (in a real database, this would be a query)
    area_questions = []
    for question in questions_db.values():
        # For demo, assign questions to fundamentals area
        if area_id == "fundamentals":
            area_questions.append(question)
    return area_questions

# Flashcards Endpoints
@app.get("/api/flashcards", response_model=List[Flashcard])
async def get_flashcards():
    return list(flashcards_db.values())

@app.get("/api/flashcards/sets")
async def get_flashcard_sets():
    sets = {}
    for flashcard in flashcards_db.values():
        if flashcard.set_name not in sets:
            sets[flashcard.set_name] = []
        sets[flashcard.set_name].append(flashcard)
    return sets

# User and Progress Endpoints (Simplified for demo)
@app.post("/api/submit-quiz")
async def submit_quiz(submission: QuizSubmission):
    """Submit quiz results (stored in memory)"""
    user_id = "demo_user"  # In real app, this would come from auth
    
    # Calculate score
    correct_answers = 0
    total_questions = len(submission.answers)
    
    for answer in submission.answers:
        question_id = answer.get("question_id")
        selected_answer = answer.get("selected_answer")
        
        if question_id in questions_db:
            question = questions_db[question_id]
            if selected_answer == question.correct_answer_id:
                correct_answers += 1
    
    score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    # Store progress in memory
    progress_key = f"{user_id}_{submission.study_area_id}"
    if progress_key not in user_progress_db:
        user_progress_db[progress_key] = UserProgress(
            user_id=user_id,
            study_area_id=submission.study_area_id
        )
    
    progress = user_progress_db[progress_key]
    progress.questions_attempted += total_questions
    progress.questions_correct += correct_answers
    progress.last_activity = datetime.now()
    
    # Add session to history
    session_data = {
        "date": datetime.now().isoformat(),
        "score": score_percentage,
        "questions_attempted": total_questions,
        "questions_correct": correct_answers,
        "time_spent": submission.time_spent
    }
    progress.quiz_sessions.append(session_data)
    
    return {
        "score": score_percentage,
        "correct_answers": correct_answers,
        "total_questions": total_questions,
        "message": f"Great job! You scored {score_percentage:.1f}%"
    }

@app.post("/api/review-flashcard")
async def review_flashcard(review: FlashcardReview):
    """Submit flashcard review (simplified spaced repetition)"""
    user_id = "demo_user"
    
    progress_key = f"{user_id}_{review.flashcard_id}"
    if progress_key not in flashcard_progress_db:
        flashcard_progress_db[progress_key] = FlashcardProgress(
            user_id=user_id,
            flashcard_id=review.flashcard_id
        )
    
    progress = flashcard_progress_db[progress_key]
    
    # Simplified SM-2 algorithm
    if review.difficulty == "easy":
        progress.ease_factor = min(progress.ease_factor + 0.15, 3.0)
        progress.interval_days = max(progress.interval_days * 2, 6)
    elif review.difficulty == "good":
        progress.interval_days = max(progress.interval_days * progress.ease_factor, 1)
    else:  # hard
        progress.ease_factor = max(progress.ease_factor - 0.15, 1.3)
        progress.interval_days = 1
    
    progress.repetitions += 1
    progress.next_review_date = datetime.now() + timedelta(days=progress.interval_days)
    progress.status = "reviewed"
    
    return {"message": "Flashcard reviewed", "next_review_in_days": progress.interval_days}

# Analytics Endpoints
@app.get("/api/analytics")
async def get_analytics():
    """Get user analytics (demo data)"""
    return {
        "total_quizzes": 3,
        "quiz_average": 16.7,
        "cards_studied": 2,
        "card_mastery": 100.0,
        "recent_sessions": [
            {"date": "2025-01-15", "score": 75.0, "questions": 4},
            {"date": "2025-01-14", "score": 50.0, "questions": 2},
            {"date": "2025-01-13", "score": 25.0, "questions": 4}
        ]
    }

# Subscription/Payment Endpoints
@app.get("/api/subscription-plans", response_model=List[SubscriptionPlan])
async def get_subscription_plans():
    """Get available subscription plans"""
    plans = [
        {
            "id": "trial",
            "name": "7-Day Free Trial",
            "description": "Full access for 7 days",
            "price": 0.00,
            "interval": "trial",
            "features": ["All study areas", "Unlimited quizzes", "Flashcards", "Progress tracking"]
        },
        {
            "id": "monthly", 
            "name": "Monthly Plan",
            "description": "Month-to-month flexibility",
            "price": 9.99,
            "interval": "month",
            "features": ["All study areas", "Unlimited quizzes", "Flashcards", "Progress tracking", "Advanced analytics"]
        },
        {
            "id": "annual",
            "name": "Annual Plan", 
            "description": "Best value - save 33%",
            "price": 79.99,
            "interval": "year",
            "features": ["All study areas", "Unlimited quizzes", "Flashcards", "Progress tracking", "Advanced analytics", "Priority support"]
        },
        {
            "id": "lifetime",
            "name": "Lifetime Access",
            "description": "One-time payment, lifetime access",
            "price": 199.99,
            "interval": "lifetime", 
            "features": ["All study areas", "Unlimited quizzes", "Flashcards", "Progress tracking", "Advanced analytics", "Priority support", "Future updates"]
        }
    ]
    return [SubscriptionPlan(**plan) for plan in plans]

@app.get("/api/subscription-status")
async def get_subscription_status():
    """Get current subscription status (demo)"""
    return {
        "tier": "free",
        "status": "active",
        "trial_days_remaining": None,
        "can_upgrade": True
    }

if STRIPE_API_KEY:
    @app.post("/api/create-checkout-session")
    async def create_checkout_session(request: CheckoutSessionRequest):
        """Create Stripe checkout session"""
        try:
            stripe_client = StripeCheckout(api_key=STRIPE_API_KEY)
            
            # Map plan IDs to Stripe price IDs (you'll need to create these in Stripe)
            price_mapping = {
                "monthly": "price_monthly_9_99",  # Replace with actual Stripe price ID
                "annual": "price_annual_79_99",   # Replace with actual Stripe price ID  
                "lifetime": "price_lifetime_199_99"  # Replace with actual Stripe price ID
            }
            
            if request.price_id not in price_mapping:
                raise HTTPException(status_code=400, detail="Invalid price ID")
            
            checkout_request = CheckoutSessionRequest(
                price_id=price_mapping[request.price_id],
                success_url=request.success_url,
                cancel_url=request.cancel_url,
                customer_email=request.customer_email
            )
            
            session = stripe_client.create_checkout_session(checkout_request)
            return session
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")

    @app.post("/api/webhooks/stripe")
    async def stripe_webhook(request: Request):
        """Handle Stripe webhooks (simplified)"""
        try:
            body = await request.body()
            # In production, verify webhook signature
            # For now, just log that webhook was received
            print("Stripe webhook received")
            return {"status": "success"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

# Startup event
@app.on_event("startup")
async def startup_event():
    print("NursePrep Pro API starting up...")
    initialize_sample_data()
    print("Sample data initialized")
    print("🚀 Ready for your custom database integration!")

# Vercel handler
app = app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)