"""
Report service — generates AI-powered evidence reports using Gemini.
Falls back to structured template if Gemini is unavailable.
"""
import uuid
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import MediaAnalysis, Report, AnalysisSignal
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)


class ReportService:
    async def generate(
        self, db: AsyncSession, analysis: MediaAnalysis, user
    ) -> Report:
        """Generate a structured evidence report, optionally enhanced by Gemini AI."""

        from sqlalchemy import select
        signals = await db.execute(
            select(AnalysisSignal)
            .where(AnalysisSignal.analysis_id == analysis.id)
        )
        signal_list = signals.scalars().all()

        # Build structured data for the report
        signal_data = [
            {
                "key": s.signal_key,
                "label": s.signal_label,
                "severity": s.severity,
                "score": s.score,
                "description": s.description,
            }
            for s in signal_list
        ]

        risk_emoji = {
            "LOW": "🟢",
            "SUSPICIOUS": "🟡",
            "HIGH": "🟠",
            "CRITICAL": "🔴",
            "UNDETERMINED": "⚪",
        }.get(analysis.risk_level.value if analysis.risk_level else "UNDETERMINED", "⚪")

        summary, recommendations = await self._generate_with_gemini(analysis, signal_data)

        report_json = {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": "Privacy Eye Analysis Engine v1.0.0-mvp",
            "file": {
                "original_filename": analysis.original_filename,
                "media_type": analysis.media_type.value,
                "file_size_bytes": analysis.file_size_bytes,
                "sha256": analysis.file_sha256,
                "mime_type": analysis.mime_type,
            },
            "assessment": {
                "risk_level": analysis.risk_level.value if analysis.risk_level else "UNDETERMINED",
                "risk_emoji": risk_emoji,
                "synthetic_probability": analysis.synthetic_probability,
                "confidence": analysis.confidence,
                "explanation": analysis.explanation,
            },
            "detected_signals": signal_data,
            "provenance": analysis.provenance_info or {},
            "raw_scores": analysis.raw_scores or {},
            "model": {
                "version": "1.0.0-mvp",
                "name": "PrivacyEye-Ensemble-v1",
                "disclaimer": (
                    "This report presents probabilistic indicators only. "
                    "Privacy Eye does not claim 100% accuracy. "
                    "Do not use this report as the sole basis for legal or disciplinary action. "
                    "Always apply human judgment."
                ),
            },
            "summary": summary,
            "recommendations": recommendations,
        }

        report = Report(
            id=str(uuid.uuid4()),
            user_id=user.id,
            analysis_id=analysis.id,
            title=f"Privacy Eye Report — {analysis.original_filename}",
            summary=summary,
            recommendations=recommendations,
            report_json=report_json,
        )
        db.add(report)
        await db.flush()
        await db.refresh(report)
        return report

    async def _generate_with_gemini(self, analysis: MediaAnalysis, signals: list) -> tuple[str, str]:
        """Use Gemini to write human-readable summary and recommendations."""
        if not settings.GEMINI_API_KEY:
            return self._fallback_summary(analysis, signals), self._fallback_recommendations(analysis)

        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)

            prompt = f"""You are the Privacy Eye Report Agent — an AI assistant that helps users understand deepfake and synthetic media detection results.

Analysis Data:
- File: {analysis.original_filename}
- Media Type: {analysis.media_type.value}
- Risk Level: {analysis.risk_level.value if analysis.risk_level else 'UNDETERMINED'}
- Synthetic Probability: {f'{analysis.synthetic_probability:.2%}' if analysis.synthetic_probability is not None else 'N/A'}
- Confidence: {f'{analysis.confidence:.2%}' if analysis.confidence is not None else 'N/A'}
- Detected Signals: {json.dumps(signals, indent=2)}

Write two sections:

SUMMARY (2-3 sentences): Explain in plain language what was found. Use cautious, probabilistic language. Never say "definitely fake" — say "indicators suggest" or "the system detected signals consistent with".

RECOMMENDATIONS (3-5 bullet points): What should the user do next? Consider: verifying with additional sources, contacting platform support, preserving evidence, not sharing the content, seeking expert review.

Format your response as JSON:
{{"summary": "...", "recommendations": "..."}}"""

            response = model.generate_content(prompt)
            text = response.text.strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            parsed = json.loads(text)
            return parsed.get("summary", ""), parsed.get("recommendations", "")

        except Exception as e:
            logger.warning("Gemini report generation failed", error=str(e))
            return self._fallback_summary(analysis, signals), self._fallback_recommendations(analysis)

    def _fallback_summary(self, analysis: MediaAnalysis, signals: list) -> str:
        risk = analysis.risk_level.value if analysis.risk_level else "UNDETERMINED"
        prob = f"{analysis.synthetic_probability:.0%}" if analysis.synthetic_probability is not None else "unknown"
        sig_count = len(signals)
        return (
            f"Privacy Eye analyzed this {analysis.media_type.value.lower()} and detected a {risk} risk level "
            f"with a synthetic media probability of {prob}. "
            f"{sig_count} indicator(s) were flagged during analysis. "
            f"These results represent probabilistic signals only and should not be treated as conclusive evidence."
        )

    def _fallback_recommendations(self, analysis: MediaAnalysis) -> str:
        risk = analysis.risk_level.value if analysis.risk_level else "UNDETERMINED"
        if risk in ("HIGH", "CRITICAL"):
            return (
                "• Do not share this media until authenticity is confirmed.\n"
                "• Preserve the original file and this report as evidence.\n"
                "• Consider reporting to the platform where you received this content.\n"
                "• Seek expert forensic review for legal or sensitive matters.\n"
                "• Contact relevant authorities if this involves potential fraud or impersonation."
            )
        elif risk == "SUSPICIOUS":
            return (
                "• Verify the source of this media through independent channels.\n"
                "• Be cautious about sharing until authenticity is clearer.\n"
                "• Save this report for your records.\n"
                "• Consider a second opinion from a digital forensics expert."
            )
        else:
            return (
                "• No strong synthetic indicators were found, but remain vigilant.\n"
                "• Verify content through trusted sources before acting on it.\n"
                "• Save this report for your records."
            )


report_service = ReportService()
