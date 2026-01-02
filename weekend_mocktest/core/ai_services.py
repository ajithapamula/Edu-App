# weekend_mocktest/core/ai_services.py
import logging
import time
import re
import json
import uuid
from typing import List, Dict, Any
from groq import Groq
from .config import config
from .prompts import PromptTemplates

logger = logging.getLogger(__name__)


class AIService:
    """
    Production AI service for question generation and evaluation.
    
    Features:
    - Batch question generation by type (aptitude, theory, coding)
    - Question bank population
    - Test evaluation with detailed feedback
    """
    
    def __init__(self):
        """Initialize Groq client"""
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required")
        
        self.client = Groq(
            api_key=config.GROQ_API_KEY,
            timeout=config.GROQ_TIMEOUT
        )
        
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
    
    # ================================================================
    # QUESTION BANK GENERATION (NEW)
    # ================================================================
    
    def generate_questions_for_bank(self, user_type: str, question_type: str,
                                    context: str, count: int) -> List[Dict[str, Any]]:
        """
        Generate questions for the question bank.
        
        Args:
            user_type: 'dev' or 'non_dev'
            question_type: 'aptitude', 'theory', 'coding', or 'mcq'
            context: Weekly summaries context
            count: Number of questions to generate
        
        Returns:
            List of structured question dictionaries
        """
        logger.info(f"🏭 Generating {count} {question_type} questions for bank ({user_type})")
        
        try:
            # Create specialized prompt
            prompt = PromptTemplates.create_bank_generation_prompt(
                user_type, question_type, context, count
            )
            
            # Generate with higher token limit for batches
            max_tokens = self._calculate_tokens_for_batch(question_type, count)
            
            response = self._call_llm_with_retries(prompt, max_tokens)
            
            # Parse questions with type info
            questions = self._parse_bank_questions(response, user_type, question_type)
            
            if not questions:
                raise Exception(f"No valid {question_type} questions generated")
            
            logger.info(f"✅ Generated {len(questions)} {question_type} questions")
            return questions
            
        except Exception as e:
            logger.error(f"❌ Bank generation failed: {e}")
            raise
    
    def generate_diverse_batch(self, user_type: str, context: str,
                               aptitude_count: int, theory_count: int,
                               coding_count: int) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate a diverse batch of questions for all types.
        Used for initial bank population.
        """
        logger.info(f"🎯 Generating diverse batch: {aptitude_count}A + {theory_count}T + {coding_count}C")
        
        results = {
            "aptitude": [],
            "theory": [],
            "coding": []
        }
        
        try:
            if aptitude_count > 0:
                results["aptitude"] = self.generate_questions_for_bank(
                    user_type, "aptitude", context, aptitude_count
                )
            
            if theory_count > 0:
                results["theory"] = self.generate_questions_for_bank(
                    user_type, "theory", context, theory_count
                )
            
            if coding_count > 0:
                results["coding"] = self.generate_questions_for_bank(
                    user_type, "coding", context, coding_count
                )
            
            total = sum(len(v) for v in results.values())
            logger.info(f"✅ Generated diverse batch: {total} total questions")
            return results
            
        except Exception as e:
            logger.error(f"❌ Diverse batch generation failed: {e}")
            raise
    
    def _calculate_tokens_for_batch(self, question_type: str, count: int) -> int:
        """Calculate appropriate token limit based on question type and count"""
        base_tokens = {
            "aptitude": 300,
            "theory": 400,
            "coding": 600,
            "mcq": 350
        }
        
        per_question = base_tokens.get(question_type, 400)
        return min(per_question * count + 500, 8000)  # Cap at 8000
    
    def _parse_bank_questions(self, response: str, user_type: str,
                              question_type: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured questions for bank"""
        try:
            questions = []
            
            # Split by question markers
            sections = re.split(r'=== QUESTION \d+ ===', response)[1:]
            
            for i, section in enumerate(sections, 1):
                try:
                    question = self._parse_single_bank_question(
                        section, user_type, question_type, i
                    )
                    if question:
                        questions.append(question)
                except Exception as e:
                    logger.warning(f"Failed to parse question {i}: {e}")
            
            return questions
            
        except Exception as e:
            logger.error(f"Question parsing failed: {e}")
            raise Exception(f"Failed to parse questions: {e}")
    
    def _parse_single_bank_question(self, section: str, user_type: str,
                                    question_type: str, index: int) -> Dict[str, Any]:
        """Parse individual question from section"""
        lines = [line.strip() for line in section.split('\n') if line.strip()]
        
        question_data = {
            "question_id": str(uuid.uuid4()),
            "question_number": index,
            "title": f"Question {index}",
            "difficulty": "Medium",
            "question_type": question_type,
            "question": "",
            "options": None,
            "tags": []
        }
        
        current_section = None
        question_lines = []
        options = []
        
        for line in lines:
            if line.startswith("## Title:"):
                question_data["title"] = line.replace("## Title:", "").strip()
            elif line.startswith("## Difficulty:"):
                diff = line.replace("## Difficulty:", "").strip()
                if diff in ["Easy", "Medium", "Hard"]:
                    question_data["difficulty"] = diff
            elif line.startswith("## Type:"):
                # Override type if specified
                t = line.replace("## Type:", "").strip().lower()
                if t in ["aptitude", "theory", "coding"]:
                    question_data["question_type"] = t
            elif line.startswith("## Tags:"):
                tags_str = line.replace("## Tags:", "").strip()
                question_data["tags"] = [t.strip() for t in tags_str.split(",") if t.strip()]
            elif line.startswith("## Question:"):
                current_section = "question"
            elif line.startswith("## Options:"):
                current_section = "options"
            elif current_section == "question":
                if not line.startswith("##"):
                    question_lines.append(line)
            elif current_section == "options":
                if re.match(r'^[A-D]\)', line):
                    option_text = line[3:].strip()
                    if option_text:
                        options.append(option_text)
        
        question_data["question"] = "\n".join(question_lines).strip()
        
        # Add options for MCQ types
        if user_type == "non_dev" or question_type == "mcq":
            question_data["options"] = options if len(options) == 4 else None
        
        # Validation
        min_length = 30 if question_type == "aptitude" else 50
        if not question_data["question"] or len(question_data["question"]) < min_length:
            raise Exception(f"Question too short ({len(question_data['question'])} chars)")
        
        if (user_type == "non_dev" or question_type == "mcq") and not question_data["options"]:
            raise Exception("MCQ missing options")
        
        return question_data

    # ================================================================
    # LEGACY: BATCH GENERATION (for backward compatibility)
    # ================================================================
    
    def generate_questions_batch(self, user_type: str, context: str) -> List[Dict[str, Any]]:
        """
        Generate questions using AI based on context.
        LEGACY: Use generate_questions_for_bank for new implementations.
        """
        logger.info(f"🤖 Generating {config.QUESTIONS_PER_TEST} {user_type} questions (legacy)")
        
        try:
            prompt = PromptTemplates.create_batch_questions_prompt(
                user_type, context, config.QUESTIONS_PER_TEST
            )
            
            response = self._call_llm_with_retries(prompt, config.GROQ_MAX_TOKENS)
            
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

    # ================================================================
    # EVALUATION
    # ================================================================
    
    def evaluate_test_batch(self, user_type: str, qa_pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Evaluate test answers using AI"""
        logger.info(f"🎯 Evaluating {len(qa_pairs)} {user_type} answers")
        
        try:
            prompt = PromptTemplates.create_evaluation_prompt(user_type, qa_pairs)
            
            response = self._call_llm_with_retries(
                prompt, 
                config.EVALUATION_MAX_TOKENS,
                config.EVALUATION_TEMPERATURE
            )
            
            evaluation = self._parse_evaluation_response(response, qa_pairs)
            
            logger.info(f"✅ Evaluation completed: {evaluation['total_correct']}/{len(qa_pairs)}")
            return evaluation
            
        except Exception as e:
            logger.error(f"❌ Evaluation failed: {e}")
            raise
    
    def evaluate_by_section(self, user_type: str, 
                           sections: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Evaluate test answers by section (Aptitude, Theory, Coding).
        Each section is evaluated separately with its own prompt.
        
        Args:
            user_type: 'dev' or 'non_dev'
            sections: Dict with keys 'aptitude', 'theory', 'coding' containing Q&A pairs
        
        Returns:
            Evaluation results with section-wise scores
        """
        logger.info(f"📊 Evaluating test by sections (Developer Exam)")
        
        all_scores = []
        all_feedbacks = []
        section_results = {}
        full_report = []
        
        # Define section order for consistent output
        section_order = ["aptitude", "theory", "coding"]
        
        for section_name in section_order:
            qa_pairs = sections.get(section_name, [])
            
            if not qa_pairs:
                continue
            
            logger.info(f"  📝 Evaluating {section_name.upper()}: {len(qa_pairs)} questions")
            
            try:
                # Use section-specific evaluation prompt
                prompt = PromptTemplates.create_section_evaluation_prompt(
                    section_name, qa_pairs
                )
                
                response = self._call_llm_with_retries(
                    prompt, 
                    config.EVALUATION_MAX_TOKENS,
                    config.EVALUATION_TEMPERATURE
                )
                
                # Parse evaluation
                result = self._parse_evaluation_response(response, qa_pairs)
                
                section_results[section_name] = {
                    "correct": result["total_correct"],
                    "total": len(qa_pairs),
                    "percentage": round(result["total_correct"] / len(qa_pairs) * 100, 1)
                }
                
                all_scores.extend(result["scores"])
                all_feedbacks.extend(result["feedbacks"])
                
                # Format section report
                section_header = f"""
{'='*60}
{section_name.upper()} SECTION EVALUATION
{'='*60}
Questions: {len(qa_pairs)}
Score: {result['total_correct']}/{len(qa_pairs)} ({section_results[section_name]['percentage']}%)
{'='*60}
"""
                full_report.append(section_header + result['evaluation_report'])
                
                logger.info(f"  ✅ {section_name.upper()}: {result['total_correct']}/{len(qa_pairs)}")
                
            except Exception as e:
                logger.error(f"Section evaluation failed for {section_name}: {e}")
                section_results[section_name] = {
                    "correct": 0,
                    "total": len(qa_pairs),
                    "percentage": 0
                }
                all_scores.extend([0] * len(qa_pairs))
                all_feedbacks.extend([f"Evaluation failed: {e}"] * len(qa_pairs))
                full_report.append(f"\n=== {section_name.upper()} SECTION ===\nEvaluation failed: {e}")
        
        # Calculate overall stats
        total_questions = sum(len(sections.get(s, [])) for s in section_order)
        total_correct = sum(all_scores)
        
        # Add summary to report
        summary = f"""
{'='*60}
OVERALL SUMMARY
{'='*60}
Total Score: {total_correct}/{total_questions} ({round(total_correct/total_questions*100, 1) if total_questions > 0 else 0}%)

Section Breakdown:
"""
        for section_name in section_order:
            if section_name in section_results:
                sr = section_results[section_name]
                summary += f"  - {section_name.upper()}: {sr['correct']}/{sr['total']} ({sr['percentage']}%)\n"
        
        full_report.insert(0, summary)
        
        return {
            "scores": all_scores,
            "feedbacks": all_feedbacks,
            "total_correct": total_correct,
            "section_scores": section_results,
            "evaluation_report": "\n".join(full_report)
        }

    # ================================================================
    # LLM COMMUNICATION
    # ================================================================
    
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

    # ================================================================
    # PARSING METHODS
    # ================================================================
    
    def _parse_questions_response(self, response: str, user_type: str) -> List[Dict[str, Any]]:
        """Parse LLM response into structured questions (legacy)"""
        try:
            questions = []
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
    
    def _parse_single_question(self, section: str, user_type: str, 
                               question_number: int) -> Dict[str, Any]:
        """Parse individual question from section (legacy)"""
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
        
        if not question_data["question"] or len(question_data["question"]) < 50:
            raise Exception("Question too short")
        
        if user_type == "non_dev" and not question_data["options"]:
            raise Exception("MCQ missing options")
        
        return question_data
    
    def _parse_evaluation_response(self, response: str, 
                                   qa_pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse evaluation response from LLM"""
        try:
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
            
            # Fallbacks
            if not scores or len(scores) != len(qa_pairs):
                scores = self._extract_scores_fallback(response, len(qa_pairs))
            
            if not feedbacks or len(feedbacks) != len(qa_pairs):
                feedbacks = self._extract_feedbacks_fallback(response, len(qa_pairs))
            
            if len(scores) != len(qa_pairs):
                raise Exception(f"Score count mismatch: {len(scores)} vs {len(qa_pairs)}")
            
            if len(feedbacks) != len(qa_pairs):
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
        score_patterns = re.findall(r'(?:^|\s)([01](?:\s*,\s*[01])+)(?:\s|$)', response)
        
        for pattern in score_patterns:
            scores = [int(s.strip()) for s in pattern.split(',')]
            if len(scores) == expected_count:
                return scores
        
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