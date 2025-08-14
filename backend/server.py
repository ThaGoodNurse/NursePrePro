from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
from pymongo import MongoClient
import uuid
from datetime import datetime
import uvicorn

# Environment variables
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "nurseprep_db")
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

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
flashcard_sets_collection = db.flashcard_sets
flashcards_collection = db.flashcards
flashcard_sessions_collection = db.flashcard_sessions

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

# Flashcard Study endpoints
@app.post("/api/flashcards/study")
async def start_flashcard_study(set_id: str, shuffle: bool = True):
    """Start a flashcard study session"""
    try:
        # Get flashcards from the set
        flashcards = list(flashcards_collection.find(
            {"set_id": set_id}, 
            {"_id": 0}
        ))
        
        if not flashcards:
            raise HTTPException(status_code=404, detail="No flashcards found for this set")
        
        # Shuffle if requested
        if shuffle:
            import random
            random.shuffle(flashcards)
        
        study_session = FlashcardStudySession(
            set_id=set_id,
            cards_studied=[],
            correct_cards=[]
        )
        
        flashcard_sessions_collection.insert_one(study_session.model_dump())
        
        return {
            "session_id": study_session.id,
            "flashcards": flashcards,
            "total_cards": len(flashcards)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/flashcards/study/{session_id}/review")
async def review_flashcard(session_id: str, review: FlashcardReviewRequest):
    """Mark a flashcard as known or unknown"""
    try:
        # Get session
        session = flashcard_sessions_collection.find_one({"id": session_id}, {"_id": 0})
        if not session:
            raise HTTPException(status_code=404, detail="Study session not found")
        
        # Update session
        update_data = {"$addToSet": {"cards_studied": review.card_id}}
        if review.known:
            update_data["$addToSet"]["correct_cards"] = review.card_id
        
        flashcard_sessions_collection.update_one(
            {"id": session_id},
            update_data
        )
        
        return {"message": "Review recorded", "known": review.known}
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

# Quiz endpoints
@app.post("/api/quiz/start")
async def start_quiz(area_id: str, question_count: int = 10):
    """Start a new quiz for a study area"""
    try:
        # Get random questions from the area
        questions = list(questions_collection.aggregate([
            {"$match": {"area_id": area_id}},
            {"$sample": {"size": question_count}}
        ]))
        
        if not questions:
            raise HTTPException(status_code=404, detail="No questions found for this area")
        
        quiz_attempt = QuizAttempt(
            area_id=area_id,
            questions=[q["id"] for q in questions],
            answers={},
            score=0,
            total_questions=len(questions),
            started_at=datetime.utcnow()
        )
        
        quiz_attempts_collection.insert_one(quiz_attempt.model_dump())
        
        # Return questions without correct answers
        safe_questions = []
        for q in questions:
            safe_q = {
                "id": q["id"],
                "question_text": q["question_text"],
                "options": q["options"],
                "difficulty": q["difficulty"]
            }
            safe_questions.append(safe_q)
        
        return {
            "quiz_id": quiz_attempt.id,
            "questions": safe_questions,
            "total_questions": len(questions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quiz/{quiz_id}/submit")
async def submit_quiz(quiz_id: str, answers: List[QuizAnswerRequest]):
    """Submit quiz answers and get results"""
    try:
        # Get quiz attempt
        quiz = quiz_attempts_collection.find_one({"id": quiz_id}, {"_id": 0})
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")
        
        # Get questions with correct answers
        question_ids = quiz["questions"]
        questions = list(questions_collection.find(
            {"id": {"$in": question_ids}}, 
            {"_id": 0}
        ))
        
        # Calculate score
        correct_count = 0
        results = []
        answer_dict = {ans.question_id: ans.selected_option_id for ans in answers}
        
        for question in questions:
            selected_option_id = answer_dict.get(question["id"])
            is_correct = selected_option_id == question["correct_answer_id"]
            
            if is_correct:
                correct_count += 1
            
            # Find selected option text
            selected_option_text = None
            correct_option_text = None
            
            for option in question["options"]:
                if option["id"] == selected_option_id:
                    selected_option_text = option["text"]
                if option["id"] == question["correct_answer_id"]:
                    correct_option_text = option["text"]
            
            results.append({
                "question_id": question["id"],
                "question_text": question["question_text"],
                "selected_option": selected_option_text,
                "correct_option": correct_option_text,
                "is_correct": is_correct,
                "explanation": question.get("explanation")
            })
        
        # Update quiz attempt
        score_percentage = int((correct_count / len(questions)) * 100)
        quiz_attempts_collection.update_one(
            {"id": quiz_id},
            {
                "$set": {
                    "answers": answer_dict,
                    "score": score_percentage,
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "score": score_percentage,
            "correct_answers": correct_count,
            "total_questions": len(questions),
            "results": results
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