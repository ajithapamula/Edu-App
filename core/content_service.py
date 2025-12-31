# weekly_interview/core/content_service.py
"""
Content processing service for Enhanced Mock Interview System
Intelligent summary fetching, fragment parsing, and content optimization
"""

import logging
import re
import random
from typing import Dict, List, Any, Tuple
from .config import config

logger = logging.getLogger(__name__)

class ContentService:
    """Enhanced content service with intelligent processing and fragment management"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        logger.info("📚 Content service initialized")
    
    async def get_interview_content_context(self) -> str:
        """Get optimized content context for interview questions"""
        try:
            logger.info(f"🔍 Generating interview content context from last {config.RECENT_SUMMARIES_DAYS} days")
            
            # Fetch recent summaries with enhanced filtering
            summaries = await self.db_manager.get_recent_summaries_fast(
                days=config.RECENT_SUMMARIES_DAYS,
                limit=config.SUMMARIES_LIMIT
            )
            
            if not summaries:
                raise Exception("No summaries available for content generation")
            
            logger.info(f"📊 Processing {len(summaries)} summaries for interview context")
            
            # Process summaries into interview-ready content
            processed_content = self._process_summaries_for_interview(summaries)
            
            # Validate content quality
            content_quality = self._validate_content_quality(processed_content)
            
            if not content_quality["is_suitable"]:
                logger.warning(f"⚠️ Content quality concerns: {content_quality['issues']}")
            
            logger.info(f"✅ Generated interview context: {len(processed_content)} characters")
            return processed_content
            
        except Exception as e:
            logger.error(f"❌ Content context generation failed: {e}")
            raise Exception(f"Content generation failed: {e}")
    
    def _process_summaries_for_interview(self, summaries: List[Dict[str, Any]]) -> str:
        """Process summaries into interview-optimized content"""
        try:
            content_parts = []
            
            for i, summary_doc in enumerate(summaries, 1):
                processed_content = self._process_individual_summary(summary_doc)
                
                if processed_content and len(processed_content.strip()) > config.MIN_CONTENT_LENGTH:
                    doc_id = str(summary_doc.get("_id", f"doc_{i}"))[:8]
                    content_parts.append(f"Technical Summary {i} (ID: {doc_id}):\n{processed_content}")
            
            if not content_parts:
                raise Exception("No valid content extracted from summaries")
            
            # Combine and optimize content
            combined_content = "\n\n".join(content_parts)
            
            # Apply intelligent content slicing
            final_content = self._apply_intelligent_slicing(combined_content)
            
            # Add interview-specific context prefix
            context_prefix = self._generate_context_prefix(len(content_parts))
            
            return context_prefix + final_content
            
        except Exception as e:
            logger.error(f"❌ Summary processing failed: {e}")
            raise Exception(f"Summary processing failed: {e}")
    
    def _process_individual_summary(self, summary_doc: Dict[str, Any]) -> str:
        """Process individual summary with enhanced filtering"""
        try:
            summary_text = summary_doc.get("summary", "")
            if not summary_text or len(summary_text) < config.MIN_CONTENT_LENGTH:
                return ""
            
            # Extract structured content
            structured_content = self._extract_structured_content(summary_text)
            
            if structured_content:
                # Use structured content with prioritization
                selected_content = self._prioritize_interview_content(structured_content)
                return self._clean_and_format_content(selected_content)
            else:
                # Use full text with intelligent slicing
                return self._clean_and_format_content(summary_text)
                
        except Exception as e:
            logger.warning(f"⚠️ Failed to process individual summary: {e}")
            return ""
    
    def _extract_structured_content(self, text: str) -> List[str]:
        """Extract structured content sections (numbered points, bullets, etc.)"""
        try:
            # Patterns for different structured formats
            extraction_patterns = [
                # Numbered sections: 1. 2. 3.
                r'^\s*(\d+)\.\s+(.+?)(?=^\s*\d+\.|$)',
                # Bullet points: - * •
                r'^\s*[-*•]\s+(.+?)(?=^\s*[-*•]|$)',
                # Letter sections: A. B. C.
                r'^\s*([A-Z])\.\s+(.+?)(?=^\s*[A-Z]\.|$)',
                # Topic headers: ## ### ####
                r'^#+\s+(.+?)(?=^#+|\Z)'
            ]
            
            structured_sections = []
            
            for pattern in extraction_patterns:
                matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
                if matches:
                    if isinstance(matches[0], tuple):
                        # Extract content from tuples (numbered/lettered sections)
                        sections = [match[1].strip().replace('\n', ' ') for match in matches]
                    else:
                        # Direct matches (headers, bullets)
                        sections = [match.strip().replace('\n', ' ') for match in matches]
                    
                    # Filter out short sections
                    sections = [section for section in sections if len(section) > 50]
                    
                    if sections:
                        structured_sections = sections
                        break
            
            logger.debug(f"📋 Extracted {len(structured_sections)} structured sections")
            return structured_sections
            
        except Exception as e:
            logger.warning(f"⚠️ Structured content extraction failed: {e}")
            return []
    
    def _prioritize_interview_content(self, content_sections: List[str]) -> str:
        """Prioritize content sections based on interview relevance"""
        try:
            # Keywords for different interview aspects
            technical_keywords = [
                'development', 'programming', 'algorithm', 'code', 'system',
                'architecture', 'database', 'api', 'framework', 'implementation',
                'optimization', 'performance', 'security', 'testing', 'deployment'
            ]
            
            communication_keywords = [
                'presentation', 'explanation', 'documentation', 'communication',
                'discussion', 'meeting', 'review', 'feedback', 'collaboration'
            ]
            
            problem_solving_keywords = [
                'problem', 'solution', 'challenge', 'issue', 'debug',
                'troubleshoot', 'analysis', 'approach', 'methodology', 'strategy'
            ]
            
            # Score sections based on relevance
            scored_sections = []
            for section in content_sections:
                score = 0
                section_lower = section.lower()
                
                # Technical relevance
                score += sum(2 for keyword in technical_keywords if keyword in section_lower)
                
                # Communication relevance
                score += sum(1.5 for keyword in communication_keywords if keyword in section_lower)
                
                # Problem-solving relevance
                score += sum(1.8 for keyword in problem_solving_keywords if keyword in section_lower)
                
                # Length bonus (longer sections often have more detail)
                score += len(section) / 200
                
                scored_sections.append((section, score))
            
            # Sort by score and select top sections
            scored_sections.sort(key=lambda x: x[1], reverse=True)
            
            # Select sections to fit within target length
            target_sections = int(len(scored_sections) * config.CONTENT_SLICE_FRACTION)
            target_sections = max(2, min(target_sections, 8))  # Between 2-8 sections
            
            selected_sections = [section for section, _ in scored_sections[:target_sections]]
            
            # Add some randomization for variety
            if len(scored_sections) > target_sections:
                remaining_sections = [section for section, _ in scored_sections[target_sections:]]
                additional_count = min(2, len(remaining_sections))
                if additional_count > 0:
                    selected_sections.extend(random.sample(remaining_sections, additional_count))
            
            return '. '.join(selected_sections)
            
        except Exception as e:
            logger.warning(f"⚠️ Content prioritization failed: {e}")
            return '. '.join(content_sections[:5])  # Fallback to first 5 sections
    
    def _apply_intelligent_slicing(self, content: str) -> str:
        """Apply intelligent content slicing while maintaining coherence"""
        if not content:
            return ""
        
        target_length = int(len(content) * config.CONTENT_SLICE_FRACTION)
        target_length = max(target_length, config.MIN_CONTENT_LENGTH * 2)  # Ensure minimum length
        target_length = min(target_length, len(content))  # Don't exceed original
        
        if target_length >= len(content):
            return content
        
        try:
            # Try to find natural break points
            sentences = re.split(r'[.!?]+', content)
            if len(sentences) > 1:
                # Select sentences that fit within target length
                selected_sentences = []
                current_length = 0
                
                # Start from a strategic position (not always beginning)
                start_idx = random.randint(0, max(0, len(sentences) // 4))
                
                for i in range(start_idx, len(sentences)):
                    sentence = sentences[i].strip()
                    if sentence and current_length + len(sentence) <= target_length:
                        selected_sentences.append(sentence)
                        current_length += len(sentence)
                    elif selected_sentences:  # Have at least one sentence
                        break
                
                if selected_sentences:
                    return '. '.join(selected_sentences) + '.'
            
            # Fallback: smart character slicing with word boundaries
            if target_length < len(content):
                # Find word boundary near target
                slice_pos = content.rfind(' ', 0, target_length)
                if slice_pos > target_length * 0.8:  # Word boundary is close enough
                    return content[:slice_pos] + '...'
            
            return content[:target_length] + '...'
            
        except Exception as e:
            logger.warning(f"⚠️ Intelligent slicing failed: {e}")
            return content[:target_length] + '...'
    
    def _clean_and_format_content(self, content: str) -> str:
        """Clean and format content for interview use"""
        if not content:
            return ""
        
        try:
            # Remove excessive whitespace
            cleaned = re.sub(r'\s+', ' ', content.strip())
            
            # Remove or replace problematic characters
            cleaned = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\"\'\/\\]', '', cleaned)
            
            # Ensure proper sentence structure
            cleaned = re.sub(r'\.{2,}', '.', cleaned)  # Remove multiple dots
            cleaned = re.sub(r'\s*\.\s*', '. ', cleaned)  # Proper dot spacing
            
            # Capitalize sentences
            sentences = cleaned.split('. ')
            formatted_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence:
                    # Capitalize first letter
                    sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
                    formatted_sentences.append(sentence)
            
            return '. '.join(formatted_sentences)
            
        except Exception as e:
            logger.warning(f"⚠️ Content cleaning failed: {e}")
            return content.strip()
    
    def _generate_context_prefix(self, summary_count: int) -> str:
        """Generate interview-specific context prefix"""
        return f"""Technical Interview Context (from {summary_count} recent project summaries):

The following content represents recent technical work, projects, and learning activities. Use this as the foundation for generating relevant, challenging interview questions that assess both technical knowledge and practical application.

"""
    
    def _validate_content_quality(self, content: str) -> Dict[str, Any]:
        """Validate generated content quality for interview suitability"""
        try:
            # Basic metrics
            word_count = len(content.split())
            char_count = len(content)
            sentence_count = len(re.split(r'[.!?]+', content))
            
            # Technical content indicators
            technical_indicators = [
                'development', 'programming', 'code', 'system', 'algorithm',
                'database', 'api', 'framework', 'architecture', 'implementation',
                'optimization', 'performance', 'security', 'testing', 'deployment',
                'analysis', 'design', 'solution', 'technology', 'software'
            ]
            
            technical_score = sum(1 for indicator in technical_indicators 
                                 if indicator.lower() in content.lower())
            
            # Quality assessment
            quality_issues = []
            
            # Length validation
            if char_count < config.MIN_CONTENT_LENGTH * 3:
                quality_issues.append(f"Content too short ({char_count} chars)")
            
            if word_count < 100:
                quality_issues.append(f"Insufficient word count ({word_count} words)")
            
            # Technical relevance
            if technical_score < 5:
                quality_issues.append(f"Low technical relevance (score: {technical_score})")
            
            # Sentence structure
            avg_sentence_length = word_count / max(sentence_count, 1)
            if avg_sentence_length < 5 or avg_sentence_length > 50:
                quality_issues.append(f"Poor sentence structure (avg: {avg_sentence_length:.1f} words/sentence)")
            
            # Content diversity (check for repetition)
            unique_words = len(set(content.lower().split()))
            repetition_ratio = unique_words / max(word_count, 1)
            if repetition_ratio < 0.3:
                quality_issues.append(f"High repetition detected (ratio: {repetition_ratio:.2f})")
            
            return {
                "is_suitable": len(quality_issues) == 0,
                "issues": quality_issues,
                "metrics": {
                    "character_count": char_count,
                    "word_count": word_count,
                    "sentence_count": sentence_count,
                    "technical_score": technical_score,
                    "avg_sentence_length": avg_sentence_length,
                    "repetition_ratio": repetition_ratio
                },
                "quality_score": max(0, 10 - len(quality_issues) * 2),
                "data_source": f"mongodb_last_{config.RECENT_SUMMARIES_DAYS}_days"
            }
            
        except Exception as e:
            logger.error(f"❌ Content validation failed: {e}")
            return {
                "is_suitable": False,
                "issues": [f"Validation error: {e}"],
                "metrics": {},
                "quality_score": 0,
                "data_source": "validation_failed"
            }
    
    def parse_content_into_fragments(self, content: str) -> Dict[str, str]:
        """Parse content into interview-relevant fragments (not used in this implementation)"""
        # This method is kept for compatibility but fragments are not used
        # as per requirements - keeping flat question generation
        logger.info("🔍 Fragment parsing not used - using flat content structure")
        return {"interview_content": content}
    
    async def get_content_analytics(self) -> Dict[str, Any]:
        """Get analytics about available content"""
        try:
            summaries = await self.db_manager.get_recent_summaries_fast()
            
            total_summaries = len(summaries)
            total_content_length = 0
            
            for summary in summaries:
                content = summary.get("summary", "")
                total_content_length += len(content)
            
            avg_content_length = total_content_length / max(total_summaries, 1)
            
            return {
                "total_summaries_available": total_summaries,
                "total_content_length": total_content_length,
                "average_content_length": round(avg_content_length, 1),
                "recent_days_window": config.RECENT_SUMMARIES_DAYS,
                "content_slice_fraction": config.CONTENT_SLICE_FRACTION,
                "min_content_length": config.MIN_CONTENT_LENGTH
            }
            
        except Exception as e:
            logger.error(f"❌ Content analytics failed: {e}")
            return {
                "total_summaries_available": 0,
                "error": str(e)
            }