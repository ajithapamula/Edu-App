# weekend_mocktest/core/content_service.py
import logging
import random
import re
from typing import List, Dict, Any
from .config import config
from .database import get_db_manager

logger = logging.getLogger(__name__)

class ContentService:
    """Service for processing summaries and creating context for questions"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        logger.info("📚 Content service initialized")
    
    def get_context_for_questions(self, user_type: str = "dev") -> str:
        """Generate context from MongoDB summaries for question generation"""
        try:
            logger.info(f"🔍 Generating context for {user_type} questions")
            
            # Fetch recent summaries
            summaries = self.db_manager.get_recent_summaries(config.RECENT_SUMMARIES_COUNT)
            
            if not summaries:
                raise Exception("No summaries available in database")
            
            logger.info(f"📊 Processing {len(summaries)} summaries")
            
            # Process summaries into context
            context_parts = []
            for i, summary_doc in enumerate(summaries, 1):
                processed_content = self._process_summary_for_context(summary_doc)
                
                if processed_content and len(processed_content.strip()) > 50:
                    doc_id = str(summary_doc.get("_id", f"doc_{i}"))[:8]
                    context_parts.append(f"Summary {i} (ID: {doc_id}): {processed_content}")
            
            if not context_parts:
                raise Exception("No valid content extracted from summaries")
            
            # Create final context
            combined_context = "\n\n".join(context_parts)
            
            # Add context prefix based on user type
            if user_type == "dev":
                context_prefix = "Technical Development Context (from recent project summaries):\n\n"
            else:
                context_prefix = "Technology Concepts and Analysis Context (from recent summaries):\n\n"
            
            final_context = context_prefix + combined_context
            
            # Validate context length
            if len(final_context) < 300:
                raise Exception(f"Context too short: {len(final_context)} chars, need at least 300")
            
            # Log sample for verification
            sample = final_context[:200] + "..." if len(final_context) > 200 else final_context
            logger.info(f"✅ Context generated: {len(final_context)} chars")
            logger.debug(f"Sample: {sample}")
            
            return final_context
            
        except Exception as e:
            logger.error(f"❌ Context generation failed: {e}")
            raise Exception(f"Context generation failed: {e}")
    
    def _process_summary_for_context(self, summary_doc: Dict[str, Any]) -> str:
        """Process individual summary into usable context"""
        try:
            summary_text = summary_doc.get("summary", "")
            if not summary_text or len(summary_text) < 100:
                return ""
            
            # Extract bullet points if available
            bullet_points = self._extract_bullet_points(summary_text)
            
            if bullet_points:
                # Use bullet points for structured content
                selected_points = self._select_relevant_points(bullet_points)
                content = ". ".join(selected_points)
            else:
                # Use full text if no bullet points found
                content = summary_text
            
            # Apply slicing for variety and performance
            sliced_content = self._slice_content_smartly(content)
            
            return sliced_content
            
        except Exception as e:
            logger.warning(f"Failed to process summary: {e}")
            return ""
    
    def _extract_bullet_points(self, text: str) -> List[str]:
        """Extract numbered bullet points from text"""
        try:
            # Patterns for different bullet formats
            patterns = [
                r'^\d+[\.\)]\s+(.+?)(?=^\d+[\.\)]|\Z)',  # 1. or 1)
                r'^[-*•]\s+(.+?)(?=^[-*•]|\Z)',          # - or * or •
                r'^[A-Z][\.\)]\s+(.+?)(?=^[A-Z][\.\)]|\Z)'  # A. or A)
            ]
            
            bullet_points = []
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
                if matches:
                    # Clean and filter points
                    points = [point.strip().replace('\n', ' ') for point in matches]
                    points = [point for point in points if len(point) > 30]  # Filter short points
                    if points:
                        bullet_points = points
                        break
            
            logger.debug(f"Extracted {len(bullet_points)} bullet points")
            return bullet_points
            
        except Exception as e:
            logger.warning(f"Bullet point extraction failed: {e}")
            return []
    
    def _select_relevant_points(self, bullet_points: List[str]) -> List[str]:
        """Select most relevant bullet points"""
        if not bullet_points:
            return []
        
        # Calculate how many points to select
        total_points = len(bullet_points)
        points_to_select = max(1, int(total_points * config.SUMMARY_SLICE_FRACTION))
        points_to_select = min(points_to_select, 8)  # Cap at 8 points
        
        if points_to_select >= total_points:
            return bullet_points
        
        # Score points by technical relevance
        scored_points = []
        technical_keywords = [
            'development', 'programming', 'algorithm', 'database', 'system',
            'api', 'framework', 'implementation', 'optimization', 'architecture',
            'security', 'performance', 'testing', 'deployment', 'integration',
            'analysis', 'solution', 'technology', 'process', 'methodology'
        ]
        
        for point in bullet_points:
            score = sum(1 for keyword in technical_keywords if keyword.lower() in point.lower())
            score += len(point) // 100  # Longer points get slight bonus
            scored_points.append((point, score))
        
        # Sort by score and select top points
        scored_points.sort(key=lambda x: x[1], reverse=True)
        selected = [point for point, _ in scored_points[:points_to_select]]
        
        # If we have fewer high-scoring points, randomly fill the rest
        if len(selected) < points_to_select:
            remaining = [point for point, _ in scored_points[len(selected):]]
            additional_count = points_to_select - len(selected)
            selected.extend(random.sample(remaining, min(additional_count, len(remaining))))
        
        return selected
    
    def _slice_content_smartly(self, content: str) -> str:
        """Apply smart slicing to content while maintaining readability"""
        if not content:
            return ""
        
        target_length = int(len(content) * config.SUMMARY_SLICE_FRACTION)
        target_length = max(target_length, 100)  # Minimum length
        target_length = min(target_length, len(content))  # Don't exceed original
        
        if target_length >= len(content):
            return content
        
        # Try to find good slice boundaries
        sentences = re.split(r'[.!?]+', content)
        if len(sentences) > 1:
            # Select sentences that fit within target length
            selected_sentences = []
            current_length = 0
            
            # Start from a random position for variety
            start_idx = random.randint(0, max(0, len(sentences) - 3))
            
            for i in range(start_idx, len(sentences)):
                sentence = sentences[i].strip()
                if sentence and current_length + len(sentence) <= target_length:
                    selected_sentences.append(sentence)
                    current_length += len(sentence)
                elif selected_sentences:  # Have at least one sentence
                    break
            
            if selected_sentences:
                return '. '.join(selected_sentences) + '.'
        
        # Fallback: simple character slicing with word boundary
        if target_length < len(content):
            # Find word boundary near target
            slice_pos = content.rfind(' ', 0, target_length)
            if slice_pos > target_length * 0.8:  # If word boundary is close enough
                return content[:slice_pos] + '...'
        
        return content[:target_length] + '...'
    
    def validate_context_quality(self, context: str) -> Dict[str, Any]:
        """Validate generated context quality"""
        try:
            # Basic metrics
            word_count = len(context.split())
            char_count = len(context)
            line_count = len(context.split('\n'))
            
            # Technical content indicators
            technical_terms = [
                'development', 'programming', 'algorithm', 'system', 'api',
                'database', 'framework', 'implementation', 'architecture',
                'security', 'performance', 'analysis', 'process', 'method'
            ]
            
            technical_score = sum(1 for term in technical_terms 
                                 if term.lower() in context.lower())
            
            # Quality scoring
            quality_factors = []
            
            # Length factor
            if char_count >= 1000:
                quality_factors.append(0.4)
            elif char_count >= 500:
                quality_factors.append(0.3)
            else:
                quality_factors.append(0.1)
            
            # Content diversity (number of summaries)
            summary_count = context.count("Summary ")
            if summary_count >= 7:
                quality_factors.append(0.3)
            elif summary_count >= 5:
                quality_factors.append(0.2)
            else:
                quality_factors.append(0.1)
            
            # Technical relevance
            if technical_score >= 8:
                quality_factors.append(0.3)
            elif technical_score >= 5:
                quality_factors.append(0.2)
            else:
                quality_factors.append(0.1)
            
            overall_score = sum(quality_factors)
            
            return {
                "char_count": char_count,
                "word_count": word_count,
                "summary_count": summary_count,
                "technical_score": technical_score,
                "quality_score": overall_score,
                "is_high_quality": overall_score >= 0.7,
                "data_source": "live_mongodb"
            }
            
        except Exception as e:
            logger.error(f"Context validation failed: {e}")
            return {
                "error": str(e),
                "is_high_quality": False,
                "data_source": "unknown"
            }

# Singleton instance
_content_service = None

def get_content_service() -> ContentService:
    """Get content service singleton"""
    global _content_service
    if _content_service is None:
        _content_service = ContentService()
    return _content_service