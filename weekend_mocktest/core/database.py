# weekend_mocktest/core/database.py
import logging
import time
import pymongo
import random
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .config import config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Production database manager with Question Bank support.
    
    Features:
    - MongoDB for summaries, test results, question bank
    - MySQL for student metadata
    - Question tracking to prevent repetition
    """
    
    def __init__(self):
        """Initialize database connections"""
        logger.info("🔗 Initializing database connections")
        self._init_mongodb()
        logger.info("✅ Database manager initialized")
    
    def _init_mongodb(self):
        """Initialize MongoDB connection with all collections"""
        try:
            self.mongo_client = pymongo.MongoClient(
                config.MONGO_CONNECTION_STRING,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                maxPoolSize=50,
                minPoolSize=5
            )
            
            # Test connection
            self.mongo_client.admin.command('ping')
            
            # Initialize database
            self.db = self.mongo_client[config.MONGO_DB_NAME]
            
            # Collections
            self.summaries_collection = self.db[config.SUMMARIES_COLLECTION]
            self.test_results_collection = self.db[config.TEST_RESULTS_COLLECTION]
            self.question_bank_collection = self.db[config.QUESTION_BANK_COLLECTION]
            self.student_history_collection = self.db[config.STUDENT_QUESTION_HISTORY_COLLECTION]
            
            # Create indexes
            self._create_indexes()
            
            # Count summaries
            summary_count = self.summaries_collection.count_documents({
                "summary": {"$exists": True, "$ne": ""}
            })
            
            # Log question bank stats
            bank_stats = self._get_question_bank_stats()
            logger.info(f"✅ MongoDB connected: {summary_count} summaries, Question Bank: {bank_stats}")
            
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise Exception(f"MongoDB initialization failed: {e}")
    
    def _create_indexes(self):
        """Create all necessary indexes"""
        try:
            # Test results indexes
            self.test_results_collection.create_index("test_id", unique=True)
            self.test_results_collection.create_index("timestamp")
            self.test_results_collection.create_index("Student_ID")
            
            # Summaries indexes
            self.summaries_collection.create_index("timestamp")
            self.summaries_collection.create_index("date")
            
            # Question bank indexes (CRITICAL for performance)
            self.question_bank_collection.create_index("question_id", unique=True)
            self.question_bank_collection.create_index("user_type")
            self.question_bank_collection.create_index("question_type")
            self.question_bank_collection.create_index("difficulty")
            self.question_bank_collection.create_index("is_active")
            self.question_bank_collection.create_index("usage_count")
            self.question_bank_collection.create_index("created_at")
            self.question_bank_collection.create_index([
                ("user_type", 1),
                ("question_type", 1),
                ("is_active", 1),
                ("usage_count", 1)
            ])
            
            # Student history indexes
            self.student_history_collection.create_index("student_id")
            self.student_history_collection.create_index("question_id")
            self.student_history_collection.create_index([
                ("student_id", 1),
                ("question_id", 1)
            ], unique=True)
            self.student_history_collection.create_index("seen_at")
            
            logger.info("📊 Database indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")

    # ================================================================
    # QUESTION BANK METHODS
    # ================================================================
    
    def add_questions_to_bank(self, questions: List[Dict[str, Any]], 
                              user_type: str, source_summary_ids: List[str] = None) -> int:
        """
        Add new questions to the question bank.
        Returns number of questions added.
        """
        logger.info(f"📥 Adding {len(questions)} questions to bank (type: {user_type})")
        
        added_count = 0
        
        for q in questions:
            try:
                # Generate unique question ID based on content
                question_hash = self._generate_question_hash(q["question"])
                question_id = f"{user_type}_{q.get('question_type', 'general')}_{question_hash}"
                
                # Check if similar question exists
                existing = self.question_bank_collection.find_one({
                    "question_id": question_id
                })
                
                if existing:
                    logger.debug(f"Question already exists: {question_id[:20]}...")
                    continue
                
                # Create question document
                question_doc = {
                    "question_id": question_id,
                    "user_type": user_type,
                    "question_type": q.get("question_type", q.get("type", "theory")).lower(),
                    "difficulty": q.get("difficulty", "Medium"),
                    "title": q.get("title", ""),
                    "question": q["question"],
                    "options": q.get("options"),  # For MCQ
                    "tags": q.get("tags", []),
                    "source_summary_ids": source_summary_ids or [],
                    "created_at": time.time(),
                    "is_active": True,
                    "usage_count": 0,
                    "last_used": None,
                    "average_score": None,
                    "feedback_summary": None
                }
                
                self.question_bank_collection.insert_one(question_doc)
                added_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to add question: {e}")
                continue
        
        logger.info(f"✅ Added {added_count}/{len(questions)} questions to bank")
        return added_count
    
    def get_unseen_questions_for_student(self, student_id: int, user_type: str,
                                          question_type: str, count: int,
                                          difficulty_mix: Dict[str, int] = None) -> List[Dict[str, Any]]:
        """
        Get questions that this student hasn't seen yet.
        
        Args:
            student_id: Student identifier
            user_type: 'dev' or 'non_dev'
            question_type: 'aptitude', 'theory', 'coding', or 'mcq'
            count: Number of questions needed
            difficulty_mix: Optional dict like {"Easy": 2, "Medium": 3, "Hard": 1}
        
        Returns:
            List of question documents
        """
        logger.info(f"🔍 Getting {count} unseen {question_type} questions for student {student_id}")
        
        try:
            # Get questions this student has already seen
            seen_question_ids = self._get_student_seen_questions(student_id)
            
            # Build query
            query = {
                "user_type": user_type,
                "question_type": question_type,
                "is_active": True,
                "question_id": {"$nin": seen_question_ids},
                "usage_count": {"$lt": config.QUESTION_MAX_USAGE}
            }
            
            questions = []
            
            if difficulty_mix:
                # Get questions by difficulty
                for difficulty, needed in difficulty_mix.items():
                    diff_query = {**query, "difficulty": difficulty}
                    diff_questions = list(
                        self.question_bank_collection.find(diff_query)
                        .sort("usage_count", 1)  # Prefer less-used questions
                        .limit(needed * 2)  # Get extra for randomization
                    )
                    
                    if len(diff_questions) >= needed:
                        selected = random.sample(diff_questions, needed)
                    else:
                        selected = diff_questions
                    
                    questions.extend(selected)
            else:
                # Get mixed difficulty
                all_questions = list(
                    self.question_bank_collection.find(query)
                    .sort("usage_count", 1)
                    .limit(count * 3)
                )
                
                if len(all_questions) >= count:
                    questions = random.sample(all_questions, count)
                else:
                    questions = all_questions
            
            # If not enough questions, include some seen questions (oldest first)
            if len(questions) < count:
                logger.warning(f"Not enough unseen questions. Found: {len(questions)}, needed: {count}")
                shortfall = count - len(questions)
                
                # Get oldest seen questions for this type
                oldest_seen = self._get_oldest_seen_questions(
                    student_id, user_type, question_type, shortfall
                )
                questions.extend(oldest_seen)
            
            logger.info(f"✅ Retrieved {len(questions)} questions")
            return questions[:count]
            
        except Exception as e:
            logger.error(f"❌ Failed to get unseen questions: {e}")
            raise
    
    def mark_questions_as_seen(self, student_id: int, question_ids: List[str]) -> bool:
        """Record that student has seen these questions"""
        logger.info(f"📝 Marking {len(question_ids)} questions as seen for student {student_id}")
        
        try:
            for qid in question_ids:
                # Add to student history
                self.student_history_collection.update_one(
                    {
                        "student_id": student_id,
                        "question_id": qid
                    },
                    {
                        "$set": {
                            "seen_at": time.time(),
                            "last_updated": time.time()
                        },
                        "$inc": {"times_seen": 1}
                    },
                    upsert=True
                )
                
                # Increment usage count in question bank
                self.question_bank_collection.update_one(
                    {"question_id": qid},
                    {
                        "$inc": {"usage_count": 1},
                        "$set": {"last_used": time.time()}
                    }
                )
            
            logger.info(f"✅ Marked questions as seen")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to mark questions: {e}")
            return False
    
    def _get_student_seen_questions(self, student_id: int) -> List[str]:
        """Get list of question IDs student has seen"""
        try:
            # Only consider questions seen within the expiry period
            expiry_time = time.time() - (config.QUESTION_EXPIRY_DAYS * 24 * 3600)
            
            seen = self.student_history_collection.find(
                {
                    "student_id": student_id,
                    "seen_at": {"$gt": expiry_time}
                },
                {"question_id": 1}
            )
            
            return [doc["question_id"] for doc in seen]
            
        except Exception as e:
            logger.warning(f"Failed to get seen questions: {e}")
            return []
    
    def _get_oldest_seen_questions(self, student_id: int, user_type: str,
                                   question_type: str, count: int) -> List[Dict[str, Any]]:
        """Get questions the student saw longest ago"""
        try:
            # Get oldest seen question IDs for this student
            oldest_seen = list(self.student_history_collection.find(
                {"student_id": student_id}
            ).sort("seen_at", 1).limit(count * 2))
            
            oldest_ids = [doc["question_id"] for doc in oldest_seen]
            
            # Fetch those questions
            questions = list(self.question_bank_collection.find({
                "question_id": {"$in": oldest_ids},
                "user_type": user_type,
                "question_type": question_type,
                "is_active": True
            }).limit(count))
            
            return questions
            
        except Exception as e:
            logger.warning(f"Failed to get oldest seen questions: {e}")
            return []
    
    def get_question_bank_stats(self, user_type: str = None) -> Dict[str, Any]:
        """Get statistics about the question bank"""
        return self._get_question_bank_stats(user_type)
    
    def _get_question_bank_stats(self, user_type: str = None) -> Dict[str, Any]:
        """Internal method to get question bank statistics"""
        try:
            query = {"is_active": True}
            if user_type:
                query["user_type"] = user_type
            
            pipeline = [
                {"$match": query},
                {"$group": {
                    "_id": {
                        "user_type": "$user_type",
                        "question_type": "$question_type"
                    },
                    "count": {"$sum": 1},
                    "avg_usage": {"$avg": "$usage_count"}
                }}
            ]
            
            results = list(self.question_bank_collection.aggregate(pipeline))
            
            stats = {
                "total": 0,
                "by_type": {},
                "by_category": {}
            }
            
            for r in results:
                user_t = r["_id"]["user_type"]
                q_type = r["_id"]["question_type"]
                count = r["count"]
                
                stats["total"] += count
                
                if user_t not in stats["by_type"]:
                    stats["by_type"][user_t] = {}
                stats["by_type"][user_t][q_type] = count
                
                if q_type not in stats["by_category"]:
                    stats["by_category"][q_type] = 0
                stats["by_category"][q_type] += count
            
            return stats
            
        except Exception as e:
            logger.warning(f"Failed to get bank stats: {e}")
            return {"total": 0, "by_type": {}, "by_category": {}}
    
    def check_bank_needs_refill(self, user_type: str) -> Dict[str, int]:
        """
        Check if question bank needs more questions.
        Returns dict of question_type -> count needed
        """
        needs = {}
        stats = self._get_question_bank_stats(user_type)
        
        type_stats = stats.get("by_type", {}).get(user_type, {})
        
        if user_type == "dev":
            aptitude_count = type_stats.get("aptitude", 0)
            theory_count = type_stats.get("theory", 0)
            coding_count = type_stats.get("coding", 0)
            
            if aptitude_count < config.MIN_BANK_APTITUDE:
                needs["aptitude"] = config.BATCH_SIZE_APTITUDE
            if theory_count < config.MIN_BANK_THEORY:
                needs["theory"] = config.BATCH_SIZE_THEORY
            if coding_count < config.MIN_BANK_CODING:
                needs["coding"] = config.BATCH_SIZE_CODING
        else:
            mcq_count = type_stats.get("mcq", 0)
            if mcq_count < config.MIN_BANK_NON_DEV:
                needs["mcq"] = config.BATCH_SIZE_NON_DEV
        
        return needs
    
    def _generate_question_hash(self, question_text: str) -> str:
        """Generate a hash for question text to detect duplicates"""
        # Normalize text
        normalized = question_text.lower().strip()
        normalized = " ".join(normalized.split())  # Normalize whitespace
        
        # Generate short hash
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def retire_overused_questions(self) -> int:
        """Retire questions that have been used too many times"""
        try:
            result = self.question_bank_collection.update_many(
                {"usage_count": {"$gte": config.QUESTION_MAX_USAGE}},
                {"$set": {"is_active": False, "retired_at": time.time()}}
            )
            
            if result.modified_count > 0:
                logger.info(f"🗑️ Retired {result.modified_count} overused questions")
            
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Failed to retire questions: {e}")
            return 0

    def clear_questions_by_type(self, user_type: str, question_type: str) -> int:
        """
        Clear (deactivate) all questions of a specific type.
        Useful for regenerating questions with updated prompts.
        
        Args:
            user_type: 'dev' or 'non_dev'
            question_type: 'aptitude', 'theory', 'coding', or 'mcq'
        
        Returns:
            Number of questions cleared
        """
        try:
            result = self.question_bank_collection.update_many(
                {
                    "user_type": user_type,
                    "question_type": question_type,
                    "is_active": True
                },
                {
                    "$set": {
                        "is_active": False,
                        "cleared_at": time.time(),
                        "clear_reason": "manual_regeneration"
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"🗑️ Cleared {result.modified_count} {question_type} questions for {user_type}")
            
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Failed to clear questions: {e}")
            return 0

    def clear_all_aptitude_questions(self) -> int:
        """Clear all aptitude questions to force regeneration with new prompts"""
        return self.clear_questions_by_type("dev", "aptitude")

    # ================================================================
    # SUMMARY METHODS (EXISTING)
    # ================================================================
    
    def get_recent_summaries(self, limit: int = None) -> List[Dict[str, Any]]:
        """Fetch recent summaries from MongoDB"""
        if limit is None:
            limit = config.RECENT_SUMMARIES_COUNT
        
        try:
            logger.info(f"📚 Fetching {limit} recent summaries")
            
            cursor = self.summaries_collection.find(
                {
                    "summary": {"$exists": True, "$ne": "", "$type": "string"},
                    "$expr": {"$gt": [{"$strLenCP": "$summary"}, 100]}
                },
                {
                    "summary": 1, 
                    "timestamp": 1, 
                    "date": 1, 
                    "session_id": 1, 
                    "_id": 1,
                    "filename": 1
                }
            ).sort("_id", pymongo.DESCENDING).limit(limit)
            
            summaries = list(cursor)
            logger.info(f"✅ Retrieved {len(summaries)} summaries")
            return summaries
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch summaries: {e}")
            return []
    
    def get_weekly_summaries(self) -> List[Dict[str, Any]]:
        """
        Fetch all summaries from the summaries collection.
        Keyword filtering is done in content_service based on user_type.
        """
        try:
            logger.info(f"📚 Fetching summaries from 'summaries' collection")
            
            cursor = self.summaries_collection.find(
                {
                    "summary": {"$exists": True, "$ne": "", "$type": "string"},
                    "$expr": {"$gt": [{"$strLenCP": "$summary"}, 100]},
                },
                {
                    "summary": 1, 
                    "timestamp": 1, 
                    "date": 1, 
                    "_id": 1,
                    "filename": 1,
                    "title": 1
                }
            ).sort("_id", pymongo.DESCENDING).limit(50)
            
            summaries = list(cursor)
            logger.info(f"📚 Retrieved {len(summaries)} summaries")
            return summaries
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch summaries: {e}")
            return []

    # ================================================================
    # TEST RESULTS METHODS (EXISTING)
    # ================================================================
    
    def save_test_results(self, test_id: str, test_data: Dict[str, Any], 
                         evaluation_result: Dict[str, Any]) -> bool:
        """Save test results to MongoDB"""
        logger.info(f"💾 Saving test results: {test_id}")
        
        try:
            student_info = self._get_student_info()
            
            score_percentage = round(
                (evaluation_result["total_correct"] / test_data["total_questions"]) * 100, 1
            )
            
            conversation_pairs = []
            for i, answer_data in enumerate(test_data.get("answers", []), 1):
                conversation_pairs.append({
                    "question_number": i,
                    "question_id": answer_data.get("question_id"),
                    "question_type": answer_data.get("question_type"),
                    "question": answer_data.get("question", ""),
                    "answer": answer_data.get("answer", ""),
                    "correct": answer_data.get("correct", False),
                    "feedback": answer_data.get("feedback", ""),
                    "time_taken": answer_data.get("time_taken")
                })
            
            document = {
                "test_id": test_id,
                "timestamp": time.time(),
                "Student_ID": student_info["student_id"],
                "name": student_info["name"],
                "session_id": student_info["session_id"],
                "user_type": test_data["user_type"],
                "score": evaluation_result["total_correct"],
                "total_questions": test_data["total_questions"],
                "score_percentage": score_percentage,
                "evaluation_report": evaluation_result["evaluation_report"],
                "conversation_pairs": conversation_pairs,
                "section_scores": test_data.get("section_scores", {}),
                "test_completed": True,
                "created_at": time.time()
            }
            
            result = self.test_results_collection.insert_one(document)
            
            if not result.inserted_id:
                raise Exception("Database insert failed")
            
            logger.info(f"✅ Test results saved: {test_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Save failed: {e}")
            raise Exception(f"Failed to save test results: {e}")
    
    def get_test_results(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get test results by ID"""
        try:
            logger.info(f"🔍 Fetching results: {test_id}")
            
            doc = self.test_results_collection.find_one(
                {"test_id": test_id}, 
                {"_id": 0}
            )
            
            if not doc:
                return None
            
            result = {
                "test_id": test_id,
                "score": doc.get("score", 0),
                "total_questions": doc.get("total_questions", 0),
                "score_percentage": doc.get("score_percentage", 0),
                "analytics": doc.get("evaluation_report", "Report not available"),
                "section_scores": doc.get("section_scores", {}),
                "timestamp": doc.get("timestamp", 0),
                "pdf_available": True
            }
            
            logger.info(f"✅ Results retrieved: {test_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to get results: {e}")
            raise Exception(f"Test results retrieval failed: {e}")
    
    def get_all_test_results(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all test results with pagination"""
        try:
            logger.info(f"📋 Fetching all test results (limit: {limit})")
            
            results = list(self.test_results_collection.find(
                {},
                {
                    "_id": 0, 
                    "test_id": 1, 
                    "name": 1, 
                    "score": 1, 
                    "total_questions": 1,
                    "score_percentage": 1, 
                    "timestamp": 1, 
                    "user_type": 1,
                    "Student_ID": 1,
                    "section_scores": 1
                }
            ).sort("timestamp", pymongo.DESCENDING).limit(limit))
            
            logger.info(f"✅ Retrieved {len(results)} test results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to get all results: {e}")
            raise Exception(f"All test results retrieval failed: {e}")
    
    def get_student_list(self) -> List[Dict[str, Any]]:
        """Get unique students from test results"""
        try:
            logger.info("👥 Fetching student list")
            
            pipeline = [
                {
                    "$group": {
                        "_id": "$Student_ID",
                        "name": {"$first": "$name"},
                        "latest_test": {"$max": "$timestamp"},
                        "test_count": {"$sum": 1}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "Student_ID": "$_id",
                        "name": 1,
                        "latest_test": 1,
                        "test_count": 1
                    }
                },
                {"$sort": {"latest_test": -1}}
            ]
            
            students = list(self.test_results_collection.aggregate(pipeline))
            
            logger.info(f"✅ Retrieved {len(students)} students")
            return students
            
        except Exception as e:
            logger.error(f"❌ Failed to get students: {e}")
            raise Exception(f"Student list retrieval failed: {e}")
    
    def get_student_tests(self, student_id: str) -> List[Dict[str, Any]]:
        """Get tests for specific student"""
        try:
            logger.info(f"📝 Fetching tests for student: {student_id}")
            
            results = list(self.test_results_collection.find(
                {"Student_ID": int(student_id)},
                {
                    "_id": 0,
                    "conversation_pairs": 0
                }
            ).sort("timestamp", pymongo.DESCENDING))
            
            logger.info(f"✅ Retrieved {len(results)} tests for student {student_id}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to get student tests: {e}")
            raise Exception(f"Student tests retrieval failed: {e}")

    # ================================================================
    # STUDENT INFO METHODS
    # ================================================================
    
    def _get_student_info(self) -> Dict[str, Any]:
        """Get student information from MySQL or generate fallback"""
        try:
            logger.info("🔍 Fetching student info from MySQL")
            
            import mysql.connector
            
            conn = mysql.connector.connect(
                user=config.DB_CONFIG['USER'],
                password=config.DB_CONFIG['PASSWORD'],
                host=config.DB_CONFIG['HOST'],
                database=config.DB_CONFIG['DATABASE'],
                port=config.DB_CONFIG['PORT'],
                connection_timeout=15
            )
            
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT ID, First_Name, Last_Name
                FROM tbl_Student 
                WHERE ID IS NOT NULL 
                  AND First_Name IS NOT NULL 
                  AND Last_Name IS NOT NULL
                ORDER BY RAND()
                LIMIT 1
            """)
            
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if result:
                student_id = result['ID']
                first_name = result['First_Name']
                last_name = result['Last_Name']
                session_id = f"session_{random.randint(100, 999)}"
                
                logger.info(f"✅ Student info from MySQL: {student_id}")
                
                return {
                    "student_id": student_id,
                    "name": f"{first_name} {last_name}",
                    "session_id": session_id
                }
            else:
                raise Exception("No valid student data found")
                
        except Exception as e:
            logger.warning(f"MySQL unavailable: {e}")
            return self._generate_fallback_student()
    
    def _generate_fallback_student(self) -> Dict[str, Any]:
        """Generate fallback student data"""
        names = [
            ("John", "Doe"), ("Jane", "Smith"), ("Alice", "Johnson"),
            ("Bob", "Wilson"), ("Carol", "Brown"), ("David", "Davis"),
            ("Emma", "Garcia"), ("Frank", "Miller"), ("Grace", "Moore"),
            ("Henry", "Taylor"), ("Ivy", "Anderson"), ("Jack", "Thomas")
        ]
        
        first_name, last_name = random.choice(names)
        student_id = random.randint(1001, 9999)
        session_id = f"session_{random.randint(100, 999)}"
        
        logger.info(f"🔧 Using fallback student: {student_id}")
        
        return {
            "student_id": student_id,
            "name": f"{first_name} {last_name}",
            "session_id": session_id
        }
    
    def validate_connection(self) -> Dict[str, Any]:
        """Validate database connections"""
        status = {
            "mongodb": False,
            "sql_server": False,
            "summaries_available": False,
            "question_bank": False,
            "overall": False
        }
        
        try:
            self.mongo_client.admin.command('ping')
            status["mongodb"] = True
            
            count = self.summaries_collection.count_documents({}, limit=1)
            status["summaries_available"] = count > 0
            
            bank_stats = self._get_question_bank_stats()
            status["question_bank"] = bank_stats.get("total", 0) > 0
            
            logger.info("✅ MongoDB validation passed")
            
        except Exception as e:
            logger.error(f"❌ MongoDB validation failed: {e}")
        
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                user=config.DB_CONFIG['USER'],
                password=config.DB_CONFIG['PASSWORD'],
                host=config.DB_CONFIG['HOST'],
                database=config.DB_CONFIG['DATABASE'],
                port=config.DB_CONFIG['PORT'],
                connection_timeout=10
            )
            conn.close()
            status["sql_server"] = True
            logger.info("✅ MySQL validation passed")
            
        except Exception as e:
            logger.warning(f"⚠️ MySQL validation failed: {e}")
        
        status["overall"] = status["mongodb"] and status["summaries_available"]
        
        return status
    
    def close(self):
        """Close database connections"""
        try:
            if hasattr(self, 'mongo_client'):
                self.mongo_client.close()
            logger.info("✅ Database connections closed")
        except Exception as e:
            logger.warning(f"Close connection warning: {e}")


# Singleton instance
_db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get database manager singleton"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

def close_db_manager():
    """Close database manager"""
    global _db_manager
    if _db_manager:
        _db_manager.close()
        _db_manager = None