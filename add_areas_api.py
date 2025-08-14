#!/usr/bin/env python3
import requests
import json

BASE_URL = "https://nurseprep-1.preview.emergentagent.com"

# New study areas to add
new_areas = [
    {
        "name": "Critical Care",
        "description": "Intensive care unit nursing and life-threatening conditions",
        "color": "#DC2626"
    },
    {
        "name": "Leadership",
        "description": "Nursing leadership, management, and professional development",
        "color": "#7C3AED"
    },
    {
        "name": "Oncology/Hematology",
        "description": "Cancer care and blood disorder management",
        "color": "#DB2777"
    },
    {
        "name": "Burn Wound Care",
        "description": "Assessment and treatment of burn injuries",
        "color": "#EA580C"
    },
    {
        "name": "Hospice",
        "description": "End-of-life care and palliative nursing",
        "color": "#6B7280"
    },
    {
        "name": "Cardiac",
        "description": "Cardiovascular nursing and heart conditions",
        "color": "#B91C1C"
    },
    {
        "name": "Gastrointestinal",
        "description": "Digestive system disorders and GI nursing care",
        "color": "#059669"
    },
    {
        "name": "Renal",
        "description": "Kidney function, dialysis, and renal nursing",
        "color": "#0284C7"
    },
    {
        "name": "Stem Cell",
        "description": "Stem cell therapy and bone marrow transplant nursing",
        "color": "#7C2D12"
    },
    {
        "name": "Transplant",
        "description": "Organ transplantation and post-transplant care",
        "color": "#15803D"
    }
]

print("Adding new study areas via API...")

for area in new_areas:
    try:
        response = requests.post(
            f"{BASE_URL}/api/study-areas",
            json=area,
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 200:
            print(f"✅ Added: {area['name']}")
        else:
            print(f"❌ Failed to add {area['name']}: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error adding {area['name']}: {e}")

# Verify the areas were added
print("\nVerifying added areas...")
try:
    response = requests.get(f"{BASE_URL}/api/study-areas")
    if response.status_code == 200:
        data = response.json()
        areas = data['study_areas']
        print(f"\nTotal study areas: {len(areas)}")
        for i, area in enumerate(areas, 1):
            print(f"{i:2d}. {area['name']:<25} ({area['question_count']} questions)")
    else:
        print(f"❌ Failed to fetch study areas: {response.status_code}")
except Exception as e:
    print(f"❌ Error fetching study areas: {e}")