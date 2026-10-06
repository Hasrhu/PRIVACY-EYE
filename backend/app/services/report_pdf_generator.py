"""
Privacy Eye — Scan Report PDF Generator
Generates a professional, multi-page or comprehensive A4 forensic evidence document
with dark cyber aesthetics, face evidence frame, test matrices, and model lineage.
"""
import io
import os
from typing import Dict, Any, List, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas
import structlog

logger = structlog.get_logger(__name__)

# Color Palette
COLOR_BG = colors.HexColor("#0B0F19")
COLOR_CARD = colors.HexColor("#111827")
COLOR_CARD_BORDER = colors.HexColor("#1F2937")
COLOR_PRIMARY = colors.HexColor("#3B82F6")   # Blue
COLOR_CYAN = colors.HexColor("#06B6D4")      # Cyan
COLOR_VIOLET = colors.HexColor("#8B5CF6")    # Violet
COLOR_SAFE = colors.HexColor("#10B981")      # Emerald / Green
COLOR_WARNING = colors.HexColor("#F59E0B")   # Amber / Warning
COLOR_DANGER = colors.HexColor("#EF4444")    # Red / Danger
COLOR_TEXT_WHITE = colors.HexColor("#F9FAFB")
COLOR_TEXT_MUTED = colors.HexColor("#9CA3AF")
COLOR_TEXT_DIM = colors.HexColor("#6B7280")


class NumberedCanvas(canvas.Canvas):
    """Adds professional header and footer with page count to all pages."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        # Page background dark wash
        self.setFillColor(COLOR_BG)
        self.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)

        # Header bar
        self.setStrokeColor(COLOR_CARD_BORDER)
        self.setLineWidth(0.5)
        self.line(40, A4[1] - 35, A4[0] - 40, A4[1] - 35)

        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(COLOR_CYAN)
        self.drawString(40, A4[1] - 28, "PRIVACY EYE")
        self.setFont("Helvetica", 7)
        self.setFillColor(COLOR_TEXT_MUTED)
        self.drawString(110, A4[1] - 28, "|   DIGITAL AUTHENTICITY AUDIT & FORENSIC DOSSIER")

        # Footer bar
        self.line(40, 35, A4[0] - 40, 35)
        self.setFont("Helvetica", 7)
        self.setFillColor(COLOR_TEXT_DIM)
        self.drawString(40, 22, "CONFIDENTIAL & PROBABILISTIC EVIDENCE — DO NOT USE AS SOLE GROUND FOR LEGAL ACTION")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(A4[0] - 40, 22, page_str)
        self.restoreState()


class ReportPdfGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._init_custom_styles()

    def _init_custom_styles(self):
        self.styles.add(ParagraphStyle(
            "DocTitle",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=COLOR_TEXT_WHITE,
            spaceAfter=4,
        ))
        self.styles.add(ParagraphStyle(
            "DocSubtitle",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=COLOR_TEXT_MUTED,
            spaceAfter=12,
        ))
        self.styles.add(ParagraphStyle(
            "SectionHeader",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=COLOR_CYAN,
            spaceBefore=10,
            spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            "BodyWhite",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=COLOR_TEXT_WHITE,
        ))
        self.styles.add(ParagraphStyle(
            "BodyMuted",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=COLOR_TEXT_MUTED,
        ))
        self.styles.add(ParagraphStyle(
            "ResultAssessment",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=COLOR_TEXT_WHITE,
            alignment=1, # Center
        ))
        self.styles.add(ParagraphStyle(
            "ResultMeta",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=COLOR_CYAN,
            alignment=1, # Center
        ))
        self.styles.add(ParagraphStyle(
            "TableCell",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9.5,
            textColor=COLOR_TEXT_WHITE,
        ))
        self.styles.add(ParagraphStyle(
            "TableCellBold",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9.5,
            textColor=COLOR_TEXT_WHITE,
        ))
        self.styles.add(ParagraphStyle(
            "TableHead",
            parent=self.styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=7.5,
            leading=9.5,
            textColor=COLOR_CYAN,
        ))
        self.styles.add(ParagraphStyle(
            "DisclaimerText",
            parent=self.styles["Normal"],
            fontName="Helvetica",
            fontSize=7,
            leading=9.5,
            textColor=COLOR_TEXT_MUTED,
        ))

    def generate_pdf(
        self,
        report_data: Dict[str, Any],
        face_img_bytes: Optional[bytes] = None,
    ) -> bytes:
        """
        Builds and returns valid PDF bytes for the specified scan report data.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=40,
            rightMargin=40,
            topMargin=45,
            bottomMargin=45,
        )

        elements = []

        # ── 1. Document Title Header ──────────────────────────────────────────
        elements.append(Paragraph("PRIVACY EYE FORENSIC DOSSIER", self.styles["DocTitle"]))
        sub_text = (
            f"DIGITAL AUTHENTICITY & BIOMETRIC LIVENESS AUDIT REPORT  •  "
            f"REPORT ID: <font color='#06B6D4'><b>{report_data.get('report_number', 'PE-UNKNOWN')}</b></font>"
        )
        elements.append(Paragraph(sub_text, self.styles["DocSubtitle"]))
        elements.append(HRFlowable(width="100%", thickness=1, color=COLOR_CARD_BORDER, spaceBefore=0, spaceAfter=10))

        # ── 2. Scan Overview Grid & Key Metrics ────────────────────────────────
        created_at_str = report_data.get("created_at_formatted") or report_data.get("created_at") or "UTC"
        user_ref = report_data.get("user_email") or report_data.get("user_id") or "Authenticated User"
        session_id = report_data.get("live_session_id", "N/A")

        info_data = [
            [
                Paragraph("<b>Report Number:</b>", self.styles["BodyMuted"]),
                Paragraph(str(report_data.get("report_number")), self.styles["BodyWhite"]),
                Paragraph("<b>Date / Time:</b>", self.styles["BodyMuted"]),
                Paragraph(str(created_at_str), self.styles["BodyWhite"]),
            ],
            [
                Paragraph("<b>Account Ref:</b>", self.styles["BodyMuted"]),
                Paragraph(str(user_ref), self.styles["BodyWhite"]),
                Paragraph("<b>Session ID:</b>", self.styles["BodyMuted"]),
                Paragraph(str(session_id), self.styles["BodyWhite"]),
            ],
            [
                Paragraph("<b>Media Type:</b>", self.styles["BodyMuted"]),
                Paragraph("LIVE CAMERA STREAM", self.styles["BodyWhite"]),
                Paragraph("<b>Processing Location:</b>", self.styles["BodyMuted"]),
                Paragraph(str(report_data.get("processing_location", "EDGE / LOCAL SERVER")), self.styles["BodyWhite"]),
            ],
            [
                Paragraph("<b>Input Quality:</b>", self.styles["BodyMuted"]),
                Paragraph(str(report_data.get("input_quality", "GOOD")), self.styles["BodyWhite"]),
                Paragraph("<b>Report Status:</b>", self.styles["BodyMuted"]),
                Paragraph(str(report_data.get("report_status", "COMPLETED")), self.styles["BodyWhite"]),
            ],
        ]
        info_table = Table(info_data, colWidths=[100, 160, 100, 155])
        info_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_CARD_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#1A2234")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 10))

        # ── 3. Visual Evidence (Face Frame) & Primary Assessment Banner ────────
        conf_val = float(report_data.get("confidence", 0.0))
        conf_pct = f"{conf_val:.1f}%"
        reliability = str(report_data.get("reliability", "MEDIUM"))
        assessment = str(report_data.get("assessment", "LIKELY_LIVE_HUMAN")).replace("_", " ")

        # Status color
        if conf_val >= 80.0 and "REPLAY" not in assessment:
            status_color = COLOR_SAFE
        elif conf_val >= 60.0 and "REPLAY" not in assessment:
            status_color = COLOR_WARNING
        else:
            status_color = COLOR_DANGER

        # Assessment callout box
        eval_cell_content = [
            Paragraph(f"<font color='{status_color.hexval()}'><b>{assessment.upper()}</b></font>", self.styles["ResultAssessment"]),
            Spacer(1, 4),
            Paragraph(f"Calibrated Confidence: <b>{conf_pct}</b>  •  Reliability: <b>{reliability}</b>", self.styles["ResultMeta"]),
            Spacer(1, 4),
            Paragraph(str(report_data.get("explanation", "Multi-signal authenticity evaluation completed.")), self.styles["BodyMuted"]),
        ]

        if face_img_bytes:
            try:
                # Wrap face image in reportlab Image
                face_io = io.BytesIO(face_img_bytes)
                rl_face = RLImage(face_io, width=140, height=140)
                face_caption = [
                    rl_face,
                    Spacer(1, 3),
                    Paragraph("<font size='6' color='#9CA3AF'>Representative evidence frame.<br/>Analyzed target: Face 1</font>", self.styles["TableCell"]),
                ]
            except Exception as e:
                logger.warning("Failed to render face image in PDF", error=str(e))
                face_caption = [Paragraph("<i>Face image preview unavailable</i>", self.styles["BodyMuted"])]
        else:
            face_caption = [
                Paragraph("<b>NO FACE IMAGE STORED</b>", self.styles["TableCellBold"]),
                Spacer(1, 4),
                Paragraph("<font size='6' color='#9CA3AF'>Zero-Biometric Storage policy enforced per user privacy preference.</font>", self.styles["TableCell"]),
            ]

        hero_table_data = [[
            face_caption,
            eval_cell_content
        ]]
        hero_table = Table(hero_table_data, colWidths=[160, 355])
        hero_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD),
            ("BOX", (0, 0), (-1, -1), 1, status_color),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(hero_table)
        elements.append(Spacer(1, 10))

        # ── 4. "Why This Confidence?" Section ─────────────────────────────────
        elements.append(Paragraph("WHY THIS CONFIDENCE WAS ASSIGNED", self.styles["SectionHeader"]))
        why_reasons = report_data.get("why_reasons") or []
        if not why_reasons and report_data.get("explanation"):
            why_reasons = [report_data["explanation"]]

        why_paragraphs = []
        for r in why_reasons[:6]:
            why_paragraphs.append([
                Paragraph("<font color='#10B981'><b>✓</b></font>", self.styles["TableCellBold"]),
                Paragraph(str(r), self.styles["BodyWhite"]),
            ])

        if why_paragraphs:
            why_table = Table(why_paragraphs, colWidths=[20, 495])
            why_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD),
                ("BOX", (0, 0), (-1, -1), 0.5, COLOR_CARD_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]))
            elements.append(why_table)
        elements.append(Spacer(1, 10))

        # ── 5. Verification Tests Matrix ──────────────────────────────────────
        elements.append(Paragraph("TEST RESULTS & VERIFICATION AUDIT", self.styles["SectionHeader"]))
        tests = report_data.get("tests", [])
        test_rows = [[
            Paragraph("TEST NAME", self.styles["TableHead"]),
            Paragraph("STATUS", self.styles["TableHead"]),
            Paragraph("SCORE", self.styles["TableHead"]),
            Paragraph("FINDINGS & OBSERVATION", self.styles["TableHead"]),
        ]]

        for t in tests:
            status = str(t.get("status", "PASS")).upper()
            if status == "PASS":
                st_color = "#10B981"
            elif status == "WARNING":
                st_color = "#F59E0B"
            elif status == "FAIL":
                st_color = "#EF4444"
            else:
                st_color = "#9CA3AF"

            score_str = f"{t['score']:.2f}" if t.get("score") is not None else "—"
            test_rows.append([
                Paragraph(str(t.get("test_name")), self.styles["TableCellBold"]),
                Paragraph(f"<font color='{st_color}'><b>{status}</b></font>", self.styles["TableCell"]),
                Paragraph(score_str, self.styles["TableCell"]),
                Paragraph(str(t.get("message", "Test passed verification criteria.")), self.styles["TableCell"]),
            ])

        test_table = Table(test_rows, colWidths=[120, 75, 45, 275])
        test_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_CARD_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#1A2234")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(test_table)
        elements.append(Spacer(1, 10))

        # ── 6. Forensic Signal Breakdown & Ocular Analysis ────────────────────
        elements.append(Paragraph("FORENSIC BIOMETRIC & OCULAR SIGNALS", self.styles["SectionHeader"]))
        signals = report_data.get("signals", [])
        signal_rows = [[
            Paragraph("SIGNAL INDICATOR", self.styles["TableHead"]),
            Paragraph("VALUE / LEVEL", self.styles["TableHead"]),
            Paragraph("SEVERITY", self.styles["TableHead"]),
            Paragraph("TECHNICAL EXPLANATION", self.styles["TableHead"]),
        ]]
        for s in signals:
            st = str(s.get("signal_status", "INFO")).upper()
            st_color = "#10B981" if st == "PASS" else ("#F59E0B" if st == "WARNING" else "#3B82F6")
            signal_rows.append([
                Paragraph(str(s.get("signal_name")), self.styles["TableCellBold"]),
                Paragraph(str(s.get("signal_value")), self.styles["TableCell"]),
                Paragraph(f"<font color='{st_color}'><b>{st}</b></font>", self.styles["TableCell"]),
                Paragraph(str(s.get("signal_explanation", "Observed biometric parameter.")), self.styles["TableCell"]),
            ])

        signal_table = Table(signal_rows, colWidths=[130, 85, 55, 245])
        signal_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
            ("BACKGROUND", (0, 1), (-1, -1), COLOR_CARD),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_CARD_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#1A2234")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(signal_table)
        elements.append(Spacer(1, 10))

        # ── 7. Model Governance & Cryptographic Proof ─────────────────────────
        elements.append(Paragraph("MODEL GOVERNANCE & ARCHITECTURE TRACEABILITY", self.styles["SectionHeader"]))
        model_data = [
            [
                Paragraph("<b>Core Detection Model:</b>", self.styles["BodyMuted"]),
                Paragraph(str(report_data.get("model_name", "YuNet-DeepLearning-Face")), self.styles["BodyWhite"]),
                Paragraph("<b>Model Version:</b>", self.styles["BodyMuted"]),
                Paragraph(str(report_data.get("model_version", "v1.2.0")), self.styles["BodyWhite"]),
            ],
            [
                Paragraph("<b>Preprocessing Pipeline:</b>", self.styles["BodyMuted"]),
                Paragraph(str(report_data.get("preprocessing_version", "v1.2.0-spatial-fft")), self.styles["BodyWhite"]),
                Paragraph("<b>Fusion Engine:</b>", self.styles["BodyMuted"]),
                Paragraph(str(report_data.get("fusion_version", "v1.4.0-guided-multisignal")), self.styles["BodyWhite"]),
            ],
            [
                Paragraph("<b>Calibration Profile:</b>", self.styles["BodyMuted"]),
                Paragraph(str(report_data.get("calibration_version", "v1.2.5-temperature")), self.styles["BodyWhite"]),
                Paragraph("<b>Target Face Association:</b>", self.styles["BodyMuted"]),
                Paragraph(f"{report_data.get('target_face_id', 'Face 1')} of {report_data.get('faces_detected_count', 1)} detected", self.styles["BodyWhite"]),
            ],
        ]
        model_table = Table(model_data, colWidths=[120, 140, 120, 135])
        model_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_CARD),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_CARD_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#1A2234")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(model_table)
        elements.append(Spacer(1, 12))

        # ── 8. Mandatory Security Disclaimer Footer ───────────────────────────
        elements.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_CARD_BORDER, spaceBefore=4, spaceAfter=6))
        disclaimer = (
            "<b>STATUTORY NOTICE & SYSTEM LIMITATIONS:</b> "
            "Privacy Eye provides a probabilistic authenticity assessment derived from multi-signal mathematical algorithms. "
            "Results can contain false positives and false negatives under non-standard lighting, severe occlusions, or hardware variances. "
            "This report should not be treated as absolute proof of identity, authenticity, or malice, and must be corroborated by "
            "independent physical or credential verifications before initiating legal or punitive actions."
        )
        elements.append(Paragraph(disclaimer, self.styles["DisclaimerText"]))

        # Build Document
        doc.build(elements, canvasmaker=NumberedCanvas)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Sanity check
        if not pdf_bytes.startswith(b"%PDF"):
            raise ValueError("Generated document does not contain valid PDF header")

        logger.info("PDF scan report generated successfully", report_id=report_data.get("id"), bytes=len(pdf_bytes))
        return pdf_bytes


report_pdf_generator = ReportPdfGenerator()
