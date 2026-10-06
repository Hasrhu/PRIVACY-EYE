"""
Privacy Eye — Scan Report Image Generator (JPG)
Renders a polished, dark-glass branded single-page JPG report graphic
suitable for immediate sharing, presentation decks, or mobile viewing.
"""
import io
import os
import math
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import structlog

logger = structlog.get_logger(__name__)

# Dimensions
WIDTH = 1200
HEIGHT = 1600

# Color palette
BG_DARK = (11, 15, 25)           # Deep Obsidian #0B0F19
CARD_BG = (17, 24, 39)           # Dark Slate #111827
CARD_BORDER = (31, 41, 55)       # Slate Border #1F2937
ACCENT_BLUE = (59, 130, 246)     # #3B82F6
ACCENT_CYAN = (6, 182, 212)      # #06B6D4
ACCENT_VIOLET = (139, 92, 246)   # #8B5CF6
COLOR_SAFE = (16, 185, 129)      # #10B981
COLOR_WARN = (245, 158, 11)      # #F59E0B
COLOR_DANGER = (239, 68, 68)     # #EF4444
TEXT_WHITE = (249, 250, 251)
TEXT_MUTED = (156, 163, 175)
TEXT_DIM = (107, 114, 128)


def get_default_font(size: int = 16, bold: bool = False):
    """Attempts to load a standard system TrueType font or falls back cleanly."""
    font_names = [
        "arialbd.ttf" if bold else "arial.ttf",
        "segoeuib.ttf" if bold else "segoeui.ttf",
        "calibrib.ttf" if bold else "calibri.ttf",
        "Helvetica.ttf",
        "DejaVuSans.ttf",
    ]
    for fn in font_names:
        try:
            return ImageFont.truetype(fn, size)
        except Exception:
            continue
    return ImageFont.load_default()


class ReportImageGenerator:
    def generate_jpg(
        self,
        report_data: Dict[str, Any],
        face_img_bytes: Optional[bytes] = None,
    ) -> bytes:
        """
        Creates a high-definition branded JPG report card.
        """
        img = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
        draw = ImageDraw.Draw(img)

        # ── Decorative Cyber Grid & Radial Glow ──────────────────────────────
        # Subtle horizontal grid lines
        for y in range(0, HEIGHT, 80):
            draw.line([(0, y), (WIDTH, y)], fill=(16, 22, 35), width=1)
        for x in range(0, WIDTH, 80):
            draw.line([(x, 0), (x, HEIGHT)], fill=(16, 22, 35), width=1)

        # Ambient header glow
        draw.rectangle([40, 40, WIDTH - 40, 180], fill=CARD_BG, outline=CARD_BORDER, width=2)

        font_brand = get_default_font(32, bold=True)
        font_sub = get_default_font(15, bold=False)
        font_h1 = get_default_font(28, bold=True)
        font_h2 = get_default_font(20, bold=True)
        font_body = get_default_font(18, bold=False)
        font_small = get_default_font(14, bold=False)
        font_tiny = get_default_font(12, bold=False)

        # Brand Title
        draw.text((70, 65), "PRIVACY EYE", fill=ACCENT_CYAN, font=font_brand)
        draw.text((70, 115), "DIGITAL AUTHENTICITY & BIOMETRIC AUDIT REPORT", fill=TEXT_MUTED, font=font_sub)

        # Report ID & Date pill on top right
        rep_num = str(report_data.get("report_number", "PE-000000"))
        date_str = str(report_data.get("created_at_formatted") or report_data.get("created_at", "2026-10-06"))[:10]
        draw.rectangle([WIDTH - 360, 65, WIDTH - 70, 135], fill=(24, 32, 47), outline=ACCENT_BLUE, width=1)
        draw.text((WIDTH - 340, 75), f"ID: {rep_num}", fill=TEXT_WHITE, font=font_sub)
        draw.text((WIDTH - 340, 102), f"DATE: {date_str}", fill=TEXT_MUTED, font=font_small)

        # ── Evidence Card (Middle Left: Face, Middle Right: Result) ───────────
        face_box_x = 70
        face_box_y = 210
        face_box_w = 420
        face_box_h = 420

        # Face Card Background
        draw.rectangle(
            [face_box_x, face_box_y, face_box_x + face_box_w, face_box_y + face_box_h],
            fill=CARD_BG,
            outline=CARD_BORDER,
            width=2,
        )

        if face_img_bytes:
            try:
                with Image.open(io.BytesIO(face_img_bytes)) as face_raw:
                    face_rgb = face_raw.convert("RGB")
                    # Crop/fit into 380x380
                    face_thumb = face_rgb.resize((380, 380), Image.Resampling.LANCZOS)
                    img.paste(face_thumb, (face_box_x + 20, face_box_y + 20))
                    # Frame overlay
                    draw.rectangle(
                        [face_box_x + 20, face_box_y + 20, face_box_x + 400, face_box_y + 400],
                        outline=ACCENT_CYAN,
                        width=2,
                    )
            except Exception as e:
                logger.warning("Failed to render face in JPG generator", error=str(e))
                draw.text((face_box_x + 60, face_box_y + 190), "IMAGE RENDERING ERROR", fill=TEXT_MUTED, font=font_sub)
        else:
            draw.rectangle(
                [face_box_x + 20, face_box_y + 20, face_box_x + 400, face_box_y + 400],
                fill=(20, 27, 40),
                outline=CARD_BORDER,
                width=1,
            )
            draw.text((face_box_x + 80, face_box_y + 180), "ZERO-BIOMETRIC POLICY", fill=TEXT_MUTED, font=font_h2)
            draw.text((face_box_x + 90, face_box_y + 220), "No face image stored per consent", fill=TEXT_DIM, font=font_small)

        caption_txt = f"Analyzed Target: {report_data.get('target_face_id', 'Face 1')} (Evidence Frame)"
        draw.text((face_box_x + 20, face_box_y + face_box_h + 10), caption_txt, fill=TEXT_DIM, font=font_tiny)

        # ── Primary Result Box (Middle Right) ─────────────────────────────────
        res_box_x = 520
        res_box_y = 210
        res_box_w = WIDTH - 520 - 70
        res_box_h = 420

        conf_val = float(report_data.get("confidence", 0.0))
        reliability = str(report_data.get("reliability", "MEDIUM"))
        assessment = str(report_data.get("assessment", "LIKELY_LIVE_HUMAN")).replace("_", " ")

        if conf_val >= 80.0 and "REPLAY" not in assessment:
            status_color = COLOR_SAFE
            status_tag = "VERIFIED"
        elif conf_val >= 60.0 and "REPLAY" not in assessment:
            status_color = COLOR_WARN
            status_tag = "CAUTION"
        else:
            status_color = COLOR_DANGER
            status_tag = "ALERT"

        draw.rectangle(
            [res_box_x, res_box_y, res_box_x + res_box_w, res_box_y + res_box_h],
            fill=CARD_BG,
            outline=status_color,
            width=2,
        )

        draw.text((res_box_x + 35, res_box_y + 35), "FINAL INFERENCE ASSESSMENT", fill=ACCENT_CYAN, font=font_sub)
        
        # Large assessment banner
        draw.text((res_box_x + 35, res_box_y + 70), assessment.upper(), fill=TEXT_WHITE, font=font_h1)

        # Confidence and Reliability
        draw.text((res_box_x + 35, res_box_y + 140), "CALIBRATED CONFIDENCE", fill=TEXT_MUTED, font=font_small)
        draw.text((res_box_x + 35, res_box_y + 170), f"{conf_val:.1f}%", fill=status_color, font=ImageFont.truetype("arialbd.ttf" if os.name == "nt" else "arial.ttf", 54) if os.name == "nt" else font_h1)

        draw.text((res_box_x + 300, res_box_y + 140), "RELIABILITY LEVEL", fill=TEXT_MUTED, font=font_small)
        draw.text((res_box_x + 300, res_box_y + 185), reliability.upper(), fill=TEXT_WHITE, font=font_h2)

        # Separator line
        draw.line([(res_box_x + 35, res_box_y + 265), (res_box_x + res_box_w - 35, res_box_y + 265)], fill=CARD_BORDER, width=1)

        # Explanation blurb
        expl = str(report_data.get("explanation", "Verification completed with multi-signal biometric models."))
        if len(expl) > 160:
            expl = expl[:157] + "..."
        draw.text((res_box_x + 35, res_box_y + 290), expl, fill=TEXT_MUTED, font=font_small)

        # ── Why Reasons & Key Tests Section ───────────────────────────────────
        why_box_y = 660
        draw.rectangle([70, why_box_y, WIDTH - 70, why_box_y + 360], fill=CARD_BG, outline=CARD_BORDER, width=2)
        draw.text((105, why_box_y + 25), "WHY THIS RESULT WAS ASSIGNED (AUDIT SIGNALS)", fill=ACCENT_CYAN, font=font_h2)

        reasons = report_data.get("why_reasons") or [expl]
        cur_y = why_box_y + 75
        for r in reasons[:5]:
            # Emerald checkmark bullet
            draw.text((110, cur_y), "✓", fill=COLOR_SAFE, font=font_h2)
            draw.text((145, cur_y + 2), str(r), fill=TEXT_WHITE, font=font_body)
            cur_y += 52

        # ── Test Matrix Highlights Section ────────────────────────────────────
        test_box_y = 1050
        draw.rectangle([70, test_box_y, WIDTH - 70, test_box_y + 360], fill=CARD_BG, outline=CARD_BORDER, width=2)
        draw.text((105, test_box_y + 25), "FORENSIC VERIFICATION TESTS", fill=ACCENT_CYAN, font=font_h2)

        tests = report_data.get("tests", [])
        # Grid of test badges (2 columns x 4 rows)
        col1_x = 105
        col2_x = 640
        t_y = test_box_y + 75

        for i, t in enumerate(tests[:8]):
            is_col2 = (i % 2 == 1)
            cx = col2_x if is_col2 else col1_x
            if is_col2:
                ty = t_y
                t_y += 62
            else:
                ty = t_y

            t_name = str(t.get("test_name", "Test"))
            t_status = str(t.get("status", "PASS")).upper()
            badge_color = COLOR_SAFE if t_status == "PASS" else (COLOR_WARN if t_status == "WARNING" else COLOR_DANGER)

            # Badge pill
            draw.rectangle([cx, ty, cx + 90, ty + 36], fill=(24, 32, 47), outline=badge_color, width=1)
            draw.text((cx + 15, ty + 8), t_status, fill=badge_color, font=font_small)
            draw.text((cx + 105, ty + 8), t_name, fill=TEXT_WHITE, font=font_body)

        # ── Statutory Disclaimer Footer ───────────────────────────────────────
        footer_y = 1440
        draw.line([(70, footer_y), (WIDTH - 70, footer_y)], fill=CARD_BORDER, width=1)
        disclaimer = (
            "STATUTORY NOTICE: Privacy Eye provides probabilistic authenticity analysis. Results can produce false "
            "positives or negatives and must not be used as absolute proof of identity or malicious intent."
        )
        draw.text((70, footer_y + 20), disclaimer, fill=TEXT_DIM, font=font_tiny)
        models_info = (
            f"Core Model: {report_data.get('model_name', 'YuNet')} {report_data.get('model_version', 'v1.2.0')}  |  "
            f"Preprocessing: {report_data.get('preprocessing_version', 'v1.2.0')}  |  "
            f"Calibration: {report_data.get('calibration_version', 'v1.2.5')}"
        )
        draw.text((70, footer_y + 45), models_info, fill=TEXT_MUTED, font=font_tiny)

        # Convert to standard JPEG bytes
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=92, optimize=True)
        jpg_bytes = buf.getvalue()
        buf.close()

        logger.info("JPG scan report generated successfully", report_id=report_data.get("id"), bytes=len(jpg_bytes))
        return jpg_bytes


report_image_generator = ReportImageGenerator()
