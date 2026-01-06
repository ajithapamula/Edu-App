# weekend_mocktest/core/ai_services.py
# FIXED: Dev=3 section eval, NonDev=2 section eval
import logging
import re
import uuid
from typing import List, Dict, Any
from groq import Groq
from .config import config
from .prompts import PromptTemplates

logger = logging.getLogger(__name__)


class AIService:
    """AI service for question generation and evaluation"""

    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        logger.info("🤖 AI Service initialized")

    def _call_llm_with_retries(self, prompt: str, max_tokens: int = None, 
                               temperature: float = None) -> str:
        """Call LLM with retries"""
        max_tokens = max_tokens or config.GROQ_MAX_TOKENS
        temperature = temperature or config.GROQ_TEMPERATURE
        
        for attempt in range(config.MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model=config.GROQ_MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert question generator and evaluator."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=config.GROQ_TIMEOUT
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
                if attempt == config.MAX_RETRIES - 1:
                    raise
        return ""

    def generate_questions_for_bank(self, user_type: str, question_type: str,
                                    context: str, count: int) -> List[Dict[str, Any]]:
        """Generate questions for question bank"""
        logger.info(f"🔧 Generating {count} {question_type} questions for {user_type}")
        
        try:
            prompt = PromptTemplates.create_bank_generation_prompt(
                user_type, question_type, context, count
            )
            
            response = self._call_llm_with_retries(prompt, config.GROQ_MAX_TOKENS, 0.7)
            questions = self._parse_generated_questions(response, user_type, question_type)
            
            logger.info(f"✅ Generated {len(questions)} {question_type} questions")
            return questions[:count]
            
        except Exception as e:
            logger.error(f"❌ Question generation failed: {e}")
            return []

    def _parse_generated_questions(self, response: str, user_type: str, 
                                   question_type: str) -> List[Dict[str, Any]]:
        """Parse generated questions from LLM response"""
        questions = []
        
        # Split by question markers
        parts = re.split(r'===\s*QUESTION\s*\d+\s*===', response, flags=re.IGNORECASE)
        
        for part in parts[1:]:  # Skip first empty part
            try:
                question_data = self._parse_single_question(part.strip(), user_type, question_type)
                if question_data and question_data.get("question"):
                    question_data["question_id"] = str(uuid.uuid4())
                    questions.append(question_data)
            except Exception as e:
                logger.debug(f"Failed to parse question: {e}")
                continue
        
        return questions

    def _parse_single_question(self, text: str, user_type: str, 
                               question_type: str) -> Dict[str, Any]:
        """Parse a single question from text"""
        question_data = {
            "title": "Question",
            "difficulty": "Medium",
            "question_type": question_type,
            "question": "",
            "options": None,
            "correct_answer": None,
            "correct_option_text": None
        }
        
        lines = text.strip().split('\n')
        question_lines = []
        options = []
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("## Title:"):
                question_data["title"] = line.replace("## Title:", "").strip()
            elif line.startswith("## Difficulty:"):
                diff = line.replace("## Difficulty:", "").strip()
                if diff in ["Easy", "Medium", "Hard"]:
                    question_data["difficulty"] = diff
            elif line.startswith("## Type:"):
                t = line.replace("## Type:", "").strip().lower()
                if t in ["aptitude", "mcq", "coding"]:
                    question_data["question_type"] = t
            elif line.startswith("## Correct:"):
                correct = line.replace("## Correct:", "").strip().upper()
                if correct in ["A", "B", "C", "D"]:
                    question_data["correct_answer"] = correct
            elif line.startswith("## Question:"):
                current_section = "question"
                inline = line.replace("## Question:", "").strip()
                if inline:
                    question_lines.append(inline)
            elif line.startswith("## Options:"):
                current_section = "options"
            elif current_section == "question" and not line.startswith("##") and not re.match(r'^[A-D]\)', line):
                question_lines.append(line)
            elif re.match(r'^[A-D]\)', line):
                current_section = "options"
                option_text = line[3:].strip()
                if option_text:
                    options.append(option_text)
        
        question_data["question"] = "\n".join(question_lines).strip()
        
        # Add options for MCQ types
        if question_type in ["mcq", "aptitude"]:
            if len(options) >= 3:
                question_data["options"] = options[:4]
                # Map correct answer
                if question_data["correct_answer"] and question_data["options"]:
                    idx = {"A": 0, "B": 1, "C": 2, "D": 3}.get(question_data["correct_answer"], 0)
                    if idx < len(question_data["options"]):
                        question_data["correct_option_text"] = question_data["options"][idx]
        
        return question_data

    # ================================================================
    # EVALUATION BY SECTION
    # ================================================================

    def evaluate_by_section(self, user_type: str, 
                           sections: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Evaluate test by sections.
        
        DEVELOPER (user_type='dev'): 3 sections
          - aptitude
          - mcq
          - coding
        
        NON-DEVELOPER (user_type='non_dev'): 2 sections only
          - aptitude
          - mcq
          - NO CODING!
        """
        logger.info(f"📊 Evaluating {user_type} test by sections")
        
        all_scores = []
        all_feedbacks = []
        section_results = {}
        full_report = []
        
        # Define section order based on user type
        if user_type == "non_dev":
            section_order = ["aptitude", "mcq"]  # 2 sections only
            logger.info("  NON-DEV: Evaluating 2 sections (Aptitude, MCQ)")
        else:
            section_order = ["aptitude", "mcq", "coding"]  # 3 sections
            logger.info("  DEV: Evaluating 3 sections (Aptitude, MCQ, Coding)")
        
        for section_name in section_order:
            qa_pairs = sections.get(section_name, [])
            
            if not qa_pairs:
                logger.info(f"  ⏭️ Skipping {section_name}: no questions")
                continue
            
            logger.info(f"  📝 Evaluating {section_name.upper()}: {len(qa_pairs)} questions")
            
            try:
                prompt = PromptTemplates.create_section_evaluation_prompt(section_name, qa_pairs)
                response = self._call_llm_with_retries(
                    prompt, config.EVALUATION_MAX_TOKENS, config.EVALUATION_TEMPERATURE
                )
                
                result = self._parse_evaluation_response(response, qa_pairs)
                
                section_results[section_name] = {
                    "correct": result["total_correct"],
                    "total": len(qa_pairs),
                    "percentage": round(result["total_correct"] / len(qa_pairs) * 100, 1)
                }
                
                all_scores.extend(result["scores"])
                all_feedbacks.extend(result["feedbacks"])
                
                report_header = f"\n{'='*50}\n{section_name.upper()} SECTION\n{'='*50}\n"
                report_header += f"Score: {result['total_correct']}/{len(qa_pairs)}\n"
                full_report.append(report_header + result.get('evaluation_report', ''))
                
                logger.info(f"  ✅ {section_name.upper()}: {result['total_correct']}/{len(qa_pairs)}")
                
            except Exception as e:
                logger.error(f"  ❌ {section_name} evaluation failed: {e}")
                section_results[section_name] = {"correct": 0, "total": len(qa_pairs), "percentage": 0}
                all_scores.extend([0] * len(qa_pairs))
                all_feedbacks.extend([f"Evaluation failed: {e}"] * len(qa_pairs))
        
        # Calculate totals
        total_questions = sum(len(sections.get(s, [])) for s in section_order)
        total_correct = sum(all_scores)
        
        # Summary
        summary = f"\n{'='*50}\nOVERALL SUMMARY\n{'='*50}\n"
        summary += f"Total: {total_correct}/{total_questions}\n\n"
        for sec in section_order:
            if sec in section_results:
                sr = section_results[sec]
                summary += f"  {sec.upper()}: {sr['correct']}/{sr['total']} ({sr['percentage']}%)\n"
        
        full_report.insert(0, summary)
        
        return {
            "scores": all_scores,
            "feedbacks": all_feedbacks,
            "total_correct": total_correct,
            "percentage": round(total_correct / total_questions * 100, 1) if total_questions > 0 else 0,
            "section_scores": section_results,
            "evaluation_report": "\n".join(full_report)
        }

    def _parse_evaluation_response(self, response: str, 
                                   qa_pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Parse evaluation response"""
        scores = []
        feedbacks = []
        
        # Try to parse structured format
        for i, qa in enumerate(qa_pairs, 1):
            # Look for score pattern
            score_pattern = rf'Q{i}[:\s]*(\d+)[/\s]*\d*|Question\s*{i}[:\s]*(\d+)'
            match = re.search(score_pattern, response, re.IGNORECASE)
            
            if match:
                score = int(match.group(1) or match.group(2) or 0)
                scores.append(min(score, 1))  # Normalize to 0 or 1
            else:
                # Try to match by answer comparison
                user_answer = str(qa.get("answer", "")).strip().lower()
                correct = str(qa.get("correct_option_text") or qa.get("correct_answer", "")).strip().lower()
                
                if user_answer and correct and (user_answer == correct or user_answer in correct or correct in user_answer):
                    scores.append(1)
                else:
                    scores.append(0)
            
            # Extract feedback
            feedback_pattern = rf'Q{i}[^Q]*?feedback[:\s]*([^\n]+)|Question\s*{i}[^Q]*?([^\n]+)'
            fb_match = re.search(feedback_pattern, response, re.IGNORECASE)
            feedbacks.append(fb_match.group(1).strip() if fb_match and fb_match.group(1) else "")
        
        # Fill missing
        while len(scores) < len(qa_pairs):
            scores.append(0)
        while len(feedbacks) < len(qa_pairs):
            feedbacks.append("")
        
        return {
            "scores": scores,
            "feedbacks": feedbacks,
            "total_correct": sum(scores),
            "evaluation_report": response
        }


# Singleton
_ai_service = None

def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service