"""
Database management module for Daily Standup application
Handles MongoDB and SQL Server connections and operations - REAL CONNECTIONS ONLY
"""

import os
import time
import logging
import asyncio
import mysql.connector
from mysql.connector import errorcode
from typing import Tuple, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import quote_plus
from .config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Optimized database management with real connections only"""
    
    def __init__(self, client_manager):
        self.client_manager = client_manager
        self._mongo_client = None
        self._mongo_db = None
        
    @property
    def mysql_config(self) -> Dict[str, Any]:
        """Get MySQL configuration from environment variables"""
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
        """Get MongoDB configuration from environment variables"""
        return {
            "username": config.MONGODB_USERNAME,
            "password": config.MONGODB_PASSWORD,
            "host": config.MONGODB_HOST,
            "port": config.MONGODB_PORT,
            "database": config.MONGODB_DATABASE,
            "auth_source": config.MONGODB_AUTH_SOURCE
        }
    
    async def get_mongo_client(self) -> AsyncIOMotorClient:
        """Get MongoDB client with connection pooling"""
        if self._mongo_client is None:
            mongo_cfg = self.mongo_config
            
            # Use same URI pattern as your check_mongo.py
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
                logger.info("? MongoDB client initialized and tested")
            except Exception as e:
                logger.error(f"? MongoDB connection failed: {e}")
                self._mongo_client = None
                raise Exception(f"MongoDB connection failed: {e}")
                
        return self._mongo_client
    
    async def get_mongo_db(self):
        """Get MongoDB database instance"""
        if self._mongo_db is None:
            client = await self.get_mongo_client()
            self._mongo_db = client[self.mongo_config["database"]]
        return self._mongo_db
    
    def get_mysql_connection(self):
        """Get MySQL connection using environment configuration"""
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
                logger.error("? MySQL: Wrong username or password")
                raise Exception("MySQL authentication failed")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                logger.error(f"? MySQL: Database '{db_config['NAME']}' does not exist")
                raise Exception(f"MySQL database '{db_config['NAME']}' not found")
            else:
                logger.error(f"? MySQL connection error: {err}")
                raise Exception(f"MySQL connection failed: {err}")
        except Exception as e:
            logger.error(f"? MySQL connection failed: {e}")
            raise Exception(f"MySQL connection failed: {e}")
    
    async def get_student_info_fast(self) -> Tuple[int, str, str, str]:
        """Fast student info retrieval from MySQL"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.client_manager.executor,
            self._sync_get_student_info
        )
    
    def _sync_get_student_info(self) -> Tuple[int, str, str, str]:
        """Synchronous student info retrieval using real MySQL connection"""
        try:
            conn = self.get_mysql_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Use same query pattern as your check_sql.py but get random student
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
            session_key = f"SESSION_{int(time.time())}"
            
            logger.info(f"? Retrieved student: {first_name} {last_name} (ID: {student_id})")
            return (student_id, first_name, last_name, session_key)
            
        except Exception as e:
            logger.error(f"? Error fetching student info: {e}")
            raise Exception(f"Student info retrieval failed: {e}")
    
    async def get_summary_fast(self) -> str:
        """Fast summary retrieval from MongoDB"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.client_manager.executor,
                self._sync_get_summary
            )
        except Exception as e:
            logger.error(f"? Error fetching summary: {e}")
            raise Exception(f"Summary retrieval failed: {e}")
    
    def _sync_get_summary(self) -> str:
        """Synchronous summary retrieval from MongoDB summaries collection"""
        try:
            # Use pymongo (sync) instead of motor (async) for thread pool execution
            from pymongo import MongoClient
            
            mongo_cfg = self.mongo_config
            username = quote_plus(mongo_cfg['username'])
            password = quote_plus(mongo_cfg['password'])
            mongo_uri = f"mongodb://{username}:{password}@{mongo_cfg['host']}:{mongo_cfg['port']}/{mongo_cfg['auth_source']}"
            
            # Synchronous MongoDB client for thread execution
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            db = client[mongo_cfg['database']]
            collection = db[config.SUMMARIES_COLLECTION]
            
            # Get latest summary similar to your check_mongo.py
            doc = collection.find_one(
                {"summary": {"$exists": True, "$ne": None, "$ne": ""}},
                sort=[("_id", -1)]  # Latest by insertion order
            )
            
            client.close()
            
            if not doc or not doc.get("summary"):
                raise Exception("No valid summary found in MongoDB summaries collection")
                
            summary = doc["summary"].strip()
            if len(summary) < 100:
                raise Exception(f"Summary too short ({len(summary)} chars): {summary}")
            
            logger.info(f"? Retrieved summary: {len(summary)} characters")
            return summary
            
        except Exception as e:
            logger.error(f"? Sync summary retrieval error: {e}")
            raise Exception(f"MongoDB summary retrieval failed: {e}")
    
    async def save_session_result_fast(self, session_data, evaluation: str, score: float) -> bool:
        """Fast session result saving to MongoDB"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.client_manager.executor,
                self._sync_save_result,
                session_data, evaluation, score
            )
        except Exception as e:
            logger.error(f"? Error saving session result: {e}")
            raise Exception(f"Session save failed: {e}")
    
    def _sync_save_result(self, session_data, evaluation: str, score: float) -> bool:
        """Synchronous save for thread pool with enhanced fragment analytics"""
        try:
            # Use pymongo (sync) instead of motor (async) for thread pool execution
            from pymongo import MongoClient
            
            mongo_cfg = self.mongo_config
            username = quote_plus(mongo_cfg['username'])
            password = quote_plus(mongo_cfg['password'])
            mongo_uri = f"mongodb://{username}:{password}@{mongo_cfg['host']}:{mongo_cfg['port']}/{mongo_cfg['auth_source']}"
            
            # Synchronous MongoDB client for thread execution
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            db = client[mongo_cfg['database']]
            collection = db[config.RESULTS_COLLECTION]
            
            # Enhanced fragment analytics
            fragment_manager = session_data.summary_manager
            progress_info = fragment_manager.get_progress_info() if fragment_manager else {}
            
            document = {
                "test_id": session_data.test_id,
                "session_id": session_data.session_id,
                "student_id": session_data.student_id,
                "student_name": session_data.student_name,
                "session_key": session_data.session_key,
                "timestamp": time.time(),
                "created_at": session_data.created_at,
                "conversation_log": [
                    {
                        "timestamp": exchange.timestamp,
                        "stage": exchange.stage.value,
                        "ai_message": exchange.ai_message,
                        "user_response": exchange.user_response,
                        "transcript_quality": exchange.transcript_quality,
                        "concept": exchange.concept,
                        "is_followup": exchange.is_followup
                    }
                    for exchange in session_data.exchanges
                ],
                "evaluation": evaluation,
                "score": score,
                "total_exchanges": len(session_data.exchanges),
                "greeting_exchanges": session_data.greeting_count,
                
                # Enhanced fragment analytics
                "fragment_analytics": {
                    "total_concepts": len(session_data.fragment_keys),
                    "concepts_covered": list(session_data.concept_question_counts.keys()),
                    "questions_per_concept": dict(session_data.concept_question_counts),
                    "followup_questions": session_data.followup_questions,
                    "main_questions": session_data.question_index,
                    "target_questions_per_concept": session_data.questions_per_concept,
                    "coverage_percentage": round(
                        (len([c for c, count in session_data.concept_question_counts.items() if count > 0]) 
                         / len(session_data.fragment_keys) * 100) 
                        if session_data.fragment_keys else 0, 1
                    )
                },
                
                "duration": time.time() - session_data.created_at
            }
            
            result = collection.insert_one(document)
            client.close()
            
            logger.info(f"? Session {session_data.session_id} saved with fragment analytics")
            return True
            
        except Exception as e:
            logger.error(f"? Sync save error: {e}")
            raise Exception(f"MongoDB save failed: {e}")
    
    async def get_session_result_fast(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Fast session result retrieval"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.client_manager.executor,
                self._sync_get_session_result,
                session_id
            )
        except Exception as e:
            logger.error(f"? Error fetching session result: {e}")
            raise Exception(f"Session result retrieval failed: {e}")
    
    def _sync_get_session_result(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous session result retrieval"""
        try:
            # Use pymongo (sync) instead of motor (async) for thread pool execution
            from pymongo import MongoClient
            
            mongo_cfg = self.mongo_config
            username = quote_plus(mongo_cfg['username'])
            password = quote_plus(mongo_cfg['password'])
            mongo_uri = f"mongodb://{username}:{password}@{mongo_cfg['host']}:{mongo_cfg['port']}/{mongo_cfg['auth_source']}"
            
            # Synchronous MongoDB client for thread execution
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            db = client[mongo_cfg['database']]
            collection = db[config.RESULTS_COLLECTION]
            
            result = collection.find_one({"session_id": session_id})
            client.close()
            
            if result:
                result['_id'] = str(result['_id'])
                logger.info(f"? Retrieved session result for {session_id}")
                return result
            
            logger.warning(f"?? No session result found for {session_id}")
            return None
            
        except Exception as e:
            logger.error(f"? Sync session result error: {e}")
            raise Exception(f"Session result retrieval failed: {e}")
    
    async def close_connections(self):
        """Cleanup method for graceful shutdown"""
        if self._mongo_client:
            self._mongo_client.close()
        logger.info("?? Database connections closed")