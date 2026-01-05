# weekend_mocktest/services/pdf_service.py
import logging
import io
import datetime
import re
from typing import Dict, Any, List, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.colors import HexColor
from reportlab.lib.units import inch
from ..core.config import config
from ..core.database import get_db_manager

logger = logging.getLogger(__name__)


class PDFService:
    """Service for generating professional PDF reports"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        
        # Colors
        self.colors = {
            "primary": HexColor("#1e40af"),      # Dark blue
            "secondary": HexColor("#7c3aed"),     # Purple
            "success": HexColor("#059669"),       # Green
            "warning": HexColor("#d97706"),       # Orange
            "danger": HexColor("#dc2626"),        # Red
            "gray": HexColor("#6b7280"),
            "light_gray": HexColor("#e5e7eb"),
            "dark": HexColor("#111827"),
            "white": HexColor("#ffffff"),
            "aptitude": HexColor("#3b82f6"),      # Blue
            "mcq": HexColor("#8b5cf6"),           # Purple
            "theory": HexColor("#06b6d4"),        # Cyan
            "coding": HexColor("#10b981"),        # Emerald
        }
    
    async def generate_test_results_pdf(self, test_id: str) -> bytes:
        """Generate comprehensive PDF report for test results"""
        logger.info(f"📄 Generating PDF for test: {test_id}")
        
        try:
            # Get test results from database
            doc = self.db_manager.test_results_collection.find_one(
                {"test_id": test_id}, 
                {"_id": 0}
            )
            
            if not doc:
                raise Exception("Test results not found")
            
            # Create PDF buffer
            buffer = io.BytesIO()
            
            # Create PDF document
            pdf = canvas.Canvas(buffer, pagesize=LETTER)
            width, height = LETTER
            
            # Generate PDF content
            self._create_pdf_content(pdf, doc, width, height)
            
            # Save PDF
            pdf.save()
            buffer.seek(0)
            
            logger.info(f"✅ PDF generated successfully for test: {test_id}")
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"❌ PDF generation failed: {e}")
            raise Exception(f"PDF generation failed: {e}")
    
    def _create_pdf_content(self, pdf: canvas.Canvas, doc: Dict[str, Any], 
                          width: float, height: float):
        """Create PDF content with professional layout"""
        
        user_type = doc.get('user_type', 'non_dev')
        
        # Page 1: Header and Summary
        y = self._add_header(pdf, doc, width, height)
        
        # Candidate Information Box
        y = self._add_candidate_info(pdf, doc, y, width)
        
        # Overall Score Card
        y = self._add_score_card(pdf, doc, y, width)
        
        # Section Performance
        y = self._add_section_breakdown(pdf, doc, y, width, user_type)
        
        # Page break for detailed feedback
        pdf.showPage()
        y = height - 50
        
        # Detailed Questions & Answers
        y = self._add_detailed_feedback(pdf, doc, y, width, height, user_type)
        
        # Add footer on last page
        self._add_footer(pdf, width, doc)
    
    def _add_header(self, pdf: canvas.Canvas, doc: Dict[str, Any], 
                   width: float, height: float) -> float:
        """Add professional header"""
        user_type = doc.get('user_type', 'non_dev')
        
        # Title based on test type
        if user_type == 'dev':
            title = "Developer Assessment Report"
            subtitle = "Aptitude • Theory • Coding"
        else:
            title = "Professional Assessment Report"
            subtitle = "Aptitude • Multiple Choice Questions"
        
        # Background header bar
        pdf.setFillColor(self.colors["primary"])
        pdf.rect(0, height - 80, width, 80, fill=1, stroke=0)
        
        # Title
        pdf.setFillColor(self.colors["white"])
        pdf.setFont("Helvetica-Bold", 24)
        pdf.drawCentredString(width/2, height - 45, title)
        
        # Subtitle
        pdf.setFont("Helvetica", 12)
        pdf.drawCentredString(width/2, height - 65, subtitle)
        
        # Reset colors
        pdf.setFillColor(self.colors["dark"])
        
        return height - 100
    
    def _add_candidate_info(self, pdf: canvas.Canvas, doc: Dict[str, Any], 
                           y: float, width: float) -> float:
        """Add candidate information box"""
        
        # Box background
        box_height = 70
        pdf.setFillColor(self.colors["light_gray"])
        pdf.roundRect(40, y - box_height, width - 80, box_height, 8, fill=1, stroke=0)
        
        pdf.setFillColor(self.colors["dark"])
        
        # Left column
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(55, y - 20, "Candidate:")
        pdf.drawString(55, y - 38, "Student ID:")
        pdf.drawString(55, y - 56, "Test Date:")
        
        pdf.setFont("Helvetica", 11)
        pdf.drawString(130, y - 20, doc.get('name', 'N/A'))
        pdf.drawString(130, y - 38, str(doc.get('Student_ID', 'N/A')))
        pdf.drawString(130, y - 56, self._format_timestamp(doc.get('timestamp', 0)))
        
        # Right column
        user_type = doc.get('user_type', 'non_dev')
        test_type = "Developer" if user_type == 'dev' else "Non-Developer"
        
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(320, y - 20, "Test Type:")
        pdf.drawString(320, y - 38, "Test ID:")
        
        pdf.setFont("Helvetica", 11)
        pdf.drawString(400, y - 20, test_type)
        pdf.drawString(400, y - 38, doc.get('test_id', 'N/A')[:20] + "...")
        
        return y - box_height - 20
    
    def _add_score_card(self, pdf: canvas.Canvas, doc: Dict[str, Any], 
                       y: float, width: float) -> float:
        """Add overall score card with visual indicator"""
        
        score = doc.get('score', 0)
        total = doc.get('total_questions', 30)
        percentage = doc.get('score_percentage', 0)
        
        # Determine status and color
        if percentage >= 70:
            status = "EXCELLENT"
            status_color = self.colors["success"]
            bg_color = HexColor("#d1fae5")
        elif percentage >= 50:
            status = "PASS"
            status_color = self.colors["warning"]
            bg_color = HexColor("#fef3c7")
        else:
            status = "NEEDS IMPROVEMENT"
            status_color = self.colors["danger"]
            bg_color = HexColor("#fee2e2")
        
        # Score card background
        card_height = 100
        pdf.setFillColor(bg_color)
        pdf.roundRect(40, y - card_height, width - 80, card_height, 10, fill=1, stroke=0)
        
        # Score circle
        circle_x = 120
        circle_y = y - card_height/2
        circle_radius = 35
        
        pdf.setFillColor(status_color)
        pdf.circle(circle_x, circle_y, circle_radius, fill=1, stroke=0)
        
        # Score text inside circle
        pdf.setFillColor(self.colors["white"])
        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawCentredString(circle_x, circle_y + 5, f"{score}")
        pdf.setFont("Helvetica", 10)
        pdf.drawCentredString(circle_x, circle_y - 12, f"of {total}")
        
        # Percentage and status
        pdf.setFillColor(self.colors["dark"])
        pdf.setFont("Helvetica-Bold", 36)
        pdf.drawString(200, y - 45, f"{percentage:.1f}%")
        
        pdf.setFillColor(status_color)
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(200, y - 70, status)
        
        # Performance label
        pdf.setFillColor(self.colors["gray"])
        pdf.setFont("Helvetica", 10)
        pdf.drawString(200, y - 90, "Overall Performance")
        
        return y - card_height - 25
    
    def _add_section_breakdown(self, pdf: canvas.Canvas, doc: Dict[str, Any], 
                               y: float, width: float, user_type: str) -> float:
        """Add section-wise performance breakdown"""
        
        # Section header
        pdf.setFillColor(self.colors["dark"])
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(40, y, "📊 Section-wise Performance")
        y -= 30
        
        # Parse scores from evaluation report if section_scores not available
        section_scores = doc.get('section_scores', {})
        
        if not section_scores:
            # Try to calculate from evaluation report
            section_scores = self._calculate_section_scores(doc, user_type)
        
        if not section_scores:
            pdf.setFont("Helvetica", 11)
            pdf.setFillColor(self.colors["gray"])
            pdf.drawString(50, y, "Section breakdown not available")
            return y - 30
        
        # Define sections based on user type
        if user_type == 'dev':
            sections = [
                ("aptitude", "APTITUDE", "Logical Reasoning", self.colors["aptitude"]),
                ("theory", "THEORY", "Conceptual Knowledge", self.colors["theory"]),
                ("coding", "CODING", "Programming Skills", self.colors["coding"]),
            ]
        else:
            sections = [
                ("aptitude", "APTITUDE", "Logical Reasoning (Q1-10)", self.colors["aptitude"]),
                ("mcq", "MCQ", "Course Content (Q11-30)", self.colors["mcq"]),
            ]
        
        bar_width = 300
        bar_height = 25
        
        for sec_key, sec_name, sec_desc, color in sections:
            if sec_key not in section_scores:
                continue
            
            sec = section_scores[sec_key]
            correct = sec.get('correct', 0)
            total = sec.get('total', 0)
            pct = sec.get('percentage', 0) if total > 0 else 0
            
            # Section name
            pdf.setFillColor(self.colors["dark"])
            pdf.setFont("Helvetica-Bold", 11)
            pdf.drawString(50, y + 5, sec_name)
            
            # Description
            pdf.setFillColor(self.colors["gray"])
            pdf.setFont("Helvetica", 9)
            pdf.drawString(50, y - 10, sec_desc)
            
            # Background bar
            bar_x = 200
            pdf.setFillColor(self.colors["light_gray"])
            pdf.roundRect(bar_x, y - 5, bar_width, bar_height, 4, fill=1, stroke=0)
            
            # Progress bar
            if pct > 0:
                pdf.setFillColor(color)
                progress_width = bar_width * (pct / 100)
                pdf.roundRect(bar_x, y - 5, progress_width, bar_height, 4, fill=1, stroke=0)
            
            # Score text
            pdf.setFillColor(self.colors["dark"])
            pdf.setFont("Helvetica-Bold", 11)
            score_text = f"{correct}/{total} ({pct:.0f}%)"
            pdf.drawRightString(bar_x + bar_width + 60, y + 3, score_text)
            
            y -= 45
        
        return y - 10
    
    def _calculate_section_scores(self, doc: Dict[str, Any], user_type: str) -> Dict[str, Any]:
        """Calculate section scores from answers if not stored"""
        
        scores_array = doc.get('scores', [])
        if not scores_array:
            # Try to parse from evaluation report
            eval_report = doc.get('evaluation_report', '')
            match = re.search(r'SCORES:\s*\[([\d,\s]+)\]', eval_report)
            if match:
                try:
                    scores_array = [int(x.strip()) for x in match.group(1).split(',')]
                except:
                    return {}
        
        if not scores_array:
            return {}
        
        if user_type == 'dev':
            # Developer: Aptitude (1-3), Theory (4-6), Coding (7-10)
            apt_scores = scores_array[:3] if len(scores_array) >= 3 else []
            theory_scores = scores_array[3:6] if len(scores_array) >= 6 else []
            coding_scores = scores_array[6:] if len(scores_array) > 6 else []
            
            return {
                "aptitude": {
                    "correct": sum(apt_scores),
                    "total": len(apt_scores),
                    "percentage": (sum(apt_scores) / len(apt_scores) * 100) if apt_scores else 0
                },
                "theory": {
                    "correct": sum(theory_scores),
                    "total": len(theory_scores),
                    "percentage": (sum(theory_scores) / len(theory_scores) * 100) if theory_scores else 0
                },
                "coding": {
                    "correct": sum(coding_scores),
                    "total": len(coding_scores),
                    "percentage": (sum(coding_scores) / len(coding_scores) * 100) if coding_scores else 0
                }
            }
        else:
            # Non-developer: Aptitude (1-10), MCQ (11-30)
            apt_scores = scores_array[:10] if len(scores_array) >= 10 else scores_array
            mcq_scores = scores_array[10:] if len(scores_array) > 10 else []
            
            return {
                "aptitude": {
                    "correct": sum(apt_scores),
                    "total": len(apt_scores),
                    "percentage": (sum(apt_scores) / len(apt_scores) * 100) if apt_scores else 0
                },
                "mcq": {
                    "correct": sum(mcq_scores),
                    "total": len(mcq_scores),
                    "percentage": (sum(mcq_scores) / len(mcq_scores) * 100) if mcq_scores else 0
                }
            }
    
    def _add_detailed_feedback(self, pdf: canvas.Canvas, doc: Dict[str, Any], 
                               y: float, width: float, height: float, 
                               user_type: str) -> float:
        """Add detailed question-by-question feedback"""
        
        # Header
        pdf.setFillColor(self.colors["primary"])
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawString(40, y, "📝 Detailed Feedback & Answers")
        y -= 30
        
        # Parse evaluation report
        eval_report = doc.get('evaluation_report', '')
        questions = self._parse_evaluation_questions(eval_report)
        
        if not questions:
            pdf.setFont("Helvetica", 11)
            pdf.setFillColor(self.colors["gray"])
            pdf.drawString(50, y, "Detailed feedback not available")
            return y - 30
        
        # Define section breaks
        if user_type == 'dev':
            section_breaks = {1: "APTITUDE SECTION", 4: "THEORY SECTION", 7: "CODING SECTION"}
        else:
            section_breaks = {1: "APTITUDE SECTION (Q1-10)", 11: "MCQ SECTION (Q11-30)"}
        
        for q in questions:
            q_num = q.get('number', 0)
            
            # Check for section header
            if q_num in section_breaks:
                if y < 150:
                    pdf.showPage()
                    y = height - 50
                
                # Section divider
                pdf.setFillColor(self.colors["primary"])
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(40, y, f"━━━ {section_breaks[q_num]} ━━━")
                y -= 25
            
            # Check if need new page
            if y < 120:
                pdf.showPage()
                y = height - 50
            
            # Question box
            y = self._add_question_box(pdf, q, y, width)
        
        return y
    
    def _add_question_box(self, pdf: canvas.Canvas, q: Dict[str, Any], 
                         y: float, width: float) -> float:
        """Add a single question feedback box"""
        
        is_correct = q.get('score', 0) == 1
        
        # Question header with status indicator
        if is_correct:
            status_color = self.colors["success"]
            status_icon = "✓"
        else:
            status_color = self.colors["danger"]
            status_icon = "✗"
        
        # Question number and status
        pdf.setFillColor(status_color)
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(40, y, f"{status_icon} Question {q.get('number', '?')}")
        
        # Score badge
        score_text = "CORRECT" if is_correct else "INCORRECT"
        pdf.setFont("Helvetica", 9)
        pdf.drawRightString(width - 40, y, score_text)
        
        y -= 18
        
        # Question text (wrapped)
        pdf.setFillColor(self.colors["dark"])
        pdf.setFont("Helvetica", 10)
        question_text = q.get('question', 'N/A')
        y = self._draw_wrapped_text(pdf, question_text, 50, y, width - 100, 12)
        
        y -= 5
        
        # Correct answer
        pdf.setFillColor(self.colors["success"])
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(50, y, "Correct Answer:")
        pdf.setFont("Helvetica", 9)
        correct_ans = q.get('correct_answer', 'N/A')
        if len(correct_ans) > 60:
            correct_ans = correct_ans[:60] + "..."
        pdf.drawString(130, y, correct_ans)
        y -= 14
        
        # User's answer
        user_color = self.colors["success"] if is_correct else self.colors["danger"]
        pdf.setFillColor(user_color)
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(50, y, "Your Answer:")
        pdf.setFont("Helvetica", 9)
        user_ans = q.get('user_answer', 'N/A')
        if len(user_ans) > 60:
            user_ans = user_ans[:60] + "..."
        pdf.drawString(130, y, user_ans)
        y -= 14
        
        # Brief explanation (only if wrong)
        if not is_correct and q.get('explanation'):
            pdf.setFillColor(self.colors["gray"])
            pdf.setFont("Helvetica-Oblique", 9)
            explanation = q.get('explanation', '')[:100]
            if len(q.get('explanation', '')) > 100:
                explanation += "..."
            pdf.drawString(50, y, f"💡 {explanation}")
            y -= 14
        
        # Divider line
        pdf.setStrokeColor(self.colors["light_gray"])
        pdf.setLineWidth(0.5)
        pdf.line(40, y, width - 40, y)
        
        return y - 15
    
    def _parse_evaluation_questions(self, eval_report: str) -> List[Dict[str, Any]]:
        """Parse evaluation report into structured questions"""
        
        questions = []
        
        # Split by question markers
        pattern = r'---+\s*Question\s+(\d+)\s*---+'
        parts = re.split(pattern, eval_report, flags=re.IGNORECASE)
        
        if len(parts) < 2:
            return questions
        
        # Process pairs (question_number, content)
        for i in range(1, len(parts), 2):
            if i + 1 >= len(parts):
                break
            
            try:
                q_num = int(parts[i])
                content = parts[i + 1]
                
                q_data = {
                    'number': q_num,
                    'question': self._extract_field(content, ['Question:', '📝 Question:']),
                    'correct_answer': self._extract_field(content, ['Correct Answer:', '✅ Correct Answer:']),
                    'user_answer': self._extract_field(content, ['User Selected:', '👤 User Selected:']),
                    'score': self._extract_score(content),
                    'explanation': self._extract_field(content, ['Explanation:', '💡 Explanation:'])
                }
                
                questions.append(q_data)
                
            except Exception as e:
                logger.warning(f"Failed to parse question: {e}")
                continue
        
        return questions
    
    def _extract_field(self, content: str, markers: List[str]) -> str:
        """Extract field value from content"""
        for marker in markers:
            if marker in content:
                start = content.find(marker) + len(marker)
                # Find end (next marker or newline patterns)
                end = len(content)
                for next_marker in ['■', '📝', '✅', '👤', '📊', '💡', '---', '\n\n']:
                    pos = content.find(next_marker, start)
                    if pos != -1 and pos < end:
                        end = pos
                return content[start:end].strip()
        return ""
    
    def _extract_score(self, content: str) -> int:
        """Extract score from content"""
        match = re.search(r'Score:\s*(\d+)', content)
        if match:
            return int(match.group(1))
        return 0
    
    def _draw_wrapped_text(self, pdf: canvas.Canvas, text: str, x: float, y: float,
                          max_width: float, line_height: float) -> float:
        """Draw text with word wrapping"""
        if not text:
            return y
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            # Approximate character width
            if len(test_line) * 5 <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        for line in lines[:3]:  # Max 3 lines
            pdf.drawString(x, y, line)
            y -= line_height
        
        if len(lines) > 3:
            pdf.drawString(x, y, "...")
            y -= line_height
        
        return y
    
    def _add_footer(self, pdf: canvas.Canvas, width: float, doc: Dict[str, Any]):
        """Add footer to the page"""
        pdf.setFillColor(self.colors["gray"])
        pdf.setFont("Helvetica", 8)
        
        # Footer text
        pdf.drawString(40, 30, "Weekend Mock Test System - Automated Assessment Report")
        pdf.drawRightString(width - 40, 30, f"API Version: {config.API_VERSION}")
        
        # Line
        pdf.setStrokeColor(self.colors["light_gray"])
        pdf.line(40, 45, width - 40, 45)
    
    def _format_timestamp(self, timestamp) -> str:
        """Format timestamp to readable string"""
        try:
            if isinstance(timestamp, (int, float)):
                dt = datetime.datetime.fromtimestamp(timestamp)
            elif isinstance(timestamp, str):
                dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                return str(timestamp)
            return dt.strftime('%Y-%m-%d %H:%M')
        except:
            return "N/A"


# Singleton instance
_pdf_service_instance = None


def get_pdf_service() -> PDFService:
    """Get singleton instance of PDFService"""
    global _pdf_service_instance
    if _pdf_service_instance is None:
        _pdf_service_instance = PDFService()
    return _pdf_service_instance