# weekend_mocktest/core/prompts.py
from typing import List, Dict, Any
from .config import config

class PromptTemplates:
    """Optimized prompt templates for AI question generation and evaluation"""
    
    @staticmethod
    def create_batch_questions_prompt(user_type: str, context: str, question_count: int = None) -> str:
        """Create prompt for batch question generation"""
        if question_count is None:
            question_count = config.QUESTIONS_PER_TEST
        
        if user_type == "dev":
            return PromptTemplates._dev_batch_prompt(context, question_count)
        else:
            return PromptTemplates._non_dev_batch_prompt(context, question_count)
    
    @staticmethod
    def _dev_batch_prompt(context: str, question_count: int) -> str:
        """Developer questions generation prompt"""
        return f"""Generate {question_count} high-quality programming questions based on the provided context. Create practical, challenging questions that test real development skills and problem-solving abilities.

CONTEXT:
{context}

REQUIREMENTS:
- Generate exactly {question_count} questions numbered sequentially
- Mix question types: 40% practical coding, 30% system design, 30% debugging/optimization
- Progressive difficulty: start easier, increase complexity
- Each question must be complete and standalone
- Include clear requirements, constraints, and expected outcomes
- Base questions on concepts and technologies mentioned in the context
- Make questions realistic and industry-relevant

FORMAT each question exactly as shown:
=== QUESTION 1 ===
## Title: [Clear, descriptive title]
## Difficulty: [Easy/Medium/Hard]
## Type: [Practical/Algorithm/System Design/Debugging]
## Question:
[Complete question with detailed requirements, constraints, input/output examples, and any code snippets needed. Include specific technical requirements and success criteria.]

=== QUESTION 2 ===
## Title: [Clear, descriptive title]
## Difficulty: [Easy/Medium/Hard]
## Type: [Practical/Algorithm/System Design/Debugging]
## Question:
[Complete question with detailed requirements...]

Continue this exact pattern for all {question_count} questions.

IMPORTANT: 
- Each question should test different aspects of development
- Include code examples where relevant
- Specify performance requirements when applicable
- Make questions challenging but solvable by a competent developer
- Ensure questions relate to the provided context

Generate all {question_count} questions now:"""

    @staticmethod
    def _non_dev_batch_prompt(context: str, question_count: int) -> str:
        """Non-developer questions generation prompt"""
        return f"""Generate {question_count} high-quality multiple-choice questions based on the provided context. Focus on conceptual understanding, analytical thinking, and practical application of technical concepts for non-technical professionals.

CONTEXT:
{context}

REQUIREMENTS:
- Generate exactly {question_count} questions numbered sequentially
- Each question must have exactly 4 options (A, B, C, D) with only 1 correct answer
- Mix question types: 40% conceptual understanding, 30% analytical reasoning, 30% practical application
- Progressive difficulty: start with fundamental concepts, advance to complex analysis
- Create sophisticated distractors based on common misconceptions
- Test deep understanding rather than memorization
- Base questions on concepts and scenarios from the provided context

FORMAT each question exactly as shown:
=== QUESTION 1 ===
## Title: [Clear, descriptive title]
## Difficulty: [Easy/Medium/Hard]
## Type: [Conceptual/Analytical/Applied]
## Question:
[Clear, specific question that tests understanding of concepts from the context. Include scenario or case study if relevant.]
## Options:
A) [First option - could be correct or plausible distractor]
B) [Second option - could be correct or plausible distractor]
C) [Third option - could be correct or plausible distractor]
D) [Fourth option - could be correct or plausible distractor]

=== QUESTION 2 ===
## Title: [Clear, descriptive title]
## Difficulty: [Easy/Medium/Hard]
## Type: [Conceptual/Analytical/Applied]
## Question:
[Clear question testing different concept...]
## Options:
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]

Continue this exact pattern for all {question_count} questions.

IMPORTANT:
- Only one option should be clearly correct for each question
- Distractors should be plausible but clearly wrong to someone who understands the concept
- Questions should test understanding, not just recall
- Relate all questions to concepts mentioned in the provided context
- Avoid trick questions or ambiguous wording

Generate all {question_count} questions now:"""

    @staticmethod
    def create_evaluation_prompt(user_type: str, qa_pairs: List[Dict[str, Any]]) -> str:
        """Create prompt for evaluating test answers"""
        
        # Format QA pairs for evaluation
        qa_text = []
        for i, qa in enumerate(qa_pairs, 1):
            question = qa['question'][:300] + "..." if len(qa['question']) > 300 else qa['question']
            answer = qa['answer'][:200] + "..." if len(qa['answer']) > 200 else qa['answer']
            qa_text.append(f"QUESTION {i}:\n{question}\n\nSTUDENT ANSWER:\n{answer}")
        
        qa_content = "\n\n" + "="*50 + "\n\n".join(qa_text)
        
        if user_type == "dev":
            return PromptTemplates._dev_evaluation_prompt(qa_content, len(qa_pairs))
        else:
            return PromptTemplates._non_dev_evaluation_prompt(qa_content, len(qa_pairs))
    
    @staticmethod
    def _dev_evaluation_prompt(qa_content: str, question_count: int) -> str:
        """Developer answers evaluation prompt"""
        return f"""Evaluate this developer assessment comprehensively. Analyze code quality, problem-solving approach, technical accuracy, and software engineering best practices.

ASSESSMENT CONTENT:
{qa_content}

EVALUATION CRITERIA:
- Code correctness and functionality (30%)
- Algorithm efficiency and optimization (25%)
- Code readability and structure (20%)
- Best practices and conventions (15%)
- Problem-solving approach and explanation (10%)

INSTRUCTIONS:
1. Score each question as 1 (acceptable/correct) or 0 (unacceptable/incorrect)
2. Be strict but fair - partial credit should round to 1 if approach is sound
3. Consider: Does the answer demonstrate competent programming skills?
4. Evaluate explanations and reasoning, not just code
5. Look for understanding of time/space complexity where relevant

REQUIRED OUTPUT FORMAT:
SCORES: [1,0,1,1,0]
FEEDBACK: [Question 1: Detailed feedback|Question 2: Detailed feedback|Question 3: Detailed feedback|Question 4: Detailed feedback|Question 5: Detailed feedback]

DETAILED ANALYSIS:
Provide comprehensive analysis covering:
- Overall programming competency level
- Strengths observed in coding approach
- Areas needing improvement
- Specific technical recommendations
- Assessment of problem-solving methodology

Score each of the {question_count} questions and provide detailed feedback. Be thorough and constructive."""

    @staticmethod
    def _non_dev_evaluation_prompt(qa_content: str, question_count: int) -> str:
        """Non-developer answers evaluation prompt"""
        return f"""Evaluate this non-developer assessment comprehensively. Focus on conceptual understanding, analytical reasoning, and practical knowledge application.

ASSESSMENT CONTENT:
{qa_content}

EVALUATION CRITERIA:
- Conceptual accuracy and understanding (40%)
- Analytical reasoning quality (30%)
- Practical application knowledge (20%)
- Communication and explanation clarity (10%)

INSTRUCTIONS:
1. Score each question as 1 (correct) or 0 (incorrect)
2. For multiple choice: only exact correct answers get 1 point
3. Evaluate understanding demonstrated in any explanations provided
4. Consider partial understanding but be consistent with scoring
5. Look for evidence of genuine comprehension vs. guessing

REQUIRED OUTPUT FORMAT:
SCORES: [1,0,1,1,0]
FEEDBACK: [Question 1: Clear feedback on answer|Question 2: Clear feedback on answer|Question 3: Clear feedback on answer|Question 4: Clear feedback on answer|Question 5: Clear feedback on answer]

DETAILED ANALYSIS:
Provide comprehensive analysis covering:
- Overall conceptual understanding level
- Analytical thinking capabilities
- Knowledge gaps identified
- Recommendations for further learning
- Assessment of technical awareness

Score each of the {question_count} questions and provide specific feedback. Focus on understanding rather than memorization."""

    @staticmethod
    def optimize_context_prompt(context: str) -> str:
        """Optimize context for better question generation"""
        return f"""Analyze and enhance this technical content to make it optimal for generating high-quality assessment questions.

ORIGINAL CONTEXT:
{context}

ENHANCEMENT REQUIREMENTS:
- Identify key technical concepts and learning objectives
- Extract practical scenarios and real-world applications
- Highlight different difficulty levels of concepts
- Organize information for question generation
- Ensure context supports both conceptual and practical questions

ENHANCED CONTEXT FORMAT:
## Key Concepts:
[List main technical concepts]

## Practical Applications:
[Real-world scenarios and use cases]

## Difficulty Progression:
- Beginner: [Fundamental concepts]
- Intermediate: [Applied knowledge]
- Advanced: [Complex analysis and synthesis]

## Question Opportunities:
[Specific areas suitable for different question types]

Provide the enhanced context optimized for question generation:"""

class PromptValidator:
    """Validation utilities for prompts and responses"""
    
    @staticmethod
    def validate_question_response(response: str, user_type: str, expected_count: int) -> Dict[str, Any]:
        """Validate question generation response"""
        validation = {
            "valid": True,
            "issues": [],
            "question_count": 0,
            "format_correct": True
        }
        
        # Count questions
        question_markers = response.count("=== QUESTION")
        validation["question_count"] = question_markers
        
        if question_markers != expected_count:
            validation["valid"] = False
            validation["issues"].append(f"Expected {expected_count} questions, found {question_markers}")
        
        # Check required sections
        required_sections = ["## Title:", "## Difficulty:", "## Type:", "## Question:"]
        if user_type == "non_dev":
            required_sections.append("## Options:")
        
        for section in required_sections:
            if response.count(section) < expected_count:
                validation["valid"] = False
                validation["issues"].append(f"Missing {section} sections")
        
        # Check format consistency
        if user_type == "non_dev":
            option_patterns = [f"{letter})" for letter in "ABCD"]
            for pattern in option_patterns:
                if response.count(pattern) < expected_count:
                    validation["format_correct"] = False
                    validation["issues"].append(f"Inconsistent option format: {pattern}")
        
        return validation
    
    @staticmethod
    def validate_evaluation_response(response: str, expected_count: int) -> Dict[str, Any]:
        """Validate evaluation response"""
        validation = {
            "valid": True,
            "issues": [],
            "has_scores": False,
            "has_feedback": False,
            "score_count": 0
        }
        
        # Check for scores
        if "SCORES:" in response:
            validation["has_scores"] = True
            # Extract and count scores
            import re
            score_match = re.search(r'SCORES:\s*\[(.*?)\]', response)
            if score_match:
                scores = score_match.group(1).split(',')
                validation["score_count"] = len([s for s in scores if s.strip() in ['0', '1']])
                
                if validation["score_count"] != expected_count:
                    validation["valid"] = False
                    validation["issues"].append(f"Expected {expected_count} scores, found {validation['score_count']}")
        else:
            validation["valid"] = False
            validation["issues"].append("Missing SCORES section")
        
        # Check for feedback
        if "FEEDBACK:" in response:
            validation["has_feedback"] = True
        else:
            validation["valid"] = False
            validation["issues"].append("Missing FEEDBACK section")
        
        return validation