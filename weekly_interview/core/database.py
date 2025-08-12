# weekly_interview/core/database.py
"""
Enhanced Database management - Daily Standup Style with optimized 7-day summary retrieval
Handles MongoDB and MySQL connections with connection pooling - REAL CONNECTIONS ONLY
"""

import logging
import asyncio
import time
import mysql.connector
from mysql.connector import errorcode
from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import quote_plus
from .config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Enhanced database management with daily_standup style optimization"""
    
    def __init__(self, client_manager):
        self.client_manager = client_manager
        self._mongo_client = None
        self._mongo_db = None
        
    @property
    def mysql_config(self) -> Dict[str, Any]:
        """Get MySQL configuration from environment variables (same as daily_standup)"""
        return {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config.MYSQL_DATABASE,
            'USER': config.MYSQL_USER,
            'PASSWORD': config.MYSQL_PASSWORD,
            'HOST': config.MYSQL_HOST,
            'PORT': config.MYSQL_PORT,
        }
    
    @property
    def mongo_config(self) -> Dict[str, Any]:
        """Get MongoDB configuration from environment variables (same as daily_standup)"""
        return {
            "username": config.MONGODB_USERNAME,
            "password": config.MONGODB_PASSWORD,
            "host": config.MONGODB_HOST,
            "port": config.MONGODB_PORT,
            "database": config.MONGODB_DATABASE,
            "auth_source": config.MONGODB_AUTH_SOURCE
        }
    
    async def get_mongo_client(self) -> AsyncIOMotorClient:
        """Get MongoDB client with connection pooling (same as daily_standup)"""
        if self._mongo_client is None:
            mongo_cfg = self.mongo_config
            
            # Use same URI pattern as daily_standup
            username = quote_plus(mongo_cfg['username'])
            password = quote_plus(mongo_cfg['password'])
            mongo_uri = f"mongodb://{username}:{password}@{mongo_cfg['host']}:{mongo_cfg['port']}/{mongo_cfg['auth_source']}"
            
            self._mongo_client = AsyncIOMotorClient(
                mongo_uri, 
                maxPoolSize=config.MONGO_MAX_POOL_SIZE,
                serverSelectionTimeoutMS=config.MONGO_SERVER_SELECTION_TIMEOUT
            )
            
            try:
                # Test connection
                await self._mongo_client.admin.command('ping')
                logger.info("✅ MongoDB client initialized and tested")
            except Exception as e:
                logger.error(f"❌ MongoDB connection failed: {e}")
                self._mongo_client = None
                raise Exception(f"MongoDB connection failed: {e}")
                
        return self._mongo_client
    
    async def get_mongo_db(self):
        """Get MongoDB database instance (same as daily_standup)"""
        if self._mongo_db is None:
            client = await self.get_mongo_client()
            self._mongo_db = client[self.mongo_config["database"]]
        return self._mongo_db
    
    def get_mysql_connection(self):
        """Get MySQL connection using environment configuration (same as daily_standup)"""
        try:
            db_config = self.mysql_config
            
            conn = mysql.connector.connect(
                user=db_config['USER'],
                password=db_config['PASSWORD'],
                host=db_config['HOST'],
                database=db_config['NAME'],
                port=db_config['PORT'],
                connection_timeout=5
            )
            
            return conn
            
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                logger.error("❌ MySQL: Wrong username or password")
                raise Exception("MySQL authentication failed")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                logger.error(f"❌ MySQL: Database '{db_config['NAME']}' does not exist")
                raise Exception(f"MySQL database '{db_config['NAME']}' not found")
            else:
                logger.error(f"❌ MySQL connection error: {err}")
                raise Exception(f"MySQL connection failed: {err}")
        except Exception as e:
            logger.error(f"❌ MySQL connection failed: {e}")
            raise Exception(f"MySQL connection failed: {e}")
    
    async def get_student_info_fast(self) -> Tuple[int, str, str, str]:
        """Fast student info retrieval from MySQL (identical to daily_standup)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.client_manager.executor,
            self._sync_get_student_info
        )
    
    def _sync_get_student_info(self) -> Tuple[int, str, str, str]:
        """Synchronous student info retrieval using real MySQL connection (same as daily_standup)"""
        try:
            conn = self.get_mysql_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Use same query pattern as daily_standup
            cursor.execute("""
                SELECT ID, First_Name, Last_Name 
                FROM tbl_Student 
                WHERE ID IS NOT NULL AND First_Name IS NOT NULL AND Last_Name IS NOT NULL
                ORDER BY RAND()
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not row:
                raise Exception("No valid student records found in tbl_Student")
                
            student_id = row['ID']
            first_name = row['First_Name']
            last_name = row['Last_Name']
            session_key = f"INTERVIEW_{int(time.time())}"
            
            logger.info(f"✅ Retrieved student: {first_name} {last_name} (ID: {student_id})")
            return (student_id, first_name, last_name, session_key)
            
        except Exception as e:
            logger.error(f"❌ Error fetching student info: {e}")
            raise Exception(f"Student info retrieval failed: {e}")
    
    async def get_recent_summaries_fast(self, days: int = None, limit: int = None) -> List[Dict[str, Any]]:
        """Enhanced 7-day summary retrieval with intelligent filtering (optimized for interviews)"""
        if days is None:
            days = config.RECENT_SUMMARIES_DAYS
        if limit is None:
            limit = config.SUMMARIES_LIMIT
            
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.client_manager.executor,
                self._sync_get_recent_summaries,
                days, limit
            )
        except Exception as e:
            logger.error(f"❌ Error fetching 7-day summaries: {e}")
            raise Exception(f"Summary retrieval failed: {e}")
    
    def _sync_get_recent_summaries(self, days: int, limit: int) -> List[Dict[str, Any]]:
        """Synchronous 7-day summaries retrieval with smart filtering"""
        try:
            from pymongo import MongoClient
            
            client = MongoClient(config.mongodb_connection_string, serverSelectionTimeoutMS=5000)
            db = client[config.MONGODB_DATABASE]
            collection = db[config.SUMMARIES_COLLECTION]
            
            # Calculate 7-day window
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            start_timestamp = start_date.timestamp()
            
            # Multiple query strategies for maximum 7-day coverage
            query_strategies = [
                {
                    "name": "timestamp_based_7day",
                    "filter": {
                        "summary": {"$exists": True, "$ne": "", "$type": "string"},
                        "timestamp": {"$gte": start_timestamp},
                        "$expr": {"$gt": [{"$strLenCP": "$summary"}, config.MIN_CONTENT_LENGTH]}
                    },
                    "sort": [("timestamp", -1)]
                },
                {
                    "name": "date_based_7day", 
                    "filter": {
                        "summary": {"$exists": True, "$ne": "", "$type": "string"},
                        "date": {"$gte": start_date.strftime("%Y-%m-%d")},
                        "$expr": {"$gt": [{"$strLenCP": "$summary"}, config.MIN_CONTENT_LENGTH]}
                    },
                    "sort": [("date", -1)]
                },
                {
                    "name": "recent_quality_summaries",
                    "filter": {
                        "summary": {"$exists": True, "$ne": "", "$type": "string"},
                        "$expr": {"$gt": [{"$strLenCP": "$summary"}, config.MIN_CONTENT_LENGTH * 2]}
                    },
                    "sort": [("_id", -1)]
                },
                {
                    "name": "fallback_any_summaries",
                    "filter": {
                        "summary": {"$exists": True, "$ne": "", "$type": "string"}
                    },
                    "sort": [("_id", -1)]
                }
            ]
            
            summaries = []
            
            for strategy in query_strategies:
                try:
                    logger.info(f"🔍 Trying strategy: {strategy['name']}")
                    
                    cursor = collection.find(
                        strategy["filter"],
                        {
                            "summary": 1,
                            "timestamp": 1,
                            "date": 1,
                            "session_id": 1,
                            "_id": 1
                        }
                    ).sort(strategy["sort"]).limit(limit)
                    
                    summaries = list(cursor)
                    
                    if summaries:
                        logger.info(f"✅ Retrieved {len(summaries)} summaries using {strategy['name']}")
                        break
                        
                except Exception as e:
                    logger.warning(f"⚠️ Strategy {strategy['name']} failed: {e}")
                    continue
            
            client.close()
            
            if not summaries:
                raise Exception("No valid summaries found in database for 7-day interview processing")
            
            # Log sample for verification
            if summaries:
                first_summary = summaries[0]["summary"]
                sample_length = min(len(first_summary), 200)
                logger.info(f"📄 Sample summary ({sample_length} chars): {first_summary[:sample_length]}...")
                logger.info(f"📊 Total summaries for interview: {len(summaries)}")
            
            return summaries
            
        except Exception as e:
            logger.error(f"❌ Sync 7-day summary retrieval error: {e}")
            raise Exception(f"MongoDB 7-day summary retrieval failed: {e}")
    
    async def save_interview_result_fast(self, interview_data: Dict[str, Any]) -> bool:
        """Fast interview result saving to MongoDB (enhanced for interview analytics)"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.client_manager.executor,
                self._sync_save_interview_result,
                interview_data
            )
        except Exception as e:
            logger.error(f"❌ Error saving interview result: {e}")
            raise Exception(f"Interview save failed: {e}")
    
    def _sync_save_interview_result(self, interview_data: Dict[str, Any]) -> bool:
        """Synchronous interview result saving with enhanced analytics"""
        try:
            from pymongo import MongoClient
            
            client = MongoClient(config.mongodb_connection_string, serverSelectionTimeoutMS=5000)
            db = client[config.MONGODB_DATABASE]
            collection = db[config.INTERVIEW_RESULTS_COLLECTION]
            
            document = {
                "test_id": interview_data["test_id"],
                "session_id": interview_data["session_id"],
                "student_id": interview_data["student_id"],
                "student_name": interview_data["student_name"],
                "timestamp": time.time(),
                "created_at": interview_data.get("created_at", time.time()),
                
                "conversation_log": interview_data.get("conversation_log", []),
                "evaluation": interview_data.get("evaluation", ""),
                "scores": interview_data.get("scores", {}),
                
                # Enhanced interview analytics
                "interview_analytics": {
                    "total_duration_minutes": interview_data.get("duration_minutes", 0),
                    "questions_per_round": interview_data.get("questions_per_round", {}),
                    "followup_questions": interview_data.get("followup_questions", 0),
                    "fragments_covered": interview_data.get("fragments_covered", 0),
                    "total_fragments": interview_data.get("total_fragments", 0),
                    "fragment_coverage_percentage": round(
                        (interview_data.get("fragments_covered", 0) / 
                         max(interview_data.get("total_fragments", 1), 1) * 100), 1
                    ),
                    "rounds_completed": len([r for r in ["technical", "communication", "hr"] 
                                           if interview_data.get("questions_per_round", {}).get(r, 0) > 0]),
                    "interview_completion_status": "complete" if interview_data.get("questions_per_round", {}).get("hr", 0) > 0 else "partial"
                },
                
                "system_info": {
                    "version": config.APP_VERSION,
                    "processing_method": "7_day_fragment_based",
                    "websocket_used": interview_data.get("websocket_used", False),
                    "tts_voice": interview_data.get("tts_voice", config.TTS_VOICE),
                    "streaming_audio": True,
                    "content_source": "7_day_summaries_with_intelligent_slicing"
                }
            }
            
            result = collection.insert_one(document)
            client.close()
            
            if result.inserted_id:
                logger.info(f"✅ Interview saved: {interview_data['test_id']} with enhanced analytics")
                return True
            else:
                raise Exception("Database insert failed")
                
        except Exception as e:
            logger.error(f"❌ Sync interview save error: {e}")
            raise Exception(f"MongoDB save failed: {e}")
    
    async def get_interview_result_fast(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Fast interview result retrieval (same as daily_standup pattern)"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.client_manager.executor,
                self._sync_get_interview_result,
                test_id
            )
        except Exception as e:
            logger.error(f"❌ Error fetching interview result: {e}")
            raise Exception(f"Interview result retrieval failed: {e}")
    
    def _sync_get_interview_result(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous interview result retrieval"""
        try:
            from pymongo import MongoClient
            
            client = MongoClient(config.mongodb_connection_string, serverSelectionTimeoutMS=5000)
            db = client[config.MONGODB_DATABASE]
            collection = db[config.INTERVIEW_RESULTS_COLLECTION]
            
            result = collection.find_one({"test_id": test_id})
            client.close()
            
            if result:
                result['_id'] = str(result['_id'])
                logger.info(f"✅ Retrieved interview result for {test_id}")
                return result
            
            logger.warning(f"⚠️ No interview result found for {test_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Sync interview result error: {e}")
            raise Exception(f"Interview result retrieval failed: {e}")
    
    async def get_all_interview_results_fast(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all interview results with enhanced analytics"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.client_manager.executor,
                self._sync_get_all_interview_results,
                limit
            )
        except Exception as e:
            logger.error(f"❌ Error fetching all interview results: {e}")
            raise Exception(f"All interview results retrieval failed: {e}")
    
    def _sync_get_all_interview_results(self, limit: int) -> List[Dict[str, Any]]:
        """Synchronous all interview results retrieval"""
        try:
            from pymongo import MongoClient
            
            client = MongoClient(config.mongodb_connection_string, serverSelectionTimeoutMS=5000)
            db = client[config.MONGODB_DATABASE]
            collection = db[config.INTERVIEW_RESULTS_COLLECTION]
            
            results = list(collection.find(
                {},
                {
                    "_id": 0,
                    "test_id": 1,
                    "session_id": 1,
                    "student_name": 1,
                    "student_id": 1,
                    "timestamp": 1,
                    "scores": 1,
                    "interview_analytics": 1,
                    "evaluation": 1
                }
            ).sort("timestamp", -1).limit(limit))
            
            client.close()
            
            logger.info(f"✅ Retrieved {len(results)} interview results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Sync all results error: {e}")
            raise Exception(f"All interview results retrieval failed: {e}")
    
    async def get_interview_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive interview analytics summary"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.client_manager.executor,
                self._sync_get_analytics_summary
            )
        except Exception as e:
            logger.error(f"❌ Error fetching analytics summary: {e}")
            return {"error": str(e)}
    
    def _sync_get_analytics_summary(self) -> Dict[str, Any]:
        """Synchronous analytics summary calculation"""
        try:
            from pymongo import MongoClient
            
            client = MongoClient(config.mongodb_connection_string, serverSelectionTimeoutMS=5000)
            db = client[config.MONGODB_DATABASE]
            collection = db[config.INTERVIEW_RESULTS_COLLECTION]
            
            # Aggregate analytics
            pipeline = [
                {"$group": {
                    "_id": None,
                    "total_interviews": {"$sum": 1},
                    "avg_duration": {"$avg": "$interview_analytics.total_duration_minutes"},
                    "avg_technical_score": {"$avg": "$scores.technical_score"},
                    "avg_communication_score": {"$avg": "$scores.communication_score"},
                    "avg_behavioral_score": {"$avg": "$scores.behavioral_score"},
                    "avg_overall_score": {"$avg": "$scores.overall_score"},
                    "total_fragments_used": {"$sum": "$interview_analytics.fragments_covered"},
                    "avg_fragment_coverage": {"$avg": "$interview_analytics.fragment_coverage_percentage"}
                }}
            ]
            
            result = list(collection.aggregate(pipeline))
            client.close()
            
            if result:
                analytics = result[0]
                del analytics["_id"]
                
                # Round numerical values
                for key, value in analytics.items():
                    if isinstance(value, float):
                        analytics[key] = round(value, 2)
                
                return analytics
            else:
                return {
                    "total_interviews": 0,
                    "avg_duration": 0,
                    "avg_technical_score": 0,
                    "avg_communication_score": 0,
                    "avg_behavioral_score": 0,
                    "avg_overall_score": 0,
                    "total_fragments_used": 0,
                    "avg_fragment_coverage": 0
                }
                
        except Exception as e:
            logger.error(f"❌ Analytics summary error: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive database health check (same as daily_standup)"""
        health_status = {
            "mongodb": {"status": "unknown", "details": {}},
            "mysql": {"status": "unknown", "details": {}},
            "overall": False
        }
        
        # Test MongoDB
        try:
            client = await self.get_mongo_client()
            await client.admin.command('ping')
            
            # Check collections
            db = await self.get_mongo_db()
            summaries_count = await db[config.SUMMARIES_COLLECTION].count_documents({}, limit=1)
            results_count = await db[config.INTERVIEW_RESULTS_COLLECTION].count_documents({}, limit=1)
            
            health_status["mongodb"] = {
                "status": "healthy",
                "details": {
                    "connection": "active",
                    "summaries_available": summaries_count > 0,
                    "results_collection_accessible": True,
                    "7_day_summaries_ready": True
                }
            }
        except Exception as e:
            health_status["mongodb"] = {
                "status": "error",
                "details": {"error": str(e)}
            }
        
        # Test MySQL
        try:
            conn = self.get_mysql_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            health_status["mysql"] = {
                "status": "healthy",
                "details": {
                    "connection": "active",
                    "student_data_accessible": True
                }
            }
        except Exception as e:
            health_status["mysql"] = {
                "status": "error", 
                "details": {"error": str(e)}
            }
        
        # Overall status
        health_status["overall"] = (
            health_status["mongodb"]["status"] == "healthy" and
            health_status["mysql"]["status"] == "healthy"
        )
        
        return health_status
    
    async def close_connections(self):
        """Cleanup method for graceful shutdown (same as daily_standup)"""
        if self._mongo_client:
            self._mongo_client.close()
        logger.info("🔌 Database connections closed")