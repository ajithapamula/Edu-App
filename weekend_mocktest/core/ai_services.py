# weekend_mocktest/core/ai_services.py
"""
AI Services - UPDATED with AI Explanations for Evaluation

Features:
- Generates AI explanations for wrong answers
- Section-wise evaluation with detailed feedback
- Proper answer comparison logic
"""

import json
import logging
import re
from typing import Dict, List, Optional, Any
from groq import Groq

from .config import config
from .prompts import PromptTemplates

logger = logging.getLogger(__name__)


class AIService:
    """AI service using Groq for question generation and evaluation"""
    
    # STRICT indicators of actual coding questions
    CODING_QUESTION_INDICATORS = [
        'write a program', 'write a function', 'write a script',
        'write code', 'write python', 'implement a function',
        'create a function', 'create a program', 'create a class',
        'code to', 'program to', 'script to',
        'in python', 'in java', 'in javascript', 'using python',
        'python program', 'python function', 'python code',
        'java program', 'javascript function',
        'def ', 'class ', 'import ', 'from ', 'return ',
        'print(', 'input(', 'len(', 'range(', 'for i in',
        '>>>', '```python', '```java', '```',
        'if __name__', 'try:', 'except:', 'lambda',
        '__init__', 'self.', '.py',
        'recursion', 'algorithm', 'data structure',
        'loop', 'iterate', 'compile', 'debug',
        'syntax error', 'runtime error', 'exception handling',
        'output:', 'input:', 'expected output',
        '→', '->', 'returns'
    ]
    
    # SAP/Business terms - if present, question is VALID for non-dev
    SAP_BUSINESS_TERMS = [
        'sap', 'erp', 'enterprise', 'business', 'company', 'organization',
        'mm', 'sd', 'fico', 'hr', 'pp', 'wm', 'qm', 'pm',
        'procurement', 'purchase', 'vendor', 'supplier',
        'sales', 'customer', 'billing', 'invoice', 'payment',
        'finance', 'accounting', 'ledger', 'cost', 'profit',
        'material', 'inventory', 'stock', 'warehouse',
        'production', 'manufacturing', 'planning',
        'human resources', 'employee', 'payroll',
        'master data', 'transaction', 'document',
        'module', 'integration', 'workflow', 'process'
    ]
    
    def __init__(self):
        self.client = Groq(api_key=config.GROQ_API_KEY)
        self.model = config.GROQ_MODEL
        logger.info("🤖 AI Service initialized with AI Explanations support")
    
    def _is_coding_question(self, question_data: Dict) -> bool:
        """Check if question is about ACTUAL CODING"""
        question_text = str(question_data.get("question", "")).lower()
        title = str(question_data.get("title", "")).lower()
        
        options = question_data.get("options", [])
        options_text = ""
        if isinstance(options, list):
            options_text = " ".join([str(opt) for opt in options]).lower()
        elif isinstance(options, dict):
            options_text = " ".join([str(v) for v in options.values()]).lower()
        
        combined = f"{question_text} {title} {options_text}"
        
        # WHITELIST: If it contains SAP/Business terms, it's VALID
        for sap_term in self.SAP_BUSINESS_TERMS:
            if sap_term in combined:
                return False
        
        # BLACKLIST: Check for actual coding indicators
        for indicator in self.CODING_QUESTION_INDICATORS:
            if indicator in combined:
                return True
        
        # Check for code-like patterns
        code_patterns = [
            r'def\s+\w+\s*\(',
            r'class\s+\w+\s*[:\(]',
            r'import\s+\w+',
            r'from\s+\w+\s+import',
            r'print\s*\(["\']',
            r'\w+\s*=\s*\[',
            r'for\s+\w+\s+in\s+',
            r'while\s+\w+\s*[:<]',
            r'if\s+\w+\s*[=<>!]',
            r'\.\w+\(\)',
        ]
        
        for pattern in code_patterns:
            if re.search(pattern, combined):
                return True
        
        return False
    
    def _filter_coding_questions_for_nondev(self, questions: List[Dict]) -> List[Dict]:
        """Filter out actual coding questions for non-dev users."""
        filtered = []
        blocked_count = 0
        
        for q in questions:
            if q.get("question_type") == "coding":
                blocked_count += 1
                continue
            
            if self._is_coding_question(q):
                blocked_count += 1
            else:
                filtered.append(q)
        
        if blocked_count > 0:
            logger.info(f"✅ Blocked {blocked_count} programming questions for non-dev")
        
        return filtered
    
    def generate_questions_for_bank(self, user_type: str, question_type: str, 
                                    context: str, count: int) -> List[Dict]:
        """Generate questions using Groq AI"""
        
        if user_type == "non_dev" and question_type == "coding":
            logger.warning(f"🚫 Blocked coding question generation for non-dev")
            return []
        
        logger.info(f"{'🟠 NON-DEV' if user_type == 'non_dev' else '🟢 DEV'}: Generating {count} {question_type} questions")
        
        try:
            prompt = PromptTemplates.create_bank_generation_prompt(user_type, question_type, context, count)
            
            if not prompt:
                logger.error(f"No prompt for {user_type}/{question_type}")
                return []
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert question generator. Generate questions in valid JSON format only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            questions = self._parse_questions(content)
            
            if not questions:
                return []
            
            for q in questions:
                q["question_type"] = question_type
                q["user_type"] = user_type
            
            if user_type == "non_dev":
                questions = self._filter_coding_questions_for_nondev(questions)
            
            logger.info(f"✅ Generated {len(questions)} {question_type} questions")
            return questions
            
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            return []
    
    def _parse_questions(self, content: str) -> List[Dict]:
        """Parse questions from AI response"""
        questions = []
        
        try:
            parts = re.split(r'===\s*QUESTION\s*\d+\s*===', content)
            
            for part in parts:
                if not part.strip():
                    continue
                
                q = {}
                
                title_match = re.search(r'##\s*Title:\s*(.+)', part)
                if title_match:
                    q['title'] = title_match.group(1).strip()
                
                diff_match = re.search(r'##\s*Difficulty:\s*(\w+)', part)
                if diff_match:
                    q['difficulty'] = diff_match.group(1).strip()
                
                q_match = re.search(r'##\s*Question:\s*\n(.+?)(?=##\s*Options:|$)', part, re.DOTALL)
                if q_match:
                    q['question'] = q_match.group(1).strip()
                
                opts_match = re.search(r'##\s*Options:\s*\n(.+?)(?=##\s*Correct:|$)', part, re.DOTALL)
                if opts_match:
                    opts_text = opts_match.group(1)
                    options = []
                    for opt in re.findall(r'[A-D]\)\s*(.+)', opts_text):
                        options.append(opt.strip())
                    if options:
                        q['options'] = options
                
                correct_match = re.search(r'##\s*Correct:\s*([A-Da-d])', part)
                if correct_match:
                    letter = correct_match.group(1).upper()
                    q['correct_answer'] = letter
                    if q.get('options'):
                        idx = ord(letter) - ord('A')
                        if 0 <= idx < len(q['options']):
                            q['correct_option_text'] = q['options'][idx]
                
                if q.get('question'):
                    questions.append(q)
            
            if questions:
                return questions
        except Exception as e:
            logger.warning(f"Could not parse === format: {e}")
        
        # Fallback parsing methods
        try:
            return json.loads(content)
        except:
            pass
        
        try:
            match = re.search(r'\[[\s\S]*\]', content)
            if match:
                return json.loads(match.group())
        except:
            pass
        
        return []

    # ════════════════════════════════════════════════════════════
    # AI EXPLANATION GENERATION
    # ════════════════════════════════════════════════════════════
    
    def generate_explanation(self, question: str, user_answer: str, correct_answer: str, 
                            question_type: str, options: List[str] = None) -> str:
        """
        Generate AI explanation for why the correct answer is right
        and where the user went wrong (if applicable).
        """
        try:
            # Build context for explanation
            options_text = ""
            if options:
                options_text = "\nOptions:\n" + "\n".join([f"{chr(65+i)}) {opt}" for i, opt in enumerate(options)])
            
            prompt = f"""You are a helpful tutor. Explain the answer to this question concisely.

Question: {question}
{options_text}

User's Answer: {user_answer}
Correct Answer: {correct_answer}

Provide a brief explanation (2-3 sentences) that:
1. Explains why the correct answer is right
2. If the user was wrong, explain their likely mistake
3. Keep it educational and encouraging

Response format: Just the explanation text, no labels or formatting."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful educational tutor. Give brief, clear explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=200
            )
            
            explanation = response.choices[0].message.content.strip()
            return explanation
            
        except Exception as e:
            logger.warning(f"Failed to generate explanation: {e}")
            # Return a generic explanation if AI fails
            if user_answer.lower() == correct_answer.lower():
                return "Correct! Well done."
            else:
                return f"The correct answer is: {correct_answer}"

    def generate_batch_explanations(self, qa_pairs: List[Dict], question_type: str) -> List[str]:
        """
        Generate explanations for a batch of questions.
        More efficient than calling one by one.
        """
        explanations = []
        
        for qa in qa_pairs:
            question = qa.get("question", "")
            user_answer = qa.get("answer", "No answer")
            correct_answer = qa.get("correct_option_text") or qa.get("correct_answer", "N/A")
            options = qa.get("options", [])
            is_correct = qa.get("is_correct", False)
            
            if is_correct:
                # For correct answers, give brief positive feedback
                explanation = self._get_correct_answer_feedback(question_type)
            else:
                # For wrong answers, generate AI explanation
                explanation = self.generate_explanation(
                    question=question,
                    user_answer=user_answer,
                    correct_answer=correct_answer,
                    question_type=question_type,
                    options=options
                )
            
            explanations.append(explanation)
        
        return explanations
    
    def _get_correct_answer_feedback(self, question_type: str) -> str:
        """Get brief positive feedback for correct answers"""
        feedbacks = {
            "aptitude": [
                "Correct! Your logical reasoning is on point.",
                "Well done! You solved this problem correctly.",
                "Excellent! Your mathematical approach was correct."
            ],
            "mcq": [
                "Correct! You have a good understanding of this concept.",
                "Well done! Your knowledge is solid here.",
                "Excellent! You understood this topic well."
            ],
            "coding": [
                "Correct! Your solution approach was right.",
                "Well done! Your code logic is sound.",
                "Excellent! Good problem-solving skills."
            ]
        }
        
        import random
        options = feedbacks.get(question_type, feedbacks["mcq"])
        return random.choice(options)

    # ════════════════════════════════════════════════════════════
    # SECTION-WISE EVALUATION WITH AI EXPLANATIONS
    # ════════════════════════════════════════════════════════════
    
    def evaluate_by_section(self, user_type: str, sections: Dict) -> Dict:
        """
        Evaluate answers by section with AI explanations.
        
        Returns detailed evaluation with:
        - Section scores
        - Question-by-question results
        - AI explanations for each answer
        """
        all_scores = []
        all_feedbacks = []
        section_scores = {}
        section_details = {}  # NEW: Detailed results per section
        
        for section_name, qa_pairs in sections.items():
            if not qa_pairs:
                continue
            
            section_correct = 0
            section_total = len(qa_pairs)
            section_results = []  # Detailed results for this section
            
            logger.info(f"📊 Evaluating {section_name.upper()} section ({section_total} questions)")
            
            for idx, qa in enumerate(qa_pairs):
                user_answer = str(qa.get("answer", "")).strip()
                correct_letter = str(qa.get("correct_answer", "")).strip().upper()
                correct_text = str(qa.get("correct_option_text", "")).strip()
                question_text = qa.get("question", "")
                options = qa.get("options", [])
                
                # Determine if answer is correct
                is_correct = self._check_answer_correct(
                    user_answer=user_answer,
                    correct_letter=correct_letter,
                    correct_text=correct_text,
                    options=options
                )
                
                # Mark for explanation generation
                qa["is_correct"] = is_correct
                
                all_scores.append(1 if is_correct else 0)
                
                if is_correct:
                    section_correct += 1
                
                # Build result entry for this question
                result_entry = {
                    "question_number": idx + 1,
                    "question": question_text[:200] + "..." if len(question_text) > 200 else question_text,
                    "user_answer": user_answer if user_answer else "No answer provided",
                    "correct_answer": correct_text if correct_text else correct_letter,
                    "is_correct": is_correct,
                    "options": options,
                    "explanation": ""  # Will be filled below
                }
                
                section_results.append(result_entry)
            
            # Generate AI explanations for this section
            logger.info(f"🤖 Generating AI explanations for {section_name}...")
            explanations = self.generate_batch_explanations(qa_pairs, section_name)
            
            # Add explanations to results
            for i, explanation in enumerate(explanations):
                if i < len(section_results):
                    section_results[i]["explanation"] = explanation
                    all_feedbacks.append(explanation)
            
            # Calculate section score
            section_pct = round((section_correct / section_total) * 100, 1) if section_total > 0 else 0
            section_scores[section_name] = {
                "correct": section_correct,
                "total": section_total,
                "percentage": section_pct
            }
            
            # Store detailed results
            section_details[section_name] = {
                "score": {
                    "correct": section_correct,
                    "total": section_total,
                    "percentage": section_pct
                },
                "questions": section_results
            }
            
            logger.info(f"✅ {section_name.upper()}: {section_correct}/{section_total} ({section_pct}%)")
        
        total_correct = sum(all_scores)
        total_questions = len(all_scores)
        overall_pct = round((total_correct / total_questions) * 100, 1) if total_questions > 0 else 0
        
        # Generate overall report
        report = self._generate_detailed_report(user_type, section_details, total_correct, total_questions)
        
        return {
            "scores": all_scores,
            "feedbacks": all_feedbacks,
            "total_correct": total_correct,
            "total_questions": total_questions,
            "overall_percentage": overall_pct,
            "section_scores": section_scores,
            "section_details": section_details,  # NEW: Detailed per-section results
            "evaluation_report": report
        }
    
    def _check_answer_correct(self, user_answer: str, correct_letter: str, 
                              correct_text: str, options: List) -> bool:
        """Check if user's answer is correct using multiple comparison methods"""
        if not user_answer:
            return False
        
        user_lower = user_answer.lower().strip()
        
        # Method 1: Direct match with correct letter (A, B, C, D)
        if user_lower == correct_letter.lower():
            return True
        
        # Method 2: Match with correct option text
        if correct_text and user_lower == correct_text.lower().strip():
            return True
        
        # Method 3: Partial match (for longer answers)
        if correct_text and len(correct_text) > 3:
            if user_lower in correct_text.lower() or correct_text.lower() in user_lower:
                return True
        
        # Method 4: If user submitted option index (0, 1, 2, 3)
        if user_answer.isdigit() and options:
            user_idx = int(user_answer)
            if 0 <= user_idx < len(options):
                selected_option = str(options[user_idx]).lower().strip()
                if correct_text and selected_option == correct_text.lower().strip():
                    return True
                # Check if index matches correct letter
                expected_idx = ord(correct_letter.upper()) - ord('A')
                if user_idx == expected_idx:
                    return True
        
        # Method 5: If user submitted full option text, find which option it matches
        if options:
            for i, opt in enumerate(options):
                if user_lower == str(opt).lower().strip():
                    expected_idx = ord(correct_letter.upper()) - ord('A')
                    if i == expected_idx:
                        return True
                    if correct_text and str(opt).lower().strip() == correct_text.lower().strip():
                        return True
        
        return False
    
    def _generate_detailed_report(self, user_type: str, section_details: Dict, 
                                   total_correct: int, total_questions: int) -> str:
        """Generate a detailed evaluation report"""
        overall_pct = round((total_correct / total_questions) * 100, 1) if total_questions > 0 else 0
        
        track_name = "Non-Developer" if user_type == "non_dev" else "Developer"
        
        report = f"""
═══════════════════════════════════════════════════════════════
                    {track_name.upper()} MOCK TEST RESULTS
═══════════════════════════════════════════════════════════════

📊 OVERALL SCORE: {total_correct}/{total_questions} ({overall_pct}%)

"""
        
        # Performance level
        if overall_pct >= 80:
            report += "🏆 Performance: EXCELLENT - Outstanding work!\n"
        elif overall_pct >= 60:
            report += "👍 Performance: GOOD - Keep improving!\n"
        elif overall_pct >= 40:
            report += "📚 Performance: AVERAGE - More practice needed\n"
        else:
            report += "⚠️ Performance: NEEDS IMPROVEMENT - Review the material\n"
        
        report += "\n═══════════════════════════════════════════════════════════════\n"
        report += "                     SECTION-WISE BREAKDOWN\n"
        report += "═══════════════════════════════════════════════════════════════\n\n"
        
        # Section-wise summary
        for section_name, details in section_details.items():
            score = details["score"]
            icon = "🧮" if section_name == "aptitude" else "📚" if section_name == "mcq" else "💻"
            status = "✅" if score["percentage"] >= 50 else "⚠️"
            
            report += f"{icon} {section_name.upper()} SECTION {status}\n"
            report += f"   Score: {score['correct']}/{score['total']} ({score['percentage']}%)\n\n"
        
        report += "═══════════════════════════════════════════════════════════════\n"
        report += "                     DETAILED QUESTION REVIEW\n"
        report += "═══════════════════════════════════════════════════════════════\n\n"
        
        # Detailed question review per section
        for section_name, details in section_details.items():
            icon = "🧮" if section_name == "aptitude" else "📚" if section_name == "mcq" else "💻"
            report += f"\n{icon} {section_name.upper()} SECTION REVIEW:\n"
            report += "─" * 60 + "\n"
            
            for q in details["questions"]:
                status = "✅" if q["is_correct"] else "❌"
                report += f"\nQ{q['question_number']}. {status}\n"
                report += f"   Question: {q['question'][:100]}...\n" if len(q['question']) > 100 else f"   Question: {q['question']}\n"
                report += f"   Your Answer: {q['user_answer']}\n"
                report += f"   Correct Answer: {q['correct_answer']}\n"
                report += f"   📝 {q['explanation']}\n"
        
        # Recommendations
        report += "\n═══════════════════════════════════════════════════════════════\n"
        report += "                       RECOMMENDATIONS\n"
        report += "═══════════════════════════════════════════════════════════════\n\n"
        
        weak_sections = [name for name, details in section_details.items() 
                        if details["score"]["percentage"] < 50]
        
        if weak_sections:
            report += "Focus areas for improvement:\n"
            for section in weak_sections:
                if section == "aptitude":
                    report += "• Aptitude: Practice more logical reasoning and quantitative problems\n"
                elif section == "mcq":
                    if user_type == "non_dev":
                        report += "• MCQ: Review SAP module concepts and business processes\n"
                    else:
                        report += "• MCQ/Theory: Review programming concepts and theory\n"
                elif section == "coding":
                    report += "• Coding: Practice more coding problems and improve problem-solving\n"
        else:
            report += "Great job! Keep up the excellent work across all sections.\n"
        
        return report


# Singleton
_ai_service = None

def get_ai_service() -> AIService:
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service