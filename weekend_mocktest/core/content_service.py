# weekend_mocktest/core/content_service.py
# Auto routes: dev→Developer collection, non_dev→Non-Developer collection
# ONLY uses 'summary' field (ignores filename, transcript_text)
import logging
import re
from typing import List, Dict, Any
from .config import config
from .database import get_db_manager

logger = logging.getLogger(__name__)


class ContentService:
    """
    Content service for question generation context.
    
    AUTO ROUTING:
    - user_type='dev' → Developer collection
    - user_type='non_dev' → Non-Developer collection
    
    IMPORTANT: Only uses 'summary' field from MongoDB.
    Ignores 'filename' and 'transcript_text' to avoid mixed content.
    """

    def __init__(self):
        self.db_manager = get_db_manager()
        logger.info("📚 ContentService initialized")

    def get_context_for_questions(self, user_type: str = "dev") -> str:
        """
        Get context for question generation.
        
        AUTO ROUTES to correct collection:
        - 'dev' → Developer collection
        - 'non_dev' → Non-Developer collection
        
        ONLY uses 'summary' field!
        """
        try:
            collection_name = "Developer" if user_type == "dev" else "Non-Developer"
            logger.info(f"🔄 AUTO ROUTING: {user_type} → '{collection_name}' collection")
            logger.info(f"⚠️ Using ONLY 'summary' field (ignoring filename, transcript_text)")

            # Get summaries (auto-routed by database manager)
            summaries = self.db_manager.get_weekly_summaries(user_type)

            if not summaries:
                raise Exception(f"No summaries found in '{collection_name}' collection")

            logger.info(f"✅ Found {len(summaries)} documents in '{collection_name}'")

            context_blocks = []
            for idx, doc in enumerate(summaries, 1):
                # ONLY use 'summary' field - ignore everything else!
                summary_text = doc.get("summary", "")
                
                if not summary_text or len(summary_text) < 100:
                    continue

                # Clean the summary
                processed = self._clean_text(summary_text)
                if not processed or len(processed) < 80:
                    continue

                # Log preview
                preview = summary_text[:80].replace('\n', ' ')
                logger.info(f"  📄 Doc {idx}: {preview}...")
                
                context_blocks.append(f"=== Content {idx} ===\n{processed}")

            if not context_blocks:
                raise Exception(f"No valid summaries in '{collection_name}'")

            # Build final context
            context = f"""COURSE CONTENT FROM {collection_name.upper()} COLLECTION:

Generate questions ONLY from this content. Do NOT include topics not mentioned here.

{'='*60}
{chr(10).join(context_blocks)}
{'='*60}

Create questions based ONLY on the content above."""

            logger.info(f"📊 Context ready: {len(context)} chars from {len(context_blocks)} summaries")
            return context

        except Exception as e:
            logger.error(f"❌ Context generation failed: {e}")
            raise

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'http[s]?://\S+', '', text)
        return text.strip()

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            dev_count = self.db_manager.developer_collection.count_documents(
                {"summary": {"$exists": True, "$ne": ""}}
            )
            non_dev_count = self.db_manager.non_developer_collection.count_documents(
                {"summary": {"$exists": True, "$ne": ""}}
            )
            
            # Get sample summaries
            dev_sample = self.db_manager.developer_collection.find_one(
                {"summary": {"$exists": True, "$ne": ""}}, {"summary": 1}
            )
            non_dev_sample = self.db_manager.non_developer_collection.find_one(
                {"summary": {"$exists": True, "$ne": ""}}, {"summary": 1}
            )
            
            return {
                "Developer": {
                    "count": dev_count,
                    "sample": dev_sample.get("summary", "")[:100] if dev_sample else "Empty"
                },
                "Non-Developer": {
                    "count": non_dev_count,
                    "sample": non_dev_sample.get("summary", "")[:100] if non_dev_sample else "Empty"
                }
            }
        except Exception as e:
            return {"error": str(e)}


# Singleton
_content_service = None

def get_content_service() -> ContentService:
    global _content_service
    if _content_service is None:
        _content_service = ContentService()
    return _content_service