# weekend_mocktest/core/database.py
import logging
import time
import pymongo
import pyodbc
import random
from typing import List, Dict, Any, Optional
from .config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Production database manager with real connections"""
    
    def __init__(self):
        """Initialize database connections"""
        logger.info("🔗 Initializing database connections")
        
        # Initialize MongoDB (primary database)
        self._init_mongodb()
        
        # Initialize MySQL connection (updated for MySQL)
        logger.info("✅ Database manager initialized")
    
    def _init_mongodb(self):
        """Initialize MongoDB connection"""
        try:
            # Create MongoDB client with working connection string
            self.mongo_client = pymongo.MongoClient(
                config.MONGO_CONNECTION_STRING,
                serverSelectionTimeoutMS=10000,
                connectTimeoutMS=10000,
                maxPoolSize=50,
                minPoolSize=5
            )
            
            # Test connection
            self.mongo_client.admin.command('ping')
            
            # Initialize collections with correct database
            self.db = self.mongo_client[config.MONGO_DB_NAME]  # ml_notes
            self.summaries_collection = self.db[config.SUMMARIES_COLLECTION]  # summaries
            self.test_results_collection = self.db[config.TEST_RESULTS_COLLECTION]
            
            # Create performance indexes
            self._create_indexes()
            
            # Verify data availability
            summary_count = self.summaries_collection.count_documents({
                "summary": {"$exists": True, "$ne": ""}
            })
            
            if summary_count == 0:
                raise Exception("No summaries found in database")
            
            logger.info(f"✅ MongoDB connected: {summary_count} summaries available")
            
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            raise Exception(f"MongoDB initialization failed: {e}")
    
    def _create_indexes(self):
        """Create database indexes for performance"""
        try:
            # Test results indexes
            self.test_results_collection.create_index("test_id", unique=True)
            self.test_results_collection.create_index("timestamp")
            self.test_results_collection.create_index("Student_ID")
            
            # Summaries indexes
            self.summaries_collection.create_index("timestamp")
            self.summaries_collection.create_index("date")
            
            logger.info("📊 Database indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    def get_recent_summaries(self, limit: int = None) -> List[Dict[str, Any]]:
        """Fetch recent summaries from MongoDB"""
        if limit is None:
            limit = config.RECENT_SUMMARIES_COUNT
        
        try:
            logger.info(f"📚 Fetching {limit} recent summaries")
            
            # Query with proper filtering and sorting
            cursor = self.summaries_collection.find(
                {
                    "summary": {"$exists": True, "$ne": "", "$type": "string"},
                    "$expr": {"$gt": [{"$strLenCP": "$summary"}, 100]}  # Minimum length
                },
                {
                    "summary": 1, 
                    "timestamp": 1, 
                    "date": 1, 
                    "session_id": 1, 
                    "_id": 1
                }
            ).sort("_id", pymongo.DESCENDING).limit(limit)
            
            summaries = list(cursor)
            
            if not summaries:
                raise Exception("No valid summaries found in database")
            
            # Log sample for verification
            if summaries:
                first_summary = summaries[0]["summary"]
                sample_length = min(len(first_summary), 150)
                logger.info(f"📄 Sample summary ({sample_length} chars): {first_summary[:sample_length]}...")
            
            logger.info(f"✅ Retrieved {len(summaries)} summaries")
            return summaries
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch summaries: {e}")
            raise Exception(f"Summary retrieval failed: {e}")
    
    def save_test_results(self, test_id: str, test_data: Dict[str, Any], 
                         evaluation_result: Dict[str, Any]) -> bool:
        """Save test results to MongoDB"""
        logger.info(f"💾 Saving test results: {test_id}")
        
        try:
            # Get student information
            student_info = self._get_student_info()
            
            # Calculate score percentage
            score_percentage = round(
                (evaluation_result["total_correct"] / test_data["total_questions"]) * 100, 1
            )
            
            # Create conversation pairs
            conversation_pairs = []
            for i, answer_data in enumerate(test_data.get("answers", []), 1):
                conversation_pairs.append({
                    "question_number": i,
                    "question": answer_data.get("question", ""),
                    "answer": answer_data.get("answer", ""),
                    "correct": answer_data.get("correct", False),
                    "feedback": answer_data.get("feedback", "")
                })
            
            # Create document
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
                "test_completed": True,
                "created_at": time.time()
            }
            
            # Insert into MongoDB
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
                    "Student_ID": 1
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
                        "latest_test": {"$max": "$timestamp"}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "Student_ID": "$_id",
                        "name": 1,
                        "latest_test": 1
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
                    "conversation_pairs": 0  # Exclude large fields
                }
            ).sort("timestamp", pymongo.DESCENDING))
            
            logger.info(f"✅ Retrieved {len(results)} tests for student {student_id}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Failed to get student tests: {e}")
            raise Exception(f"Student tests retrieval failed: {e}")
    
    def _get_student_info(self) -> Dict[str, Any]:
        """Get student information from MySQL or generate fallback"""
        try:
            # Try MySQL first (updated connection)
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
            
            # Get random student
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
            # Generate realistic fallback data
            return self._generate_fallback_student()
    
    def _generate_fallback_student(self) -> Dict[str, Any]:
        """Generate fallback student data when SQL Server is unavailable"""
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
            "overall": False
        }
        
        try:
            # Test MongoDB
            self.mongo_client.admin.command('ping')
            status["mongodb"] = True
            
            # Test summaries collection
            count = self.summaries_collection.count_documents({}, limit=1)
            status["summaries_available"] = count > 0
            
            logger.info("✅ MongoDB validation passed")
            
        except Exception as e:
            logger.error(f"❌ MongoDB validation failed: {e}")
        
        try:
            # Test MySQL
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
        
        # Overall status - MongoDB is critical
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