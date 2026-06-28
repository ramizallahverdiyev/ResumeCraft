from dataclasses import dataclass, field, asdict
import json


@dataclass
class Experience:
    company: str = ""
    role: str = ""
    dates: str = ""
    start_date: str | None = None
    end_date: str | None = None
    description: list[str] = field(default_factory=list)
    technologies_used: list[str] = field(default_factory=list)


@dataclass
class Education:
    institution: str = ""
    degree: str = ""
    field: str = ""
    dates: str = ""


@dataclass
class Certification:
    name: str = ""
    issuer: str = ""
    date: str = ""


@dataclass
class Language:
    language: str = ""
    proficiency: str = ""


@dataclass
class CVData:
    personal_info: dict[str, str | None] = field(default_factory=lambda: {
        "name": None, "email": None, "phone": None,
        "location": None, "linkedin": None, "github": None,
    })
    professional_summary: str | None = None
    skills: dict[str, list[str]] = field(default_factory=lambda: {
        "technical": [], "soft": [],
    })
    experience: list[dict] = field(default_factory=list)
    education: list[dict] = field(default_factory=list)
    certifications: list[dict] = field(default_factory=list)
    languages: list[dict] = field(default_factory=list)
    parsing_confidence: dict = field(default_factory=lambda: {
        "score": 0.0, "inferred_fields": [],
    })

    @staticmethod
    def _migrate_from_old(d: dict) -> dict:
        """Handle old-format cv-data.json gracefully."""
        if isinstance(d.get("skills"), list):
            d["skills"] = {"technical": d["skills"], "soft": []}
        if "summary" in d and "professional_summary" not in d:
            d["professional_summary"] = d.pop("summary")
        if "languages" not in d:
            d["languages"] = []
        if "parsing_confidence" not in d:
            d["parsing_confidence"] = {"score": 0.0, "inferred_fields": []}
        if "github" not in d.get("personal_info", {}):
            if "personal_info" in d:
                d["personal_info"]["github"] = None
        return d

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "CVData":
        d = cls._migrate_from_old(d)
        return cls(
            personal_info=d.get("personal_info", {}),
            professional_summary=d.get("professional_summary"),
            skills=d.get("skills", {"technical": [], "soft": []}),
            experience=d.get("experience", []),
            education=d.get("education", []),
            certifications=d.get("certifications", []),
            languages=d.get("languages", []),
            parsing_confidence=d.get("parsing_confidence", {"score": 0.0, "inferred_fields": []}),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, s: str) -> "CVData":
        return cls.from_dict(json.loads(s))


@dataclass
class JDData:
    role: str | None = None
    company: str | None = None
    location: str | None = None
    employment_type: str | None = None
    seniority_level: str | None = None
    summary: str | None = None
    must_have: dict = field(default_factory=lambda: {
        "skills": [], "experience_years": None,
        "education": None, "qualifications": [],
    })
    nice_to_have: dict = field(default_factory=lambda: {
        "skills": [], "qualifications": [],
    })
    soft_skills: list[str] = field(default_factory=list)
    responsibilities: list[str] = field(default_factory=list)
    company_industry: str | None = None
    benefits: list[str] = field(default_factory=list)

    @staticmethod
    def _migrate_from_old(d: dict) -> dict:
        """Handle old-format jd-data.json gracefully."""
        if "requirements" in d and "must_have" not in d:
            d["must_have"] = {
                "skills": d.pop("requirements", []),
                "experience_years": None,
                "education": None,
                "qualifications": [],
            }
        if isinstance(d.get("nice_to_have"), list):
            d["nice_to_have"] = {
                "skills": d["nice_to_have"] if isinstance(d["nice_to_have"], list) else [],
                "qualifications": [],
            }
        for k in ("location", "employment_type", "seniority_level", "summary", "company_industry"):
            d.setdefault(k, None)
        d.setdefault("soft_skills", [])
        d.setdefault("benefits", [])
        return d

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "JDData":
        d = cls._migrate_from_old(d)
        return cls(
            role=d.get("role"),
            company=d.get("company"),
            location=d.get("location"),
            employment_type=d.get("employment_type"),
            seniority_level=d.get("seniority_level"),
            summary=d.get("summary"),
            must_have=d.get("must_have", {"skills": [], "experience_years": None, "education": None, "qualifications": []}),
            nice_to_have=d.get("nice_to_have", {"skills": [], "qualifications": []}),
            soft_skills=d.get("soft_skills", []),
            responsibilities=d.get("responsibilities", []),
            company_industry=d.get("company_industry"),
            benefits=d.get("benefits", []),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, s: str) -> "JDData":
        return cls.from_dict(json.loads(s))


@dataclass
class OptimizeResult:
    optimized_cv: dict
    changes: list[str]
    pdf_script: str = ""
    ats_score_estimate: dict | None = None
