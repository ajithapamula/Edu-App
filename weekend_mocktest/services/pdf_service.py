# weekend_mocktest/services/pdf_service.py
"""
PDF Service - Generate Professional Test Result PDFs

Features:
- Section-wise breakdown (Aptitude → MCQ → Coding)
- Question-by-question analysis
- User Answer vs Correct Answer with PROPER CODE FORMATTING
- AI-generated step-by-step explanations (Groq)
- ✅/❌/⏭ status indicators (skipped questions shown in amber)
- Professional formatting
- ☁️ AWS S3 Upload with URL stored in MongoDB
- Student name, course, batch shown in PDF header
- 🔁 Serves cached PDF if already generated (no duplicate S3 uploads)
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

        self.output_dir = "static/pdf_reports"
        os.makedirs(self.output_dir, exist_ok=True)

        from ..core.config import config as app_config

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=app_config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=app_config.AWS_SECRET_ACCESS_KEY,
            region_name=app_config.AWS_REGION
        )
        self.s3_bucket = app_config.S3_BUCKET_NAME
        self.s3_folder = app_config.S3_PDF_FOLDER

        # Groq client for generating explanations on-the-fly
        try:
            from groq import Groq
            from ..core.config import config as app_config2
            self._groq = Groq(api_key=app_config2.GROQ_API_KEY)
            self._groq_model = app_config2.GROQ_MODEL
        except Exception as e:
            logger.warning(f"⚠️ Groq not available in PDFService: {e}")
            self._groq = None
            self._groq_model = "llama-3.1-8b-instant"

        logger.info("📄 PDF Service initialized with S3 Upload + Groq Explanation support")

    # ════════════════════════════════════════════════════════════
    # GROQ EXPLANATION GENERATOR
    # ════════════════════════════════════════════════════════════

    def _generate_explanation_for_question(
        self,
        question: str,
        user_answer: str,
        correct_answer: str,
        options: list = None,
    ) -> str:
        """
        Call Groq to generate a step-by-step explanation for a wrong question.
        Returns a plain-text explanation string.
        Falls back to a simple hint if Groq is unavailable.
        """
        if not self._groq:
            return f"The correct answer is {correct_answer}. Review the concept and understand the step-by-step working."

        try:
            options_text = ""
            if options:
                options_text = "\nOptions:\n" + "\n".join(
                    f"{chr(65+i)}) {opt}" for i, opt in enumerate(options)
                )

            prompt = (
                f"Question: {question}{options_text}\n"
                f"Student's Answer: {user_answer if user_answer else 'No answer (skipped)'}\n"
                f"Correct Answer: {correct_answer}\n\n"
                "Write a clear step-by-step explanation showing HOW to arrive at the correct answer.\n\n"
                "RULES:\n"
                "1. Show the actual calculation or reasoning steps (e.g. Step 1: ... Step 2: ...)\n"
                "2. For math/aptitude: write out the formula, plug in the numbers, show the working\n"
                "3. Point out WHERE the student went wrong if their answer differs\n"
                "4. End with: Therefore, the correct answer is [answer]\n"
                "5. Keep it under 5 lines total — be concise but complete\n"
                "6. NEVER just restate the answer — always show the WHY and HOW"
            )

            response = self._groq.chat.completions.create(
                model=self._groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert tutor. Give step-by-step explanations. "
                            "For math questions always show the calculation. Be concise and educational."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=250,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"❌ Groq explanation failed: {e}")
            return f"The correct answer is {correct_answer}. Review the step-by-step working for this topic."

    def _generate_explanations_batch_sync(self, wrong_items: List[Dict]) -> Dict[int, str]:
        """
        Generate explanations for multiple wrong questions in one Groq call.
        Returns {question_number: explanation_text}.
        """
        if not wrong_items or not self._groq:
            return {}

        try:
            lines = []
            for item in wrong_items:
                q_num     = item["question_number"]
                question  = item.get("question", "")
                correct   = item.get("correct_answer", "")
                user_ans  = item.get("user_answer") or item.get("answer") or "No answer (skipped)"
                options   = item.get("options", [])
                opts_text = ""
                if options:
                    opts_text = " Options: " + " / ".join(
                        f"{chr(65+i)}) {o}" for i, o in enumerate(options)
                    )
                lines.append(
                    f"Q{q_num}:\n"
                    f"Question: {question}{opts_text}\n"
                    f"Student answered: {user_ans}\n"
                    f"Correct answer: {correct}"
                )

            prompt = (
                "You are an expert tutor reviewing a student's test. "
                "For each question below, write a step-by-step explanation showing HOW to reach the correct answer.\n\n"
                "RULES:\n"
                "- Show calculation steps for math/aptitude (Step 1: ... Step 2: ...)\n"
                "- Identify exactly where the student went wrong\n"
                "- End each explanation with: Therefore, the correct answer is [answer]\n"
                "- Keep each explanation under 5 lines\n"
                "- NEVER just restate the answer — show the WHY and HOW\n\n"
                "Respond in this EXACT format for each question:\n"
                "Q<number>: <explanation>\n\n"
                + "\n\n".join(lines)
            )

            response = self._groq.chat.completions.create(
                model=self._groq_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert tutor. Give concise step-by-step explanations. Respond only with Q<n>: <explanation> lines.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1200,
            )

            raw = response.choices[0].message.content.strip()
            logger.info(f"💡 Groq batch explanations generated for {len(wrong_items)} questions")

            import re
            explanations = {}
            for match in re.finditer(r"Q(\d+):\s*(.+?)(?=\nQ\d+:|\Z)", raw, re.DOTALL):
                q_num = int(match.group(1))
                text  = match.group(2).strip().replace("\n", " ")
                explanations[q_num] = text

            return explanations

        except Exception as e:
            logger.error(f"❌ Batch explanation generation failed: {e}")
            return {}

    # ════════════════════════════════════════════════════════════
    # AWS S3
    # ════════════════════════════════════════════════════════════

    def _upload_to_s3(self, pdf_bytes: bytes, test_id: str, student_id: str = "unknown") -> Optional[str]:
        try:
            timestamp       = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_student_id = str(student_id) if student_id and str(student_id) not in ("N/A", "None", "", "0") else "unknown"
            s3_key          = f"{self.s3_folder}/student_{safe_student_id}/test_results_{test_id}_{timestamp}.pdf"

            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=pdf_bytes,
                ContentType='application/pdf',
                ContentDisposition=f'inline; filename="test_results_{test_id}.pdf"',
                Metadata={
                    'test_id':       test_id,
                    'student_id':    str(safe_student_id),
                    'generated_at':  datetime.now().isoformat(),
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
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.s3_bucket, 'Key': s3_key},
                ExpiresIn=expiration,
            )
            logger.info(f"🔗 Presigned URL generated (expires in {expiration}s)")
            return url
        except ClientError as e:
            logger.error(f"❌ Presigned URL generation failed: {e}")
            return None

    # ════════════════════════════════════════════════════════════
    # HELPERS
    # ════════════════════════════════════════════════════════════

    def _generate_presigned_url(self, s3_key: str, expiration: int = 86400) -> Optional[str]:
        """Generate a presigned URL for private S3 objects."""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.s3_bucket, 'Key': s3_key},
                ExpiresIn=expiration,
            )
            logger.info(f"🔗 Presigned URL generated (expires in {expiration}s)")
            return url
        except ClientError as e:
            logger.error(f"❌ Presigned URL generation failed: {e}")
            return None

    def _is_code_content(self, text: str) -> bool:
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
        if not code:
            return ""
        code = str(code)
        code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        code = code.replace('\n', '<br/>')
        code = code.replace('    ', '&nbsp;&nbsp;&nbsp;&nbsp;')
        code = code.replace('  ', '&nbsp;&nbsp;')
        return code

    def _get_student_info(self, doc: dict) -> dict:
        student_id   = doc.get("student_id")
        student_name = doc.get("student_name", "")
        course       = doc.get("course", "")
        batch        = doc.get("batch", "")
        role_type    = doc.get("role_type", "")

        profile = doc.get("student_profile", {})
        if profile:
            student_id   = student_id   or profile.get("student_id")
            student_name = student_name or profile.get("student_name", "")
            course       = course       or profile.get("course", "")
            batch        = batch        or profile.get("batch", "")
            role_type    = role_type    or profile.get("role_type", "")

        student_id_str = str(student_id) if student_id and str(student_id) not in ("None", "0", "") else "N/A"
        student_name   = student_name.strip() if student_name else "N/A"
        course         = course.strip()       if course       else "N/A"
        batch          = batch.strip()        if batch        else "N/A"

        return {
            "student_id":   student_id_str,
            "student_name": student_name,
            "course":       course,
            "batch":        batch,
            "role_type":    role_type,
            "raw_id":       student_id,
        }

    def _is_skipped(self, user_answer) -> bool:
        return not user_answer or str(user_answer).strip() in ("", "No answer", "None", "No answer (Skipped)")

    def _safe(self, text: str) -> str:
        """Escape HTML special chars for ReportLab paragraphs."""
        return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    # ════════════════════════════════════════════════════════════
    # MAIN PDF GENERATOR
    # ════════════════════════════════════════════════════════════

    async def generate_test_results_pdf(self, test_id: str) -> bytes:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                PageBreak, HRFlowable,
            )
            from reportlab.lib.units import inch
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
        except ImportError:
            raise Exception("PDF generation requires reportlab: pip install reportlab --break-system-packages")

        # ── Cache check ───────────────────────────────────────────
        doc_check = self.db_manager.test_results_collection.find_one(
            {"test_id": test_id}, {"pdf_path": 1, "pdf_url": 1}
        )
        if doc_check and doc_check.get("pdf_path"):
            cached_path = doc_check["pdf_path"]
            if os.path.exists(cached_path):
                logger.info(f"📄 Serving cached PDF for {test_id[:8]}")
                with open(cached_path, 'rb') as f:
                    return f.read()
            else:
                logger.info(f"🔄 Cached path missing on disk — regenerating for {test_id[:8]}")
        # ──────────────────────────────────────────────────────────

        doc = self.db_manager.test_results_collection.find_one({"test_id": test_id}, {"_id": 0})
        if not doc:
            raise Exception(f"Test results not found: {test_id}")

        student_info = self._get_student_info(doc)
        student_id   = student_info["student_id"]
        student_name = student_info["student_name"]
        course       = student_info["course"]
        batch        = student_info["batch"]

        logger.info(f"📄 Generating PDF for {student_id} ({student_name})")

        # ════════════════════════════════════════════════════════════
        # PRE-GENERATE EXPLANATIONS for all wrong questions (one Groq call)
        # ════════════════════════════════════════════════════════════
        section_details    = doc.get("section_details", {})
        conversation_pairs = doc.get("conversation_pairs", [])

        # Build a lookup from question_number → existing explanation from conversation_pairs
        cp_explanation_map: Dict[int, str] = {}
        for cp in conversation_pairs:
            q_num    = cp.get("question_number")
            feedback = str(cp.get("feedback", "")).strip()
            if q_num and feedback:
                cp_explanation_map[q_num] = feedback

        # Collect all wrong/skipped questions that lack a good explanation
        wrong_items_needing_explanation = []
        # Maps global_idx → (sec_name, q_num) to avoid cross-section q_num collisions
        groq_index_to_key: Dict[int, tuple] = {}
        global_idx = 1

        def _needs_explanation(q_num: int, explanation: str, is_correct: bool, skipped: bool) -> bool:
            if is_correct:
                return False
            if explanation and len(explanation.strip()) > 20:
                return False  # already has one
            if cp_explanation_map.get(q_num) and len(cp_explanation_map[q_num]) > 20:
                return False  # conversation_pairs has one
            return True  # needs Groq

        if section_details:
            for sec_name, details in section_details.items():
                # Coding questions already have explanations from evaluate_by_section
                if sec_name == "coding":
                    continue
                for q in details.get("questions", []):
                    q_num       = q.get("question_number", 0)
                    is_correct  = q.get("is_correct", False)
                    user_ans    = q.get("user_answer", "")
                    skipped     = self._is_skipped(user_ans)
                    explanation = str(q.get("explanation", "")).strip()
                    if _needs_explanation(q_num, explanation, is_correct, skipped):
                        wrong_items_needing_explanation.append({
                            "question_number": global_idx,
                            "question":        q.get("question", ""),
                            "user_answer":     user_ans,
                            "correct_answer":  q.get("correct_answer", "N/A"),
                            "options":         q.get("options", []),
                        })
                        groq_index_to_key[global_idx] = (sec_name, q_num)
                        global_idx += 1
        elif conversation_pairs:
            for cp in conversation_pairs:
                q_num      = cp.get("question_number", 0)
                q_type     = cp.get("question_type", "mcq")
                is_correct = cp.get("correct", False)
                user_ans   = cp.get("answer", "")
                skipped    = self._is_skipped(user_ans)
                feedback   = str(cp.get("feedback", "")).strip()
                # Coding questions have their own explanation
                if q_type == "coding":
                    continue
                if _needs_explanation(q_num, feedback, is_correct, skipped):
                    wrong_items_needing_explanation.append({
                        "question_number": global_idx,
                        "question":        cp.get("question", ""),
                        "user_answer":     user_ans,
                        "correct_answer":  cp.get("correct_answer", "N/A"),
                        "options":         cp.get("options", []),
                    })
                    groq_index_to_key[global_idx] = ("cp", q_num)
                    global_idx += 1

        # One Groq call for all missing explanations
        # groq_raw_map: {global_idx: explanation_text}
        groq_raw_map: Dict[int, str] = {}
        if wrong_items_needing_explanation:
            logger.info(f"💡 Calling Groq for {len(wrong_items_needing_explanation)} missing explanations...")
            groq_raw_map = self._generate_explanations_batch_sync(wrong_items_needing_explanation)
            logger.info(f"✅ Groq returned {len(groq_raw_map)} explanations")

        # Rebuild keyed by (sec_name, q_num) to avoid cross-section collisions
        groq_key_map: Dict[tuple, str] = {}
        for gidx, exp_text in groq_raw_map.items():
            key = groq_index_to_key.get(gidx)
            if key:
                groq_key_map[key] = exp_text

        def _get_explanation(q_num: int, stored_exp: str, is_correct: bool,
                             sec_name: str = "mcq") -> str:
            """Return best available explanation for a question."""
            if is_correct:
                return ""
            if stored_exp and len(stored_exp.strip()) > 20:
                return stored_exp.strip()
            if cp_explanation_map.get(q_num) and len(cp_explanation_map[q_num]) > 20:
                return cp_explanation_map[q_num]
            groq_val = groq_key_map.get((sec_name, q_num)) or groq_key_map.get(("cp", q_num))
            if groq_val:
                return groq_val
            return ""

        # ════════════════════════════════════════════════════════════
        # STYLES
        # ════════════════════════════════════════════════════════════
        buffer  = io.BytesIO()
        pdf_doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            topMargin=0.5*inch, bottomMargin=0.5*inch,
            leftMargin=0.5*inch, rightMargin=0.5*inch,
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'CustomTitle', parent=styles['Heading1'],
            fontSize=20, alignment=TA_CENTER, spaceAfter=10,
            textColor=colors.HexColor('#1a365d'),
        )
        subtitle_style = ParagraphStyle(
            'SubTitle', parent=styles['Normal'],
            fontSize=11, alignment=TA_CENTER, spaceAfter=15,
            textColor=colors.HexColor('#374151'),
        )
        section_header_style = ParagraphStyle(
            'SectionHeader', parent=styles['Heading2'],
            fontSize=14, spaceBefore=15, spaceAfter=10,
            textColor=colors.HexColor('#2563eb'),
        )
        answer_style = ParagraphStyle(
            'AnswerStyle', parent=styles['Normal'],
            fontSize=9, leftIndent=20,
            textColor=colors.HexColor('#374151'),
        )
        explanation_style = ParagraphStyle(
            'ExplanationStyle', parent=styles['Normal'],
            fontSize=9, leftIndent=20,
            textColor=colors.HexColor('#4b5563'),
            fontName='Helvetica-Oblique',
        )
        correct_style = ParagraphStyle(
            'CorrectStyle', parent=styles['Normal'],
            fontSize=9, leftIndent=20,
            textColor=colors.HexColor('#059669'),
        )
        wrong_style = ParagraphStyle(
            'WrongStyle', parent=styles['Normal'],
            fontSize=9, leftIndent=20,
            textColor=colors.HexColor('#dc2626'),
        )
        skipped_style = ParagraphStyle(
            'SkippedStyle', parent=styles['Normal'],
            fontSize=9, leftIndent=20,
            textColor=colors.HexColor('#d97706'),
            fontName='Helvetica-Oblique',
        )
        code_style = ParagraphStyle(
            'CodeStyle', parent=styles['Normal'],
            fontSize=8, fontName='Courier',
            leftIndent=25, rightIndent=10,
            spaceBefore=5, spaceAfter=5,
            backColor=colors.HexColor('#1e293b'),
            textColor=colors.HexColor('#4ade80'),
            borderColor=colors.HexColor('#334155'),
            borderWidth=1, borderPadding=8, leading=12,
        )
        code_label_style = ParagraphStyle(
            'CodeLabelStyle', parent=styles['Normal'],
            fontSize=8, fontName='Helvetica-Bold',
            leftIndent=20, spaceBefore=5, spaceAfter=2,
            textColor=colors.HexColor('#059669'),
        )
        user_code_style = ParagraphStyle(
            'UserCodeStyle', parent=styles['Normal'],
            fontSize=8, fontName='Courier',
            leftIndent=25, rightIndent=10,
            spaceBefore=5, spaceAfter=5,
            backColor=colors.HexColor('#fef2f2'),
            textColor=colors.HexColor('#991b1b'),
            borderColor=colors.HexColor('#fecaca'),
            borderWidth=1, borderPadding=8, leading=12,
        )

        elements = []

        # ════════════════════════════════════════════════════════════
        # HEADER
        # ════════════════════════════════════════════════════════════
        user_type  = doc.get("user_type", "dev")
        track_name = "Non-Developer" if user_type == "non_dev" else "Developer"

        elements.append(Paragraph(f"📋 {track_name} Mock Test Results", title_style))
        if student_name and student_name != "N/A":
            elements.append(Paragraph(f"Student: <b>{student_name}</b>", subtitle_style))
        elements.append(Spacer(1, 10))

        # ════════════════════════════════════════════════════════════
        # INFO TABLE
        # ════════════════════════════════════════════════════════════
        score         = doc.get("score", 0)
        total         = doc.get("total_questions", 0)
        percentage    = doc.get("score_percentage", 0)
        warning_count = doc.get("warning_count", 0)
        terminated    = doc.get("terminated_by_warnings", False)
        timestamp     = doc.get("timestamp", 0)

        try:
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S') if timestamp else "N/A"
        except:
            date_str = "N/A"

        if percentage >= 80:   performance = "🏆 Excellent"
        elif percentage >= 60: performance = "👍 Good"
        elif percentage >= 40: performance = "📚 Average"
        else:                  performance = "⚠️ Needs Improvement"

        info_data = [
            ["Name:",          student_name,        "Student ID:",   student_id],
            ["Date:",          date_str,             "Performance:",  performance],
            ["Overall Score:", f"{score}/{total} ({percentage}%)",
             "Test ID:",       test_id[:18] + "..." if len(test_id) > 18 else test_id],
            ["Warnings:",      f"{warning_count}/3", "Status:",       "TERMINATED ❌" if terminated else "Completed ✅"],
        ]

        info_table = Table(info_data, colWidths=[1.3*inch, 2.2*inch, 1.3*inch, 1.8*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE',      (0, 0), (-1, -1), 9),
            ('FONTNAME',      (0, 0), (0, -1),  'Helvetica-Bold'),
            ('FONTNAME',      (2, 0), (2, -1),  'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING',    (0, 0), (-1, -1), 8),
            ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX',           (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
            ('LINEBELOW',     (0, 0), (-1, -2), 0.5, colors.HexColor('#e2e8f0')),
            ('BACKGROUND',    (0, 0), (0, -1),  colors.HexColor('#eef2f7')),
            ('BACKGROUND',    (2, 0), (2, -1),  colors.HexColor('#eef2f7')),
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
                "coding":   "💻 Coding",
            }
            for section, data in section_scores.items():
                if isinstance(data, dict):
                    correct   = data.get("correct", 0)
                    total_sec = data.get("total", 0)
                    pct       = data.get("percentage", 0)
                    sec_name  = section_icons.get(section, section.upper())
                    status    = "✅ Pass" if pct >= 50 else "⚠️ Needs Work"
                    section_data.append([sec_name, f"{correct}/{total_sec}", f"{pct}%", status])

            if len(section_data) > 1:
                sec_table = Table(section_data, colWidths=[2.5*inch, 1.2*inch, 1.2*inch, 1.5*inch])
                sec_table.setStyle(TableStyle([
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
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')]),
                ]))
                elements.append(sec_table)
                elements.append(Spacer(1, 20))

        # ════════════════════════════════════════════════════════════
        # DETAILED QUESTION REVIEW
        # ════════════════════════════════════════════════════════════
        elements.append(Paragraph("📝 Detailed Question Review", section_header_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
        elements.append(Spacer(1, 10))

        def _render_question_block(
            q_num, is_correct, question_text, user_answer, correct_answer,
            explanation, options, is_coding_section, sec_name="mcq",
        ):
            """Render one question block into elements list."""
            skipped        = self._is_skipped(user_answer)
            is_code_answer = is_coding_section or self._is_code_content(correct_answer) or self._is_code_content(user_answer)

            if skipped:
                status       = "⏭"
                status_color = colors.HexColor('#d97706')
            elif is_correct:
                status       = "✅"
                status_color = colors.HexColor('#059669')
            else:
                status       = "❌"
                status_color = colors.HexColor('#dc2626')

            q_header_style = ParagraphStyle(
                f'QHeader_{q_num}', parent=styles['Normal'],
                fontSize=10, fontName='Helvetica-Bold',
                textColor=status_color, spaceBefore=12, spaceAfter=4,
            )

            q_display = (question_text[:150] + '...') if len(question_text) > 150 else question_text
            elements.append(Paragraph(f"{status} Q{q_num}. {self._safe(q_display)}", q_header_style))

            if is_code_answer:
                wrong_label_style = ParagraphStyle(
                    f'WrongLabel_{q_num}', parent=styles['Normal'],
                    fontSize=8, fontName='Helvetica-Bold', leftIndent=20,
                    spaceBefore=5, spaceAfter=2,
                    textColor=colors.HexColor('#dc2626'),
                )
                user_answer_str   = str(user_answer)   if user_answer   else ""
                correct_answer_str = str(correct_answer) if correct_answer else ""

                if skipped:
                    elements.append(Paragraph("⏭ <b>Skipped</b> — no answer submitted", skipped_style))
                else:
                    elements.append(Paragraph(
                        "Your Answer:",
                        code_label_style if is_correct else wrong_label_style,
                    ))
                    formatted_user = self._format_code_for_pdf(user_answer_str)
                    elements.append(Paragraph(
                        formatted_user if formatted_user else "<i>(No code submitted)</i>",
                        code_style if is_correct else user_code_style,
                    ))
                if not is_correct:
                    elements.append(Paragraph("Correct Answer:", code_label_style))
                    formatted_correct = self._format_code_for_pdf(correct_answer_str)
                    elements.append(Paragraph(
                        formatted_correct if formatted_correct else "<i>See approach hint in explanation below</i>",
                        code_style,
                    ))
            else:
                ca_safe = self._safe(correct_answer)
                if skipped:
                    elements.append(Paragraph("⏭ <b>Skipped</b> — no answer submitted", skipped_style))
                    elements.append(Paragraph(f"<b>Correct Answer:</b> {ca_safe}", correct_style))
                elif is_correct:
                    elements.append(Paragraph(f"<b>Your Answer:</b> {self._safe(user_answer)}", correct_style))
                else:
                    elements.append(Paragraph(f"<b>Your Answer:</b> {self._safe(user_answer)}", wrong_style))
                    elements.append(Paragraph(f"<b>Correct Answer:</b> {ca_safe}", correct_style))

            # ── Explanation ───────────────────────────────────────
            if is_correct:
                pass  # no explanation needed for correct answers
            else:
                final_explanation = _get_explanation(q_num, explanation, is_correct, sec_name)
                if final_explanation:
                    # Split explanation into individual steps and render each on its own line
                    import re as _re
                    # Split on "Step N:" or "Therefore," patterns
                    step_parts = _re.split(
                        r'(?=Step\s+\d+\s*:|Therefore[,\s])',
                        final_explanation,
                        flags=_re.IGNORECASE
                    )
                    step_parts = [s.strip() for s in step_parts if s.strip()]

                    if len(step_parts) > 1:
                        # Render 💡 label once, then each step on its own line
                        elements.append(Paragraph("💡 <i>Explanation:</i>", explanation_style))
                        for step in step_parts:
                            # Bold the "Step N:" prefix, italicise rest
                            step_safe = self._safe(step)
                            step_match = _re.match(r'^(Step\s+\d+\s*:)(.*)', step_safe, _re.IGNORECASE)
                            therefore_match = _re.match(r'^(Therefore[,\s].*)', step_safe, _re.IGNORECASE)
                            if step_match:
                                label = step_match.group(1)
                                body  = step_match.group(2).strip()
                                elements.append(Paragraph(
                                    f"&nbsp;&nbsp;&nbsp;<b>{label}</b> <i>{body}</i>",
                                    explanation_style,
                                ))
                            elif therefore_match:
                                elements.append(Paragraph(
                                    f"&nbsp;&nbsp;&nbsp;<b><i>{step_safe}</i></b>",
                                    explanation_style,
                                ))
                            else:
                                elements.append(Paragraph(
                                    f"&nbsp;&nbsp;&nbsp;<i>{step_safe}</i>",
                                    explanation_style,
                                ))
                    else:
                        # No steps found — render as single paragraph
                        elements.append(Paragraph(
                            f"💡 <i>{self._safe(final_explanation)}</i>",
                            explanation_style,
                        ))
                else:
                    # Last-resort fallback (should rarely happen)
                    elements.append(Paragraph(
                        f"💡 <i>The correct answer is <b>{self._safe(correct_answer)}</b>. "
                        f"Review the step-by-step working for this topic.</i>",
                        explanation_style,
                    ))
            # ─────────────────────────────────────────────────────

            elements.append(Spacer(1, 8))

        # ── Render section_details (normal completed tests) ──────
        if section_details:
            for section_name, details in section_details.items():
                section_icon  = "🧮" if section_name == "aptitude" else ("📚" if section_name in ["mcq", "theory"] else "💻")
                section_score = details.get("score", {})
                questions     = details.get("questions", [])
                is_coding_sec = section_name == "coding"

                elements.append(Paragraph(
                    f"{section_icon} {section_name.upper()} SECTION "
                    f"({section_score.get('correct', 0)}/{section_score.get('total', 0)} - "
                    f"{section_score.get('percentage', 0)}%)",
                    section_header_style,
                ))

                for q in questions:
                    _render_question_block(
                        q_num          = q.get("question_number", "?"),
                        is_correct     = q.get("is_correct", False),
                        question_text  = q.get("question", ""),
                        user_answer    = q.get("user_answer", ""),
                        correct_answer = q.get("correct_answer", "N/A"),
                        explanation    = q.get("explanation", ""),
                        options        = q.get("options", []),
                        is_coding_section = is_coding_sec,
                        sec_name       = section_name,
                    )

                elements.append(Spacer(1, 10))
                elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#e2e8f0')))

        elif conversation_pairs:
            # ── Fallback: terminated tests use conversation_pairs ─
            sections_grouped = {"aptitude": [], "mcq": [], "coding": []}
            for qa in conversation_pairs:
                q_type = qa.get("question_type", "mcq")
                sections_grouped.get(q_type, sections_grouped["mcq"]).append(qa)

            for section_name, questions in sections_grouped.items():
                if not questions:
                    continue

                section_icon = "🧮" if section_name == "aptitude" else ("📚" if section_name == "mcq" else "💻")
                correct_in_section = sum(1 for q in questions if q.get("correct", False))
                is_coding_sec      = section_name == "coding"

                elements.append(Paragraph(
                    f"{section_icon} {section_name.upper()} SECTION ({correct_in_section}/{len(questions)})",
                    section_header_style,
                ))

                for qa in questions:
                    _render_question_block(
                        q_num          = qa.get("question_number", "?"),
                        is_correct     = qa.get("correct", False),
                        question_text  = qa.get("question", "")[:150],
                        user_answer    = qa.get("answer", ""),
                        correct_answer = qa.get("correct_answer", "N/A"),
                        explanation    = qa.get("feedback", ""),
                        options        = qa.get("options", []),
                        is_coding_section = is_coding_sec,
                        sec_name       = section_name,
                    )

                elements.append(Spacer(1, 10))

        # ════════════════════════════════════════════════════════════
        # WARNINGS
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
                    w.get("timestamp_readable", "N/A"),
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
                    textColor=colors.HexColor('#dc2626'), fontName='Helvetica-Bold',
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
                styles['Normal'],
            ))

        # ════════════════════════════════════════════════════════════
        # FOOTER
        # ════════════════════════════════════════════════════════════
        elements.append(Spacer(1, 30))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
        footer_style = ParagraphStyle(
            'Footer', parent=styles['Normal'],
            fontSize=8, textColor=colors.HexColor('#6b7280'), alignment=TA_CENTER,
        )
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Mock Test Assessment System",
            footer_style,
        ))

        # ════════════════════════════════════════════════════════════
        # BUILD + SAVE + S3
        # ════════════════════════════════════════════════════════════
        pdf_doc.build(elements)
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()

        pdf_path = os.path.join(self.output_dir, f"test_results_{test_id}.pdf")
        with open(pdf_path, 'wb') as f:
            f.write(pdf_bytes)

        s3_url = self._upload_to_s3(pdf_bytes, test_id, str(student_info["raw_id"] or "unknown"))

        update_fields = {"pdf_path": pdf_path, "pdf_generated_at": datetime.now().isoformat()}
        if s3_url:
            update_fields["pdf_url"] = s3_url
        else:
            update_fields["pdf_url"] = None
            logger.warning(f"⚠️ S3 upload failed for test: {test_id}")

        self.db_manager.test_results_collection.update_one(
            {"test_id": test_id}, {"$set": update_fields}
        )

        logger.info(f"📄 PDF complete for {test_id[:8]} | student={student_name}")
        buffer.seek(0)
        return pdf_bytes

    # ════════════════════════════════════════════════════════════
    # GETTERS
    # ════════════════════════════════════════════════════════════

    async def get_pdf_path(self, test_id: str) -> Optional[str]:
        doc = self.db_manager.test_results_collection.find_one({"test_id": test_id}, {"pdf_path": 1})
        return doc.get("pdf_path") if doc else None

    async def get_pdf_url(self, test_id: str) -> Optional[str]:
        doc = self.db_manager.test_results_collection.find_one({"test_id": test_id}, {"pdf_url": 1})
        return doc.get("pdf_url") if doc else None


# Singleton
_pdf_service = None

def get_pdf_service() -> PDFService:
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFService()
    return _pdf_service
