#!/usr/bin/env python3
"""
MongoDB Atlas Connection Test Script
Run this to verify your MongoDB Atlas setup works
"""

import os
from pymongo import MongoClient
from datetime import datetime

def test_mongodb_connection():
    # Replace this with your actual MongoDB Atlas connection string
    MONGO_URL = input("Paste your MongoDB Atlas connection string here: ").strip()
    DB_NAME = "nurseprep_prod"
    
    try:
        print("🔄 Connecting to MongoDB Atlas...")
        client = MongoClient(MONGO_URL)
        
        # Test connection
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")
        
        # Test database access
        db = client[DB_NAME]
        
        # Insert a test document
        test_collection = db.connection_test
        test_doc = {
            "test_id": "connection_test_1",
            "message": "NursePrep Pro MongoDB connection successful!",
            "timestamp": datetime.now(),
            "status": "success"
        }
        
        result = test_collection.insert_one(test_doc)
        print(f"✅ Test document inserted with ID: {result.inserted_id}")
        
        # Retrieve the test document
        retrieved = test_collection.find_one({"test_id": "connection_test_1"})
        if retrieved:
            print("✅ Successfully retrieved test document")
            print(f"   Message: {retrieved['message']}")
        
        # Clean up test document
        test_collection.delete_one({"test_id": "connection_test_1"})
        print("✅ Test document cleaned up")
        
        print("\n🎉 MongoDB Atlas setup is PERFECT!")
        print(f"📝 Your connection string: {MONGO_URL}")
        print(f"📝 Your database name: {DB_NAME}")
        print("\n✅ Ready for Vercel deployment!")
        
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Double-check your password in the connection string")
        print("2. Ensure you added 0.0.0.0/0 to IP whitelist")
        print("3. Wait a few minutes for cluster to fully deploy")
        print("4. Make sure you replaced <password> with actual password")

if __name__ == "__main__":
    test_mongodb_connection()