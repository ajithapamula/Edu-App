"""
Unified Database Management Module
==================================

This merges the three previous database.py implementations from:
- daily_standup
- weekend_mocktest
- weekly_interview

Handles:
- MySQL connections
- MongoDB connections (async + sync)
- Summaries, test results, interview results, session results

Each method retains its original name and behavior to avoid breaking imports.
"""

import os
import time
import random
import logging
import asyncio
from typing import Tuple, Optional, Dict, Any, List
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import errorcode
from motor.motor_asyncio import AsyncIOMotorClient
from urllib.parse import quote_plus

import pymongo
from pymongo import MongoClient

from .config import config

logger = logging.getLogger(__name__)

# =====================================================


# ============================================================================
# CORE CLASS
# ============================================================================
class DatabaseManager:
    """Unified Database Manager supporting Daily Standup, Mock Tests, and Weekly Interviews."""

    def __init__(self, client_manager=None):
        self.client_manager = client_manager
        self._mongo_client = None
        self._mongo_db = None

        # weekend_mocktest style mongo client
        self.mongo_client = None
        self.db = None
        self.summaries_collection = None
        self.test_results_collection = None

    # ------------------------------------------------------------------------
    # CONFIGURATION PROPERTIES
    # ------------------------------------------------------------------------
    @property
    def mysql_config(self) -> Dict[str, Any]:
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
        return {
            "username": config.MONGODB_USERNAME,
            "password": config.MONGODB_PASSWORD,
            "host": config.MONGODB_HOST,
            "port": config.MONGODB_PORT,
            "database": config.MONGODB_DATABASE,
            "auth_source": config.MONGODB_AUTH_SOURCE,
        }

    # ------------------------------------------------------------------------
    # MYSQL CONNECTION
    # ------------------------------------------------------------------------
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

    # ------------------------------------------------------------------------
    # ASYNC MONGO CONNECTION (used by daily_standup + weekly_interview)
    # ------------------------------------------------------------------------
    async def get_mongo_client(self) -> AsyncIOMotorClient:
        """Get MongoDB client with connection pooling"""
        if self._mongo_client is None:
            mongo_cfg = self.mongo_config
            username = quote_plus(mongo_cfg['username'])
            password = quote_plus(mongo_cfg['password'])
            mongo_uri = f"mongodb://{username}:{password}@{mongo_cfg['host']}:{mongo_cfg['port']}/{mongo_cfg['auth_source']}"

            self._mongo_client = AsyncIOMotorClient(
                mongo_uri,
                maxPoolSize=config.MONGO_MAX_POOL_SIZE,
                serverSelectionTimeoutMS=config.MONGO_SERVER_SELECTION_TIMEOUT
            )

            try:
                await self._mongo_client.admin.command('ping')
                logger.info("✅ MongoDB client initialized and tested")
            except Exception as e:
                logger.error(f"❌ MongoDB connection failed: {e}")
                self._mongo_client = None
                raise Exception(f"MongoDB connection failed: {e}")

        return self._mongo_client

    async def get_mongo_db(self):
        """Get MongoDB database instance"""
        if self._mongo_db is None:
            client = await self.get_mongo_client()
            self._mongo_db = client[self.mongo_config["database"]]
        return self._mongo_db

    # ------------------------------------------------------------------------
    # DAILY_STANDUP SPECIFIC
    # ------------------------------------------------------------------------
    async def get_student_info_fast(self) -> Tuple[int, str, str, str]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.client_manager.executor,
            self._sync_get_student_info
        )

    def _sync_get_student_info(self) -> Tuple[int, str, str, str]:
        try:
            conn = self.get_mysql_connection()
            cursor = conn.cursor(dictionary=True)
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

            session_key = f"SESSION_{int(time.time())}"
            return (row['ID'], row['First_Name'], row['Last_Name'], session_key)

        except Exception as e:
            logger.error(f"❌ Error fetching student info: {e}")
            raise

    async def get_summary_fast(self) -> str:
        """Fetch summary from MongoDB (daily_standup style)"""
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.client_manager.executor,
                self._sync_get_summary
            )
        except Exception as e:
            raise

    def _sync_get_summary(self) -> str:
        mongo_cfg = self.mongo_config
        username = quote_plus(mongo_cfg['username'])
        password = quote_plus(mongo_cfg['password'])
        mongo_uri = f"mongodb://{username}:{password}@{mongo_cfg['host']}:{mongo_cfg['port']}/{mongo_cfg['auth_source']}"

        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        db = client[mongo_cfg['database']]
        collection = db[config.SUMMARIES_COLLECTION]
        doc = collection.find_one(
            {"summary": {"$exists": True, "$ne": None, "$ne": ""}},
            sort=[("_id", -1)]
        )
        client.close()

        if not doc or not doc.get("summary"):
            raise Exception("No valid summary found")
        return doc["summary"].strip()

    # ------------------------------------------------------------------------
    # WEEKEND MOCKTEST SPECIFIC
    # ------------------------------------------------------------------------
    def _init_mongodb_weekend(self):
        """Initialize MongoDB (weekend mocktest style)"""
        self.mongo_client = pymongo.MongoClient(
            config.MONGO_CONNECTION_STRING,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
            maxPoolSize=50,
            minPoolSize=5
        )
        self.db = self.mongo_client[config.MONGO_DB_NAME]
        self.summaries_collection = self.db[config.SUMMARIES_COLLECTION]
        self.test_results_collection = self.db[config.TEST_RESULTS_COLLECTION]

    def get_recent_summaries(self, limit: int = None) -> List[Dict[str, Any]]:
        """Fetch recent summaries (weekend_mocktest)"""
        if not self.summaries_collection:
            self._init_mongodb_weekend()
        if limit is None:
            limit = config.RECENT_SUMMARIES_COUNT
        cursor = self.summaries_collection.find(
            {"summary": {"$exists": True, "$ne": "", "$type": "string"}},
            {"summary": 1, "timestamp": 1, "date": 1}
        ).sort("_id", pymongo.DESCENDING).limit(limit)
        return list(cursor)

    def save_test_results(self, test_id: str, test_data: Dict[str, Any], evaluation_result: Dict[str, Any]) -> bool:
        if not self.test_results_collection:
            self._init_mongodb_weekend()
        doc = {
            "test_id": test_id,
            "timestamp": time.time(),
            "evaluation_report": evaluation_result.get("evaluation_report", ""),
            "total_questions": test_data.get("total_questions"),
            "score": evaluation_result.get("total_correct", 0),
        }
        result = self.test_results_collection.insert_one(doc)
        return bool(result.inserted_id)

    # ------------------------------------------------------------------------
    # WEEKLY INTERVIEW SPECIFIC
    # ------------------------------------------------------------------------
    async def get_recent_summaries_fast(self, days: int = None, limit: int = None) -> List[Dict[str, Any]]:
        """Weekly Interview: fetch recent summaries with 7-day filter"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.client_manager.executor,
            self._sync_get_recent_summaries,
            days or config.RECENT_SUMMARIES_DAYS,
            limit or config.SUMMARIES_LIMIT
        )

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


    # ------------------------------------------------------------------------
    # COMMON UTILITIES
    # ------------------------------------------------------------------------
    async def close_connections(self):
        if self._mongo_client:
            self._mongo_client.close()
        if self.mongo_client:
            self.mongo_client.close()
        logger.info("🔌 Database connections closed")


# ============================================================================
# SINGLETON HELPERS (weekend_mocktest style)
# ============================================================================
_db_manager = None


def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def close_db_manager():
    global _db_manager
    if _db_manager:
        _db_manager.close_connections()
        _db_manager = None
