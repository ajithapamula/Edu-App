# weekend_mocktest/services/pdf_service.py
import logging
import io
import datetime
from typing import Dict, Any, Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from ..core.config import config
from ..core.database import get_db_manager

logger = logging.getLogger(__name__)

class PDFService:
    """Service for generating PDF reports"""
    
    def __init__(self):
        self.db_manager = get_db_manager()
    
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
        """Create PDF content with proper formatting"""
        
        # Header
        self._add_header(pdf, width, height)
        
        # Test Information
        y_position = height - 120
        y_position = self._add_test_info(pdf, doc, y_position, width)
        
        # Score Summary
        y_position = self._add_score_summary(pdf, doc, y_position, width)
        
        # Evaluation Report
        y_position = self._add_evaluation_report(pdf, doc, y_position, width)
        
        # Footer
        self._add_footer(pdf, width)
    
    def _add_header(self, pdf: canvas.Canvas, width: float, height: float):
        """Add PDF header"""
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawCentredText(width/2, height - 50, "Mock Test Results Report")
        
        pdf.setFont("Helvetica", 10)
        generated_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        pdf.drawRightString(width - 50, height - 70, f"Generated: {generated_date}")
        
        # Draw line
        pdf.line(50, height - 80, width - 50, height - 80)
    
    def _add_test_info(self, pdf: canvas.Canvas, doc: Dict[str, Any], 
                      y_position: float, width: float) -> float:
        """Add test information section"""
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y_position, "Test Information")
        y_position -= 25
        
        pdf.setFont("Helvetica", 11)
        
        # Test details
        info_items = [
            ("Test ID:", doc.get('test_id', 'N/A')),
            ("Student Name:", doc.get('name', 'N/A')),
            ("Student ID:", str(doc.get('Student_ID', 'N/A'))),
            ("Test Type:", doc.get('user_type', 'N/A').title().replace('_', '-')),
            ("Completion Date:", self._format_timestamp(doc.get('timestamp', 0))),
            ("Session ID:", doc.get('session_id', 'N/A'))
        ]
        
        for label, value in info_items:
            pdf.setFont("Helvetica-Bold", 10)
            pdf.drawString(50, y_position, label)
            pdf.setFont("Helvetica", 10)
            pdf.drawString(150, y_position, str(value))
            y_position -= 18
        
        return y_position - 10
    
    def _add_score_summary(self, pdf: canvas.Canvas, doc: Dict[str, Any], 
                          y_position: float, width: float) -> float:
        """Add score summary section"""
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y_position, "Score Summary")
        y_position -= 25
        
        # Score box
        score = doc.get('score', 0)
        total = doc.get('total_questions', 0)
        percentage = doc.get('score_percentage', 0)
        
        # Draw score box
        box_x, box_y = 50, y_position - 60
        box_width, box_height = 200, 50
        
        pdf.setStrokeColorRGB(0.2, 0.2, 0.2)
        pdf.setFillColorRGB(0.95, 0.95, 0.95)
        pdf.roundRect(box_x, box_y, box_width, box_height, 5, fill=1)
        
        # Score text
        pdf.setFillColorRGB(0, 0, 0)
        pdf.setFont("Helvetica-Bold", 16)
        pdf.drawCentredText(box_x + box_width/2, box_y + 30, f"{score}/{total}")
        pdf.setFont("Helvetica", 12)
        pdf.drawCentredText(box_x + box_width/2, box_y + 10, f"{percentage}%")
        
        # Performance level
        performance_level = self._get_performance_level(percentage)
        pdf.setFont("Helvetica-Bold", 12)
        color = self._get_performance_color(percentage)
        pdf.setFillColorRGB(*color)
        pdf.drawString(270, box_y + 25, f"Performance: {performance_level}")
        
        pdf.setFillColorRGB(0, 0, 0)  # Reset color
        return y_position - 80
    
    def _add_evaluation_report(self, pdf: canvas.Canvas, doc: Dict[str, Any], 
                             y_position: float, width: float) -> float:
        """Add evaluation report section"""
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y_position, "Detailed Evaluation")
        y_position -= 25
        
        # Get evaluation report
        eval_report = doc.get('evaluation_report', 'No detailed evaluation available.')
        
        # Split report into manageable chunks
        pdf.setFont("Helvetica", 9)
        line_height = 12
        max_width = width - 100
        
        # Simple text wrapping
        words = eval_report.split()
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + " " + word if current_line else word
            # Simple width estimation
            if len(test_line) * 5.4 < max_width:  # Approximate character width
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Add lines to PDF
        for line in lines[:30]:  # Limit to prevent page overflow
            if y_position < 100:  # Check for page bottom
                pdf.showPage()  # New page
                y_position = height - 100
            
            pdf.drawString(50, y_position, line)
            y_position -= line_height
        
        return y_position
    
    def _add_footer(self, pdf: canvas.Canvas, width: float):
        """Add PDF footer"""
        pdf.setFont("Helvetica", 8)
        pdf.drawCentredText(width/2, 30, "This is an automatically generated report from the Mock Test System")
        pdf.drawCentredText(width/2, 20, f"API Version: {config.API_VERSION}")
    
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
        else:
            return "Needs Improvement"
    
    def _get_performance_color(self, percentage: float) -> tuple:
        """Get RGB color for performance level"""
        if percentage >= 80:
            return (0, 0.7, 0)  # Green
        elif percentage >= 60:
            return (0.8, 0.6, 0)  # Orange
        else:
            return (0.8, 0, 0)  # Red

# Singleton pattern for PDF service
_pdf_service = None

def get_pdf_service() -> PDFService:
    """Get PDF service instance (singleton)"""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFService()
    return _pdf_service