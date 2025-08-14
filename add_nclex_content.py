#!/usr/bin/env python3
import os
import uuid
from pymongo import MongoClient
from datetime import datetime

# Environment variables
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

# MongoDB setup
client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Collections
study_areas_collection = db.study_areas
questions_collection = db.questions

def create_nclex_questions():
    """Create comprehensive NCLEX-RN style questions"""
    
    # Get study area IDs
    fundamentals_area = study_areas_collection.find_one({"name": "Fundamentals of Nursing"})
    pharmacology_area = study_areas_collection.find_one({"name": "Pharmacology"})
    med_surg_area = study_areas_collection.find_one({"name": "Medical-Surgical Nursing"})
    critical_care_area = study_areas_collection.find_one({"name": "Critical Care"})
    cardiac_area = study_areas_collection.find_one({"name": "Cardiac"})
    
    if not all([fundamentals_area, pharmacology_area, med_surg_area, critical_care_area, cardiac_area]):
        print("Error: Not all required study areas found")
        return
    
    nclex_questions = [
        # SAFE AND EFFECTIVE CARE ENVIRONMENT - Management of Care
        {
            "id": str(uuid.uuid4()),
            "question_text": "A charge nurse is making assignments for the upcoming shift. Which client should be assigned to the most experienced registered nurse?",
            "question_type": "multiple_choice",
            "options": [
                {"id": str(uuid.uuid4()), "text": "A 45-year-old client 2 days post-operative from a cholecystectomy"},
                {"id": str(uuid.uuid4()), "text": "A 30-year-old client with pneumonia receiving IV antibiotics"},
                {"id": str(uuid.uuid4()), "text": "A 65-year-old client with multiple trauma injuries requiring frequent assessment"},
                {"id": str(uuid.uuid4()), "text": "A 55-year-old client with diabetes mellitus requiring insulin administration"}
            ],
            "correct_answer_id": "",  # Will be set below
            "explanation": "The client with multiple trauma injuries requires the most experienced nurse due to the complexity of care and potential for rapid deterioration.",
            "rationale": "Assignment decisions should be based on client acuity, complexity of care, and nurse competency. Critically injured clients require the most experienced staff.",
            "difficulty": "medium",
            "cognitive_level": "analysis",
            "nclex_category": "safe_effective_care",
            "nclex_subcategory": "management_of_care",
            "client_needs": "Safe and Effective Care Environment",
            "priority_level": "high",
            "area_id": fundamentals_area["id"],
            "time_limit": 75,
            "created_at": datetime.utcnow()
        },
        
        # SAFE AND EFFECTIVE CARE ENVIRONMENT - Safety and Infection Control
        {
            "id": str(uuid.uuid4()),
            "question_text": "A nurse is caring for a client with Clostridium difficile infection. Which infection control precaution should the nurse implement?",
            "question_type": "multiple_choice",
            "options": [
                {"id": str(uuid.uuid4()), "text": "Standard precautions only"},
                {"id": str(uuid.uuid4()), "text": "Droplet precautions"},
                {"id": str(uuid.uuid4()), "text": "Airborne precautions"},
                {"id": str(uuid.uuid4()), "text": "Contact precautions"}
            ],
            "correct_answer_id": "",
            "explanation": "C. difficile requires contact precautions due to spore transmission through direct contact and contaminated surfaces.",
            "rationale": "Contact precautions are used for infections transmitted by direct contact or contact with contaminated items. C. diff spores can survive on surfaces.",
            "difficulty": "easy",
            "cognitive_level": "knowledge",
            "nclex_category": "safe_effective_care",
            "nclex_subcategory": "safety_infection_control",
            "client_needs": "Safe and Effective Care Environment",
            "priority_level": "high",
            "area_id": fundamentals_area["id"],
            "time_limit": 60,
            "created_at": datetime.utcnow()
        },
        
        # HEALTH PROMOTION AND MAINTENANCE
        {
            "id": str(uuid.uuid4()),
            "question_text": "A nurse is providing education to a 35-year-old female client about breast self-examination. When should the nurse instruct the client to perform the examination?",
            "question_type": "multiple_choice",
            "options": [
                {"id": str(uuid.uuid4()), "text": "The same day each month"},
                {"id": str(uuid.uuid4()), "text": "One week before menstruation"},
                {"id": str(uuid.uuid4()), "text": "One week after menstruation"},
                {"id": str(uuid.uuid4()), "text": "During menstruation"}
            ],
            "correct_answer_id": "",
            "explanation": "Breast self-examination should be performed one week after menstruation when hormonal influences are minimal and breast tissue is least tender.",
            "rationale": "Hormonal changes during the menstrual cycle affect breast tissue. The week after menstruation provides the most accurate assessment.",
            "difficulty": "easy",
            "cognitive_level": "comprehension",
            "nclex_category": "health_promotion",
            "nclex_subcategory": "health_maintenance",
            "client_needs": "Health Promotion and Maintenance",
            "priority_level": "medium",
            "area_id": fundamentals_area["id"],
            "time_limit": 60,
            "created_at": datetime.utcnow()
        },
        
        # PSYCHOSOCIAL INTEGRITY
        {
            "id": str(uuid.uuid4()),
            "question_text": "A client diagnosed with terminal cancer tells the nurse, 'I just want to live long enough to see my daughter graduate from college.' The nurse recognizes this as which stage of grief?",
            "question_type": "multiple_choice",
            "options": [
                {"id": str(uuid.uuid4()), "text": "Denial"},
                {"id": str(uuid.uuid4()), "text": "Anger"},
                {"id": str(uuid.uuid4()), "text": "Bargaining"},
                {"id": str(uuid.uuid4()), "text": "Depression"}
            ],
            "correct_answer_id": "",
            "explanation": "Bargaining involves attempting to negotiate or make deals, often with a higher power, to postpone the inevitable.",
            "rationale": "According to Kübler-Ross, bargaining is characterized by 'if only' or 'what if' statements and attempts to postpone death.",
            "difficulty": "medium",
            "cognitive_level": "application",
            "nclex_category": "psychosocial_integrity",
            "nclex_subcategory": "coping_adaptation",
            "client_needs": "Psychosocial Integrity",
            "priority_level": "medium",
            "area_id": fundamentals_area["id"],
            "time_limit": 60,
            "created_at": datetime.utcnow()
        },
        
        # PHYSIOLOGICAL INTEGRITY - Basic Care and Comfort
        {
            "id": str(uuid.uuid4()),
            "question_text": "A client is receiving continuous tube feeding through a nasogastric tube. Which nursing intervention is the priority to prevent aspiration?",
            "question_type": "multiple_choice",
            "options": [
                {"id": str(uuid.uuid4()), "text": "Check tube placement every 8 hours"},
                {"id": str(uuid.uuid4()), "text": "Keep the head of the bed elevated 30-45 degrees"},
                {"id": str(uuid.uuid4()), "text": "Monitor gastric residual volumes every 4 hours"},
                {"id": str(uuid.uuid4()), "text": "Flush the tube with water every 4 hours"}
            ],
            "correct_answer_id": "",
            "explanation": "Keeping the head of bed elevated 30-45 degrees prevents reflux and reduces the risk of aspiration during continuous feeding.",
            "rationale": "Elevation uses gravity to prevent gastric contents from refluxing into the esophagus and potentially being aspirated.",
            "difficulty": "medium",
            "cognitive_level": "application",
            "nclex_category": "physiological_integrity",
            "nclex_subcategory": "basic_care_comfort",
            "client_needs": "Physiological Integrity",
            "priority_level": "high",
            "area_id": fundamentals_area["id"],
            "time_limit": 75,
            "created_at": datetime.utcnow()
        },
        
        # PHYSIOLOGICAL INTEGRITY - Pharmacological Therapies
        {
            "id": str(uuid.uuid4()),
            "question_text": "A client is prescribed digoxin 0.25 mg daily. Before administering the medication, the nurse notes the client's apical pulse is 58 beats per minute. What is the nurse's priority action?",
            "question_type": "multiple_choice",
            "options": [
                {"id": str(uuid.uuid4()), "text": "Administer the medication as prescribed"},
                {"id": str(uuid.uuid4()), "text": "Hold the medication and notify the healthcare provider"},
                {"id": str(uuid.uuid4()), "text": "Recheck the pulse in 30 minutes"},
                {"id": str(uuid.uuid4()), "text": "Administer half the prescribed dose"}
            ],
            "correct_answer_id": "",
            "explanation": "Digoxin should be held if the apical pulse is less than 60 bpm in adults due to risk of further bradycardia and heart block.",
            "rationale": "Digoxin slows the heart rate and can cause dangerous bradycardia. Safety protocols require holding the medication when pulse <60.",
            "difficulty": "medium",
            "cognitive_level": "application",
            "nclex_category": "physiological_integrity",
            "nclex_subcategory": "pharmacological_therapies",
            "client_needs": "Physiological Integrity",
            "priority_level": "high",
            "area_id": pharmacology_area["id"],
            "time_limit": 75,
            "created_at": datetime.utcnow()
        },
        
        # PHYSIOLOGICAL INTEGRITY - Reduction of Risk Potential
        {
            "id": str(uuid.uuid4()),
            "question_text": "A client is scheduled for a cardiac catheterization. Which pre-procedure intervention is most important for the nurse to implement?",
            "question_type": "multiple_choice",
            "options": [
                {"id": str(uuid.uuid4()), "text": "Obtain baseline vital signs"},
                {"id": str(uuid.uuid4()), "text": "Assess for allergies to iodine or shellfish"},
                {"id": str(uuid.uuid4()), "text": "Ensure informed consent is signed"},
                {"id": str(uuid.uuid4()), "text": "Start an IV line"}
            ],
            "correct_answer_id": "",
            "explanation": "Assessing for iodine/shellfish allergies is critical because contrast dye used in cardiac catheterization contains iodine and can cause severe allergic reactions.",
            "rationale": "Anaphylactic reactions to iodine-based contrast can be life-threatening. This assessment must be done before the procedure.",
            "difficulty": "medium",
            "cognitive_level": "analysis",
            "nclex_category": "physiological_integrity",
            "nclex_subcategory": "reduction_risk_potential",
            "client_needs": "Physiological Integrity",
            "priority_level": "critical",
            "area_id": cardiac_area["id"],
            "time_limit": 75,
            "created_at": datetime.utcnow()
        },
        
        # PHYSIOLOGICAL INTEGRITY - Physiological Adaptation
        {
            "id": str(uuid.uuid4()),
            "question_text": "A client with acute myocardial infarction suddenly develops ventricular fibrillation. What is the nurse's immediate priority action?",
            "question_type": "multiple_choice",
            "options": [
                {"id": str(uuid.uuid4()), "text": "Prepare for synchronized cardioversion"},
                {"id": str(uuid.uuid4()), "text": "Begin immediate defibrillation"},
                {"id": str(uuid.uuid4()), "text": "Administer amiodarone IV push"},
                {"id": str(uuid.uuid4()), "text": "Start CPR compressions"}
            ],
            "correct_answer_id": "",
            "explanation": "Ventricular fibrillation is a shockable rhythm requiring immediate defibrillation to restore normal cardiac rhythm.",
            "rationale": "V-fib is a life-threatening arrhythmia with no cardiac output. Immediate defibrillation is the definitive treatment.",
            "difficulty": "hard",
            "cognitive_level": "application",
            "nclex_category": "physiological_integrity",
            "nclex_subcategory": "physiological_adaptation",
            "client_needs": "Physiological Integrity",
            "priority_level": "critical",
            "area_id": critical_care_area["id"],
            "time_limit": 60,
            "created_at": datetime.utcnow()
        },
        
        # Multiple Response Question
        {
            "id": str(uuid.uuid4()),
            "question_text": "A nurse is caring for a client with diabetic ketoacidosis (DKA). Which findings would the nurse expect to assess? (Select all that apply)",
            "question_type": "multiple_response",
            "options": [
                {"id": str(uuid.uuid4()), "text": "Blood glucose level of 450 mg/dL", "is_correct": True},
                {"id": str(uuid.uuid4()), "text": "Fruity breath odor", "is_correct": True},
                {"id": str(uuid.uuid4()), "text": "Bradycardia", "is_correct": False},
                {"id": str(uuid.uuid4()), "text": "Kussmaul respirations", "is_correct": True},
                {"id": str(uuid.uuid4()), "text": "Increased appetite", "is_correct": False},
                {"id": str(uuid.uuid4()), "text": "Dehydration", "is_correct": True}
            ],
            "correct_answer_ids": [],  # Will be populated below
            "explanation": "DKA presents with hyperglycemia, ketosis (fruity breath), compensatory Kussmaul respirations, and severe dehydration.",
            "rationale": "DKA is characterized by hyperglycemia >250 mg/dL, ketosis, metabolic acidosis, and severe fluid loss leading to dehydration.",
            "difficulty": "medium",
            "cognitive_level": "analysis",
            "nclex_category": "physiological_integrity",
            "nclex_subcategory": "physiological_adaptation",
            "client_needs": "Physiological Integrity",
            "priority_level": "high",
            "area_id": med_surg_area["id"],
            "time_limit": 90,
            "created_at": datetime.utcnow()
        },
        
        # Priority/Delegation Question
        {
            "id": str(uuid.uuid4()),
            "question_text": "A nurse receives report on four clients. Which client should the nurse assess first?",
            "question_type": "multiple_choice",
            "options": [
                {"id": str(uuid.uuid4()), "text": "A client with pneumonia who has an oxygen saturation of 92%"},
                {"id": str(uuid.uuid4()), "text": "A client post-operative day 1 who reports pain level 7/10"},
                {"id": str(uuid.uuid4()), "text": "A client with heart failure who gained 3 pounds overnight"},
                {"id": str(uuid.uuid4()), "text": "A client with diabetes who has a blood glucose of 180 mg/dL"}
            ],
            "correct_answer_id": "",
            "explanation": "The client with heart failure who gained 3 pounds overnight indicates fluid retention and potential decompensation requiring immediate assessment.",
            "rationale": "Using ABC priorities and Maslow's hierarchy, fluid overload in heart failure can quickly lead to pulmonary edema and respiratory failure.",
            "difficulty": "hard",
            "cognitive_level": "analysis",
            "nclex_category": "safe_effective_care",
            "nclex_subcategory": "management_of_care",
            "client_needs": "Safe and Effective Care Environment",
            "priority_level": "critical",
            "area_id": cardiac_area["id"],
            "time_limit": 75,
            "created_at": datetime.utcnow()
        }
    ]
    
    # Set correct answer IDs for multiple choice questions
    for i, question in enumerate(nclex_questions):
        if question["question_type"] == "multiple_choice":
            # Set the correct answer based on the explanation pattern
            correct_indices = [2, 3, 2, 2, 1, 1, 1, 1, 2]  # Based on the correct answers
            if i < len(correct_indices):
                question["correct_answer_id"] = question["options"][correct_indices[i]]["id"]
        elif question["question_type"] == "multiple_response":
            # Set correct answer IDs for multiple response
            correct_ids = []
            for option in question["options"]:
                if option.get("is_correct", False):
                    correct_ids.append(option["id"])
            question["correct_answer_ids"] = correct_ids
    
    return nclex_questions

def main():
    print("🏥 Adding NCLEX-RN Style Questions...")
    
    # Create NCLEX questions
    nclex_questions = create_nclex_questions()
    
    if nclex_questions:
        try:
            # Insert questions
            result = questions_collection.insert_many(nclex_questions)
            print(f"✅ Successfully added {len(result.inserted_ids)} NCLEX-RN style questions")
            
            # Show breakdown by category
            categories = {}
            for q in nclex_questions:
                cat = q.get("nclex_category", "unknown")
                categories[cat] = categories.get(cat, 0) + 1
            
            print("\n📊 Questions by NCLEX Category:")
            for category, count in categories.items():
                print(f"   {category.replace('_', ' ').title()}: {count} questions")
            
            # Show breakdown by difficulty
            difficulties = {}
            for q in nclex_questions:
                diff = q.get("difficulty", "medium")
                difficulties[diff] = difficulties.get(diff, 0) + 1
            
            print("\n📈 Questions by Difficulty:")
            for difficulty, count in difficulties.items():
                print(f"   {difficulty.title()}: {count} questions")
            
            print(f"\n🎯 Total NCLEX-RN questions added: {len(nclex_questions)}")
            
        except Exception as e:
            print(f"❌ Error adding questions: {e}")
    else:
        print("❌ No questions created")

if __name__ == "__main__":
    main()