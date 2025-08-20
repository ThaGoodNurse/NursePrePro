#!/usr/bin/env python3
"""
Direct MongoDB connection test for NursePrep Pro
"""

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime

def test_connection():
    # Your connection string
    uri = "mongodb+srv://thagoodnurse:f8INupvEshFl5c2o@nursepreprov1.nzoumpi.mongodb.net/?retryWrites=true&w=majority&appName=NursePreProV1"
    DB_NAME = "nurseprep_prod"
    
    try:
        print("🔄 Testing MongoDB Atlas connection...")
        
        # Create client with Server API version 1
        client = MongoClient(uri, server_api=ServerApi('1'))
        
        # Test basic connection
        client.admin.command('ping')
        print("✅ SUCCESS: Connected to MongoDB Atlas!")
        
        # Test database operations
        db = client[DB_NAME]
        
        # Create test document
        test_collection = db.connection_test
        test_doc = {
            "test_id": "nurseprep_production_test",
            "app_name": "NursePrep Pro",
            "message": "MongoDB Atlas ready for production!",
            "timestamp": datetime.now(),
            "cluster": "nursepreprov1",
            "organization": "ThagoodnurseV2",
            "project": "Project0",
            "status": "ready_for_vercel"
        }
        
        # Insert and retrieve test
        result = test_collection.insert_one(test_doc)
        print(f"✅ SUCCESS: Test document inserted with ID: {result.inserted_id}")
        
        retrieved = test_collection.find_one({"test_id": "nurseprep_production_test"})
        if retrieved:
            print("✅ SUCCESS: Document retrieval working")
            print(f"   App: {retrieved['app_name']}")
            print(f"   Status: {retrieved['status']}")
        
        # Clean up test document
        test_collection.delete_one({"test_id": "nurseprep_production_test"})
        print("✅ SUCCESS: Test cleanup completed")
        
        print("\n" + "="*60)
        print("🎉 MONGODB ATLAS CONNECTION PERFECT!")
        print("="*60)
        print(f"✅ Organization: ThagoodnurseV2")
        print(f"✅ Project: Project0") 
        print(f"✅ Cluster: nursepreprov1")
        print(f"✅ Database: {DB_NAME}")
        print(f"✅ User: thagoodnurse")
        print("="*60)
        print("🚀 READY FOR VERCEL DEPLOYMENT!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        print("\n🔧 Check these items:")
        print("1. Password is correct: f8INupvEshFl5c2o")
        print("2. IP whitelist includes 0.0.0.0/0") 
        print("3. User 'thagoodnurse' has proper permissions")
        print("4. Cluster 'nursepreprov1' is running")
        return False

if __name__ == "__main__":
    test_connection()