from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, HRFlowable, Table, TableStyle

BULLET = "\u2022"
BULLET_SEP = " \u00b7 "
DASH = " \u2014 "

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm


def render_pdf(cv_data: dict, output_path: str) -> str | None:
    try:
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=MARGIN,
            rightMargin=MARGIN,
            topMargin=MARGIN,
            bottomMargin=MARGIN,
        )
        story = []
        s = _styles()

        pi = cv_data.get("personal_info", {})

        # Name
        if pi.get("name"):
            story.append(Paragraph(pi["name"], s["name"]))

        # Contact
        contact = [str(pi[k]) for k in ("email", "phone", "location") if pi.get(k)]
        if contact:
            story.append(Paragraph(BULLET_SEP.join(contact), s["contact"]))

        # Links (clickable)
        links = []
        if pi.get("linkedin"):
            links.append(f'<a href="{pi["linkedin"]}" color="#2563eb">LinkedIn</a>')
        if pi.get("github"):
            links.append(f'<a href="{pi["github"]}" color="#2563eb">GitHub</a>')
        if links:
            story.append(Paragraph(BULLET_SEP.join(links), s["contact"]))

        # Summary
        summary = cv_data.get("professional_summary") or cv_data.get("summary", "")
        if summary:
            story.append(_rule())
            story.append(Paragraph("Professional Summary", s["section"]))
            story.append(Paragraph(summary, s["body"]))

        # Skills
        skills = cv_data.get("skills", {})
        tech = skills.get("technical", []) if isinstance(skills, dict) else (skills if isinstance(skills, list) else [])
        soft = skills.get("soft", []) if isinstance(skills, dict) else []
        if tech or soft:
            story.append(_rule())
            story.append(Paragraph("Skills", s["section"]))
            if tech:
                story.append(Paragraph(f'<b>Technical:</b> {", ".join(tech)}', s["body"]))
            if soft:
                story.append(Paragraph(f'<b>Soft:</b> {", ".join(soft)}', s["body"]))

        # Experience
        if cv_data.get("experience"):
            story.append(_rule())
            story.append(Paragraph("Experience", s["section"]))
            for exp in cv_data["experience"]:
                left = f'<b>{exp.get("role", "")}</b>'
                if exp.get("company"):
                    left += f" at {exp['company']}"
                right = exp.get("dates", "")
                t = Table(
                    [[Paragraph(left, s["exp_left"]), Paragraph(right, s["exp_right"])]],
                    colWidths=[PAGE_W - 2 * MARGIN - 50 * mm, 50 * mm],
                )
                t.setStyle(
                    TableStyle([
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ])
                )
                story.append(t)
                for d in exp.get("description", []):
                    story.append(Paragraph(f"{BULLET} {d}", s["bullet"]))

        # Education
        if cv_data.get("education"):
            story.append(_rule())
            story.append(Paragraph("Education", s["section"]))
            for edu in cv_data["education"]:
                degree = edu.get("degree", "") or ""
                field = edu.get("field", "") or ""
                inst = edu.get("institution", "") or ""
                dates = edu.get("dates", "") or ""
                parts = []
                if degree:
                    parts.append(f"<b>{degree}</b>")
                if field:
                    parts.append(f"in {field}")
                if inst:
                    parts.append(inst)
                if dates:
                    parts.append(dates)
                if parts:
                    story.append(Paragraph(DASH.join(parts), s["body"]))

        # Certifications
        certs = [c for c in cv_data.get("certifications", []) if c.get("name")]
        if certs:
            story.append(_rule())
            story.append(Paragraph("Certifications", s["section"]))
            for c in certs:
                parts = [p for p in [c.get("name", ""), c.get("issuer", ""), c.get("date", "")] if p]
                if parts:
                    story.append(Paragraph(f"{BULLET} {DASH.join(parts)}", s["bullet"]))

        # Languages
        langs = [l for l in cv_data.get("languages", []) if l.get("language")]
        if langs:
            story.append(_rule())
            story.append(Paragraph("Languages", s["section"]))
            parts = []
            for l in langs:
                p = [p for p in [l.get("language", ""), l.get("proficiency", "")] if p]
                if p:
                    parts.append(" ".join(p))
            if parts:
                story.append(Paragraph(BULLET_SEP.join(parts), s["body"]))

        doc.build(story)
        return None
    except Exception as e:
        return str(e)


def _styles():
    return {
        "name": ParagraphStyle(
            "Name", fontSize=20, leading=24,
            textColor=HexColor("#1a1a1a"),
            alignment=TA_CENTER, spaceAfter=2 * mm,
            fontName="Helvetica-Bold",
        ),
        "contact": ParagraphStyle(
            "Contact", fontSize=9, leading=12,
            textColor=HexColor("#555555"),
            alignment=TA_CENTER, spaceAfter=1 * mm,
        ),
        "section": ParagraphStyle(
            "Section", fontSize=10, leading=12,
            textColor=HexColor("#2563eb"),
            fontName="Helvetica-Bold",
            spaceBefore=4 * mm, spaceAfter=2 * mm,
        ),
        "body": ParagraphStyle(
            "Body", fontSize=10, leading=14,
            textColor=HexColor("#333333"),
            spaceAfter=2 * mm,
            alignment=TA_JUSTIFY,
        ),
        "bullet": ParagraphStyle(
            "Bullet", fontSize=10, leading=14,
            textColor=HexColor("#333333"),
            leftIndent=4 * mm,
            spaceAfter=1 * mm,
        ),
        "exp_left": ParagraphStyle(
            "ExpLeft", fontSize=10, leading=13,
            textColor=HexColor("#1a1a1a"),
            spaceAfter=1 * mm,
        ),
        "exp_right": ParagraphStyle(
            "ExpRight", fontSize=9, leading=13,
            textColor=HexColor("#777777"),
            alignment=TA_RIGHT,
        ),
    }


def _rule():
    return HRFlowable(width="100%", thickness=0.5, color=HexColor("#dddddd"))
