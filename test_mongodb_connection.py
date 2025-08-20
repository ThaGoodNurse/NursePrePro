#!/usr/bin/env python3
"""
MongoDB Atlas Connection Test Script for NursePrep Pro
"""

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime

def test_your_connection():
    # Your connection string - REPLACE <db_password> with your actual password
    uri = "mongodb+srv://thagoodnurse:<db_password>@nursepreprov1.nzoumpi.mongodb.net/?retryWrites=true&w=majority&appName=NursePreProV1"
    
    print("⚠️  IMPORTANT: Make sure you replaced <db_password> with your actual password!")
    actual_uri = input("Paste your connection string with REAL password: ").strip()
    
    DB_NAME = "nurseprep_prod"
    
    try:
        print("🔄 Connecting to MongoDB Atlas...")
        
        # Create client with Server API version 1 (as MongoDB Atlas recommends)
        client = MongoClient(actual_uri, server_api=ServerApi('1'))
        
        # Test basic connection
        client.admin.command('ping')
        print("✅ Pinged your deployment. You successfully connected to MongoDB!")
        
        # Test database operations
        db = client[DB_NAME]
        
        # Create a test collection and document
        test_collection = db.connection_test
        test_doc = {
            "test_id": "nurseprep_connection_test",
            "app_name": "NursePrep Pro",
            "message": "Production database connection successful!",
            "timestamp": datetime.now(),
            "cluster_name": "nursepreprov1",
            "status": "ready_for_production"
        }
        
        # Insert test document
        result = test_collection.insert_one(test_doc)
        print(f"✅ Test document inserted with ID: {result.inserted_id}")
        
        # Retrieve and verify
        retrieved = test_collection.find_one({"test_id": "nurseprep_connection_test"})
        if retrieved:
            print("✅ Successfully retrieved test document")
            print(f"   App: {retrieved['app_name']}")
            print(f"   Message: {retrieved['message']}")
            print(f"   Timestamp: {retrieved['timestamp']}")
        
        # Clean up
        test_collection.delete_one({"test_id": "nurseprep_connection_test"})
        print("✅ Test document cleaned up")
        
        print("\n🎉 MONGODB ATLAS SETUP IS PERFECT!")
        print("="*50)
        print(f"📝 Your connection works with cluster: nursepreprov1")
        print(f"📝 Database name for production: {DB_NAME}")
        print("📝 Username: thagoodnurse")
        print("\n✅ READY FOR VERCEL DEPLOYMENT!")
        print("="*50)
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\n🔧 Troubleshooting checklist:")
        print("1. ✅ Replace <db_password> with your ACTUAL password")
        print("2. ✅ Ensure IP whitelist includes 0.0.0.0/0")
        print("3. ✅ Wait 2-3 minutes after creating cluster") 
        print("4. ✅ Verify password doesn't contain special characters that need URL encoding")
        print("5. ✅ Double-check username is exactly: thagoodnurse")
        
        return False

if __name__ == "__main__":
    success = test_your_connection()
    if success:
        print("\n🚀 Next step: Deploy to Vercel!")
    else:
        print("\n🔄 Fix the connection issue and try again")