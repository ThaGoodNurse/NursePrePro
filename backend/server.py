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
    """Initialize the app with comprehensive nursing content"""
    
    # Complete Study Areas (restored from original)
    study_areas = [
        {
            "id": "fundamentals",
            "name": "Fundamentals of Nursing",
            "description": "Basic nursing concepts, patient care, and safety",
            "color": "#3b82f6",
            "icon": "stethoscope",
            "question_count": 25
        },
        {
            "id": "pharmacology", 
            "name": "Pharmacology",
            "description": "Drug classifications, actions, and administration",
            "color": "#10b981",
            "icon": "pill",
            "question_count": 30
        },
        {
            "id": "med-surg",
            "name": "Medical-Surgical Nursing", 
            "description": "Adult health conditions and nursing interventions",
            "color": "#8b5cf6",
            "icon": "hospital",
            "question_count": 35
        },
        {
            "id": "maternal-child",
            "name": "Maternal-Child Health",
            "description": "Pregnancy, childbirth, and pediatric nursing care",
            "color": "#f59e0b", 
            "icon": "baby",
            "question_count": 28
        },
        {
            "id": "critical-care",
            "name": "Critical Care",
            "description": "Intensive care, emergency situations, and life support",
            "color": "#ef4444",
            "icon": "activity",
            "question_count": 22
        },
        {
            "id": "leadership",
            "name": "Leadership & Management",
            "description": "Healthcare leadership, delegation, and management",
            "color": "#6366f1",
            "icon": "users",
            "question_count": 18
        },
        {
            "id": "oncology",
            "name": "Oncology/Hematology", 
            "description": "Cancer care, blood disorders, and treatments",
            "color": "#dc2626",
            "icon": "shield",
            "question_count": 20
        },
        {
            "id": "burn-wound",
            "name": "Burn & Wound Care",
            "description": "Burn treatment, wound healing, and skin integrity",
            "color": "#ea580c",
            "icon": "bandage",
            "question_count": 15
        },
        {
            "id": "hospice",
            "name": "Hospice & Palliative Care",
            "description": "End-of-life care, comfort measures, and family support",
            "color": "#7c3aed",
            "icon": "heart",
            "question_count": 12
        },
        {
            "id": "cardiac",
            "name": "Cardiac Nursing",
            "description": "Heart conditions, cardiovascular interventions",
            "color": "#be123c",
            "icon": "heart-pulse",
            "question_count": 26
        },
        {
            "id": "gastrointestinal", 
            "name": "Gastrointestinal",
            "description": "Digestive system disorders and treatments",
            "color": "#059669",
            "icon": "stomach",
            "question_count": 20
        },
        {
            "id": "renal",
            "name": "Renal Nursing",
            "description": "Kidney function, dialysis, and urinary disorders", 
            "color": "#0891b2",
            "icon": "droplet",
            "question_count": 18
        },
        {
            "id": "stem-cell",
            "name": "Stem Cell Transplant",
            "description": "Bone marrow transplant and stem cell therapy",
            "color": "#c026d3",
            "icon": "dna",
            "question_count": 14
        },
        {
            "id": "transplant",
            "name": "Organ Transplant", 
            "description": "Organ transplantation and immunosuppression",
            "color": "#16a34a",
            "icon": "refresh-cw",
            "question_count": 16
        }
    ]
    
    for area_data in study_areas:
        study_areas_db[area_data["id"]] = StudyArea(**area_data)
    
    # Comprehensive Sample Questions across multiple study areas
    sample_questions = [
        # Fundamentals of Nursing
        {
            "id": "fund_q1",
            "study_area_id": "fundamentals",
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
            "id": "fund_q2", 
            "study_area_id": "fundamentals",
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
        },
        {
            "id": "fund_q3",
            "study_area_id": "fundamentals", 
            "question_text": "A nurse is preparing to insert a urinary catheter. What is the priority action?",
            "question_type": "multiple_choice",
            "options": [
                {"id": "a", "text": "Gather all equipment", "is_correct": False},
                {"id": "b", "text": "Explain procedure to patient", "is_correct": False},
                {"id": "c", "text": "Perform hand hygiene", "is_correct": True},
                {"id": "d", "text": "Position the patient", "is_correct": False}
            ],
            "correct_answer_id": "c",
            "explanation": "Hand hygiene is the first and most important step in any sterile procedure to prevent infection.",
            "difficulty_level": 2,
            "nclex_category": "Safe and Effective Care Environment"
        },
        
        # Pharmacology
        {
            "id": "pharm_q1",
            "study_area_id": "pharmacology",
            "question_text": "A patient is prescribed digoxin 0.25mg daily. Which finding would require the nurse to hold the medication?",
            "question_type": "multiple_choice",
            "options": [
                {"id": "a", "text": "Blood pressure 130/80 mmHg", "is_correct": False},
                {"id": "b", "text": "Heart rate 55 bpm", "is_correct": True},
                {"id": "c", "text": "Potassium 4.2 mEq/L", "is_correct": False},
                {"id": "d", "text": "Respiratory rate 18/min", "is_correct": False}
            ],
            "correct_answer_id": "b",
            "explanation": "Digoxin should be held if heart rate is less than 60 bpm due to risk of further bradycardia.",
            "difficulty_level": 3,
            "nclex_category": "Physiological Integrity"
        },
        {
            "id": "pharm_q2",
            "study_area_id": "pharmacology",
            "question_text": "Which medication requires monitoring of INR levels?",
            "question_type": "multiple_choice", 
            "options": [
                {"id": "a", "text": "Heparin", "is_correct": False},
                {"id": "b", "text": "Warfarin", "is_correct": True},
                {"id": "c", "text": "Aspirin", "is_correct": False},
                {"id": "d", "text": "Clopidogrel", "is_correct": False}
            ],
            "correct_answer_id": "b",
            "explanation": "Warfarin requires regular INR monitoring to ensure therapeutic anticoagulation levels.",
            "difficulty_level": 2,
            "nclex_category": "Physiological Integrity"
        },
        
        # Medical-Surgical
        {
            "id": "medsurg_q1",
            "study_area_id": "med-surg",
            "question_text": "A post-operative patient reports severe incisional pain rated 8/10. What is the nurse's priority action?",
            "question_type": "multiple_choice",
            "options": [
                {"id": "a", "text": "Reassess pain in 30 minutes", "is_correct": False},
                {"id": "b", "text": "Administer prescribed analgesic", "is_correct": True},
                {"id": "c", "text": "Apply ice to incision", "is_correct": False},
                {"id": "d", "text": "Document the pain level", "is_correct": False}
            ],
            "correct_answer_id": "b",
            "explanation": "Severe post-operative pain requires immediate intervention with prescribed analgesics to provide relief.",
            "difficulty_level": 2,
            "nclex_category": "Physiological Integrity"
        },
        
        # Critical Care
        {
            "id": "critical_q1",
            "study_area_id": "critical-care",
            "question_text": "A patient in the ICU has a blood pressure of 70/40 mmHg and heart rate of 120 bpm. What condition should the nurse suspect?",
            "question_type": "multiple_choice",
            "options": [
                {"id": "a", "text": "Hypertensive crisis", "is_correct": False},
                {"id": "b", "text": "Cardiogenic shock", "is_correct": True},
                {"id": "c", "text": "Respiratory failure", "is_correct": False},
                {"id": "d", "text": "Diabetic ketoacidosis", "is_correct": False}
            ],
            "correct_answer_id": "b",
            "explanation": "Hypotension with tachycardia indicates possible cardiogenic shock requiring immediate intervention.",
            "difficulty_level": 4,
            "nclex_category": "Physiological Integrity"
        },
        
        # Maternal-Child Health
        {
            "id": "maternity_q1", 
            "study_area_id": "maternal-child",
            "question_text": "A pregnant woman at 38 weeks gestation reports decreased fetal movement. What is the nurse's priority action?",
            "question_type": "multiple_choice",
            "options": [
                {"id": "a", "text": "Schedule routine follow-up", "is_correct": False},
                {"id": "b", "text": "Perform non-stress test", "is_correct": True},
                {"id": "c", "text": "Reassure patient this is normal", "is_correct": False},
                {"id": "d", "text": "Document the concern", "is_correct": False}
            ],
            "correct_answer_id": "b",
            "explanation": "Decreased fetal movement requires immediate assessment with non-stress test to evaluate fetal well-being.",
            "difficulty_level": 3,
            "nclex_category": "Physiological Integrity"
        },
        
        # Cardiac Nursing
        {
            "id": "cardiac_q1",
            "study_area_id": "cardiac",
            "question_text": "A patient with heart failure is prescribed furosemide. Which lab value should be monitored closely?",
            "question_type": "multiple_choice",
            "options": [
                {"id": "a", "text": "Hemoglobin", "is_correct": False},
                {"id": "b", "text": "Potassium", "is_correct": True},
                {"id": "c", "text": "Glucose", "is_correct": False},
                {"id": "d", "text": "Protein", "is_correct": False}
            ],
            "correct_answer_id": "b",
            "explanation": "Furosemide causes potassium loss, requiring close monitoring to prevent dangerous hypokalemia.",
            "difficulty_level": 2,
            "nclex_category": "Physiological Integrity"
        }
    ]
    
    for q_data in sample_questions:
        questions_db[q_data["id"]] = Question(**q_data)
    
    # Comprehensive Flashcard Sets
    sample_flashcards = [
        # Medical Terminology Essentials
        {
            "id": "med_term_1",
            "set_name": "Medical Terminology Essentials",
            "term": "Tachycardia",
            "definition": "Rapid heart rate, typically over 100 beats per minute",
            "pronunciation": "tak-i-KAR-dee-ah"
        },
        {
            "id": "med_term_2",
            "set_name": "Medical Terminology Essentials", 
            "term": "Bradycardia",
            "definition": "Slow heart rate, typically under 60 beats per minute",
            "pronunciation": "brad-i-KAR-dee-ah"
        },
        {
            "id": "med_term_3",
            "set_name": "Medical Terminology Essentials",
            "term": "Hypertension", 
            "definition": "High blood pressure, consistently above 140/90 mmHg",
            "pronunciation": "hahy-per-TEN-shuhn"
        },
        {
            "id": "med_term_4",
            "set_name": "Medical Terminology Essentials",
            "term": "Hypotension",
            "definition": "Low blood pressure, typically below 90/60 mmHg", 
            "pronunciation": "hahy-poh-TEN-shuhn"
        },
        {
            "id": "med_term_5",
            "set_name": "Medical Terminology Essentials",
            "term": "Dyspnea",
            "definition": "Difficulty breathing or shortness of breath",
            "pronunciation": "DISP-nee-ah"
        },
        {
            "id": "med_term_6",
            "set_name": "Medical Terminology Essentials",
            "term": "Apnea", 
            "definition": "Temporary cessation of breathing",
            "pronunciation": "AP-nee-ah"
        },
        
        # Pharmacology Terms
        {
            "id": "pharm_1",
            "set_name": "Pharmacology Fundamentals",
            "term": "Agonist",
            "definition": "A drug that binds to and activates a receptor to produce a response",
            "pronunciation": "AG-uh-nist"
        },
        {
            "id": "pharm_2", 
            "set_name": "Pharmacology Fundamentals",
            "term": "Antagonist",
            "definition": "A drug that blocks or inhibits the action of another drug or natural substance",
            "pronunciation": "an-TAG-uh-nist"
        },
        {
            "id": "pharm_3",
            "set_name": "Pharmacology Fundamentals",
            "term": "Bioavailability",
            "definition": "The fraction of an administered dose that reaches systemic circulation",
            "pronunciation": "bahy-oh-uh-vey-luh-BIL-i-tee"
        },
        {
            "id": "pharm_4",
            "set_name": "Pharmacology Fundamentals", 
            "term": "Half-life",
            "definition": "Time required for the concentration of a drug to decrease by half",
            "pronunciation": "HAF-lahyf"
        },
        
        # Pathophysiology Terms  
        {
            "id": "patho_1",
            "set_name": "Pathophysiology Basics",
            "term": "Inflammation",
            "definition": "Body's response to injury or infection, characterized by redness, swelling, heat, and pain",
            "pronunciation": "in-fluh-MEY-shuhn"
        },
        {
            "id": "patho_2",
            "set_name": "Pathophysiology Basics",
            "term": "Necrosis", 
            "definition": "Death of cells or tissues due to disease or injury",
            "pronunciation": "nuh-KROH-sis"
        },
        {
            "id": "patho_3",
            "set_name": "Pathophysiology Basics",
            "term": "Ischemia",
            "definition": "Insufficient blood supply to an organ or tissue",
            "pronunciation": "is-KEE-mee-ah"
        },
        {
            "id": "patho_4",
            "set_name": "Pathophysiology Basics",
            "term": "Edema",
            "definition": "Swelling caused by excess fluid trapped in body tissues",
            "pronunciation": "ih-DEE-mah"
        }
    ]
    
    for f_data in sample_flashcards:
        flashcards_db[f_data["id"]] = Flashcard(**f_data)

# ===== API ENDPOINTS =====

@app.get("/")
async def root():
    return {"message": "NursePrep Pro API - Database Free Version", "status": "running"}

# Study Areas Endpoints
@app.get("/api/study-areas")
async def get_study_areas():
    return {"study_areas": list(study_areas_db.values())}

@app.get("/api/study-areas/{area_id}/questions", response_model=List[Question])
async def get_questions_by_area(area_id: str):
    """Get questions for a specific study area"""
    area_questions = []
    for question in questions_db.values():
        if hasattr(question, 'study_area_id') and question.study_area_id == area_id:
            area_questions.append(question)
    return area_questions

# Flashcards Endpoints
@app.get("/api/flashcards", response_model=List[Flashcard])
async def get_flashcards():
    return list(flashcards_db.values())

@app.get("/api/flashcard-sets")
async def get_flashcard_sets():
    """Get flashcard sets (frontend expects this endpoint)"""
    sets = {}
    for flashcard in flashcards_db.values():
        if flashcard.set_name not in sets:
            sets[flashcard.set_name] = []
        sets[flashcard.set_name].append(flashcard.dict())
    
    # Convert to array format that frontend expects
    formatted_sets = []
    for set_name, cards in sets.items():
        formatted_sets.append({
            "id": set_name.lower().replace(" ", "_"),
            "name": set_name,
            "description": f"Master essential {set_name.lower()} terms and definitions",
            "card_count": len(cards),
            "color": "#3b82f6",  # Blue color for all sets
            "spaced_repetition_enabled": True,
            "cards": cards
        })
    
    return {"flashcard_sets": formatted_sets}

@app.get("/api/flashcards/sets") 
async def get_flashcard_sets_alt():
    """Alternative endpoint for flashcard sets"""
    return await get_flashcard_sets()

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

@app.get("/api/stats")
async def get_stats():
    """Get user stats (demo data)"""
    return {
        "total_quizzes": 3,
        "average_score": 16.7,
        "total_questions": 10,
        "correct_answers": 5,
        "study_streak": 3,
        "last_activity": datetime.now().isoformat()
    }

@app.get("/api/flashcards/stats") 
async def get_flashcard_stats():
    """Get flashcard statistics (demo data)"""
    return {
        "cards_studied": 2,
        "cards_mastered": 2,
        "cards_learning": 0,
        "cards_new": 0,
        "study_streak": 1,
        "total_reviews": 5,
        "mastery_percentage": 100.0
    }

@app.get("/api/subscription/status")
async def get_detailed_subscription_status():
    """Get detailed subscription status (demo)"""
    return {
        "tier": "free",
        "status": "active", 
        "trial_days_remaining": None,
        "can_upgrade": True,
        "features": ["Basic quizzes", "Limited flashcards"],
        "billing_cycle": None,
        "next_billing_date": None
    }

@app.get("/api/packages")
async def get_packages():
    """Get available packages/plans"""
    packages = [
        {
            "id": "monthly",
            "name": "Monthly Premium", 
            "price": 9.99,
            "interval": "month",
            "features": ["All study areas", "Unlimited quizzes", "Advanced analytics"]
        },
        {
            "id": "annual",
            "name": "Annual Premium",
            "price": 79.99, 
            "interval": "year",
            "features": ["All study areas", "Unlimited quizzes", "Advanced analytics", "Save 33%"]
        }
    ]
    return {"packages": packages}

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
    
    @app.post("/api/payments/checkout/session")
    async def create_payment_checkout_session(request: dict):
        """Create Stripe checkout session (alternative endpoint)"""
        return await create_checkout_session(CheckoutSessionRequest(**request))
        
    @app.get("/api/payments/checkout/status/{session_id}")
    async def get_checkout_status(session_id: str):
        """Get checkout session status"""
        return {
            "status": "complete",
            "payment_status": "paid",
            "subscription_tier": "premium"
        }

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

# Quiz Endpoints
@app.post("/api/quiz/start-advanced")
async def start_advanced_quiz(request: dict):
    """Start an advanced quiz session"""
    study_area = request.get("study_area")
    quiz_type = request.get("quiz_type", "practice")
    settings = request.get("settings", {})
    
    # Create quiz session
    quiz_id = str(uuid.uuid4())
    
    # Get questions for the study area
    quiz_questions = []
    for question in questions_db.values():
        if study_area == "fundamentals":  # Demo: only fundamentals has questions
            quiz_questions.append(question)
    
    return {
        "quiz_id": quiz_id,
        "questions": [q.dict() for q in quiz_questions],
        "settings": settings,
        "total_questions": len(quiz_questions)
    }

@app.post("/api/quiz/{quiz_id}/submit-advanced")
async def submit_advanced_quiz(quiz_id: str, submission: dict):
    """Submit advanced quiz results"""
    answers = submission.get("answers", [])
    time_spent = submission.get("time_spent", 0)
    
    # Calculate results
    correct_count = 0
    total_questions = len(answers)
    
    for answer in answers:
        question_id = answer.get("question_id")
        selected_answer = answer.get("selected_answer")
        
        if question_id in questions_db:
            question = questions_db[question_id]
            if selected_answer == question.correct_answer_id:
                correct_count += 1
    
    score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
    
    return {
        "quiz_id": quiz_id,
        "score": score_percentage,
        "correct_answers": correct_count,
        "total_questions": total_questions,
        "time_spent": time_spent,
        "passed": score_percentage >= 75,
        "detailed_results": [
            {
                "question_id": ans.get("question_id"),
                "correct": ans.get("selected_answer") == questions_db.get(ans.get("question_id"), {}).correct_answer_id if ans.get("question_id") in questions_db else False,
                "selected_answer": ans.get("selected_answer"),
                "correct_answer": questions_db.get(ans.get("question_id"), {}).correct_answer_id if ans.get("question_id") in questions_db else None
            }
            for ans in answers
        ]
    }

# Flashcard Study Endpoints  
@app.post("/api/flashcards/study")
async def start_flashcard_study(request: dict = None):
    """Start flashcard study session"""
    session_id = str(uuid.uuid4())
    
    return {
        "session_id": session_id,
        "total_cards": len(flashcards_db),
        "cards_due": 2  # Demo data
    }

@app.post("/api/flashcards/study/{session_id}/review")
async def review_flashcard_basic(session_id: str, request: dict):
    """Basic flashcard review"""
    return {"status": "recorded", "next_card": True}

@app.post("/api/flashcards/study/{session_id}/review-spaced")
async def review_flashcard_spaced(session_id: str, request: dict):
    """Spaced repetition flashcard review"""
    return await review_flashcard(FlashcardReview(
        flashcard_id=request.get("card_id"),
        difficulty="good" if request.get("quality", 3) >= 3 else "hard"
    ))

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