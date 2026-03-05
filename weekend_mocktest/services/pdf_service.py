# weekend_mocktest/services/pdf_service.py
"""
PDF Service - Generate Professional Test Result PDFs

Features:
- Section-wise breakdown (Aptitude → MCQ → Coding)
- Question-by-question analysis
- User Answer vs Correct Answer with PROPER CODE FORMATTING
- AI-generated explanations
- ✅/❌ status indicators
- Professional formatting
- ☁️ AWS S3 Upload with URL stored in MongoDB
- Student name, course, batch shown in PDF header
"""

import io
import logging
import os
import boto3
from botocore.exceptions import ClientError
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class PDFService:
    """PDF generation service for detailed test results"""
    
    def __init__(self):
        from ..core.database import get_db_manager
        self.db_manager = get_db_manager()
        
        # Create output directory
        self.output_dir = "static/pdf_reports"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # ════════════════════════════════════════════════════════════
        # AWS S3 Configuration (from config.py)
        # ════════════════════════════════════════════════════════════
        from ..core.config import config as app_config
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=app_config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=app_config.AWS_SECRET_ACCESS_KEY,
            region_name=app_config.AWS_REGION
        )
        self.s3_bucket = app_config.S3_BUCKET_NAME
        self.s3_folder = app_config.S3_PDF_FOLDER
        
        logger.info("📄 PDF Service initialized with S3 Upload + Code Formatting support")

    # ════════════════════════════════════════════════════════════
    # AWS S3 UPLOAD
    # ════════════════════════════════════════════════════════════
    def _upload_to_s3(self, pdf_bytes: bytes, test_id: str, student_id: str = "unknown") -> Optional[str]:
        """Upload PDF to AWS S3 and return the public URL."""
        try:
            # S3 key: pdf-reports/student_123/test_results_abc123.pdf
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # Ensure student_id is never "N/A" or empty in the path
            safe_student_id = str(student_id) if student_id and str(student_id) not in ("N/A", "None", "", "0") else "unknown"
            s3_key = f"{self.s3_folder}/student_{safe_student_id}/test_results_{test_id}_{timestamp}.pdf"
            
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=pdf_bytes,
                ContentType='application/pdf',
                ContentDisposition=f'inline; filename="test_results_{test_id}.pdf"',
                Metadata={
                    'test_id': test_id,
                    'student_id': str(safe_student_id),
                    'generated_at': datetime.now().isoformat()
                }
            )
            
            region = os.environ.get('AWS_REGION', 'ap-south-1')
            s3_url = f"https://{self.s3_bucket}.s3.{region}.amazonaws.com/{s3_key}"
            
            logger.info(f"☁️ PDF uploaded to S3: {s3_url}")
            return s3_url
            
        except ClientError as e:
            logger.error(f"❌ S3 upload failed: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected S3 error: {e}")
            return None

    def _generate_presigned_url(self, s3_key: str, expiration: int = 86400) -> Optional[str]:
        """Generate a presigned URL for private S3 objects."""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.s3_bucket, 'Key': s3_key},
                ExpiresIn=expiration
            )
            logger.info(f"🔗 Presigned URL generated (expires in {expiration}s)")
            return url
        except ClientError as e:
            logger.error(f"❌ Presigned URL generation failed: {e}")
            return None

    def _is_code_content(self, text: str) -> bool:
        """Check if text looks like code"""
        if not text:
            return False
        code_indicators = [
            'def ', 'class ', 'import ', 'from ', 'return ',
            'print(', 'if ', 'for ', 'while ', 'try:', 'except',
            '= ', '==', '!=', '>=', '<=', '+=', '-=',
            'function', 'const ', 'let ', 'var ',
            '=>', '__init__', 'self.'
        ]
        return any(indicator in text for indicator in code_indicators)

    def _format_code_for_pdf(self, code: str) -> str:
        """Format code for PDF display with proper line breaks."""
        if not code:
            return code
        code = code.replace('&', '&amp;')
        code = code.replace('<', '&lt;')
        code = code.replace('>', '&gt;')
        code = code.replace('\n', '<br/>')
        code = code.replace('    ', '&nbsp;&nbsp;&nbsp;&nbsp;')
        code = code.replace('  ', '&nbsp;&nbsp;')
        return code

    def _get_student_info(self, doc: dict) -> dict:
        """
        Extract student info from MongoDB doc reliably.
        Tries multiple field locations since older docs may not have all fields.
        """
        # Direct fields (new format — stored by _save_results)
        student_id   = doc.get("student_id")
        student_name = doc.get("student_name", "")
        course       = doc.get("course", "")
        batch        = doc.get("batch", "")
        role_type    = doc.get("role_type", "")

        # Fallback: nested student_profile (also stored in test_data)
        profile = doc.get("student_profile", {})
        if profile:
            student_id   = student_id   or profile.get("student_id")
            student_name = student_name or profile.get("student_name", "")
            course       = course       or profile.get("course", "")
            batch        = batch        or profile.get("batch", "")
            role_type    = role_type    or profile.get("role_type", "")

        # Normalize
        student_id_str = str(student_id) if student_id and str(student_id) not in ("None", "0", "") else "N/A"
        student_name   = student_name.strip() if student_name else "N/A"
        course         = course.strip()    if course    else "N/A"
        batch          = batch.strip()     if batch     else "N/A"

        return {
            "student_id":   student_id_str,
            "student_name": student_name,
            "course":       course,
            "batch":        batch,
            "role_type":    role_type,
            "raw_id":       student_id,   # original value for S3 path
        }

    async def generate_test_results_pdf(self, test_id: str) -> bytes:
        """Generate comprehensive PDF report with AI explanations and proper code formatting"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                PageBreak, HRFlowable, ListFlowable, ListItem, Preformatted
            )
            from reportlab.lib.units import inch, cm
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        except ImportError:
            logger.error("ReportLab not installed")
            raise Exception("PDF generation requires reportlab: pip install reportlab --break-system-packages")
        
        # Get test results from MongoDB
        doc = self.db_manager.test_results_collection.find_one(
            {"test_id": test_id}, {"_id": 0}
        )
        
        if not doc:
            raise Exception(f"Test results not found: {test_id}")
        
        # ── Extract student info ──────────────────────────────────
        student_info = self._get_student_info(doc)
        student_id   = student_info["student_id"]
        student_name = student_info["student_name"]
        course       = student_info["course"]
        batch        = student_info["batch"]

        logger.info(f"📄 Generating PDF for student {student_id} ({student_name}) | course={course} batch={batch}")

        # Create PDF buffer
        buffer = io.BytesIO()
        pdf_doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            topMargin=0.5*inch, 
            bottomMargin=0.5*inch,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch
        )
        
        # Setup styles
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=20,
            alignment=TA_CENTER,
            spaceAfter=10,
            textColor=colors.HexColor('#1a365d')
        )

        subtitle_style = ParagraphStyle(
            'SubTitle',
            parent=styles['Normal'],
            fontSize=11,
            alignment=TA_CENTER,
            spaceAfter=15,
            textColor=colors.HexColor('#374151')
        )
        
        section_header_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=10,
            textColor=colors.HexColor('#2563eb')
        )
        
        question_style = ParagraphStyle(
            'QuestionStyle',
            parent=styles['Normal'],
            fontSize=10,
            spaceBefore=8,
            spaceAfter=4,
            leftIndent=10
        )
        
        answer_style = ParagraphStyle(
            'AnswerStyle',
            parent=styles['Normal'],
            fontSize=9,
            leftIndent=20,
            textColor=colors.HexColor('#374151')
        )
        
        explanation_style = ParagraphStyle(
            'ExplanationStyle',
            parent=styles['Normal'],
            fontSize=9,
            leftIndent=20,
            textColor=colors.HexColor('#4b5563'),
            fontName='Helvetica-Oblique'
        )
        
        correct_style = ParagraphStyle(
            'CorrectStyle',
            parent=styles['Normal'],
            fontSize=9,
            leftIndent=20,
            textColor=colors.HexColor('#059669')
        )
        
        wrong_style = ParagraphStyle(
            'WrongStyle',
            parent=styles['Normal'],
            fontSize=9,
            leftIndent=20,
            textColor=colors.HexColor('#dc2626')
        )
        
        code_style = ParagraphStyle(
            'CodeStyle',
            parent=styles['Normal'],
            fontSize=8,
            fontName='Courier',
            leftIndent=25,
            rightIndent=10,
            spaceBefore=5,
            spaceAfter=5,
            backColor=colors.HexColor('#1e293b'),
            textColor=colors.HexColor('#4ade80'),
            borderColor=colors.HexColor('#334155'),
            borderWidth=1,
            borderPadding=8,
            leading=12
        )
        
        code_label_style = ParagraphStyle(
            'CodeLabelStyle',
            parent=styles['Normal'],
            fontSize=8,
            fontName='Helvetica-Bold',
            leftIndent=20,
            spaceBefore=5,
            spaceAfter=2,
            textColor=colors.HexColor('#059669')
        )
        
        user_code_style = ParagraphStyle(
            'UserCodeStyle',
            parent=styles['Normal'],
            fontSize=8,
            fontName='Courier',
            leftIndent=25,
            rightIndent=10,
            spaceBefore=5,
            spaceAfter=5,
            backColor=colors.HexColor('#fef2f2'),
            textColor=colors.HexColor('#991b1b'),
            borderColor=colors.HexColor('#fecaca'),
            borderWidth=1,
            borderPadding=8,
            leading=12
        )
        
        elements = []
        
        # ════════════════════════════════════════════════════════════
        # HEADER — Title + Student Name
        # ════════════════════════════════════════════════════════════
        user_type  = doc.get("user_type", "dev")
        track_name = "Non-Developer" if user_type == "non_dev" else "Developer"
        
        elements.append(Paragraph(f"📋 {track_name} Mock Test Results", title_style))

        # Student name subtitle (only if we have a real name)
        if student_name and student_name != "N/A":
            elements.append(Paragraph(f"Student: <b>{student_name}</b>", subtitle_style))

        elements.append(Spacer(1, 10))
        
        # ════════════════════════════════════════════════════════════
        # TEST INFO TABLE — now includes Student Name + Course + Batch
        # ════════════════════════════════════════════════════════════
        score        = doc.get("score", 0)
        total        = doc.get("total_questions", 0)
        percentage   = doc.get("score_percentage", 0)
        warning_count = doc.get("warning_count", 0)
        terminated   = doc.get("terminated_by_warnings", False)
        timestamp    = doc.get("timestamp", 0)
        
        if timestamp:
            try:
                date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            except:
                date_str = "N/A"
        else:
            date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if percentage >= 80:
            performance = "🏆 Excellent"
            perf_color  = colors.HexColor('#059669')
        elif percentage >= 60:
            performance = "👍 Good"
            perf_color  = colors.HexColor('#2563eb')
        elif percentage >= 40:
            performance = "📚 Average"
            perf_color  = colors.HexColor('#d97706')
        else:
            performance = "⚠️ Needs Improvement"
            perf_color  = colors.HexColor('#dc2626')
        
        # Layout: Label | Value | Label | Value
        # Row 1: Name          | <name>       | Student ID   | <id>
        # Row 2: Date          | <date>       | Performance  | <perf>
        # Row 3: Overall Score | <score>      | Test ID      | <test_id>
        # Row 4: Warnings      | <warnings>   | Status       | <status>
        info_data = [
            ["Name:",          student_name,
             "Student ID:",    student_id],
            ["Date:",          date_str,
             "Performance:",   performance],
            ["Overall Score:", f"{score}/{total} ({percentage}%)",
             "Test ID:",       test_id[:18] + "..." if len(test_id) > 18 else test_id],
            ["Warnings:",      f"{warning_count}/3",
             "Status:",        "TERMINATED ❌" if terminated else "Completed ✅"],
        ]
        
        info_table = Table(info_data, colWidths=[1.3*inch, 2.2*inch, 1.3*inch, 1.8*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE',      (0, 0), (-1, -1), 9),
            ('FONTNAME',      (0, 0), (0, -1), 'Helvetica-Bold'),   # left labels bold
            ('FONTNAME',      (2, 0), (2, -1), 'Helvetica-Bold'),   # right labels bold
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING',    (0, 0), (-1, -1), 8),
            ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX',           (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('LINEBELOW',     (0, 0), (-1, -2), 0.5, colors.HexColor('#e2e8f0')),
            # Highlight label columns with slightly darker bg
            ('BACKGROUND',    (0, 0), (0, -1), colors.HexColor('#eef2f7')),
            ('BACKGROUND',    (2, 0), (2, -1), colors.HexColor('#eef2f7')),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 20))
        
        # ════════════════════════════════════════════════════════════
        # SECTION SCORES SUMMARY
        # ════════════════════════════════════════════════════════════
        section_scores = doc.get("section_scores", {})
        
        if section_scores:
            elements.append(Paragraph("📊 Section-wise Performance", section_header_style))
            
            section_data = [["Section", "Score", "Percentage", "Status"]]
            
            section_icons = {
                "aptitude": "🧮 Aptitude",
                "mcq":      "📚 MCQ/Theory",
                "theory":   "📚 Theory",
                "coding":   "💻 Coding"
            }
            
            for section, data in section_scores.items():
                if isinstance(data, dict):
                    correct    = data.get("correct", 0)
                    total_sec  = data.get("total", 0)
                    pct        = data.get("percentage", 0)
                    section_name = section_icons.get(section, section.upper())
                    status     = "✅ Pass" if pct >= 50 else "⚠️ Needs Work"
                    section_data.append([section_name, f"{correct}/{total_sec}", f"{pct}%", status])
            
            if len(section_data) > 1:
                section_table = Table(section_data, colWidths=[2.5*inch, 1.2*inch, 1.2*inch, 1.5*inch])
                section_table.setStyle(TableStyle([
                    ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                    ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
                    ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE',      (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('TOPPADDING',    (0, 0), (-1, 0), 12),
                    ('BACKGROUND',    (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
                    ('BOX',           (0, 0), (-1, -1), 1, colors.HexColor('#1e40af')),
                    ('LINEBELOW',     (0, 0), (-1, -2), 0.5, colors.HexColor('#e2e8f0')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')])
                ]))
                elements.append(section_table)
                elements.append(Spacer(1, 20))
        
        # ════════════════════════════════════════════════════════════
        # DETAILED QUESTION REVIEW
        # ════════════════════════════════════════════════════════════
        elements.append(Paragraph("📝 Detailed Question Review", section_header_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
        elements.append(Spacer(1, 10))
        
        section_details    = doc.get("section_details", {})
        conversation_pairs = doc.get("conversation_pairs", [])
        
        if section_details:
            for section_name, details in section_details.items():
                section_icon  = "🧮" if section_name == "aptitude" else "📚" if section_name in ["mcq", "theory"] else "💻"
                section_score = details.get("score", {})
                questions     = details.get("questions", [])
                is_coding_section = section_name == "coding"
                
                elements.append(Paragraph(
                    f"{section_icon} {section_name.upper()} SECTION "
                    f"({section_score.get('correct', 0)}/{section_score.get('total', 0)} - "
                    f"{section_score.get('percentage', 0)}%)",
                    section_header_style
                ))
                
                for q in questions:
                    q_num        = q.get("question_number", "?")
                    is_correct   = q.get("is_correct", False)
                    question_text = q.get("question", "")
                    user_answer  = q.get("user_answer", "No answer")
                    correct_answer = q.get("correct_answer", "N/A")
                    explanation  = q.get("explanation", "")
                    
                    is_code_answer = is_coding_section or self._is_code_content(correct_answer) or self._is_code_content(user_answer)
                    
                    status       = "✅" if is_correct else "❌"
                    status_color = colors.HexColor('#059669') if is_correct else colors.HexColor('#dc2626')
                    
                    q_header_style = ParagraphStyle(
                        'QHeader',
                        parent=styles['Normal'],
                        fontSize=10,
                        fontName='Helvetica-Bold',
                        textColor=status_color,
                        spaceBefore=12,
                        spaceAfter=4
                    )
                    
                    q_display = question_text[:150] + '...' if len(question_text) > 150 else question_text
                    q_display = q_display.replace('<', '&lt;').replace('>', '&gt;')
                    
                    elements.append(Paragraph(f"{status} Q{q_num}. {q_display}", q_header_style))
                    
                    if is_code_answer:
                        wrong_label_style = ParagraphStyle(
                            'WrongLabel', parent=styles['Normal'], fontSize=8,
                            fontName='Helvetica-Bold', leftIndent=20, spaceBefore=5,
                            spaceAfter=2, textColor=colors.HexColor('#dc2626')
                        )
                        elements.append(Paragraph(
                            "Your Answer:",
                            code_label_style if is_correct else wrong_label_style
                        ))
                        user_code_formatted = self._format_code_for_pdf(user_answer)
                        elements.append(Paragraph(user_code_formatted, code_style if is_correct else user_code_style))
                        
                        if not is_correct:
                            elements.append(Paragraph("Correct Answer:", code_label_style))
                            elements.append(Paragraph(self._format_code_for_pdf(correct_answer), code_style))
                    else:
                        user_answer_safe   = str(user_answer).replace('<', '&lt;').replace('>', '&gt;')
                        correct_answer_safe = str(correct_answer).replace('<', '&lt;').replace('>', '&gt;')
                        
                        if is_correct:
                            elements.append(Paragraph(f"<b>Your Answer:</b> {user_answer_safe}", correct_style))
                        else:
                            elements.append(Paragraph(f"<b>Your Answer:</b> {user_answer_safe}", wrong_style))
                            elements.append(Paragraph(f"<b>Correct Answer:</b> {correct_answer_safe}", correct_style))
                    
                    if explanation:
                        explanation_safe = str(explanation).replace('<', '&lt;').replace('>', '&gt;')
                        elements.append(Paragraph(f"💡 <i>{explanation_safe}</i>", explanation_style))
                    
                    elements.append(Spacer(1, 8))
                
                elements.append(Spacer(1, 10))
                elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0')))
        
        elif conversation_pairs:
            # FALLBACK: old format
            sections_grouped = {"aptitude": [], "mcq": [], "coding": []}
            for qa in conversation_pairs:
                q_type = qa.get("question_type", "mcq")
                sections_grouped.get(q_type, sections_grouped["mcq"]).append(qa)
            
            for section_name, questions in sections_grouped.items():
                if not questions:
                    continue
                
                section_icon = "🧮" if section_name == "aptitude" else "📚" if section_name == "mcq" else "💻"
                correct_in_section = sum(1 for q in questions if q.get("correct", False))
                is_coding_section  = section_name == "coding"
                
                elements.append(Paragraph(
                    f"{section_icon} {section_name.upper()} SECTION ({correct_in_section}/{len(questions)})",
                    section_header_style
                ))
                
                for qa in questions:
                    q_num        = qa.get("question_number", "?")
                    is_correct   = qa.get("correct", False)
                    question_text = qa.get("question", "")[:150]
                    user_answer  = qa.get("answer", "No answer")
                    correct_answer = qa.get("correct_answer", "N/A")
                    feedback     = qa.get("feedback", "")
                    is_code_answer = is_coding_section or self._is_code_content(correct_answer)
                    
                    status       = "✅" if is_correct else "❌"
                    status_color = colors.HexColor('#059669') if is_correct else colors.HexColor('#dc2626')
                    
                    q_header_style = ParagraphStyle(
                        'QHeader', parent=styles['Normal'], fontSize=10,
                        fontName='Helvetica-Bold', textColor=status_color,
                        spaceBefore=12, spaceAfter=4
                    )
                    
                    q_display = question_text.replace('<', '&lt;').replace('>', '&gt;')
                    elements.append(Paragraph(
                        f"{status} Q{q_num}. {q_display}{'...' if len(question_text) >= 150 else ''}",
                        q_header_style
                    ))
                    
                    if is_code_answer:
                        wrong_label_style = ParagraphStyle(
                            'WrongLabel', parent=styles['Normal'], fontSize=8,
                            fontName='Helvetica-Bold', leftIndent=20, spaceBefore=5,
                            spaceAfter=2, textColor=colors.HexColor('#dc2626')
                        )
                        elements.append(Paragraph(
                            "Your Answer:",
                            code_label_style if is_correct else wrong_label_style
                        ))
                        elements.append(Paragraph(
                            self._format_code_for_pdf(user_answer),
                            code_style if is_correct else user_code_style
                        ))
                        if not is_correct:
                            elements.append(Paragraph("Correct Answer:", code_label_style))
                            elements.append(Paragraph(self._format_code_for_pdf(correct_answer), code_style))
                    else:
                        user_answer_safe    = str(user_answer).replace('<', '&lt;').replace('>', '&gt;')
                        correct_answer_safe = str(correct_answer).replace('<', '&lt;').replace('>', '&gt;')
                        if is_correct:
                            elements.append(Paragraph(f"<b>Your Answer:</b> {user_answer_safe}", correct_style))
                        else:
                            elements.append(Paragraph(f"<b>Your Answer:</b> {user_answer_safe}", wrong_style))
                            elements.append(Paragraph(f"<b>Correct Answer:</b> {correct_answer_safe}", correct_style))
                    
                    if feedback:
                        feedback_safe = str(feedback).replace('<', '&lt;').replace('>', '&gt;')
                        elements.append(Paragraph(f"💡 <i>{feedback_safe}</i>", explanation_style))
                    
                    elements.append(Spacer(1, 8))
                
                elements.append(Spacer(1, 10))
        
        # ════════════════════════════════════════════════════════════
        # WARNINGS SECTION
        # ════════════════════════════════════════════════════════════
        warnings = doc.get("warnings", [])
        if warnings:
            elements.append(PageBreak())
            elements.append(Paragraph("⚠️ Proctoring Warnings", section_header_style))
            
            warning_data = [["#", "Type", "Time"]]
            for i, w in enumerate(warnings, 1):
                warning_data.append([
                    str(i),
                    w.get("type", "unknown").replace("_", " ").title(),
                    w.get("timestamp_readable", "N/A")
                ])
            
            warning_table = Table(warning_data, colWidths=[0.5*inch, 3*inch, 2.5*inch])
            warning_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
                ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
                ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',   (0, 0), (-1, -1), 9),
                ('BOX',        (0, 0), (-1, -1), 1, colors.HexColor('#dc2626')),
                ('LINEBELOW',  (0, 0), (-1, -2), 0.5, colors.HexColor('#fecaca')),
            ]))
            elements.append(warning_table)
            
            if terminated:
                term_reason = doc.get("termination_reason", "Maximum warnings exceeded")
                elements.append(Spacer(1, 10))
                term_style = ParagraphStyle(
                    'Terminated', parent=styles['Normal'],
                    textColor=colors.HexColor('#dc2626'), fontName='Helvetica-Bold'
                )
                elements.append(Paragraph(f"❌ TEST TERMINATED: {term_reason}", term_style))
        
        # ════════════════════════════════════════════════════════════
        # RECOMMENDATIONS
        # ════════════════════════════════════════════════════════════
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("📌 Recommendations", section_header_style))
        
        weak_sections = [
            s for s, d in section_scores.items()
            if isinstance(d, dict) and d.get("percentage", 0) < 50
        ]
        
        if weak_sections:
            elements.append(Paragraph("Areas that need improvement:", styles['Normal']))
            for section in weak_sections:
                if section == "aptitude":
                    rec = "• <b>Aptitude:</b> Practice more logical reasoning, quantitative aptitude, and problem-solving questions."
                elif section in ["mcq", "theory"]:
                    if user_type == "non_dev":
                        rec = "• <b>MCQ/Theory:</b> Review SAP module concepts, business processes, and ERP fundamentals."
                    else:
                        rec = "• <b>MCQ/Theory:</b> Review programming concepts, data structures, and algorithms theory."
                elif section == "coding":
                    rec = "• <b>Coding:</b> Practice more coding problems on platforms like LeetCode or HackerRank."
                else:
                    rec = f"• <b>{section}:</b> Review this section thoroughly."
                elements.append(Paragraph(rec, answer_style))
        else:
            elements.append(Paragraph(
                "🎉 Great performance across all sections! Keep up the excellent work.",
                styles['Normal']
            ))
        
        # ════════════════════════════════════════════════════════════
        # FOOTER
        # ════════════════════════════════════════════════════════════
        elements.append(Spacer(1, 30))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
        
        footer_style = ParagraphStyle(
            'Footer', parent=styles['Normal'],
            fontSize=8, textColor=colors.HexColor('#6b7280'), alignment=TA_CENTER
        )
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Mock Test Assessment System",
            footer_style
        ))
        
        # Build PDF
        pdf_doc.build(elements)
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        
        # ════════════════════════════════════════════════════════════
        # SAVE LOCAL + UPLOAD TO S3 + UPDATE MONGODB
        # ════════════════════════════════════════════════════════════
        pdf_path = os.path.join(self.output_dir, f"test_results_{test_id}.pdf")
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)
        
        # Use raw student_id (int/str) for S3 path
        s3_url = self._upload_to_s3(pdf_bytes, test_id, str(student_info["raw_id"] or "unknown"))
        
        update_fields = {
            "pdf_path": pdf_path,
            "pdf_generated_at": datetime.now().isoformat()
        }
        
        if s3_url:
            update_fields["pdf_url"] = s3_url
            logger.info(f"☁️ S3 URL stored in MongoDB: {s3_url}")
        else:
            update_fields["pdf_url"] = None
            logger.warning(f"⚠️ S3 upload failed, pdf_url set to None for test: {test_id}")
        
        self.db_manager.test_results_collection.update_one(
            {"test_id": test_id},
            {"$set": update_fields}
        )
        
        logger.info(f"📄 PDF generated, saved locally, uploaded to S3, and MongoDB updated: {test_id}")
        
        buffer.seek(0)
        return pdf_bytes
    
    async def get_pdf_path(self, test_id: str) -> Optional[str]:
        """Get stored PDF path for a test"""
        doc = self.db_manager.test_results_collection.find_one(
            {"test_id": test_id}, {"pdf_path": 1}
        )
        return doc.get("pdf_path") if doc else None

    async def get_pdf_url(self, test_id: str) -> Optional[str]:
        """Get S3 PDF URL for a test"""
        doc = self.db_manager.test_results_collection.find_one(
            {"test_id": test_id}, {"pdf_url": 1}
        )
        return doc.get("pdf_url") if doc else None


# Singleton
_pdf_service = None

def get_pdf_service() -> PDFService:
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFService()
    return _pdf_service