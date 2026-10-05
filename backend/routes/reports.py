"""
routes/reports.py — PDF incident report generation and retrieval.
"""
from fastapi import APIRouter, Depends, HTTPException, Response
from bson import ObjectId
from datetime import datetime, timezone, timedelta
import io

from database import get_users_collection, get_activities_collection, get_alerts_collection, get_reports_collection
from middleware.auth import require_analyst_or_admin

router = APIRouter()


@router.get("/generate/{user_id}")
async def generate_report(
    user_id: str,
    current_user: dict = Depends(require_analyst_or_admin),
):
    """
    Generate a PDF incident investigation report for a specific user.
    Includes: risk score, activity timeline, SHAP explanations, recommended actions.
    """
    users_col = get_users_collection()
    activities_col = get_activities_collection()
    alerts_col = get_alerts_collection()
    reports_col = get_reports_collection()

    # Fetch user
    try:
        user = await users_col.find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch recent activities and alerts
    since = datetime.now(timezone.utc) - timedelta(days=30)
    activities = await activities_col.find(
        {"user_id": user_id, "timestamp": {"$gte": since}}
    ).sort("timestamp", -1).to_list(length=50)

    alerts = await alerts_col.find(
        {"user_id": user_id}
    ).sort("timestamp", -1).to_list(length=20)

    # Generate PDF
    pdf_bytes = _generate_pdf_report(user, activities, alerts)

    # Save report record
    report_doc = {
        "user_id": user_id,
        "generated_by": str(current_user["_id"]),
        "generated_at": datetime.now(timezone.utc),
        "filename": f"incident_report_{user.get('username', user_id)}_{datetime.now().strftime('%Y%m%d')}.pdf",
    }
    await reports_col.insert_one(report_doc)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"{report_doc['filename']}\"",
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.get("/list", response_model=dict)
async def list_reports(current_user: dict = Depends(require_analyst_or_admin)):
    """List all generated reports."""
    reports_col = get_reports_collection()
    users_col = get_users_collection()

    reports = await reports_col.find({}).sort("generated_at", -1).to_list(length=50)

    result = []
    for r in reports:
        try:
            user = await users_col.find_one({"_id": ObjectId(r["user_id"])})
            username = user["username"] if user else "Unknown"
        except Exception:
            username = "Unknown"
        result.append({
            "id": str(r["_id"]),
            "user_id": r["user_id"],
            "username": username,
            "filename": r.get("filename", "report.pdf"),
            "generated_at": r["generated_at"].isoformat(),
        })

    return {"reports": result, "total": len(result)}


# ─── PDF Generation ────────────────────────────────────────────────────────────

def _generate_pdf_report(user: dict, activities: list, alerts: list) -> bytes:
    """Generate a professional PDF incident report using ReportLab."""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
            HRFlowable, PageBreak
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    except ImportError:
        raise HTTPException(status_code=503, detail="reportlab not installed")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)

    styles = getSampleStyleSheet()
    elements = []

    # ── Color palette ─────────────────────────────────────────────────
    dark_bg = colors.HexColor("#0f172a")
    accent = colors.HexColor("#6366f1")
    danger = colors.HexColor("#ef4444")
    warning = colors.HexColor("#f59e0b")
    success = colors.HexColor("#10b981")
    text_primary = colors.HexColor("#1e293b")
    text_secondary = colors.HexColor("#475569")

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Title"],
        fontSize=22, textColor=dark_bg, spaceAfter=6,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=11, textColor=text_secondary, spaceAfter=20,
    )
    section_style = ParagraphStyle(
        "Section", parent=styles["Heading2"],
        fontSize=13, textColor=accent, spaceBefore=16, spaceAfter=8,
        fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, textColor=text_primary, spaceAfter=6,
    )

    # ── Header ───────────────────────────────────────────────────────
    elements.append(Paragraph("🔐 INSIDER THREAT INTELLIGENCE PLATFORM", title_style))
    elements.append(Paragraph("AI-Powered Security Incident Investigation Report", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=accent))
    elements.append(Spacer(1, 12))

    # ── User Summary ──────────────────────────────────────────────────
    elements.append(Paragraph("User Profile Summary", section_style))

    risk_score = user.get("risk_score", 0.0)
    risk_level = user.get("risk_level", "LOW")
    risk_color = danger if risk_level == "HIGH" else warning if risk_level == "MEDIUM" else success

    user_data = [
        ["Field", "Value"],
        ["Full Name", user.get("full_name", "N/A")],
        ["Username", user.get("username", "N/A")],
        ["Email", user.get("email", "N/A")],
        ["Department", user.get("department", "N/A")],
        ["Role", user.get("role", "N/A").upper()],
        ["Account Status", "Active" if user.get("is_active", True) else "Disabled"],
        ["Risk Score", f"{risk_score:.1f} / 100"],
        ["Threat Level", risk_level],
        ["Last Login", str(user.get("last_login", "N/A"))[:19]],
        ["Report Date", datetime.now().strftime("%Y-%m-%d %H:%M UTC")],
    ]

    user_table = Table(user_data, colWidths=[2.5*inch, 4*inch])
    user_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), dark_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(user_table)
    elements.append(Spacer(1, 16))

    # ── Risk Analysis ─────────────────────────────────────────────────
    elements.append(Paragraph("Risk Assessment", section_style))
    elements.append(Paragraph(
        f"This user has been assessed with a <b>{risk_level}</b> threat level based on behavioral "
        f"analytics over the past 30 days. The dynamic risk score of <b>{risk_score:.1f}/100</b> "
        f"was calculated using an ensemble of Machine Learning models including Random Forest, "
        f"XGBoost, and Isolation Forest, with SHAP-based explainability.",
        body_style,
    ))
    elements.append(Spacer(1, 8))

    # ── Activity Timeline ─────────────────────────────────────────────
    elements.append(Paragraph("Recent Activity Timeline (Last 30 Days)", section_style))

    if activities:
        act_data = [["Timestamp", "Event Type", "Sensitivity", "After Hours", "Risk"]]
        for act in activities[:20]:
            ts = act.get("timestamp", datetime.now())
            if hasattr(ts, "strftime"):
                ts_str = ts.strftime("%Y-%m-%d %H:%M")
            else:
                ts_str = str(ts)[:16]
            act_data.append([
                ts_str,
                act.get("event_type", "").replace("_", " ").title(),
                act.get("sensitivity_level", "low").upper(),
                "Yes" if act.get("is_after_hours") else "No",
                f"+{act.get('risk_contribution', 0):.0f}",
            ])

        act_table = Table(act_data, colWidths=[1.5*inch, 1.8*inch, 1.2*inch, 1.1*inch, 0.8*inch])
        act_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), dark_bg),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(act_table)
    else:
        elements.append(Paragraph("No activity records found for this period.", body_style))

    elements.append(Spacer(1, 16))

    # ── Alerts Summary ────────────────────────────────────────────────
    elements.append(Paragraph("Security Alerts", section_style))

    if alerts:
        alert_data = [["Date", "Alert Type", "Severity", "Status"]]
        for alert in alerts[:10]:
            ts = alert.get("timestamp", datetime.now())
            ts_str = ts.strftime("%Y-%m-%d") if hasattr(ts, "strftime") else str(ts)[:10]
            alert_data.append([
                ts_str,
                alert.get("alert_type", "").replace("_", " ").title(),
                alert.get("severity", "").upper(),
                alert.get("status", "open").upper(),
            ])

        alert_table = Table(alert_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 1.5*inch])
        alert_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), dark_bg),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fff7ed")]),
        ]))
        elements.append(alert_table)
    else:
        elements.append(Paragraph("No alerts generated for this user.", body_style))

    elements.append(Spacer(1, 16))

    # ── Recommended Actions ────────────────────────────────────────────
    elements.append(Paragraph("Recommended Investigative Actions", section_style))
    actions = []
    if risk_level == "HIGH":
        actions = [
            "1. Immediately escalate to the Security Operations Center (SOC).",
            "2. Suspend user account access pending full investigation.",
            "3. Preserve all digital evidence and logs.",
            "4. Notify HR and Legal departments.",
            "5. Conduct forensic analysis of the user's endpoints.",
            "6. Review all file transfers and USB device logs.",
            "7. Interview user's manager and colleagues.",
        ]
    elif risk_level == "MEDIUM":
        actions = [
            "1. Increase monitoring intensity for this user.",
            "2. Schedule a review meeting with the user's manager.",
            "3. Audit recent file access and download history.",
            "4. Enforce multi-factor authentication.",
            "5. Review and tighten data access permissions.",
        ]
    else:
        actions = [
            "1. Continue standard monitoring procedures.",
            "2. Ensure security awareness training is up to date.",
            "3. Periodic review scheduled in 30 days.",
        ]

    for action in actions:
        elements.append(Paragraph(action, body_style))

    elements.append(Spacer(1, 16))

    # ── Footer ────────────────────────────────────────────────────────
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0")))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        f"Generated by AI Insider Threat Intelligence Platform | "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M UTC')} | CONFIDENTIAL",
        ParagraphStyle("Footer", fontSize=8, textColor=text_secondary, alignment=TA_CENTER),
    ))

    doc.build(elements)
    return buffer.getvalue()
