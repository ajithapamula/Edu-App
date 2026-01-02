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
    
    Features:
    - Weekly summary aggregation
    - Keyword-based relevance scoring
    - Content optimization for AI generation
    """

    DEV_KEYWORDS = {
        "python", "java", "javascript", "typescript",
        "api", "backend", "frontend", "fullstack",
        "database", "sql", "nosql", "mongodb", "postgresql",
        "algorithm", "data structure", "binary tree", "graph",
        "code", "coding", "programming", "debug",
        "architecture", "system design", "microservice", "distributed",
        "performance", "optimization", "scalability", "caching",
        "deployment", "ci/cd", "docker", "kubernetes",
        "framework", "fastapi", "django", "spring", "express",
        "react", "node", "angular", "vue",
        "git", "version control", "pull request",
        "testing", "unit test", "integration test",
        "security", "authentication", "authorization",
        "rest", "graphql", "grpc", "websocket"
    }

    NON_DEV_KEYWORDS = {
        "testing", "qa", "manual testing", "automation testing",
        "sdlc", "agile", "scrum", "kanban", "sprint",
        "requirement", "requirement gathering", "user story",
        "analysis", "business analysis", "gap analysis",
        "process", "workflow", "documentation",
        "defect", "bug", "issue tracking", "jira",
        "test case", "test plan", "test scenario", "regression",
        "documentation", "reporting", "status report",
        "sap", "crm", "erp", "salesforce",
        "stakeholder", "communication", "presentation",
        "uml", "flowchart", "bpmn",
        "quality", "metrics", "kpi"
    }

    def __init__(self):
        self.db_manager = get_db_manager()
        logger.info("📚 ContentService initialized")

    # ======================================================
    # PUBLIC METHODS
    # ======================================================
    
    def get_context_for_questions(self, user_type: str = None) -> str:
        """
        Build AI context from MongoDB summaries for question generation.
        
        Fetches summaries from the 'summaries' collection and uses them
        to generate course-specific questions. No dev/non_dev filtering.
        
        Args:
            user_type: Ignored - kept for backward compatibility
        
        Returns:
            Formatted context string for AI question generation
            
        Raises:
            Exception if no summaries found
        """
        try:
            logger.info(f"🔍 Building context from course summaries")

            # Get ALL summaries - no filtering by type
            summaries = self.db_manager.get_weekly_summaries()

            if not summaries:
                summaries = self.db_manager.get_recent_summaries(config.RECENT_SUMMARIES_COUNT)

            if not summaries:
                raise Exception(
                    "No summaries found in MongoDB 'summaries' collection.\n"
                    "Please ensure course content has been added."
                )

            context_blocks = []

            for idx, doc in enumerate(summaries, 1):
                summary_text = doc.get("summary", "")
                if not summary_text or len(summary_text) < 100:
                    continue

                # Process summary
                processed = self._process_summary(summary_text)
                if not processed or len(processed) < 80:
                    continue

                # Extract topics from summary
                topics = self._extract_all_topics(summary_text)
                topics_str = f" [Topics: {', '.join(topics[:5])}]" if topics else ""

                doc_id = str(doc.get("_id", f"doc_{idx}"))[:8]
                filename = doc.get("filename", "")[:40]
                source_info = f" - {filename}" if filename else ""
                
                context_blocks.append(
                    f"Summary {idx} (ID: {doc_id}{source_info}){topics_str}:\n{processed}"
                )

            if not context_blocks:
                raise Exception(
                    "No valid summaries found!\n"
                    "Each summary should have a 'summary' field with at least 100 characters."
                )

            # Build context
            prefix = f"""Course Content Context
=====================================
Based on {len(context_blocks)} weekly summaries

"""
            final_context = prefix + "\n\n".join(context_blocks)

            logger.info(f"✅ Context: {len(context_blocks)} summaries loaded")
            return final_context

        except Exception as e:
            logger.error(f"❌ Context generation failed: {e}")
            raise
    
    def _extract_all_topics(self, text: str) -> List[str]:
        """Extract all relevant topics from text"""
        text_l = text.lower()
        topics = []
        
        # Combined keywords from both dev and non-dev
        all_keywords = self.DEV_KEYWORDS | self.NON_DEV_KEYWORDS
        
        for kw in all_keywords:
            if kw in text_l:
                topics.append(kw)
        
        return topics[:10]

    def get_context_for_question_type(self, user_type: str, question_type: str) -> str:
        """
        Get optimized context for specific question type.
        
        Args:
            user_type: 'dev' or 'non_dev'
            question_type: 'aptitude', 'theory', 'coding', or 'mcq'
        
        Returns:
            Context optimized for the question type
        """
        base_context = self.get_context_for_questions(user_type)
        
        type_guidance = {
            "aptitude": """
Focus areas for APTITUDE questions:
- Logical reasoning scenarios
- Problem-solving patterns
- Mathematical concepts mentioned
- Analytical thinking challenges
""",
            "theory": """
Focus areas for THEORY questions:
- Technical concepts and definitions
- Architecture patterns
- Best practices and conventions
- Comparison of technologies
- Design principles
""",
            "coding": """
Focus areas for CODING questions:
- Algorithm implementations mentioned
- Data structures used
- Code optimization techniques
- Common programming patterns
- Debugging scenarios
""",
            "mcq": """
Focus areas for MCQ questions:
- Testing methodologies
- SDLC phases and concepts
- Business analysis techniques
- Process and workflow scenarios
- Quality metrics
"""
        }
        
        guidance = type_guidance.get(question_type, "")
        
        return f"{guidance}\n\n{base_context}"

    def validate_context_quality(self, context: str) -> Dict[str, Any]:
        """
        Validate context quality for question generation.
        
        Args:
            context: The generated context string
        
        Returns:
            Quality assessment dictionary
        """
        try:
            char_count = len(context or "")
            word_count = len((context or "").split())
            summary_count = (context or "").count("Summary ")

            # Count keyword hits
            dev_hits = sum(1 for k in self.DEV_KEYWORDS if k in (context or "").lower())
            nondev_hits = sum(1 for k in self.NON_DEV_KEYWORDS if k in (context or "").lower())

            # Calculate quality score
            score = 0.0
            
            # Length scoring
            if char_count >= 2000:
                score += 0.4
            elif char_count >= 1000:
                score += 0.3
            elif char_count >= 500:
                score += 0.2
            else:
                score += 0.1

            # Summary count scoring
            if summary_count >= 8:
                score += 0.3
            elif summary_count >= 5:
                score += 0.2
            else:
                score += 0.1

            # Keyword density scoring
            total_hits = dev_hits + nondev_hits
            if total_hits >= 15:
                score += 0.3
            elif total_hits >= 8:
                score += 0.2
            else:
                score += 0.1

            return {
                "char_count": char_count,
                "word_count": word_count,
                "summary_count": summary_count,
                "keyword_hits": {"dev": dev_hits, "non_dev": nondev_hits},
                "quality_score": round(score, 2),
                "is_high_quality": score >= 0.6,
                "data_source": "live_mongodb"
            }

        except Exception as e:
            logger.error(f"Context validation failed: {e}")
            return {
                "is_high_quality": False, 
                "error": str(e), 
                "data_source": "unknown"
            }

    # ======================================================
    # INTERNAL HELPERS
    # ======================================================
    
    def _score_relevance(self, text: str, user_type: str) -> int:
        """Score text relevance for user type"""
        text_l = text.lower()
        score = 0

        if user_type == "dev":
            for kw in self.DEV_KEYWORDS:
                if kw in text_l:
                    # Weight by keyword importance
                    if kw in {"algorithm", "coding", "system design", "architecture"}:
                        score += 2
                    else:
                        score += 1
        else:
            for kw in self.NON_DEV_KEYWORDS:
                if kw in text_l:
                    if kw in {"testing", "qa", "requirement", "analysis"}:
                        score += 2
                    else:
                        score += 1
            
            # Penalize heavy coding content for non-dev
            for kw in {"algorithm", "coding", "compile", "syntax"}:
                if kw in text_l:
                    score -= 1

        return max(0, score)

    def _extract_topics(self, text: str, user_type: str) -> List[str]:
        """Extract relevant topics from text"""
        text_l = text.lower()
        topics = []
        
        keywords = self.DEV_KEYWORDS if user_type == "dev" else self.NON_DEV_KEYWORDS
        
        for kw in keywords:
            if kw in text_l:
                topics.append(kw)
        
        return topics[:10]  # Return top 10 topics

    def _process_summary(self, text: str) -> str:
        """Process summary text for optimal context"""
        # Try to extract structured content
        bullets = self._extract_bullets(text)
        
        if bullets:
            selected = self._select_points(bullets)
            content = ". ".join(selected)
        else:
            content = text
        
        return self._slice_content(content)

    def _extract_bullets(self, text: str) -> List[str]:
        """Extract bullet points from text"""
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
        """Select most relevant points"""
        if not points:
            return []
        
        # Select based on length (longer = more content)
        target = min(10, max(3, int(len(points) * config.SUMMARY_SLICE_FRACTION)))
        
        scored = [(p, len(p)) for p in points]
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [p for p, _ in scored[:target]]

    def _slice_content(self, content: str) -> str:
        """Slice content to appropriate length"""
        if not content:
            return ""
        
        max_len = max(200, int(len(content) * config.SUMMARY_SLICE_FRACTION))
        
        if len(content) <= max_len:
            return content
        
        # Cut at word boundary
        cut = content.rfind(" ", 0, max_len)
        if cut < 0:
            cut = max_len
        
        return content[:cut] + "..."


# ======================================================
# SINGLETON
# ======================================================

_content_service = None

def get_content_service() -> ContentService:
    """Get content service singleton"""
    global _content_service
    if _content_service is None:
        _content_service = ContentService()
    return _content_service