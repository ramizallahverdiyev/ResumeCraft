import json
from app.models import CVData, JDData
from app.ai import AIProvider

CV_SYSTEM_PROMPT = """You are a precise CV/resume parser. Extract structured information from the CV text and return valid JSON.

RULES:
- Only extract information explicitly stated in the text — never fabricate or infer experience
- If a field is not present, use null (not empty string)
- Normalize dates to YYYY-MM format when possible
- List skills as individual items, never comma-separated strings in one entry
- Extract both spelled-out terms AND acronyms when both appear (e.g. "Continuous Integration (CI)")
- Differentiate technical skills from soft skills
- For experience descriptions, preserve each achievement as a separate bullet point
- Infer degree field from degree name if not explicitly listed
- Translate all extracted text to English — names, titles, companies, descriptions must be in English

Return EXACTLY this JSON structure (no markdown, no code fences, no extra text):
{
  "personal_info": {
    "name": null,
    "email": null,
    "phone": null,
    "location": null,
    "linkedin": null,
    "github": null
  },
  "professional_summary": null,
  "skills": {
    "technical": [],
    "soft": []
  },
  "experience": [
    {
      "company": null,
      "role": null,
      "dates": null,
      "start_date": null,
      "end_date": null,
      "description": [],
      "technologies_used": []
    }
  ],
  "education": [
    {
      "institution": null,
      "degree": null,
      "field": null,
      "dates": null
    }
  ],
  "certifications": [
    {
      "name": null,
      "issuer": null,
      "date": null
    }
  ],
  "languages": [
    {
      "language": null,
      "proficiency": null
    }
  ],
  "parsing_confidence": {
    "score": 0.0,
    "inferred_fields": []
  }
}

Fill all fields you can find. Be thorough and accurate."""

JD_SYSTEM_PROMPT = """You are a precise job description parser. Extract structured information from the job posting text.

EXTRACTION PROCESS:
1. First, identify all technical skills, tools, and technologies mentioned
2. Then, classify each by intent: must-have (required), nice-to-have (preferred), or soft skill
3. Extract role metadata (seniority, employment type, location)
4. Extract responsibilities as distinct bullet points
5. Extract education requirements (degree level, field)

RULES:
- Distinguish must-have from nice-to-have — do not conflate them
- If a field is not mentioned, use null
- Extract years of experience when specified
- Identify seniority level from title and requirements
- Preserve exact skill names as written (including version numbers e.g. "Python 3.11")
- Translate all extracted fields to English — role, company, responsibilities, skills, qualifications, etc. must be in English regardless of the input language

Return EXACTLY this JSON (no markdown, no code fences):
{
  "role": null,
  "company": null,
  "location": null,
  "employment_type": null,
  "seniority_level": null,
  "summary": null,
  "must_have": {
    "skills": [],
    "experience_years": null,
    "education": null,
    "qualifications": []
  },
  "nice_to_have": {
    "skills": [],
    "qualifications": []
  },
  "soft_skills": [],
  "responsibilities": [],
  "company_industry": null,
  "benefits": []
}

Be thorough and accurate."""


def parse_cv(raw_text: str, ai: AIProvider) -> CVData:
    response = ai.chat(
        messages=[{"role": "user", "content": raw_text}],
        system_prompt=CV_SYSTEM_PROMPT,
        format="json",
    )
    response = response.strip()
    if response.startswith("```"):
        lines = [l for l in response.splitlines() if not l.startswith("```")]
        response = "\n".join(lines)

    data = json.loads(response)
    return CVData.from_dict(data)


def parse_jd(jd_text: str, ai: AIProvider) -> JDData:
    response = ai.chat(
        messages=[{"role": "user", "content": jd_text}],
        system_prompt=JD_SYSTEM_PROMPT,
        format="json",
    )
    response = response.strip()
    if response.startswith("```"):
        lines = [l for l in response.splitlines() if not l.startswith("```")]
        response = "\n".join(lines)
    data = json.loads(response)
    return JDData.from_dict(data)


def _get_skills(cv: CVData) -> list[str]:
    skills = cv.skills or {}
    if isinstance(skills, dict):
        result = []
        if skills.get("technical"):
            result.extend(skills["technical"])
        if skills.get("soft"):
            result.extend(skills["soft"])
        return result
    if isinstance(skills, list):
        return skills
    return []


def cv_to_markdown(cv: CVData) -> str:
    lines = []
    pi = cv.personal_info
    if pi.get("name"):
        lines.append(f"# {pi['name']}")
    info_parts = [pi.get(k, "") for k in ("email", "phone", "location") if pi.get(k)]
    if info_parts:
        lines.append(" | ".join(info_parts))
    lines.append("")
    summary = cv.professional_summary or ""
    if summary:
        lines.append("## Summary")
        lines.append(summary)
        lines.append("")
    skill_list = _get_skills(cv)
    if skill_list:
        lines.append("## Skills")
        lines.append(", ".join(skill_list))
        lines.append("")
    if cv.experience:
        lines.append("## Experience")
        for exp in cv.experience:
            e = exp if isinstance(exp, dict) else exp.__dict__
            header = e.get("role", "")
            if e.get("company"):
                header += f" at {e['company']}"
            if e.get("dates"):
                header += f" ({e['dates']})"
            if header:
                lines.append(f"### {header}")
            for d in e.get("description", []):
                lines.append(f"- {d}")
        lines.append("")
    if cv.education:
        lines.append("## Education")
        for edu in cv.education:
            e = edu if isinstance(edu, dict) else edu.__dict__
            parts = []
            if e.get("degree"):
                parts.append(e["degree"])
                if e.get("field"):
                    parts[-1] += f" in {e['field']}"
            if e.get("institution"):
                parts.append(e["institution"])
            if e.get("dates"):
                parts.append(e["dates"])
            if parts:
                lines.append(f"- {' — '.join(parts)}")
        lines.append("")
    if cv.certifications:
        lines.append("## Certifications")
        for cert in cv.certifications:
            c = cert if isinstance(cert, dict) else cert.__dict__
            parts = [p for p in [c.get("name"), c.get("issuer"), c.get("date")] if p]
            if parts:
                lines.append(f"- {' — '.join(parts)}")
    if cv.languages:
        lines.append("## Languages")
        for lang in cv.languages:
            l = lang if isinstance(lang, dict) else lang.__dict__
            parts = [p for p in [l.get("language"), l.get("proficiency")] if p]
            if parts:
                lines.append(f"- {' — '.join(parts)}")
    return "\n".join(lines)
