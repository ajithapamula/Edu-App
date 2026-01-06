# weekend_mocktest/core/database.py
# FIXED: Auto collection routing + No question repetition for large scale
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
    - Auto collection routing: dev → Developer, non_dev → Non-Developer
    - Question tracking to prevent repetition (large scale)
    - Question Bank for reusable questions
    """
    
    def __init__(self):
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
            
            self.mongo_client.admin.command('ping')
            self.db = self.mongo_client[config.MONGO_DB_NAME]
            
            # Content Collections - AUTO ROUTING
            self.developer_collection = self.db["Developer"]
            self.non_developer_collection = self.db["Non-Developer"]
            
            # System Collections
            self.test_results_collection = self.db[config.TEST_RESULTS_COLLECTION]
            self.question_bank_collection = self.db[config.QUESTION_BANK_COLLECTION]
            self.student_history_collection = self.db[config.STUDENT_QUESTION_HISTORY_COLLECTION]
            
            self._create_indexes()
            
            # Log collection stats
            dev_count = self.developer_collection.count_documents({"summary": {"$exists": True, "$ne": ""}})
            non_dev_count = self.non_developer_collection.count_documents({"summary": {"$exists": True, "$ne": ""}})
            
            logger.info(f"✅ MongoDB connected:")
            logger.info(f"   - Developer collection: {dev_count} summaries")
            logger.info(f"   - Non-Developer collection: {non_dev_count} summaries")
            
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise
    
    def _create_indexes(self):
        """Create indexes for performance"""
        try:
            # Question bank indexes
            self.question_bank_collection.create_index([("user_type", 1), ("question_type", 1)])
            self.question_bank_collection.create_index([("question_hash", 1)], unique=True, sparse=True)
            self.question_bank_collection.create_index([("usage_count", 1)])
            self.question_bank_collection.create_index([("created_at", -1)])
            
            # Student history index - for preventing repetition
            self.student_history_collection.create_index([("student_id", 1)])
            self.student_history_collection.create_index([("student_id", 1), ("question_id", 1)], unique=True)
            self.student_history_collection.create_index([("seen_at", -1)])
            
            # Test results
            self.test_results_collection.create_index([("test_id", 1)], unique=True)
            self.test_results_collection.create_index([("student_id", 1), ("created_at", -1)])
            
            logger.info("✅ Database indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")

    # ================================================================
    # AUTO COLLECTION ROUTING
    # ================================================================
    
    def get_summaries_by_user_type(self, user_type: str) -> List[Dict[str, Any]]:
        """
        AUTO ROUTING: Fetch from correct collection based on user_type
        
        dev → Developer collection
        non_dev → Non-Developer collection
        """
        try:
            # AUTO ROUTE to correct collection
            if user_type == "dev":
                collection = self.developer_collection
                collection_name = "Developer"
            else:
                collection = self.non_developer_collection
                collection_name = "Non-Developer"
            
            logger.info(f"🔄 AUTO ROUTING: {user_type} → '{collection_name}' collection")
            
            # ONLY fetch 'summary' field - ignore filename, transcript_text
            cursor = collection.find(
                {
                    "summary": {"$exists": True, "$ne": "", "$type": "string"},
                    "$expr": {"$gt": [{"$strLenCP": "$summary"}, 100]}
                },
                {"summary": 1, "_id": 1}  # ONLY summary field!
            ).sort("_id", pymongo.DESCENDING).limit(50)
            
            summaries = list(cursor)
            logger.info(f"📄 Found {len(summaries)} summaries in '{collection_name}'")
            
            # Log preview of first summary
            if summaries:
                preview = summaries[0].get("summary", "")[:100]
                logger.info(f"📝 Sample: {preview}...")
            
            return summaries
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch summaries: {e}")
            return []
    
    def get_weekly_summaries(self, user_type: str = None) -> List[Dict[str, Any]]:
        """Get summaries - routes to correct collection if user_type provided"""
        if user_type:
            return self.get_summaries_by_user_type(user_type)
        return []

    # ================================================================
    # QUESTION BANK - NO REPETITION FOR LARGE SCALE
    # ================================================================
    
    def get_questions_from_bank(self, user_type: str, question_type: str, 
                                count: int, student_id: int = None) -> List[Dict[str, Any]]:
        """
        Get questions from bank, EXCLUDING ones the student has already seen.
        For large scale - prevents repetition across all users.
        """
        try:
            # Get question IDs this student has already seen
            seen_question_ids = set()
            if student_id:
                seen_docs = self.student_history_collection.find(
                    {"student_id": student_id},
                    {"question_id": 1}
                )
                seen_question_ids = {doc["question_id"] for doc in seen_docs}
                logger.info(f"📊 Student {student_id} has seen {len(seen_question_ids)} questions")
            
            # Query for questions NOT seen by this student
            query = {
                "user_type": user_type,
                "question_type": question_type,
                "active": {"$ne": False}
            }
            
            # Exclude seen questions
            if seen_question_ids:
                query["question_id"] = {"$nin": list(seen_question_ids)}
            
            # Get questions sorted by usage_count (prefer less used)
            cursor = self.question_bank_collection.find(query).sort([
                ("usage_count", 1),  # Least used first
                ("created_at", -1)   # Newer questions preferred
            ]).limit(count * 2)  # Get extra in case some are filtered
            
            questions = list(cursor)
            
            if len(questions) < count:
                logger.warning(f"⚠️ Only {len(questions)} unused questions available (need {count})")
                # If not enough, include some seen questions (better than nothing)
                if len(questions) < count:
                    remaining = count - len(questions)
                    seen_cursor = self.question_bank_collection.find({
                        "user_type": user_type,
                        "question_type": question_type,
                        "active": {"$ne": False},
                        "question_id": {"$in": list(seen_question_ids)}
                    }).sort("usage_count", 1).limit(remaining)
                    questions.extend(list(seen_cursor))
            
            # Shuffle and take required count
            random.shuffle(questions)
            selected = questions[:count]
            
            # Increment usage count for selected questions
            if selected:
                selected_ids = [q["question_id"] for q in selected if q.get("question_id")]
                if selected_ids:
                    self.question_bank_collection.update_many(
                        {"question_id": {"$in": selected_ids}},
                        {"$inc": {"usage_count": 1}}
                    )
            
            logger.info(f"✅ Retrieved {len(selected)} {question_type} questions for {user_type}")
            return selected
            
        except Exception as e:
            logger.error(f"❌ Failed to get questions from bank: {e}")
            return []
    
    def add_questions_to_bank(self, questions: List[Dict[str, Any]], user_type: str) -> int:
        """Add new questions to bank with deduplication"""
        added = 0
        for q in questions:
            try:
                # Create unique hash for deduplication
                question_text = q.get("question", "")
                question_hash = hashlib.md5(question_text.encode()).hexdigest()
                
                # Check if already exists
                existing = self.question_bank_collection.find_one({"question_hash": question_hash})
                if existing:
                    continue
                
                # Add new question
                question_id = str(uuid.uuid4())
                doc = {
                    "question_id": question_id,
                    "question_hash": question_hash,
                    "user_type": user_type,
                    "question_type": q.get("question_type", "mcq"),
                    "question": question_text,
                    "title": q.get("title", "Question"),
                    "difficulty": q.get("difficulty", "Medium"),
                    "options": q.get("options"),
                    "correct_answer": q.get("correct_answer"),
                    "correct_option_text": q.get("correct_option_text"),
                    "usage_count": 0,
                    "active": True,
                    "created_at": datetime.utcnow()
                }
                
                self.question_bank_collection.insert_one(doc)
                added += 1
                
            except pymongo.errors.DuplicateKeyError:
                continue
            except Exception as e:
                logger.warning(f"Failed to add question: {e}")
        
        logger.info(f"📦 Added {added} new questions to bank")
        return added
    
    def mark_questions_as_seen(self, student_id: int, question_ids: List[str]):
        """Mark questions as seen by student - prevents repetition"""
        try:
            if not student_id or not question_ids:
                return
            
            for qid in question_ids:
                try:
                    self.student_history_collection.update_one(
                        {"student_id": student_id, "question_id": qid},
                        {
                            "$set": {"seen_at": datetime.utcnow()},
                            "$inc": {"times_seen": 1}
                        },
                        upsert=True
                    )
                except pymongo.errors.DuplicateKeyError:
                    pass
            
            logger.info(f"📝 Marked {len(question_ids)} questions as seen for student {student_id}")
            
        except Exception as e:
            logger.error(f"Failed to mark questions as seen: {e}")
    
    def check_bank_needs_refill(self, user_type: str) -> Dict[str, int]:
        """Check if question bank needs more questions"""
        needs = {}
        
        question_types = ["aptitude", "mcq"]
        if user_type == "dev":
            question_types.append("coding")
        
        for q_type in question_types:
            count = self.question_bank_collection.count_documents({
                "user_type": user_type,
                "question_type": q_type,
                "active": {"$ne": False},
                "usage_count": {"$lt": config.QUESTION_MAX_USAGE}
            })
            
            min_required = getattr(config, f"MIN_BANK_{q_type.upper()}", 50)
            if count < min_required:
                batch_size = getattr(config, f"BATCH_SIZE_{q_type.upper()}", 20)
                needs[q_type] = batch_size
        
        return needs
    
    def get_question_bank_stats(self) -> Dict[str, Any]:
        """Get question bank statistics"""
        try:
            stats = {}
            for user_type in ["dev", "non_dev"]:
                question_types = ["aptitude", "mcq"]
                if user_type == "dev":
                    question_types.append("coding")
                
                user_stats = {}
                for q_type in question_types:
                    count = self.question_bank_collection.count_documents({
                        "user_type": user_type,
                        "question_type": q_type,
                        "active": {"$ne": False}
                    })
                    user_stats[q_type] = count
                
                stats[user_type] = user_stats
            
            return stats
        except Exception as e:
            return {"error": str(e)}
    
    def retire_overused_questions(self):
        """Retire questions that have been used too many times"""
        try:
            result = self.question_bank_collection.update_many(
                {"usage_count": {"$gte": config.QUESTION_MAX_USAGE}},
                {"$set": {"active": False, "retired_at": datetime.utcnow()}}
            )
            if result.modified_count > 0:
                logger.info(f"🔄 Retired {result.modified_count} overused questions")
        except Exception as e:
            logger.error(f"Failed to retire questions: {e}")

    # ================================================================
    # TEST RESULTS
    # ================================================================
    
    def save_test_results(self, test_id: str, test_data: Dict[str, Any], 
                         evaluation_result: Dict[str, Any]):
        """Save test results to database"""
        try:
            doc = {
                "test_id": test_id,
                "user_type": test_data.get("user_type"),
                "student_id": test_data.get("student_id"),
                "total_questions": test_data.get("total_questions"),
                "total_correct": evaluation_result.get("total_correct", 0),
                "percentage": evaluation_result.get("percentage", 0),
                "section_scores": evaluation_result.get("section_scores", {}),
                "answers": test_data.get("answers", []),
                "evaluation_report": evaluation_result.get("evaluation_report", ""),
                "terminated": evaluation_result.get("terminated", False),
                "termination_reason": evaluation_result.get("termination_reason"),
                "created_at": datetime.utcnow()
            }
            
            self.test_results_collection.update_one(
                {"test_id": test_id},
                {"$set": doc},
                upsert=True
            )
            
            logger.info(f"💾 Saved test results: {test_id}")
            
        except Exception as e:
            logger.error(f"Failed to save test results: {e}")
    
    def _get_student_info(self) -> Dict[str, Any]:
        """Get current student info (placeholder)"""
        return {"student_id": random.randint(1000, 9999)}


# Singleton
_db_manager = None

def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager

def close_db_manager():
    """Close database connections"""
    global _db_manager
    if _db_manager is not None:
        try:
            if hasattr(_db_manager, 'mongo_client'):
                _db_manager.mongo_client.close()
                logger.info("🔌 MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")
        _db_manager = None