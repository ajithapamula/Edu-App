# weekend_mocktest/core/content_service.py
import logging
import random
import re
from typing import List, Dict, Any
from .config import config
from .database import get_db_manager

logger = logging.getLogger(__name__)


class ContentService:
    """
    Service for processing MongoDB summaries and generating
    developer / non-developer specific context for mock tests.
    """

    DEV_KEYWORDS = {
        "python", "java", "javascript", "typescript",
        "api", "backend", "frontend", "fullstack",
        "database", "sql", "nosql",
        "algorithm", "data structure",
        "code", "coding",
        "architecture", "system design", "microservice",
        "performance", "optimization",
        "deployment", "ci/cd",
        "framework", "fastapi", "django", "spring",
        "react", "node", "angular"
    }

    NON_DEV_KEYWORDS = {
        "testing", "qa", "manual testing", "automation testing",
        "sdlc", "agile", "scrum", "kanban",
        "requirement", "requirement gathering",
        "analysis", "business analysis",
        "process", "workflow",
        "defect", "bug",
        "test case", "test plan",
        "documentation", "reporting",
        "sap", "crm", "erp"
    }

    def __init__(self):
        self.db_manager = get_db_manager()
        logger.info("📚 ContentService initialized")

    # ======================================================
    # PUBLIC
    # ======================================================
    def get_context_for_questions(self, user_type: str = "dev") -> str:
        """
        Build AI context from weekly MongoDB summaries based on interview type.
        """
        try:
            logger.info(f"🔍 Building context for user_type={user_type}")

            summaries = self.db_manager.get_recent_summaries(
                config.RECENT_SUMMARIES_COUNT
            )

            if not summaries:
                raise Exception("No summaries found in MongoDB")

            context_blocks = []

            for idx, doc in enumerate(summaries, 1):
                summary_text = doc.get("summary", "")
                if not summary_text or len(summary_text) < 120:
                    continue

                relevance_score = self._score_relevance(summary_text, user_type)
                if relevance_score <= 0:
                    continue

                processed = self._process_summary(summary_text)
                if not processed or len(processed) < 80:
                    continue

                doc_id = str(doc.get("_id", f"doc_{idx}"))[:8]
                context_blocks.append(
                    f"Summary {idx} (ID: {doc_id}, relevance={relevance_score}): {processed}"
                )

            if not context_blocks:
                raise Exception("No relevant summaries after filtering")

            prefix = (
                "Developer Interview Context (coding, systems, architecture):\n\n"
                if user_type == "dev"
                else "Non-Developer Interview Context (process, testing, analysis):\n\n"
            )

            final_context = prefix + "\n\n".join(context_blocks)

            if len(final_context) < 400:
                raise Exception("Generated context too short")

            logger.info(f"✅ Context generated ({len(final_context)} chars)")
            return final_context

        except Exception as e:
            logger.error(f"❌ Context generation failed: {e}")
            raise

    def validate_context_quality(self, context: str) -> Dict[str, Any]:
        """
        Quality check (kept for compatibility with existing test_service.py).
        Does NOT block unless extremely weak.
        """
        try:
            char_count = len(context or "")
            word_count = len((context or "").split())
            summary_count = (context or "").count("Summary ")

            # Simple “signal” check
            dev_hits = sum(1 for k in self.DEV_KEYWORDS if k in (context or "").lower())
            nondev_hits = sum(1 for k in self.NON_DEV_KEYWORDS if k in (context or "").lower())

            # Score
            score = 0.0
            if char_count >= 1200:
                score += 0.4
            elif char_count >= 600:
                score += 0.25
            else:
                score += 0.1

            if summary_count >= 6:
                score += 0.3
            elif summary_count >= 4:
                score += 0.2
            else:
                score += 0.1

            if (dev_hits + nondev_hits) >= 8:
                score += 0.3
            elif (dev_hits + nondev_hits) >= 4:
                score += 0.2
            else:
                score += 0.1

            return {
                "char_count": char_count,
                "word_count": word_count,
                "summary_count": summary_count,
                "keyword_hits": {"dev": dev_hits, "non_dev": nondev_hits},
                "quality_score": score,
                "is_high_quality": score >= 0.65,
                "data_source": "live_mongodb",
            }

        except Exception as e:
            logger.error(f"Context validation failed: {e}")
            return {"is_high_quality": False, "error": str(e), "data_source": "unknown"}

    # ======================================================
    # INTERNAL HELPERS
    # ======================================================
    def _score_relevance(self, text: str, user_type: str) -> int:
        text_l = text.lower()
        score = 0.0

        if user_type == "dev":
            for kw in self.DEV_KEYWORDS:
                if kw in text_l:
                    score += 1
        else:
            for kw in self.NON_DEV_KEYWORDS:
                if kw in text_l:
                    score += 1
            # Penalize heavy coding summaries for non-dev
            for kw in self.DEV_KEYWORDS:
                if kw in text_l:
                    score -= 0.5

        return max(0, int(score))

    def _process_summary(self, text: str) -> str:
        bullets = self._extract_bullets(text)
        if bullets:
            selected = self._select_points(bullets)
            content = ". ".join(selected)
        else:
            content = text
        return self._slice_content(content)

    def _extract_bullets(self, text: str) -> List[str]:
        patterns = [
            r'^\d+[\.\)]\s+(.+?)(?=^\d+[\.\)]|\Z)',
            r'^[-*•]\s+(.+?)(?=^[-*•]|\Z)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
            cleaned = [
                m.strip().replace("\n", " ")
                for m in matches
                if len(m.strip()) > 30
            ]
            if cleaned:
                return cleaned
        return []

    def _select_points(self, points: List[str]) -> List[str]:
        if not points:
            return []
        target = min(8, max(2, int(len(points) * config.SUMMARY_SLICE_FRACTION)))
        scored = [(p, len(p)) for p in points]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in scored[:target]]

    def _slice_content(self, content: str) -> str:
        if not content:
            return ""
        max_len = max(150, int(len(content) * config.SUMMARY_SLICE_FRACTION))
        if len(content) <= max_len:
            return content
        cut = content.rfind(" ", 0, max_len)
        if cut < 0:
            cut = max_len
        return content[:cut] + "..."


_content_service = None

def get_content_service() -> ContentService:
    global _content_service
    if _content_service is None:
        _content_service = ContentService()
    return _content_service
