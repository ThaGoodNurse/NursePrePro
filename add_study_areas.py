#!/usr/bin/env python3
import os
import uuid
from pymongo import MongoClient

# Environment variables
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

# MongoDB setup
client = MongoClient(MONGO_URL)
db = client[DB_NAME]
study_areas_collection = db.study_areas

# New study areas to add
new_areas = [
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

# Insert new study areas
try:
    result = study_areas_collection.insert_many(new_areas)
    print(f"✅ Successfully added {len(result.inserted_ids)} new study areas:")
    
    # Display all areas
    all_areas = list(study_areas_collection.find({}, {"_id": 0}))
    for i, area in enumerate(all_areas, 1):
        print(f"{i:2d}. {area['name']:<25} - {area['description']}")
    
    print(f"\nTotal study areas: {len(all_areas)}")
    
except Exception as e:
    print(f"❌ Error adding study areas: {e}")