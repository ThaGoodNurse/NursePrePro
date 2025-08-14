import requests
import sys
import json
from datetime import datetime
import time

class NursePrepAPITester:
    def __init__(self, base_url="https://ad26c181-45a9-4cac-bd86-b5e22309edce.preview.emergentagent.com"):
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
        print(f"   URL: {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, params=params)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text[:200]}")
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

    def test_study_areas(self):
        """Test study areas endpoints"""
        print("\n📚 Testing Study Areas...")
        
        # Get study areas
        success, response = self.run_test(
            "Get Study Areas",
            "GET",
            "api/study-areas",
            200
        )
        
        if success and 'study_areas' in response:
            self.study_areas = response['study_areas']
            print(f"   Found {len(self.study_areas)} study areas")
            
            # Test creating a new study area
            new_area_data = {
                "name": "Test Study Area",
                "description": "A test study area for API testing",
                "color": "#FF5733"
            }
            
            create_success, create_response = self.run_test(
                "Create Study Area",
                "POST",
                "api/study-areas",
                200,
                data=new_area_data
            )
            
            return success and create_success
        
        return success

    def test_questions(self):
        """Test questions endpoints"""
        print("\n❓ Testing Questions...")
        
        if not self.study_areas:
            print("❌ No study areas available for testing questions")
            return False
        
        area_id = self.study_areas[0]['id']
        
        # Get questions for an area
        success, response = self.run_test(
            "Get Questions by Area",
            "GET",
            f"api/study-areas/{area_id}/questions",
            200,
            params={"limit": 10}
        )
        
        if success and 'questions' in response:
            self.sample_questions = response['questions']
            print(f"   Found {len(self.sample_questions)} questions")
        
        # Test creating a new question
        new_question_data = {
            "question_text": "What is the normal heart rate range for adults?",
            "question_type": "multiple_choice",
            "options": [
                "40-60 bpm",
                "60-100 bpm", 
                "100-120 bpm",
                "120-140 bpm"
            ],
            "correct_answer_index": 1,
            "explanation": "Normal adult heart rate is 60-100 beats per minute at rest.",
            "difficulty": "easy",
            "cognitive_level": "knowledge",
            "nclex_category": "physiological_integrity",
            "area_id": area_id
        }
        
        create_success, create_response = self.run_test(
            "Create Question",
            "POST",
            "api/questions",
            200,
            data=new_question_data
        )
        
        return success and create_success

    def test_flashcard_sets(self):
        """Test flashcard sets endpoints"""
        print("\n🃏 Testing Flashcard Sets...")
        
        # Get flashcard sets
        success, response = self.run_test(
            "Get Flashcard Sets",
            "GET",
            "api/flashcard-sets",
            200
        )
        
        if success and 'flashcard_sets' in response:
            self.flashcard_sets = response['flashcard_sets']
            print(f"   Found {len(self.flashcard_sets)} flashcard sets")
        
        # Test creating a new flashcard set
        new_set_data = {
            "name": "Test Medical Terms",
            "description": "Test flashcard set for API testing",
            "category": "Medical Terminology",
            "color": "#4CAF50",
            "spaced_repetition_enabled": True
        }
        
        create_success, create_response = self.run_test(
            "Create Flashcard Set",
            "POST",
            "api/flashcard-sets",
            200,
            data=new_set_data
        )
        
        return success and create_success

    def test_flashcards(self):
        """Test flashcards endpoints"""
        print("\n📇 Testing Flashcards...")
        
        if not self.flashcard_sets:
            print("❌ No flashcard sets available for testing flashcards")
            return False
        
        set_id = self.flashcard_sets[0]['id']
        
        # Get flashcards for a set
        success, response = self.run_test(
            "Get Flashcards by Set",
            "GET",
            f"api/flashcard-sets/{set_id}/flashcards",
            200,
            params={"limit": 20}
        )
        
        if success and 'flashcards' in response:
            self.sample_flashcards = response['flashcards']
            print(f"   Found {len(self.sample_flashcards)} flashcards")
        
        # Test creating a new flashcard
        new_flashcard_data = {
            "term": "Tachypnea",
            "definition": "Rapid breathing, typically over 20 breaths per minute",
            "pronunciation": "tak-ip-NEE-ah",
            "word_type": "term",
            "category": "Respiratory",
            "examples": ["The patient exhibited tachypnea during the anxiety attack"],
            "set_id": set_id,
            "difficulty": "medium"
        }
        
        create_success, create_response = self.run_test(
            "Create Flashcard",
            "POST",
            "api/flashcards",
            200,
            data=new_flashcard_data
        )
        
        return success and create_success

    def test_spaced_repetition(self):
        """Test spaced repetition functionality"""
        print("\n🧠 Testing Spaced Repetition...")
        
        if not self.flashcard_sets:
            print("❌ No flashcard sets available for testing spaced repetition")
            return False
        
        set_id = self.flashcard_sets[0]['id']
        
        # Test due cards count
        due_success, due_response = self.run_test(
            "Get Due Cards Count",
            "GET",
            f"api/flashcards/{set_id}/due-count",
            200
        )
        
        if due_success:
            print(f"   Due cards: {due_response.get('due_count', 0)}")
            print(f"   Total cards: {due_response.get('total_count', 0)}")
        
        # Test starting spaced repetition study
        study_success, study_response = self.run_test(
            "Start Spaced Repetition Study",
            "POST",
            "api/flashcards/study-spaced",
            200,
            params={"set_id": set_id, "max_cards": 5}
        )
        
        if study_success and 'session_id' in study_response:
            session_id = study_response['session_id']
            flashcards = study_response.get('flashcards', [])
            
            if flashcards:
                # Test reviewing a flashcard with spaced repetition
                card_id = flashcards[0]['id']
                review_data = {
                    "card_id": card_id,
                    "quality": 4,  # Good recall
                    "response_time": 3.5
                }
                
                review_success, review_response = self.run_test(
                    "Review Flashcard (Spaced Repetition)",
                    "POST",
                    f"api/flashcards/study/{session_id}/review-spaced",
                    200,
                    data=review_data
                )
                
                if review_success:
                    print(f"   Next review in: {review_response.get('next_review_in_days', 0)} days")
                    print(f"   Success rate: {review_response.get('success_rate', 0):.2f}")
                
                return due_success and study_success and review_success
        
        return due_success and study_success

    def test_advanced_quiz(self):
        """Test advanced quiz functionality"""
        print("\n🎯 Testing Advanced Quiz System...")
        
        if not self.study_areas:
            print("❌ No study areas available for testing quiz")
            return False
        
        area_id = self.study_areas[0]['id']
        
        # Test different quiz types
        quiz_types = [
            {
                "name": "Practice Quiz",
                "settings": {
                    "area_id": area_id,
                    "quiz_type": "practice",
                    "question_count": 5,
                    "difficulty_level": "medium"
                }
            },
            {
                "name": "Adaptive Quiz",
                "settings": {
                    "area_id": area_id,
                    "quiz_type": "adaptive",
                    "question_count": 5,
                    "difficulty_level": "adaptive"
                }
            },
            {
                "name": "Timed Quiz",
                "settings": {
                    "area_id": area_id,
                    "quiz_type": "timed",
                    "question_count": 3,
                    "time_limit": 5  # 5 minutes
                }
            },
            {
                "name": "NCLEX Simulation",
                "settings": {
                    "quiz_type": "nclex_simulation",
                    "question_count": 4,
                    "time_limit": 10,
                    "nclex_categories": ["physiological_integrity", "safe_effective_care"]
                }
            }
        ]
        
        all_success = True
        
        for quiz_config in quiz_types:
            print(f"\n   Testing {quiz_config['name']}...")
            
            # Start quiz
            start_success, start_response = self.run_test(
                f"Start {quiz_config['name']}",
                "POST",
                "api/quiz/start-advanced",
                200,
                data=quiz_config['settings']
            )
            
            if start_success and 'quiz_id' in start_response:
                quiz_id = start_response['quiz_id']
                questions = start_response.get('questions', [])
                
                print(f"     Quiz ID: {quiz_id}")
                print(f"     Questions: {len(questions)}")
                print(f"     Quiz Type: {start_response.get('quiz_type')}")
                print(f"     Time Limit: {start_response.get('time_limit')} seconds")
                
                if questions:
                    # Prepare sample answers
                    answers = []
                    for question in questions:
                        if question.get('question_type') == 'multiple_response':
                            # Select first two options for multiple response
                            selected_ids = [opt['id'] for opt in question['options'][:2]]
                            answers.append({
                                "question_id": question['id'],
                                "selected_option_ids": selected_ids,
                                "time_spent": 2000  # 2 seconds
                            })
                        else:
                            # Select first option for single choice
                            answers.append({
                                "question_id": question['id'],
                                "selected_option_id": question['options'][0]['id'],
                                "time_spent": 3000  # 3 seconds
                            })
                    
                    # Submit quiz
                    submit_success, submit_response = self.run_test(
                        f"Submit {quiz_config['name']}",
                        "POST",
                        f"api/quiz/{quiz_id}/submit-advanced",
                        200,
                        data=answers,
                        params={"time_taken": 60}  # 1 minute
                    )
                    
                    if submit_success:
                        print(f"     Score: {submit_response.get('score', 0)}%")
                        print(f"     Correct: {submit_response.get('correct_answers', 0)}/{submit_response.get('total_questions', 0)}")
                        print(f"     Passed: {submit_response.get('passed', False)}")
                        
                        # Check NCLEX performance if available
                        nclex_perf = submit_response.get('nclex_performance', {})
                        if nclex_perf:
                            print(f"     NCLEX Categories: {len(nclex_perf)}")
                    
                    all_success = all_success and start_success and submit_success
                else:
                    print(f"     ❌ No questions returned for {quiz_config['name']}")
                    all_success = False
            else:
                print(f"     ❌ Failed to start {quiz_config['name']}")
                all_success = False
        
        return all_success

    def test_statistics(self):
        """Test statistics endpoints"""
        print("\n📊 Testing Statistics...")
        
        # Test user stats
        user_stats_success, user_stats_response = self.run_test(
            "Get User Stats",
            "GET",
            "api/stats",
            200
        )
        
        if user_stats_success:
            print(f"   Total quizzes: {user_stats_response.get('total_quizzes', 0)}")
            print(f"   Average score: {user_stats_response.get('average_score', 0)}%")
        
        # Test flashcard stats
        flashcard_stats_success, flashcard_stats_response = self.run_test(
            "Get Flashcard Stats",
            "GET",
            "api/flashcards/stats",
            200
        )
        
        if flashcard_stats_success:
            print(f"   Total sessions: {flashcard_stats_response.get('total_sessions', 0)}")
            print(f"   Cards studied: {flashcard_stats_response.get('total_cards_studied', 0)}")
            print(f"   Average accuracy: {flashcard_stats_response.get('average_accuracy', 0)}%")
        
        return user_stats_success and flashcard_stats_success

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting NursePrep API Tests...")
        print(f"Base URL: {self.base_url}")
        
        test_results = []
        
        # Run all test categories
        test_results.append(("Root Endpoint", self.test_root_endpoint()))
        test_results.append(("Study Areas", self.test_study_areas()))
        test_results.append(("Questions", self.test_questions()))
        test_results.append(("Flashcard Sets", self.test_flashcard_sets()))
        test_results.append(("Flashcards", self.test_flashcards()))
        test_results.append(("Spaced Repetition", self.test_spaced_repetition()))
        test_results.append(("Advanced Quiz System", self.test_advanced_quiz()))
        test_results.append(("Statistics", self.test_statistics()))
        
        # Print summary
        print("\n" + "="*60)
        print("📋 TEST SUMMARY")
        print("="*60)
        
        for test_name, success in test_results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{test_name:<25} {status}")
        
        passed_categories = sum(1 for _, success in test_results if success)
        total_categories = len(test_results)
        
        print(f"\n📊 Overall Results:")
        print(f"   Test Categories: {passed_categories}/{total_categories} passed")
        print(f"   Individual Tests: {self.tests_passed}/{self.tests_run} passed")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if passed_categories == total_categories:
            print("\n🎉 All test categories passed! Backend is ready for frontend testing.")
            return 0
        else:
            print(f"\n⚠️  {total_categories - passed_categories} test categories failed. Review backend implementation.")
            return 1

def main():
    tester = NursePrepAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())