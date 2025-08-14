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

class Question(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question_text: str
    options: List[QuestionOption]
    correct_answer_id: str
    explanation: Optional[str] = None
    difficulty: str = "medium"  # easy, medium, hard
    area_id: str

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
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FlashcardSet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    category: str
    color: str = "#3B82F6"
    card_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FlashcardStudySession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    set_id: str
    cards_studied: List[str]  # flashcard IDs
    correct_cards: List[str]  # flashcard IDs marked as known
    session_duration: Optional[int] = None  # in seconds
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

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

class QuizAnswerRequest(BaseModel):
    question_id: str
    selected_option_id: str

# Initialize collections
study_areas_collection = db.study_areas
questions_collection = db.questions
quiz_attempts_collection = db.quiz_attempts

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
        
        print("Sample data initialized successfully")
    except Exception as e:
        print(f"Error initializing sample data: {e}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)