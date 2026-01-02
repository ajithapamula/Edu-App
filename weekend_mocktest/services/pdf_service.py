# weekend_mocktest/services/pdf_service.py
import logging
import io
import datetime
from typing import Dict, Any, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.colors import HexColor
from ..core.config import config
from ..core.database import get_db_manager

logger = logging.getLogger(__name__)


class PDFService:
    """Service for generating PDF reports with section-wise breakdown"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        
        # Colors
        self.colors = {
            "primary": HexColor("#2563eb"),
            "success": HexColor("#16a34a"),
            "warning": HexColor("#ca8a04"),
            "danger": HexColor("#dc2626"),
            "gray": HexColor("#6b7280"),
            "light_gray": HexColor("#f3f4f6"),
            "dark": HexColor("#1f2937")
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
        """Create PDF content with section breakdown"""
        
        # Page 1: Header and Summary
        self._add_header(pdf, width, height)
        y = height - 120
        
        # Test Information
        y = self._add_test_info(pdf, doc, y, width)
        
        # Score Summary with section breakdown
        y = self._add_score_summary(pdf, doc, y, width)
        
        # Section Performance Chart
        y = self._add_section_performance(pdf, doc, y, width)
        
        # Page break if needed
        if y < 300:
            pdf.showPage()
            y = height - 50
        
        # Detailed Evaluation
        y = self._add_evaluation_report(pdf, doc, y, width, height)
        
        # Footer
        self._add_footer(pdf, width)
    
    def _add_header(self, pdf: canvas.Canvas, width: float, height: float):
        """Add PDF header"""
        # Title
        pdf.setFillColor(self.colors["primary"])
        pdf.setFont("Helvetica-Bold", 22)
        pdf.drawCentredString(width/2, height - 50, "Developer Assessment Report")
        
        # Subtitle
        pdf.setFillColor(self.colors["gray"])
        pdf.setFont("Helvetica", 11)
        pdf.drawCentredString(width/2, height - 70, "Section-wise Performance Analysis")
        
        # Generated date
        pdf.setFont("Helvetica", 9)
        generated_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        pdf.drawRightString(width - 50, height - 85, f"Generated: {generated_date}")
        
        # Divider line
        pdf.setStrokeColor(self.colors["primary"])
        pdf.setLineWidth(2)
        pdf.line(50, height - 95, width - 50, height - 95)
        
        # Reset
        pdf.setFillColor(self.colors["dark"])
        pdf.setStrokeColor(self.colors["dark"])
        pdf.setLineWidth(1)
    
    def _add_test_info(self, pdf: canvas.Canvas, doc: Dict[str, Any], 
                      y: float, width: float) -> float:
        """Add test information section"""
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "Candidate Information")
        y -= 25
        
        # Info grid
        info_items = [
            ("Test ID:", doc.get('test_id', 'N/A')[:20] + "..."),
            ("Candidate:", doc.get('name', 'N/A')),
            ("Student ID:", str(doc.get('Student_ID', 'N/A'))),
            ("Test Type:", "Developer Assessment" if doc.get('user_type') == 'dev' else "Non-Developer"),
            ("Date:", self._format_timestamp(doc.get('timestamp', 0))),
        ]
        
        pdf.setFont("Helvetica", 10)
        col1_x = 50
        col2_x = 300
        
        for i, (label, value) in enumerate(info_items):
            x = col1_x if i % 2 == 0 else col2_x
            if i % 2 == 0 and i > 0:
                y -= 18
            
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(x, y, label)
            pdf.setFont("Helvetica", 10)
            pdf.drawString(x + 80, y, str(value))
        
        return y - 30
    
    def _add_score_summary(self, pdf: canvas.Canvas, doc: Dict[str, Any], 
                          y: float, width: float) -> float:
        """Add score summary with overall score box"""
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "Overall Performance")
        y -= 30
        
        score = doc.get('score', 0)
        total = doc.get('total_questions', 0)
        percentage = doc.get('score_percentage', 0)
        
        # Score box
        box_width = 150
        box_height = 70
        box_x = 50
        box_y = y - box_height
        
        # Background
        if percentage >= 70:
            bg_color = HexColor("#dcfce7")  # Light green
            text_color = self.colors["success"]
        elif percentage >= 50:
            bg_color = HexColor("#fef3c7")  # Light yellow
            text_color = self.colors["warning"]
        else:
            bg_color = HexColor("#fee2e2")  # Light red
            text_color = self.colors["danger"]
        
        pdf.setFillColor(bg_color)
        pdf.roundRect(box_x, box_y, box_width, box_height, 8, fill=1, stroke=0)
        
        # Score text
        pdf.setFillColor(text_color)
        pdf.setFont("Helvetica-Bold", 28)
        pdf.drawCentredString(box_x + box_width/2, box_y + 40, f"{score}/{total}")
        
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawCentredString(box_x + box_width/2, box_y + 15, f"{percentage}%")
        
        # Performance label
        pdf.setFillColor(self.colors["dark"])
        performance = self._get_performance_level(percentage)
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(box_x + box_width + 30, box_y + 50, f"Performance: {performance}")
        
        # Status
        status = "PASS" if percentage >= 50 else "NEEDS IMPROVEMENT"
        pdf.setFillColor(text_color)
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(box_x + box_width + 30, box_y + 30, f"Status: {status}")
        
        pdf.setFillColor(self.colors["dark"])
        return box_y - 20
    
    def _add_section_performance(self, pdf: canvas.Canvas, doc: Dict[str, Any], 
                                y: float, width: float) -> float:
        """Add section-wise performance breakdown"""
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "Section-wise Breakdown")
        y -= 25
        
        section_scores = doc.get('section_scores', {})
        
        if not section_scores:
            pdf.setFont("Helvetica", 10)
            pdf.drawString(50, y, "Section breakdown not available")
            return y - 30
        
        # Section bars
        bar_width = 200
        bar_height = 20
        x_start = 150
        
        section_order = [
            ("aptitude", "APTITUDE", self.colors["primary"]),
            ("theory", "THEORY", HexColor("#8b5cf6")),
            ("coding", "CODING", HexColor("#06b6d4"))
        ]
        
        for sec_name, display_name, color in section_order:
            if sec_name not in section_scores:
                continue
            
            sec = section_scores[sec_name]
            correct = sec.get('correct', 0)
            total = sec.get('total', 0)
            pct = sec.get('percentage', 0)
            
            # Section label
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(50, y + 5, display_name)
            
            # Background bar
            pdf.setFillColor(HexColor("#e5e7eb"))
            pdf.roundRect(x_start, y, bar_width, bar_height, 3, fill=1, stroke=0)
            
            # Progress bar
            if pct > 0:
                pdf.setFillColor(color)
                progress_width = bar_width * (pct / 100)
                pdf.roundRect(x_start, y, progress_width, bar_height, 3, fill=1, stroke=0)
            
            # Score text
            pdf.setFillColor(self.colors["dark"])
            pdf.setFont("Helvetica", 10)
            pdf.drawString(x_start + bar_width + 10, y + 5, f"{correct}/{total} ({pct}%)")
            
            y -= 30
        
        return y - 10
    
    def _add_evaluation_report(self, pdf: canvas.Canvas, doc: Dict[str, Any], 
                              y: float, width: float, height: float) -> float:
        """Add detailed evaluation report with answers"""
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, "Detailed Feedback & Answers")
        y -= 25
        
        # Get evaluation report
        eval_report = doc.get('evaluation_report', 'No detailed evaluation available.')
        
        # Simple text wrapping
        line_height = 12
        max_chars = 90
        
        lines = []
        for paragraph in eval_report.split('\n'):
            if len(paragraph) <= max_chars:
                lines.append(paragraph)
            else:
                words = paragraph.split()
                current_line = ""
                for word in words:
                    test_line = current_line + " " + word if current_line else word
                    if len(test_line) <= max_chars:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = word
                if current_line:
                    lines.append(current_line)
        
        # Add lines to PDF with styling
        for line in lines:
            if y < 60:
                pdf.showPage()
                y = height - 50
                pdf.setFont("Helvetica", 9)
            
            # Style different line types
            stripped = line.strip()
            
            # Section headers
            if stripped.startswith("-------") or stripped.startswith("═══"):
                pdf.setFont("Helvetica-Bold", 10)
                pdf.setFillColor(self.colors["primary"])
                y -= 5  # Extra space before section
            # Question line
            elif stripped.startswith("📝") or stripped.startswith("Question"):
                pdf.setFont("Helvetica-Bold", 10)
                pdf.setFillColor(HexColor("#1e40af"))
            # Correct answer
            elif stripped.startswith("✅") or stripped.startswith("Correct Answer"):
                pdf.setFont("Helvetica-Bold", 9)
                pdf.setFillColor(self.colors["success"])
            # User answer
            elif stripped.startswith("👤") or stripped.startswith("User"):
                pdf.setFont("Helvetica", 9)
                pdf.setFillColor(HexColor("#7c3aed"))
            # Score
            elif stripped.startswith("📊") or stripped.startswith("Score"):
                pdf.setFont("Helvetica-Bold", 9)
                if "1" in stripped or "correct" in stripped.lower():
                    pdf.setFillColor(self.colors["success"])
                else:
                    pdf.setFillColor(self.colors["danger"])
            # Explanation/Feedback
            elif stripped.startswith("💡") or stripped.startswith("Explanation") or stripped.startswith("Feedback"):
                pdf.setFont("Helvetica-Oblique", 9)
                pdf.setFillColor(self.colors["gray"])
            # Summary headers
            elif stripped.startswith("📈") or stripped.startswith("🎯") or stripped.startswith("💪") or stripped.startswith("📚") or stripped.startswith("🔑"):
                pdf.setFont("Helvetica-Bold", 10)
                pdf.setFillColor(self.colors["primary"])
            # SCORES line
            elif stripped.startswith("SCORES:"):
                pdf.setFont("Helvetica-Bold", 11)
                pdf.setFillColor(self.colors["primary"])
            # Code blocks
            elif stripped.startswith("```"):
                pdf.setFont("Courier", 8)
                pdf.setFillColor(self.colors["dark"])
            else:
                pdf.setFont("Helvetica", 9)
                pdf.setFillColor(self.colors["dark"])
            
            pdf.drawString(50, y, line[:100])  # Limit line length
            y -= line_height
        
        return y
    
    def _add_footer(self, pdf: canvas.Canvas, width: float):
        """Add PDF footer"""
        pdf.setFont("Helvetica", 8)
        pdf.setFillColor(self.colors["gray"])
        pdf.drawCentredString(width/2, 30, "Weekend Mock Test System - Automated Assessment Report")
        pdf.drawCentredString(width/2, 20, f"API Version: {config.API_VERSION}")
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp to readable date"""
        try:
            if timestamp:
                dt = datetime.datetime.fromtimestamp(timestamp)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            return "N/A"
        except (ValueError, OSError):
            return "Invalid date"
    
    def _get_performance_level(self, percentage: float) -> str:
        """Get performance level based on percentage"""
        if percentage >= 90:
            return "Excellent"
        elif percentage >= 80:
            return "Very Good"
        elif percentage >= 70:
            return "Good"
        elif percentage >= 60:
            return "Average"
        elif percentage >= 50:
            return "Below Average"
        else:
            return "Needs Improvement"


# Singleton
_pdf_service = None

def get_pdf_service() -> PDFService:
    """Get PDF service singleton"""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFService()
    return _pdf_service