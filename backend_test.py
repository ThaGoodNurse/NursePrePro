import requests
import sys
import json
from datetime import datetime
import time

class NursePrepAPITester:
    def __init__(self, base_url="https://nurseprep-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.study_areas = []
        self.flashcard_sets = []
        self.sample_questions = []
        self.sample_flashcards = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)

            print(f"   Status Code: {response.status_code}")
            
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root endpoint"""
        success, response = self.run_test(
            "Root Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_get_study_areas(self):
        """Test getting study areas"""
        success, response = self.run_test(
            "Get Study Areas",
            "GET",
            "api/study-areas",
            200
        )
        if success and 'study_areas' in response:
            self.study_areas = response['study_areas']
            print(f"   Found {len(self.study_areas)} study areas")
            for area in self.study_areas:
                print(f"   - {area['name']}: {area['question_count']} questions")
        return success

    def test_get_stats(self):
        """Test getting user statistics"""
        success, response = self.run_test(
            "Get User Stats",
            "GET",
            "api/stats",
            200
        )
        if success:
            print(f"   Total Quizzes: {response.get('total_quizzes', 0)}")
            print(f"   Average Score: {response.get('average_score', 0)}%")
        return success

    def test_start_quiz(self):
        """Test starting a quiz"""
        if not self.study_areas:
            print("❌ No study areas available for quiz test")
            return False
        
        # Find an area with questions
        area_with_questions = None
        for area in self.study_areas:
            if area['question_count'] > 0:
                area_with_questions = area
                break
        
        if not area_with_questions:
            print("❌ No study areas with questions available")
            return False

        success, response = self.run_test(
            "Start Quiz",
            "POST",
            "api/quiz/start",
            200,
            params={"area_id": area_with_questions['id'], "question_count": 2}
        )
        
        if success and 'quiz_id' in response:
            self.quiz_id = response['quiz_id']
            print(f"   Quiz ID: {self.quiz_id}")
            print(f"   Questions: {len(response.get('questions', []))}")
            return True
        return False

    def test_submit_quiz(self):
        """Test submitting quiz answers"""
        if not self.quiz_id:
            print("❌ No quiz ID available for submission test")
            return False

        # Get quiz questions first to create answers
        success, quiz_response = self.run_test(
            "Get Quiz for Submission",
            "POST",
            "api/quiz/start",
            200,
            params={"area_id": self.study_areas[0]['id'], "question_count": 2}
        )
        
        if not success or 'questions' not in quiz_response:
            print("❌ Could not get quiz questions for submission")
            return False

        # Create sample answers (select first option for each question)
        questions = quiz_response['questions']
        answers = []
        for question in questions:
            if question['options']:
                answers.append({
                    "question_id": question['id'],
                    "selected_option_id": question['options'][0]['id']
                })

        success, response = self.run_test(
            "Submit Quiz",
            "POST",
            f"api/quiz/{quiz_response['quiz_id']}/submit",
            200,
            data=answers
        )
        
        if success:
            print(f"   Score: {response.get('score', 0)}%")
            print(f"   Correct: {response.get('correct_answers', 0)}/{response.get('total_questions', 0)}")
        return success

    def test_get_questions_by_area(self):
        """Test getting questions for a specific area"""
        if not self.study_areas:
            print("❌ No study areas available for questions test")
            return False
        
        # Find an area with questions
        area_with_questions = None
        for area in self.study_areas:
            if area['question_count'] > 0:
                area_with_questions = area
                break
        
        if not area_with_questions:
            print("❌ No study areas with questions available")
            return False

        success, response = self.run_test(
            "Get Questions by Area",
            "GET",
            f"api/study-areas/{area_with_questions['id']}/questions",
            200,
            params={"limit": 5}
        )
        
        if success and 'questions' in response:
            print(f"   Found {len(response['questions'])} questions")
        return success

def main():
    print("🚀 Starting NursePrep API Tests")
    print("=" * 50)
    
    # Setup
    tester = NursePrepAPITester()
    
    # Run all tests
    tests = [
        tester.test_root_endpoint,
        tester.test_get_study_areas,
        tester.test_get_stats,
        tester.test_get_questions_by_area,
        tester.test_start_quiz,
        tester.test_submit_quiz,
    ]
    
    for test in tests:
        test()
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())