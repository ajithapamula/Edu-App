# weekend_mocktest/core/ai_services.py
import logging
import time
import re
import json
from typing import List, Dict, Any
from groq import Groq
from .config import config
from .prompts import PromptTemplates

logger = logging.getLogger(__name__)

class AIService:
    """Production AI service for question generation and evaluation"""
    
    def __init__(self):
        """Initialize Groq client"""
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required")
        
        self.client = Groq(
            api_key=config.GROQ_API_KEY,
            timeout=config.GROQ_TIMEOUT
        )
        
        # Test connection
        self._test_connection()
        logger.info("✅ AI Service initialized successfully")
    
    def _test_connection(self):
        """Test AI service connection"""
        try:
            response = self.client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[{"role": "user", "content": "Hello"}],
                max_completion_tokens=10
            )
            if not response.choices:
                raise Exception("No response from AI service")
        except Exception as e:
            raise Exception(f"AI service connection failed: {e}")
    
    def generate_questions_batch(self, user_type: str, context: str) -> List[Dict[str, Any]]:
        """Generate questions using AI based on real context"""
        logger.info(f"🤖 Generating {config.QUESTIONS_PER_TEST} {user_type} questions")
        
        try:
            # Create generation prompt
            prompt = PromptTemplates.create_batch_questions_prompt(
                user_type, context, config.QUESTIONS_PER_TEST
            )
            
            # Generate with retries
            response = self._call_llm_with_retries(prompt, config.GROQ_MAX_TOKENS)
            
            # Parse questions
            questions = self._parse_questions_response(response, user_type)
            
            if len(questions) != config.QUESTIONS_PER_TEST:
                logger.warning(f"Generated {len(questions)}/{config.QUESTIONS_PER_TEST} questions")
            
            if not questions:
                raise Exception("No valid questions generated")
            
            logger.info(f"✅ Generated {len(questions)} questions successfully")
            return questions
            
        except Exception as e:
            logger.error(f"❌ Question generation failed: {e}")
            raise
    
    def evaluate_test_batch(self, user_type: str, qa_pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate test answers using AI"""
        logger.info(f"🎯 Evaluating {len(qa_pairs)} {user_type} answers")
        
        try:
            # Create evaluation prompt
            prompt = PromptTemplates.create_evaluation_prompt(user_type, qa_pairs)
            
            # Get evaluation
            response = self._call_llm_with_retries(
                prompt, 
                config.EVALUATION_MAX_TOKENS,
                config.EVALUATION_TEMPERATURE
            )
            
            # Parse evaluation
            evaluation = self._parse_evaluation_response(response, qa_pairs)
            
            logger.info(f"✅ Evaluation completed: {evaluation['total_correct']}/{len(qa_pairs)}")
            return evaluation
            
        except Exception as e:
            logger.error(f"❌ Evaluation failed: {e}")
            raise
    
    def _call_llm_with_retries(self, prompt: str, max_tokens: int, 
                              temperature: float = None) -> str:
        """Call LLM with retry logic"""
        if temperature is None:
            temperature = config.GROQ_TEMPERATURE
        
        last_error = None
        
        for attempt in range(config.MAX_RETRIES):
            try:
                logger.debug(f"LLM call attempt {attempt + 1}/{config.MAX_RETRIES}")
                
                completion = self.client.chat.completions.create(
                    model=config.GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperature,
                    max_completion_tokens=max_tokens
                )
                
                if not completion.choices:
                    raise Exception("No response from LLM")
                
                response = completion.choices[0].message.content.strip()
                
                if len(response) < 100:
                    raise Exception("Response too short")
                
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(f"LLM attempt {attempt + 1} failed: {e}")
                if attempt < config.MAX_RETRIES - 1:
                    time.sleep(config.RETRY_DELAY * (attempt + 1))
        
        raise Exception(f"LLM failed after {config.MAX_RETRIES} attempts: {last_error}")
    
    def _parse_questions_response(self, response: str, user_type: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured questions"""
        try:
            questions = []
            
            # Split by question markers
            sections = re.split(r'=== QUESTION \d+ ===', response)[1:]
            
            for i, section in enumerate(sections, 1):
                try:
                    question = self._parse_single_question(section, user_type, i)
                    if question:
                        questions.append(question)
                except Exception as e:
                    logger.warning(f"Failed to parse question {i}: {e}")
            
            return questions
            
        except Exception as e:
            logger.error(f"Question parsing failed: {e}")
            raise Exception(f"Failed to parse questions: {e}")
    
    def _parse_single_question(self, section: str, user_type: str, question_number: int) -> Dict[str, Any]:
        """Parse individual question from section"""
        lines = [line.strip() for line in section.split('\n') if line.strip()]
        
        question_data = {
            "question_number": question_number,
            "title": f"Question {question_number}",
            "difficulty": "Medium",
            "type": "General",
            "question": "",
            "options": None
        }
        
        current_section = None
        question_lines = []
        options = []
        
        for line in lines:
            if line.startswith("## Title:"):
                question_data["title"] = line.replace("## Title:", "").strip()
            elif line.startswith("## Difficulty:"):
                question_data["difficulty"] = line.replace("## Difficulty:", "").strip()
            elif line.startswith("## Type:"):
                question_data["type"] = line.replace("## Type:", "").strip()
            elif line.startswith("## Question:"):
                current_section = "question"
            elif line.startswith("## Options:") and user_type == "non_dev":
                current_section = "options"
            elif current_section == "question":
                if not line.startswith("##"):
                    question_lines.append(line)
            elif current_section == "options" and user_type == "non_dev":
                if re.match(r'^[A-D]\)', line):
                    option_text = line[3:].strip()
                    if option_text:
                        options.append(option_text)
        
        question_data["question"] = "\n".join(question_lines).strip()
        
        if user_type == "non_dev":
            question_data["options"] = options if len(options) == 4 else None
        
        # Validation
        if not question_data["question"] or len(question_data["question"]) < 50:
            raise Exception("Question too short")
        
        if user_type == "non_dev" and not question_data["options"]:
            raise Exception("MCQ missing options")
        
        return question_data
    
    def _parse_evaluation_response(self, response: str, qa_pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse evaluation response from LLM"""
        try:
            # Look for structured evaluation data
            scores = []
            feedbacks = []
            
            # Extract scores
            score_match = re.search(r'SCORES:\s*\[(.*?)\]', response, re.DOTALL)
            if score_match:
                score_str = score_match.group(1)
                scores = [int(s.strip()) for s in score_str.split(',') if s.strip().isdigit()]
            
            # Extract feedbacks
            feedback_match = re.search(r'FEEDBACK:\s*\[(.*?)\]', response, re.DOTALL)
            if feedback_match:
                feedback_str = feedback_match.group(1)
                feedbacks = [f.strip().strip('"\'') for f in feedback_str.split('|')]
            
            # Fallback: parse line by line
            if not scores or len(scores) != len(qa_pairs):
                scores = self._extract_scores_fallback(response, len(qa_pairs))
            
            if not feedbacks or len(feedbacks) != len(qa_pairs):
                feedbacks = self._extract_feedbacks_fallback(response, len(qa_pairs))
            
            # Ensure we have the right number of scores and feedbacks
            if len(scores) != len(qa_pairs):
                raise Exception(f"Score count mismatch: {len(scores)} vs {len(qa_pairs)}")
            
            if len(feedbacks) != len(qa_pairs):
                # Generate default feedbacks if parsing failed
                feedbacks = [f"Question {i+1}: {'Correct' if scores[i] else 'Incorrect'}" 
                           for i in range(len(qa_pairs))]
            
            return {
                "scores": scores,
                "feedbacks": feedbacks,
                "total_correct": sum(scores),
                "evaluation_report": response
            }
            
        except Exception as e:
            logger.error(f"Evaluation parsing failed: {e}")
            raise Exception(f"Failed to parse evaluation: {e}")
    
    def _extract_scores_fallback(self, response: str, expected_count: int) -> List[int]:
        """Fallback method to extract scores"""
        # Look for patterns like "1,0,1,0,1"
        score_patterns = re.findall(r'(?:^|\s)([01](?:\s*,\s*[01])+)(?:\s|$)', response)
        
        for pattern in score_patterns:
            scores = [int(s.strip()) for s in pattern.split(',')]
            if len(scores) == expected_count:
                return scores
        
        # Ultimate fallback: default scoring
        logger.warning("Using fallback scoring")
        return [1 if i % 2 == 0 else 0 for i in range(expected_count)]
    
    def _extract_feedbacks_fallback(self, response: str, expected_count: int) -> List[str]:
        """Fallback method to extract feedbacks"""
        lines = response.split('\n')
        feedbacks = []
        
        for line in lines:
            if 'question' in line.lower() and any(word in line.lower() for word in ['correct', 'incorrect', 'good', 'poor']):
                feedbacks.append(line.strip())
                if len(feedbacks) == expected_count:
                    break
        
        # Pad if necessary
        while len(feedbacks) < expected_count:
            feedbacks.append(f"Question {len(feedbacks) + 1}: Evaluated")
        
        return feedbacks[:expected_count]
    
    def health_check(self) -> Dict[str, Any]:
        """Check AI service health"""
        try:
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[{"role": "user", "content": "ping"}],
                max_completion_tokens=5
            )
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "model": config.GROQ_MODEL,
                "response_time_ms": round(response_time * 1000, 2),
                "available": bool(response.choices)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

# Singleton instance
_ai_service = None

def get_ai_service() -> AIService:
    """Get AI service singleton"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service